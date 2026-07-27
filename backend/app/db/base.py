"""SQLAlchemy declarative base and metadata."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Shared ORM base for all table models."""

    pass
