# data/chroma — 확인된 문장 벡터

`data/feedback` 의 교정·좋아요만 담는 Chroma 저장소다. 컬렉션 이름은 `verified_feedback`.

의사 라벨과 파이프라인 실패는 넣지 않는다. 임베딩 모델은 받지 않고 한글 글자 벡터를 쓴다.
실행 파일은 Git에 올리지 않는다. 저장소 루트에서 `python scripts/chroma_feedback.py` 로 다시 만든다.
백엔드가 문장 해석을 할 때도 이 폴더를 읽어, 학습 DB에 아직 없는 확인 문장을 예시로 보탠다.
