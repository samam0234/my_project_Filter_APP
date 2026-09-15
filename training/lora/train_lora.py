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
  python training/lora/train_lora.py --base-model D:\\models\\gemma-2-2b-it --epochs 3
"""

from __future__ import annotations

import argparse
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
        "--output",
        type=Path,
        default=_LORA_DIR.parent / "outputs" / "lora",
        help="어댑터 출력 루트 (하위에 run 폴더 생성)",
    )
    parser.add_argument("--name", default="", help="run 이름 (기본: 시각 스탬프)")
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--lr", type=float, default=1e-4)
    parser.add_argument("--batch", type=int, default=1)
    parser.add_argument("--rank", type=int, default=8, help="LoRA rank r")
    parser.add_argument("--max-seq-len", type=int, default=512)
    parser.add_argument(
        "--base-model",
        default="",
        help="로컬 HuggingFace 형식 체크포인트 경로 (Ollama GGUF 불가)",
    )
    parser.add_argument(
        "--target-modules",
        default="q_proj,v_proj",
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


def train_adapter(args: argparse.Namespace, texts: list[str], run_dir: Path) -> Path:
    """PEFT LoRA 학습 후 adapter 디렉터리 경로를 반환한다."""
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
    print(f"epochs={args.epochs} lr={args.lr} batch={args.batch} rank={args.rank}")

    tokenizer = AutoTokenizer.from_pretrained(str(base), local_files_only=local_only)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    dtype = torch.float16 if device.type == "cuda" else torch.float32
    model = AutoModelForCausalLM.from_pretrained(
        str(base),
        local_files_only=local_only,
        torch_dtype=dtype,
    )

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
    model.print_trainable_parameters()
    model.to(device)
    model.train()

    class _TextDataset(Dataset):
        def __init__(self, corpus: list[str]):
            self.corpus = corpus

        def __len__(self) -> int:
            return len(self.corpus)

        def __getitem__(self, idx: int) -> str:
            return self.corpus[idx]

    def collate(batch: list[str]):
        enc = tokenizer(
            batch,
            truncation=True,
            max_length=int(args.max_seq_len),
            padding=True,
            return_tensors="pt",
        )
        labels = enc["input_ids"].clone()
        labels[enc["attention_mask"] == 0] = -100
        enc["labels"] = labels
        return enc

    loader = DataLoader(
        _TextDataset(texts),
        batch_size=max(1, int(args.batch)),
        shuffle=True,
        collate_fn=collate,
    )
    optimizer = torch.optim.AdamW((p for p in model.parameters() if p.requires_grad), lr=float(args.lr))

    for epoch in range(1, int(args.epochs) + 1):
        running = 0.0
        steps = 0
        for batch in loader:
            batch = {k: v.to(device) for k, v in batch.items()}
            optimizer.zero_grad(set_to_none=True)
            loss = model(**batch).loss
            loss.backward()
            optimizer.step()
            running += float(loss.detach().cpu())
            steps += 1
        mean_loss = running / max(1, steps)
        print(f"epoch {epoch}/{args.epochs} loss={mean_loss:.4f} steps={steps}")

    adapter_dir = run_dir / "adapter"
    adapter_dir.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(str(adapter_dir))
    tokenizer.save_pretrained(str(adapter_dir))
    print(f"adapter saved → {adapter_dir}")
    return adapter_dir


def main() -> None:
    args = parse_args()

    # =============================================================================
    # [하드코딩 파트] LoRA 샘플 정책 · 프롬프트 템플릿 · target_modules
    # -----------------------------------------------------------------------------
    # [임무] 어떤 피드백을 학습에 넣을지, instruction 문자열, LoRA 부착 모듈
    # [연결] dataset.to_instruction_records, CLI --target-modules/--skip-pipeline-failure
    # [규칙] dislike 의 시스템 parsed_prompt 는 오답. 코멘트가 JSON 일 때만 정답.
    #        YOLO 세그 가중치는 여기서 학습하지 말 것 (training/yolo).
    # [힌트] TEMPLATE = """...{prompt}...{response}..."""
    #        include_pipeline_failure = False  로 약한 정답 제외
    # =============================================================================
    # >>> 여기에 정책만 덮어쓰기 (비우면 아래 바이브 기본값) <<<
    #
    instruction_template = DEFAULT_INSTRUCTION_TEMPLATE
    include_pipeline_failure = not bool(args.skip_pipeline_failure)

    # =============================================================================
    # [이미 구현된 구간 · 바이브] 데이터 적재 · dry-run · PEFT 학습 본선
    # -----------------------------------------------------------------------------
    # torch/peft 는 실제 학습 시에만 import. --dry-run 과 --help 는 학습 의존성 없이 동작.
    # =============================================================================
    feedback_cases = discover_feedback_cases(args.feedback_dir)
    pseudo_cases = discover_pseudo_cases(args.pseudo_dir)
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
    all_cases = feedback_cases + pseudo_cases
    summary = summarize_cases(all_cases, records)
    _print_summary("LoRA train", len(feedback_cases), len(pseudo_cases), summary)
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

    adapter_dir = train_adapter(args, [r.text for r in records], run_dir)
    extra["adapter"] = str(adapter_dir)
    write_run_manifest(
        run_dir / "run.json",
        args=args_to_jsonable(args),
        summary=summary,
        records=records,
        extra=extra,
    )
    print("적용: adapter 폴더를 models/lora/ 로 복사한 뒤 프롬프트 분석기에 로드 (Phase 2).")
    print("지금은 학습 산출만 합니다. backend 핫스왑은 후속입니다.")


if __name__ == "__main__":
    main()
