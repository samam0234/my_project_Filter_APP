"""SQLAlchemy Declarative Base 및 메타데이터."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """모든 테이블 모델의 공통 ORM 베이스."""

    pass
