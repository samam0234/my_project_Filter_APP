#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LoRA fine-tuning 진입점 (Phase 2).

의도:
  - 피드백/의사라벨 JSON → 프롬프트 분석기용 instruction 어댑터
  - 산출물은 training/outputs/lora/<run>/adapter/ 에만 저장 (베이스 모델 재배포 없음)
  - YOLO 세그 본선 학습은 training/yolo/ 를 사용

실행:
  python training/lora/train_lora.py --dry-run
  python training/lora/train_lora.py --base-model training/models/qwen2.5-1.5b-instruct --name instance_v1
  python training/lora/eval_parser.py --adapter training/outputs/lora/instance_v1/adapter  # 평가

데이터:
  - seed/train.jsonl : 인스턴스 선택·물체 지우기 시드 (seed/build_seed.py 로 생성)
  - data/feedback    : 사용자 피드백 (like / dislike+정답 JSON 코멘트)
  - data/pseudo_labels : 단순 "X만 크롭" 계열 — --max-pseudo 로 샘플링 (selector 학습 희석 방지)
"""

from __future__ import annotations

import argparse
import random
import sys
from datetime import datetime
from pathlib import Path

_LORA_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _LORA_DIR.parents[1]
if str(_LORA_DIR) not in sys.path:
    sys.path.insert(0, str(_LORA_DIR))

from dataset import (  # noqa: E402
    DEFAULT_INSTRUCTION_TEMPLATE,
    args_to_jsonable,
    discover_feedback_cases,
    discover_pseudo_cases,
    discover_seed_cases,
    summarize_cases,
    to_instruction_records,
    write_run_manifest,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="LoRA fine-tune (Phase 2)")
    parser.add_argument(
        "--feedback-dir",
        type=Path,
        default=_REPO_ROOT / "data" / "feedback",
        help="피드백 이미지+JSON 디렉터리",
    )
    parser.add_argument(
        "--pseudo-dir",
        type=Path,
        default=_REPO_ROOT / "data" / "pseudo_labels",
        help="의사 라벨 디렉터리",
    )
    parser.add_argument(
        "--seed-file",
        type=Path,
        default=_LORA_DIR / "seed" / "train.jsonl",
        help="인스턴스 선택 시드 JSONL (없으면 건너뜀)",
    )
    parser.add_argument(
        "--seed-repeat",
        type=int,
        default=2,
        help="시드 데이터 반복 횟수 (selector 예제 비중 확보)",
    )
    parser.add_argument(
        "--max-pseudo",
        type=int,
        default=600,
        help="의사 라벨 최대 사용 수 (-1 = 전부, 0 = 사용 안 함)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=_LORA_DIR.parent / "outputs" / "lora",
        help="어댑터 출력 루트 (하위에 run 폴더 생성)",
    )
    parser.add_argument("--name", default="", help="run 이름 (기본: 시각 스탬프)")
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--lr", type=float, default=2e-4)
    parser.add_argument("--batch", type=int, default=4)
    parser.add_argument(
        "--grad-accum",
        type=int,
        default=2,
        help="gradient accumulation 단계 (실효 배치 = batch × grad-accum)",
    )
    parser.add_argument(
        "--no-grad-checkpoint",
        action="store_true",
        help="gradient checkpointing 끄기 (VRAM 여유 있을 때 속도↑)",
    )
    parser.add_argument("--rank", type=int, default=16, help="LoRA rank r")
    parser.add_argument("--max-seq-len", type=int, default=320)
    parser.add_argument(
        "--base-model",
        default="",
        help="로컬 HuggingFace 형식 체크포인트 경로 (Ollama GGUF 불가)",
    )
    parser.add_argument(
        "--target-modules",
        default="q_proj,k_proj,v_proj,o_proj",
        help="LoRA 를 붙일 모듈 이름 (쉼표 구분)",
    )
    parser.add_argument(
        "--device",
        default="",
        help="cuda / cpu / cuda:0 (빈 값이면 자동)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="학습 없이 데이터 계약만 검증하고 run.json 저장",
    )
    parser.add_argument(
        "--skip-pipeline-failure",
        action="store_true",
        help="pipeline_failure 약한 정답을 학습에서 제외",
    )
    parser.add_argument(
        "--local-files-only",
        action="store_true",
        default=True,
        help="허브에서 베이스 모델을 받지 않음 (기본 True)",
    )
    return parser.parse_args()


def _run_dir(output: Path, name: str) -> Path:
    stamp = name.strip() or datetime.now().strftime("%Y%m%d_%H%M%S")
    path = output / stamp
    path.mkdir(parents=True, exist_ok=True)
    return path


def _pick_device(requested: str):
    try:
        import torch
    except ImportError as exc:
        raise SystemExit(
            "torch 가 필요합니다. training venv 에서 로컬 wheel 로 설치하세요."
        ) from exc
    if requested:
        return torch.device(requested)
    return torch.device("cuda" if torch.cuda.is_available() else "cpu")


def _print_summary(title: str, feedback_n: int, pseudo_n: int, summary: dict) -> None:
    print(f"=== {title} ===")
    print(f"feedback_cases = {feedback_n}")
    print(f"pseudo_cases   = {pseudo_n}")
    print(f"records        = {summary.get('records')}")
    print(f"skipped        = {summary.get('skipped')}")
    print(f"with_image     = {summary.get('with_image')}")
    print(f"votes          = {summary.get('votes')}")


def _resolve_target_modules(model, requested: list[str]) -> list[str]:
    suffixes = {name.split(".")[-1] for name, _ in model.named_modules()}
    found = [m for m in requested if m in suffixes]
    if found:
        return found
    sample = ", ".join(sorted(s for s in suffixes if s)[:40])
    raise SystemExit(
        f"target_modules {requested} 를 모델에서 찾지 못했습니다.\n"
        f"named_modules 접미사 예: {sample}\n"
        f"--target-modules 로 맞춰 주세요."
    )


def train_adapter(
    args: argparse.Namespace,
    samples: list[tuple[str, str]],
    run_dir: Path,
) -> Path:
    """PEFT LoRA 학습 후 adapter 디렉터리 경로를 반환한다.

    samples: (prefix, full_text) — prefix(지시+프롬프트) 토큰은 loss 에서 제외하고
    응답 JSON 토큰에만 학습한다. 지시문을 외우는 대신 변환만 배우게 하기 위함.
    """
    try:
        import torch
        from torch.utils.data import DataLoader, Dataset
        from transformers import AutoModelForCausalLM, AutoTokenizer
        from peft import LoraConfig, TaskType, get_peft_model
    except ImportError as exc:
        print("필수 의존성이 없습니다. training/requirements-training.txt 의 LoRA 줄을 확인하세요.")
        print("  pip install peft transformers accelerate")
        print(f"import error: {exc}")
        raise SystemExit(1) from exc

    base = Path(args.base_model).expanduser()
    if not args.base_model or not base.exists():
        raise SystemExit(
            "--base-model 에 로컬 HuggingFace 체크포인트 디렉터리(config.json + 가중치)를 주세요.\n"
            "Ollama gemma4:e4b 는 GGUF 이라 PEFT 학습에 바로 쓰지 못합니다.\n"
            "허브 자동 다운로드는 하지 않습니다 (용량·네트워크 가드)."
        )

    device = _pick_device(args.device)
    local_only = bool(args.local_files_only)
    print(f"base-model = {base}")
    print(f"device     = {device}")
    print(
        f"epochs={args.epochs} lr={args.lr} batch={args.batch}x{args.grad_accum} "
        f"rank={args.rank} grad_checkpoint={not args.no_grad_checkpoint}"
    )

    tokenizer = AutoTokenizer.from_pretrained(str(base), local_files_only=local_only)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    # bf16 이 되면 bf16 (fp16 은 LoRA 학습이 불안정), 아니면 fp32
    if device.type == "cuda" and torch.cuda.is_bf16_supported():
        dtype = torch.bfloat16
    elif device.type == "cuda":
        dtype = torch.float16
    else:
        dtype = torch.float32
    model = AutoModelForCausalLM.from_pretrained(
        str(base),
        local_files_only=local_only,
        torch_dtype=dtype,
    )

    # 【수동·튜닝】 VRAM 절약: 활성값을 저장하지 않고 역전파 때 다시 계산
    # (Ollama·백엔드가 같은 GPU 를 쓰는 로컬 환경에서 OOM 방지)
    if not args.no_grad_checkpoint:
        model.gradient_checkpointing_enable()
        model.enable_input_require_grads()  # PEFT + checkpointing 에서 입력 grad 필요
        model.config.use_cache = False

    requested = [m.strip() for m in str(args.target_modules).split(",") if m.strip()]
    target_modules = _resolve_target_modules(model, requested)
    lora_config = LoraConfig(
        r=int(args.rank),
        lora_alpha=int(args.rank) * 2,
        lora_dropout=0.05,
        bias="none",
        task_type=TaskType.CAUSAL_LM,
        target_modules=target_modules,
    )
    model = get_peft_model(model, lora_config)
    # 학습 파라미터(LoRA)만 fp32 로 — 저정밀 옵티마이저 업데이트 손실 방지
    for param in model.parameters():
        if param.requires_grad:
            param.data = param.data.float()
    model.print_trainable_parameters()
    model.to(device)
    model.train()

    class _TextDataset(Dataset):
        def __init__(self, corpus: list[tuple[str, str]]):
            self.corpus = corpus

        def __len__(self) -> int:
            return len(self.corpus)

        def __getitem__(self, idx: int) -> tuple[str, str]:
            return self.corpus[idx]

    eos = tokenizer.eos_token or ""
    tokenizer.padding_side = "right"

    def collate(batch: list[tuple[str, str]]):
        # 응답 끝에 EOS 를 붙여 "JSON 한 줄 후 멈춤"까지 학습
        enc = tokenizer(
            [full + eos for _, full in batch],
            truncation=True,
            max_length=int(args.max_seq_len),
            padding=True,
            return_tensors="pt",
        )
        labels = enc["input_ids"].clone()
        labels[enc["attention_mask"] == 0] = -100
        for row, (prefix, _) in enumerate(batch):
            n_prefix = len(tokenizer(prefix, add_special_tokens=True)["input_ids"])
            labels[row, :n_prefix] = -100
        enc["labels"] = labels
        return enc

    loader = DataLoader(
        _TextDataset(samples),
        batch_size=max(1, int(args.batch)),
        shuffle=True,
        collate_fn=collate,
    )
    optimizer = torch.optim.AdamW((p for p in model.parameters() if p.requires_grad), lr=float(args.lr))

    accum = max(1, int(args.grad_accum))
    for epoch in range(1, int(args.epochs) + 1):
        running = 0.0
        steps = 0
        optimizer.zero_grad(set_to_none=True)
        for i, batch in enumerate(loader, start=1):
            batch = {k: v.to(device) for k, v in batch.items()}
            loss = model(**batch).loss
            (loss / accum).backward()
            if i % accum == 0 or i == len(loader):
                optimizer.step()
                optimizer.zero_grad(set_to_none=True)
            running += float(loss.detach().cpu())
            steps += 1
            if steps % 50 == 0:
                print(f"  epoch {epoch} step {steps}/{len(loader)} loss={running / steps:.4f}", flush=True)
        mean_loss = running / max(1, steps)
        print(f"epoch {epoch}/{args.epochs} loss={mean_loss:.4f} steps={steps}", flush=True)

    adapter_dir = run_dir / "adapter"
    adapter_dir.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(str(adapter_dir))
    tokenizer.save_pretrained(str(adapter_dir))
    print(f"adapter saved → {adapter_dir}")
    return adapter_dir


def main() -> None:
    args = parse_args()

    # =============================================================================
    # [이미 구현된 구간 · 바이브] LoRA 샘플 정책 · 프롬프트 템플릿 · target_modules
    # -----------------------------------------------------------------------------
    # - 템플릿: prompt_spec.LORA_TEMPLATE (서빙 services/prompt_lora 와 동일)
    # - vote: like → 시스템 출력 정답 / dislike → 코멘트가 JSON 일 때만 / pipeline_failure → 약한 정답
    # - seed: 인스턴스 선택·물체 지우기 시드를 --seed-repeat 배 반복
    # - pseudo: 단순 예제가 selector 학습을 희석하지 않게 --max-pseudo 로 샘플링
    # - target_modules 기본 q/k/v/o_proj (Qwen2·Llama 계열 어텐션 전체)
    # YOLO 세그 가중치는 여기서 학습하지 말 것 (training/yolo).
    # =============================================================================
    instruction_template = DEFAULT_INSTRUCTION_TEMPLATE
    include_pipeline_failure = not bool(args.skip_pipeline_failure)

    # =============================================================================
    # [이미 구현된 구간 · 바이브] 데이터 적재 · dry-run · PEFT 학습 본선
    # -----------------------------------------------------------------------------
    # torch/peft 는 실제 학습 시에만 import. --dry-run 과 --help 는 학습 의존성 없이 동작.
    # =============================================================================
    feedback_cases = discover_feedback_cases(args.feedback_dir)
    pseudo_cases = discover_pseudo_cases(args.pseudo_dir)
    if args.max_pseudo >= 0 and len(pseudo_cases) > args.max_pseudo:
        pseudo_cases = random.Random(0).sample(pseudo_cases, args.max_pseudo)
    seed_cases = discover_seed_cases(args.seed_file)
    records = to_instruction_records(
        feedback_cases,
        template=instruction_template,
        include_pipeline_failure=include_pipeline_failure,
        origin="feedback",
    )
    records.extend(
        to_instruction_records(
            pseudo_cases,
            template=instruction_template,
            include_pipeline_failure=True,
            origin="pseudo",
        )
    )
    seed_records = to_instruction_records(
        seed_cases,
        template=instruction_template,
        origin="seed",
    )
    records.extend(seed_records * max(1, int(args.seed_repeat)))
    all_cases = feedback_cases + pseudo_cases + seed_cases
    summary = summarize_cases(all_cases, records)
    summary["seed_cases"] = len(seed_cases)
    _print_summary("LoRA train", len(feedback_cases), len(pseudo_cases), summary)
    print(f"seed_cases     = {len(seed_cases)} x{args.seed_repeat}  ({args.seed_file})")
    print(f"feedback_dir = {args.feedback_dir} exists={args.feedback_dir.exists()}")
    print(f"pseudo_dir   = {args.pseudo_dir} exists={args.pseudo_dir.exists()}")
    print(f"output       = {args.output}")

    run_dir = _run_dir(args.output, args.name)
    extra: dict = {"dry_run": bool(args.dry_run)}

    if args.dry_run:
        write_run_manifest(
            run_dir / "run.json",
            args=args_to_jsonable(args),
            summary=summary,
            records=records,
            extra=extra,
        )
        print(f"dry-run manifest → {run_dir / 'run.json'}")
        print("학습 루프는 실행하지 않았습니다. --base-model 을 주고 --dry-run 없이 다시 실행하세요.")
        print("YOLO 세그 학습은 training/yolo/ 를 사용하세요.")
        raise SystemExit(0)

    if not records:
        write_run_manifest(
            run_dir / "run.json",
            args=args_to_jsonable(args),
            summary=summary,
            records=records,
            extra={**extra, "error": "no_records"},
        )
        raise SystemExit(
            "학습 레코드가 0건입니다. data/feedback/*.json 에 prompt + parsed_prompt 가 있는지 "
            "먼저 --dry-run 으로 확인하세요."
        )

    samples = [
        (instruction_template.format(prompt=r.prompt, response=""), r.text) for r in records
    ]
    adapter_dir = train_adapter(args, samples, run_dir)
    extra["adapter"] = str(adapter_dir)
    write_run_manifest(
        run_dir / "run.json",
        args=args_to_jsonable(args),
        summary=summary,
        records=records,
        extra=extra,
    )
    print("평가: python training/lora/eval_parser.py --adapter", adapter_dir)
    print("서빙: adapter 를 backend/models/lora/ 로 복사 후 .env LLM_PROVIDER=lora (backend 재시작)")


if __name__ == "__main__":
    main()
