# Scribble — 개인 로컬 메모장

이 폴더는 **본인만의 짜잘한 기록·실험·임시 메모**를 두는 곳이다.  
팀/원격 저장소와 공유하지 않는 것을 기본으로 한다.

---

## Git 정책

| 대상 | 추적 여부 |
|------|-----------|
| `Scribble/README.md` (이 파일) | **추적함** (용도 안내) |
| `Scribble/` 아래 그 외 모든 파일 | **ignore** (커밋 안 함) |

`.gitignore` 에 다음이 있다:

```gitignore
Scribble/**
!Scribble/README.md
```

→ 여기에 뭘 적어도 **실수로 push 되지 않도록** 막아 둔다.  
(이미 추적 중인 파일을 넣었다면 `git rm --cached` 로 제외)

---

## 여기다 무엇을 두나

**해도 됨 (권장 용도)**

- 로컬 TODO, 당일 잡생각
- 임시 테스트 결과 캡처·메모
- 개인 API 키 **메모는 비추천** — 그래도 둘 거면 절대 커밋 안 되는 것만 (이 폴더는 ignore)
- 실험용 스크립트 초안, SQL 연습
- “나중에 docs로 옮길” 초고

**공식 문서 자리 아님**

| 내용 | 올바른 위치 |
|------|-------------|
| 팀과 공유할 가이드 | `docs/guidance/` |
| 커밋 이력 | `docs/branchs/commits/` |
| 재현 가능한 장애 기록 | `docs/repeater/`, `docs/find_debug/` |
| 아키텍처 | `docs/Architecture/` |

공유할 내용이 정리되면 **Scribble → docs 해당 폴더로 옮긴 뒤 커밋**한다.

---

## 사용 팁

1. 날짜 파일: `2026-07-27-notes.md`  
2. 주제 파일: `todo.md`, `wip-opencv.md`  
3. 민감 정보: 가능하면 OS 비밀 저장소 / `.env` (이미 ignore) 사용  
4. 정리 주기: 주 1회 Scribble 훑고 공유할 것만 docs 로 승격  

---

## 실행·서버 가이드

서버 띄우는 법은 루트 **[RUN.md](../RUN.md)** 를 본다.
