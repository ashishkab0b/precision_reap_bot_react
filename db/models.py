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

from flask_app.extensions import db


class Base(DeclarativeBase):
    pass


class RoleEnum(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    

class ConvoStateEnum(str, Enum):
    START = "start"
    ISSUE_INTERVIEW = "issue_interview"
    RATE_ISSUE = "rate_issue"
    GENERATE_REAP = "generate_reap"
    RATE_REAP_1 = "rate_reap_1"
    REFINE_REAP = "refine_reap"
    RATE_REAP_2 = "rate_reap_2"
    COMPLETE = "complete"
    
    
class FeedbackEnum(str, Enum):
    GENERAL = "general"
    HELP = "help"
    BUG = "bug"
    FEATURE = "feature"


class ResponseTypeEnum(str, Enum):
    TEXT = "text"
    SLIDER = "slider"
    MULTISELECT = "multiselect"
    SINGLESELECT = "singleselect"
    CONTINUE = "continue"
    NOINPUT = "noinput"
        

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    # Identifiers
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String, nullable=True, unique=True)
    password_hash: Mapped[str] = mapped_column(String, nullable=True)
    reddit_username: Mapped[str] = mapped_column(String, nullable=True)
    # reddit_uuid: Mapped[str] = mapped_column(String, nullable=True)
    reddit_refresh_token: Mapped[str] = mapped_column(String, nullable=True)
    
    # Data
    age: Mapped[int] = mapped_column(Integer, nullable=True)
    age_init: Mapped[bool] = mapped_column(Integer, nullable=True)
    gender: Mapped[str] = mapped_column(String, nullable=True)
    research_consent: Mapped[bool] = mapped_column(Boolean, nullable=True)
    
    
    # OTP
    otp: Mapped[str] = mapped_column(String, nullable=True)
    otp_expiry_ts: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    
    # UTM parameters
    utm_source: Mapped[str] = mapped_column(String, nullable=True)
    utm_medium: Mapped[str] = mapped_column(String, nullable=True)
    utm_campaign: Mapped[str] = mapped_column(String, nullable=True)
    utm_term: Mapped[str] = mapped_column(String, nullable=True)
    utm_content: Mapped[str] = mapped_column(String, nullable=True)
    

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    deleted_at: Mapped[datetime] = mapped_column(default=None, nullable=True)
    
    # Indexes
    Index('users_email_index', email)
    
    
class Conversation(db.Model):
    __tablename__ = 'conversations'
    
    # Identifiers
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'), nullable=False)
    
    # Data
    state: Mapped[ConvoStateEnum] = mapped_column(SQLAlchemyEnum(ConvoStateEnum), nullable=False, default=ConvoStateEnum.START)
    oneline_summary: Mapped[str] = mapped_column(String, nullable=True)
    ephemeral: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    
    # Timestamps
    last_active_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    deleted_at: Mapped[datetime] = mapped_column(default=None, nullable=True)
    
    # Relationships
    user = relationship('User', backref='conversations')
    
   # Indexes
    Index('conversations_user_id_index', user_id)


class Message(db.Model):
    __tablename__ = 'messages'
    
    # Identifiers
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'), nullable=False)
    conversation_id: Mapped[int] = mapped_column(Integer, ForeignKey('conversations.id'), nullable=False)
    
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
    user = relationship('User', backref='messages')
    conversation = relationship('Conversation', backref='messages')
    
    # Indexes
    Index('messages_user_id_index', user_id)
    Index('messages_conversation_id_index', conversation_id)

class AnalysisData(db.Model):
    __tablename__ = 'analysis_data'
    
    # Identifiers
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'), nullable=False)
    conversation_id: Mapped[int] = mapped_column(Integer, ForeignKey('conversations.id'), nullable=False)
    # message_id: Mapped[int] = mapped_column(Integer, ForeignKey('messages.id'), nullable=False)
    
    # Data
    field: Mapped[str] = mapped_column(String, nullable=False)
    content: Mapped[int] = mapped_column(String, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    deleted_at: Mapped[datetime] = mapped_column(default=None, nullable=True)
    
    # Relationships
    user = relationship('User', backref='ratings')
    conversation = relationship('Conversation', backref='ratings')
    # message = relationship('Message', backref='ratings')
    
    # Indexes
    Index('ratings_user_id_index', user_id)
    Index('ratings_conversation_id_index', conversation_id)
    # Index('ratings_message_id_index', message_id)
    
    
    
    
class Donation(db.Model):
    __tablename__ = 'donations'
    
    # Identifiers
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'), nullable=False)
    
    # Data
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    deleted_at: Mapped[datetime] = mapped_column(default=None, nullable=True)
    
    # Relationships
    user = relationship('User', backref='donations')
    
    # Indexes
    Index('donations_user_id_index', user_id)
    
class Support(db.Model):
    __tablename__ = 'support'
    
    # Identifiers
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'), nullable=False)
    
    # Data
    query_type: Mapped[FeedbackEnum] = mapped_column(SQLAlchemyEnum(FeedbackEnum), nullable=False)
    is_urgent: Mapped[bool] = mapped_column(Boolean, nullable=False)
    is_resolved: Mapped[bool] = mapped_column(Boolean, nullable=False)
    query: Mapped[str] = mapped_column(String, nullable=False)  # e.g., "I am having trouble logging in."s
    messages: Mapped[dict] = mapped_column(JSONB, nullable=True)  # e.g., [{"message": "I am having trouble logging in.", "attachments": ["screenshot.png"], "sender": "user"}]
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    deleted_at: Mapped[datetime] = mapped_column(default=None, nullable=True)
    
    # Relationships
    user = relationship('User', backref='support')
    
    # Indexes
    Index('support_user_id_index', user_id)


class LLMQuery(db.Model):
    __tablename__ = 'llm_queries'
    
    # Identifiers
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'), nullable=True)
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
    user = relationship('User', backref='llm_queries')
    message = relationship('Message', backref='llm_queries')
    
    # Indexes
    Index('llm_queries_user_id_index', user_id)
    Index('llm_queries_message_id_index', message_id)