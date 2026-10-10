# 그래프 테스트가 실제 업로드 폴더 대신 임시 폴더를 쓰게 / `16dd40a66787bcee3f35bcc0805f0aac4ea6c593`

> 브랜치: `feature/security-hardening`  
> 작성일: `2026-10-09 04:08`  
> 작성자: `agent`  
> 파일명: `261009_0408_16dd40a_pipeline-test-tmp-uploads_feature-security-hardening.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `test(pipeline): 그래프 테스트가 실제 업로드 폴더 대신 임시 폴더를 쓰게` |
| **커밋 번호 (SHA)** | `16dd40a66787bcee3f35bcc0805f0aac4ea6c593` |
| **짧은 SHA** | `16dd40a` |
| **브랜치** | `feature/security-hardening` |
| **부모 커밋** | `335d024` |

## 2. 주 커밋 내용

- `test_pipeline_graph` 의 `run` fixture 가 업로드 폴더를 임시 폴더로 바꾼다

## 3. 상세 내용

### 3.1 배경 / 목적
테스트 파일별로 실제 `backend/data/uploads` 수정 시각 변화를 확인한 결과 이 테스트만 실제 폴더에 작업 폴더를 만들었다가 지웠다 (테스트 위생).

### 3.2 변경 범위
- 수정: `tests/unit/test_pipeline_graph.py`

### 3.3 기술 포인트
- 다른 API 테스트와 같은 방식(`monkeypatch.setattr(settings, "upload_dir", tmp)`)

### 3.4 의도적으로 하지 않은 것
- 없음

## 4. 커밋 관련 결과

### 4.1 동작 결과
- [x] 테스트 5건 통과, 실행 전후 실제 업로드 폴더 수정 시각 동일

### 4.2 부작용 / 리스크
- 없음

### 4.3 후속 작업
- 없음

### 4.4 관련 문서
- `tests/README.md`
