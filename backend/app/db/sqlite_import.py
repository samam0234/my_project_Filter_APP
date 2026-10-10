"""서비스 DB 를 SQLite 에서 MariaDB 로 옮기기.

SQLite 는 한 파일에 한 프로세스씩 쓰는 구조라 동시 접속이 늘면 잠금 대기가 생기고, 2026-10-08 처럼 두 프로세스가 같은 파일을
쓰다 깨질 수도 있다. Docker 는 서비스 DB 를 MariaDB(학습 DB 와 같은 서버 · 같은 데이터베이스, 테이블 이름은 겹치지 않음)로 쓴다.

- `import_sqlite(src, engine)`: SQLite 파일의 users · auth_sessions · auth_codes · jobs · batch_jobs 를 대상 DB 로 복사.
  외래 키 순서대로, 이미 있는 행(같은 기본 키)은 건너뛴다 — 여러 번 돌려도 안전
- 양쪽에 다 있는 열만 옮긴다 (예전 SQLite 에 없는 새 열은 기본값)
- `auto_import(settings, engine)`: 기동 시 — 대상이 MariaDB 이고 회원 · 작업이 하나도 없고 옛 SQLite 파일이 있으면 한 번 옮긴다.
  옛 파일은 지우지 않는다 (되돌리기용)

손으로 돌리기: `python -m app.db.sqlite_import data/cutnkeep.db` (backend/ 에서, 대상은 지금 설정의 서비스 DB)
"""

from __future__ import annotations

import sys
from pathlib import Path

from loguru import logger
from sqlalchemy import Engine, create_engine, func, inspect, select

from app.core.config import Settings, get_settings
from app.db.base import Base

# 외래 키 순서 (users 가 먼저)
TABLES = ("users", "auth_sessions", "auth_codes", "jobs", "batch_jobs")
CHUNK = 500


def import_sqlite(src: Path, target: Engine) -> dict[str, int]:
    """src(SQLite 파일) → target. 반환: 표마다 새로 넣은 행 수."""
    import app.models  # noqa: F401 — 메타데이터 등록

    source = create_engine(f"sqlite:///{src.as_posix()}")
    Base.metadata.create_all(target)
    src_tables = set(inspect(source).get_table_names())
    copied: dict[str, int] = {}
    try:
        for name in TABLES:
            if name not in src_tables:
                copied[name] = 0
                continue
            table = Base.metadata.tables[name]
            src_cols = {c["name"] for c in inspect(source).get_columns(name)}
            cols = [c for c in table.columns if c.name in src_cols]
            pk = [c for c in table.primary_key.columns]
            with target.connect() as tconn:
                existing = {tuple(r) for r in tconn.execute(select(*pk))}
            added = 0
            with source.connect() as sconn, target.begin() as tconn:
                rows = sconn.execute(select(*cols)).mappings()
                batch = []
                for row in rows:
                    key = tuple(row[c.name] for c in pk)
                    if key in existing:
                        continue
                    batch.append(dict(row))
                    if len(batch) >= CHUNK:
                        tconn.execute(table.insert(), batch)
                        added += len(batch)
                        batch = []
                if batch:
                    tconn.execute(table.insert(), batch)
                    added += len(batch)
            copied[name] = added
    finally:
        source.dispose()
    return copied


def auto_import(settings: Settings, engine: Engine, *, skip_sqlite: bool = True) -> dict[str, int] | None:
    """MariaDB 로 처음 바꿨을 때 옛 SQLite 서비스 DB 를 한 번 옮긴다. 옮기지 않으면 None.

    skip_sqlite: 대상도 SQLite 면 하지 않는다 (호스트 개발 서버) — 테스트에서만 False.
    """
    if (skip_sqlite and engine.dialect.name == "sqlite") or not settings.service_db_import_from:
        return None
    src = settings.resolve_runtime_path(settings.service_db_import_from)
    if not src.is_file():
        return None
    users = Base.metadata.tables["users"]
    jobs = Base.metadata.tables["jobs"]
    with engine.connect() as conn:
        if conn.execute(select(func.count()).select_from(users)).scalar() or conn.execute(
            select(func.count()).select_from(jobs)
        ).scalar():
            return None  # 이미 쓰고 있는 DB — 건드리지 않는다
    try:
        copied = import_sqlite(src, engine)
    except Exception:
        logger.exception("옛 SQLite 서비스 DB 옮기기 실패 — 빈 DB 로 시작한다 ({})", src)
        return None
    logger.warning("옛 SQLite 서비스 DB 를 {} 로 옮겼다: {} (원본 {} 는 그대로 둔다)", engine.dialect.name, copied, src)
    return copied


def main(argv: list[str]) -> int:
    from app.db.session import get_engine

    if len(argv) < 2:
        print("사용: python -m app.db.sqlite_import <SQLite 파일 경로>  (대상: 지금 설정의 서비스 DB)")
        return 2
    src = Path(argv[1])
    if not src.is_absolute():
        src = get_settings().resolve_runtime_path(argv[1])
    engine = get_engine()
    print(f"{src} → {engine.dialect.name}: {import_sqlite(src, engine)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
