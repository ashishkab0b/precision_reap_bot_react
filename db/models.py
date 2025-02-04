# db/models.py

from datetime import datetime, timezone
from enum import Enum
from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    Boolean,
    Text,
    ForeignKey,
    DateTime,
    Enum as SQLAlchemyEnum,
    create_engine,
    Index,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
    Session,
)
from flask_login import UserMixin
from sqlalchemy.orm import declarative_base

# from flask_app.extensions import db


Base = declarative_base()


class RoleEnum(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    DEVELOPER = "developer"
    

class ConvoStateEnum(str, Enum):
    START = "start"
    ISSUE_INTERVIEW = "issue_interview"
    RATE_ISSUE = "rate_issue"
    RATE_VALUES = "rate_values"
    RANK_REAPS = "rank_reaps"
    RATE_REAPS = "rate_reaps"
    GENERATE_REAP = "generate_reap"
    RATE_REAP_1 = "rate_reap_1"
    REFINE_REAP = "refine_reap"
    RATE_REAP_2 = "rate_reap_2"
    COMPLETE = "complete"

class ResponseTypeEnum(str, Enum):
    TEXT = "text"
    SLIDER = "slider"
    MULTISELECT = "multiselect"
    SINGLESELECT = "singleselect"
    RANKING = "ranking"
    CONTINUE = "continue"
    NOINPUT = "noinput"
    
class Conversation(Base):
    __tablename__ = 'conversations'
    
    # Identifiers
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    pid: Mapped[str] = mapped_column(String, nullable=False, unique=False)
    convo_code: Mapped[str] = mapped_column(String, nullable=True, unique=False)
    
    # Data
    state: Mapped[ConvoStateEnum] = mapped_column(SQLAlchemyEnum(ConvoStateEnum), nullable=False, default=ConvoStateEnum.START)
    
    # Timestamps
    last_active_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    deleted_at: Mapped[datetime] = mapped_column(default=None, nullable=True)
    
   # Indexes
    Index('conversations_pid_index', pid)
    
    # Enforce that pid convo_code are unique together
    __table_args__ = (
        Index('conversations_pid_convo_code_index', pid, convo_code, unique=True),
    )
    


class Message(Base):
    __tablename__ = 'messages'
    
    # Identifiers
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    convo_id: Mapped[int] = mapped_column(Integer, ForeignKey('conversations.id'), nullable=False)
    
    # Data
    state: Mapped[ConvoStateEnum] = mapped_column(SQLAlchemyEnum(ConvoStateEnum), nullable=False)
    content: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[RoleEnum] = mapped_column(SQLAlchemyEnum(RoleEnum), nullable=False)
    response_type: Mapped[ResponseTypeEnum] = mapped_column(SQLAlchemyEnum(ResponseTypeEnum), nullable=False)
    options: Mapped[dict] = mapped_column(JSONB, nullable=True)
    tokens_prompt: Mapped[int] = mapped_column(Integer, nullable=True)
    tokens_completion: Mapped[int] = mapped_column(Integer, nullable=True)
    llm_model: Mapped[str] = mapped_column(String, nullable=True)
    
    bot_version: Mapped[str] = mapped_column(String, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    deleted_at: Mapped[datetime] = mapped_column(default=None, nullable=True)
    
    # Relationships
    conversation = relationship('Conversation', backref='messages')
    
    # Indexes
    Index('messages_convo_id_index', convo_id)

class AnalysisData(Base):
    __tablename__ = 'analysis_data'
    
    # Identifiers
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    convo_id: Mapped[int] = mapped_column(Integer, ForeignKey('conversations.id'), nullable=False)
    # message_id: Mapped[int] = mapped_column(Integer, ForeignKey('messages.id'), nullable=False)
    
    # Data
    field: Mapped[str] = mapped_column(String, nullable=False)
    content: Mapped[str] = mapped_column(String, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    deleted_at: Mapped[datetime] = mapped_column(default=None, nullable=True)
    
    # Relationships
    conversation = relationship('Conversation', backref='ratings')
    # message = relationship('Message', backref='ratings')
    
    # Indexes
    Index('ratings_convo_id_index', convo_id)
    # Index('ratings_message_id_index', message_id)


class LLMQuery(Base):
    __tablename__ = 'llm_queries'
    
    # Identifiers
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    convo_id: Mapped[int] = mapped_column(Integer, ForeignKey('conversations.id'), nullable=False)
    message_id: Mapped[int] = mapped_column(Integer, ForeignKey('messages.id'), nullable=True)
    
    # Data
    completion: Mapped[JSONB] = mapped_column(JSONB, nullable=False)
    tokens_prompt: Mapped[int] = mapped_column(Integer, nullable=True)
    tokens_completion: Mapped[int] = mapped_column(Integer, nullable=True)
    llm_model: Mapped[str] = mapped_column(String, nullable=True)
    
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    deleted_at: Mapped[datetime] = mapped_column(default=None, nullable=True)
    
    # Relationships
    message = relationship('Message', backref='llm_queries')
    conversation = relationship('Conversation', backref='llm_queries')
    
    # Indexes
    Index('llm_queries_message_id_index', message_id)
    Index('llm_queries_convo_id_index', convo_id)