# Pre-deploy Checklist

- [ ] `.env` 시크릿 교체 (`SECRET_KEY`, DB password)
- [ ] `DB_DIALECT=mariadb` 및 호스트 확인
- [ ] 이미지 빌드 성공 (`backend`, `frontend`)
- [ ] 포트 충돌 없음 (`ports-inventory.md`)
- [ ] 콘솔 외부 노출 여부 결정 (기본 비권장/내부망)
- [ ] 백업: MariaDB 볼륨 / 피드백 데이터
