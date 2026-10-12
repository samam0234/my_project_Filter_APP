# backend/data/chroma — 승인 문장 벡터

문장 해석이 방금 색인한 승인 예시를 컬렉션 `approved_prompts`에 둔다.
루트 `data/chroma`의 `verified_feedback`과는 따로다. 임베딩 모델은 받지 않는다.
실행 파일은 Git에 올리지 않고, 승인 목록이 바뀌면 서비스가 다시 맞춘다.
