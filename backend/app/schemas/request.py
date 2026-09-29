"""요청·구조화 프롬프트 스키마 (Pydantic).

API multipart 폼과 LangGraph 노드 사이에서 오가는
공통 구조체 정의.
"""

from typing import List, Optional

from pydantic import BaseModel, Field


# 인스턴스 위치 선택자 — services/instance_selector 가 정렬 기준으로 사용
POSITIONS = ("front", "back", "left", "right", "center", "largest", "smallest")
# effect 허용 값 — remove_object 만 "선택 대상을 지움", 나머지는 "선택 대상을 남김"
EFFECTS = ("remove_bg", "blur", "crop", "none", "remove_object")


class InstanceSelector(BaseModel):
    """같은 클래스 인스턴스 중 **어느 것**인지 고르는 조건.

      position   : front(맨 앞) | back | left | right | center | largest | smallest
      rank       : position 정렬에서 몇 번째부터 (1-based). "오른쪽에서 두 번째" → right, 2
      count      : 고를 개수. None 이면 position 있을 때 1, 없으면 조건 맞는 전부
      attributes : "red helmet", "neon vest" 처럼 영어 색+부위 구 (색 매칭용)
    """

    position: Optional[str] = None
    rank: Optional[int] = Field(default=None, ge=1, le=50)
    count: Optional[int] = Field(default=None, ge=1, le=50)
    attributes: List[str] = Field(default_factory=list)

    def is_empty(self) -> bool:
        return (
            self.position is None
            and self.rank is None
            and self.count is None
            and not self.attributes
        )


class ParsedPrompt(BaseModel):
    """자연어 프롬프트 분석 결과 구조체.

    prompt_analyzer 휴리스틱(또는 LLM)이 채운다.
      target    : 대상 클래스 목록 (예: ["person", "dog"])
      effect    : remove_bg | blur | crop | none  → 선택 대상을 **남기고** 나머지에 효과
                  remove_object                 → 선택 대상을 **지우고** 주변으로 메움
      intensity : 블러 강도 등 0~100
      crop      : 주 효과 후 추가 크롭 여부
      selector  : 특정 인스턴스 선택 조건 (None 이면 target 클래스 전부)
    """

    # 【수동】 스키마 기본값 — 분석기가 비운 필드 채울 때 사용
    # target: YOLO 클래스명 리스트 (학습 names 와 일치)
    # effect: remove_bg | blur | crop | none  (effects.apply_effects 분기)
    # intensity: 블러 등 강도 0~100
    # crop: True 이면 주 효과 후 추가 크롭
    target: List[str] = Field(default_factory=lambda: ["person"])
    effect: str = Field(default="remove_bg")  # EFFECTS 참고
    intensity: int = Field(default=15, ge=0, le=100)
    crop: bool = False
    selector: Optional[InstanceSelector] = None


class UploadFormMeta(BaseModel):
    """multipart 업로드 부가 메타데이터 (문서/검증용)."""

    prompt: str = Field(..., min_length=1, max_length=1000)
