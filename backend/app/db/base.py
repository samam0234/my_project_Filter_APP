"""SQLAlchemy Declarative Base 및 메타데이터.

서비스 DB 모델(Job, BatchJob, User, AuthSession, AuthCode)이 이 Base 를 상속한다.
init_db() 가 Base.metadata.create_all 로 테이블을 만든다.
학습 DB 모델(Feedback, LearningSample)은 app.db.learning.LearningBase 를 쓴다.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """모든 테이블 모델의 공통 ORM 베이스."""

    pass
