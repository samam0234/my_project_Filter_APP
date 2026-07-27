# frontend — 사용자 웹 앱

일반 사용자가 **이미지를 올리고 프롬프트로 필터**를 적용하는 React 앱이다.

## 역할

| 영역 | 경로 | 설명 |
|------|------|------|
| 업로드 | `src/components/image/` | 드롭존, Before/After, 처리 상태 |
| 프롬프트 | `src/components/prompt/` | 자연어 입력 |
| 피드백 | `src/components/feedback/` | 좋아요/싫어요 |
| 상태 | `src/store/` | Zustand |
| API | `src/api/client.ts` | axios → backend `/api/v1` |
| 훅 | `src/hooks/` | 처리·피드백 호출 |

운영 관리 UI는 여기가 아니라 **`console/`** (포트 5174) 이다.

## 실행

```powershell
cd frontend
npm install   # 최초 1회
npm run dev
```

- URL: http://localhost:5173  
- Vite 프록시: `/api`, `/health` → `http://localhost:8000`  
- 백엔드가 떠 있어야 처리·결과가 동작한다.

## 스크립트

| 명령 | 설명 |
|------|------|
| `npm run dev` | 개발 서버 |
| `npm run build` | 프로덕션 빌드 |
| `npm run preview` | 빌드 미리보기 |

## 관련 문서

- `docs/guidance/user-frontend.md`
- `docs/Architecture/apps.md`
- `RUN.md`
