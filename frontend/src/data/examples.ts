/**
 * 예시 프롬프트 — 홈 · 작업실 · 가이드 공용.
 * 각 문장은 백엔드가 실제로 지원하는 규격(ParsedPrompt · selector)을 보여주도록 고른다.
 */

export interface ExamplePrompt {
  text: string;
  /** 무엇을 보여주는 예시인지 (가이드 표 · 칩 툴팁) */
  point: string;
  group: "keep" | "remove" | "select" | "effect";
}

export const EXAMPLES: ExamplePrompt[] = [
  { text: "사람만 남기고 배경 제거해줘", point: "대상 남기기 (배경 투명)", group: "keep" },
  { text: "강아지만 남기고 배경 블러 강도 40", point: "배경 블러 + 강도", group: "effect" },
  { text: "고양이만 크롭해줘", point: "대상 주변으로 자르기", group: "effect" },
  {
    text: "맨 앞에 빨간 안전모와 형광 조끼를 입은 남자만 남기고 전부 제거",
    point: "위치 + 색 속성으로 한 명 고르기",
    group: "select",
  },
  { text: "왼쪽에서 두 번째 사람 지워줘", point: "위치 + 순서로 고른 대상 지우기", group: "remove" },
  { text: "흰색 차 없애줘", point: "색으로 고른 대상 지우기", group: "remove" },
  { text: "가장 큰 강아지만 남기고 배경 블러", point: "크기로 고르기", group: "select" },
  { text: "사람 2명만 남기고 배경 제거", point: "개수 (큰 순서)", group: "select" },
  { text: "파란 셔츠 입은 사람만 남겨", point: "옷 색으로 고르기", group: "select" },
  { text: "오른쪽 사람 지워줘", point: "위치로 고른 대상 지우기", group: "remove" },
];

export const GROUP_LABELS: Record<ExamplePrompt["group"], string> = {
  keep: "남기기",
  effect: "효과",
  select: "특정 대상 고르기",
  remove: "지우기",
};
