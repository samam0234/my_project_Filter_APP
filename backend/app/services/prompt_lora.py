"""LoRA 어댑터 프롬프트 분석기 (LLM_PROVIDER=lora).

training/lora 에서 학습한 어댑터(Qwen2.5-1.5B 기본)를 로컬 GPU/CPU 로 직접 돌린다.
Ollama 는 Qwen2 safetensors 어댑터를 바로 붙이지 못하므로 transformers + peft 로 서빙한다.

- torch / transformers / peft 는 **호출 시점에만** import (없으면 LLMError → 휴리스틱)
- 모델은 프로세스당 1회 로드 후 재사용 (첫 요청만 수 초)
- 입력 형식은 prompt_spec.LORA_TEMPLATE — 학습과 반드시 같아야 한다
- training/lora/eval_parser.py 도 이 클래스를 그대로 써서 평가 = 서빙 동작
"""

from __future__ import annotations

import threading
from pathlib import Path
from typing import Optional

from loguru import logger

from app.core.config import Settings
from app.schemas.request import ParsedPrompt
from app.services.prompt_spec import (
    LORA_TEMPLATE,
    LLMError,
    extract_json_object,
    normalize_parsed,
)

# 【수동·튜닝】 생성 길이 — 정답 JSON 한 줄은 보통 60~90 토큰
MAX_NEW_TOKENS = 160


class LoraPromptParser:
    """베이스 모델 + (선택) LoRA 어댑터로 프롬프트 → ParsedPrompt."""

    def __init__(
        self,
        base_model: Path,
        adapter: Optional[Path] = None,
        device: str = "",
    ) -> None:
        try:
            import torch
            from transformers import AutoModelForCausalLM, AutoTokenizer
        except ImportError as exc:
            raise LLMError(f"LoRA 서빙 의존성 없음 (torch/transformers/peft): {exc}") from exc

        if not base_model.is_dir():
            raise LLMError(f"LORA_BASE_MODEL 디렉터리 없음: {base_model}")
        if adapter is not None and not (adapter / "adapter_config.json").is_file():
            raise LLMError(f"LoRA 어댑터 없음 (adapter_config.json): {adapter}")

        self._torch = torch
        self.device = torch.device(device or ("cuda" if torch.cuda.is_available() else "cpu"))
        if self.device.type == "cuda":
            dtype = torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16
        else:
            dtype = torch.float32

        self.tokenizer = AutoTokenizer.from_pretrained(str(base_model), local_files_only=True)
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
        model = AutoModelForCausalLM.from_pretrained(
            str(base_model), local_files_only=True, torch_dtype=dtype
        )
        if adapter is not None:
            try:
                from peft import PeftModel
            except ImportError as exc:
                raise LLMError(f"peft 없음: {exc}") from exc
            model = PeftModel.from_pretrained(model, str(adapter))
        self.model = model.to(self.device).eval()
        self._lock = threading.Lock()  # generate 는 스레드 안전하지 않음
        logger.info(
            "LoRA 파서 준비 base={} adapter={} device={} dtype={}",
            base_model, adapter, self.device, dtype,
        )

    def generate_text(self, prompt: str) -> str:
        """템플릿 적용 → greedy 생성 → 응답 부분 텍스트."""
        text = LORA_TEMPLATE.format(prompt=prompt.strip(), response="")
        enc = self.tokenizer(text, return_tensors="pt").to(self.device)
        with self._lock, self._torch.inference_mode():
            out = self.model.generate(
                **enc,
                max_new_tokens=MAX_NEW_TOKENS,
                do_sample=False,
                eos_token_id=self.tokenizer.eos_token_id,
                pad_token_id=self.tokenizer.pad_token_id,
            )
        generated = out[0, enc["input_ids"].shape[1]:]
        reply = self.tokenizer.decode(generated, skip_special_tokens=True)
        # 학습 템플릿 밖으로 이어 쓰면 다음 섹션 전에서 자름
        return reply.split("###", 1)[0].strip()

    def parse(self, prompt: str) -> ParsedPrompt:
        return normalize_parsed(extract_json_object(self.generate_text(prompt)))


_PARSER: Optional[LoraPromptParser] = None
_PARSER_KEY: Optional[tuple] = None
_INIT_LOCK = threading.Lock()


def get_lora_parser(settings: Settings) -> LoraPromptParser:
    """설정 경로 기준 싱글톤. 경로가 바뀌면 다시 로드."""
    global _PARSER, _PARSER_KEY
    if not settings.lora_base_model:
        raise LLMError("LORA_BASE_MODEL 미설정")
    base = settings.resolve_runtime_path(settings.lora_base_model)
    adapter = (
        settings.resolve_runtime_path(settings.lora_adapter_path)
        if settings.lora_adapter_path
        else None
    )
    key = (str(base), str(adapter))
    with _INIT_LOCK:
        if _PARSER is None or _PARSER_KEY != key:
            _PARSER = LoraPromptParser(base, adapter)
            _PARSER_KEY = key
    return _PARSER


def parse_prompt_lora(prompt: str, settings: Settings) -> ParsedPrompt:
    return get_lora_parser(settings).parse(prompt)
