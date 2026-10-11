# deploy — 배포 부속 파일

| 경로 | 용도 |
|------|------|
| [cloudflare/](./cloudflare/) | 프런트를 **Cloudflare Worker** 로 — `worker.js`(정적 화면 + `/api` 프록시), `wrangler.jsonc`, `set_edge_secret.sh`(비밀 값을 서버 · Worker 에 같은 값으로 숨겨 저장) |

자세한 순서와 이유: [`docs/guidance/cloudflare-deploy.md`](../docs/guidance/cloudflare-deploy.md) · 인수인계 [`docs/HANDOVER.md`](../docs/HANDOVER.md)
