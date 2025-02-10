# db/crud.py

from typing import Optional, List, Dict
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta
from sqlalchemy.sql import or_, and_
from db.models import (
    Conversation, 
    Message, 
    AnalysisData,
    LLMQuery,
    RoleEnum,
    ResponseTypeEnum,
    ConvoStateEnum
)
from flask import current_app
import secrets

# ======================= Helper Functions =======================
def include_deleted_records(query, model, include_deleted: bool):
    """
    Helper function to include or exclude soft-deleted records in a query.

    Args:
        query: The SQLAlchemy query object.
        model: The model class (e.g., Conversation).
        include_deleted: Whether to include soft-deleted records.

    Returns:
        The modified query.
    """
    if not include_deleted:
        query = query.where(model.deleted_at.is_(None))
    return query



# ======================= CONVERSATIONS =======================
def get_conversation_by_id(
    session: Session,
    convo_id: int,
    include_deleted: bool = False
) -> Optional[Conversation]:
    """
    Fetch a Conversation by its ID, optionally including soft-deleted conversations.

    Args:
        session (Session): The database session.
        convo_id (int): The ID of the conversation to fetch.
        include_deleted (bool): Whether to include soft-deleted conversations.

    Returns:
        Optional[Conversation]: The Conversation object if found, else None.
    """
    stmt = select(Conversation).where(Conversation.id == convo_id)
    stmt = include_deleted_records(stmt, Conversation, include_deleted)
    result = session.execute(stmt)
    return result.scalar_one_or_none()


def get_conversation_by_pid_code(
    session: Session,
    pid: str,
    convo_code: str,
    include_deleted: bool = False
) -> List[Conversation]:
    """
    Fetch all conversations for a given PID, optionally including soft-deleted conversations.

    Args:
        session (Session): The database session.
        pid (str): The PID of the user.
        convo_code (str): The conversation code.
        include_deleted (bool): Whether to include soft-deleted conversations.

    Returns:
        List[Conversation]: A list of Conversation objects.
    """
    stmt = select(Conversation).where(Conversation.pid == pid,
                                      Conversation.convo_code == convo_code)
    stmt = include_deleted_records(stmt, Conversation, include_deleted)
    result = session.execute(stmt)
    return result.scalar_one_or_none()


def create_conversation(
    session: Session,
    pid: int,
    convo_code: str,
) -> Conversation:
    """
    Create a new Conversation record for a given user.

    Args:
        session (Session): The database session.
        pid (int): The pid of the user for whom to create the conversation.
        convo_code (str): The conversation code.

    Returns:
        Conversation: The newly created conversation object. (No commit here)
    """
    conversation = Conversation(
        pid=pid,
        convo_code=convo_code,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        deleted_at=None
    )
    session.add(conversation)
    return conversation


def update_conversation(
    session: Session,
    conversation: Conversation,
    **kwargs
) -> Conversation:
    """
    Update an existing Conversation record with provided keyword arguments.

    Args:
        session (Session): The database session.
        conversation (Conversation): The Conversation object to update.
        **kwargs: Fields to be updated

    Returns:
        Conversation: The updated Conversation object. (No commit here)
    """
    for key, value in kwargs.items():
        setattr(conversation, key, value)
    conversation.updated_at = datetime.now(timezone.utc)
    return conversation


def soft_delete_conversation(
    session: Session,
    conversation: Conversation
) -> Conversation:
    """
    Soft-delete a conversation by setting its deleted_at field.

    Args:
        session (Session): The database session.
        conversation (Conversation): The Conversation object to soft-delete.

    Returns:
        Conversation: The soft-deleted conversation object. (No commit here)
    """
    conversation.deleted_at = datetime.now(timezone.utc)
    conversation.updated_at = datetime.now(timezone.utc)
    return conversation


# ======================= MESSAGES =======================
def get_message_by_id(
    session: Session,
    message_id: int,
    include_deleted: bool = False
) -> Optional[Message]:
    """
    Fetch a Message by its ID, optionally including soft-deleted messages.

    Args:
        session (Session): The database session.
        message_id (int): The ID of the message to fetch.
        include_deleted (bool): Whether to include soft-deleted messages.

    Returns:
        Optional[Message]: The Message object if found, else None.
    """
    stmt = select(Message).where(Message.id == message_id)
    stmt = include_deleted_records(stmt, Message, include_deleted)
    result = session.execute(stmt)
    return result.scalar_one_or_none()


def get_conversation_messages(
    session: Session,
    convo_id: int,
    include_deleted: bool = False
) -> List[Message]:
    """
    Fetch all messages for a given conversation, optionally including soft-deleted messages.

    Args:
        session (Session): The database session.
        convo_id (int): The ID of the conversation.
        include_deleted (bool): Whether to include soft-deleted messages.

    Returns:
        List[Message]: A list of Message objects.
    """
    stmt = select(Message).where(Message.convo_id == convo_id).order_by(Message.created_at)
    stmt = include_deleted_records(stmt, Message, include_deleted)
    result = session.execute(stmt)
    return result.scalars().all()

def create_message(
    session: Session,
    convo_id: int,
    content: str,
    state: ConvoStateEnum,
    role: RoleEnum,
    response_type: ResponseTypeEnum,
    options: Optional[Dict] = None,
) -> Message:
    """
    Create a new Message record.
    Update the conversation's last_active_at and state fields.

    Args:
        session (Session): The database session.
        convo_id (int): The ID of the conversation to which the message belongs.
        content (str): The message content.
        state (ConvoStateEnum): The state of the conversation.
        role (RoleEnum): The role of the message sender.
        response_type (ResponseTypeEnum): The type of response (e.g., text, image).

    Returns:
        Message: The newly created message object. 
    """
    conversation = get_conversation_by_id(session, convo_id)
    if conversation:
        conversation.last_active_at = datetime.now(timezone.utc)
        conversation.state = state
    msg = Message(
        convo_id=convo_id,
        content=str(content),
        role=role,
        response_type=response_type,
        options=options,
        state=state,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        deleted_at=None
    )
    session.add(msg)
    return msg


def update_message(
    session: Session,
    message: Message,
    **kwargs
) -> Message:
    """
    Update an existing Message record with provided keyword arguments.

    Args:
        session (Session): The database session.
        message (Message): The Message object to update.
        **kwargs: Fields to be updated, e.g., message="New text content".

    Returns:
        Message: The updated Message object. (No commit here)
    """
    for key, value in kwargs.items():
        setattr(message, key, value)
    message.updated_at = datetime.now(timezone.utc)
    return message


def soft_delete_message(
    session: Session,
    message: Message
) -> Message:
    """
    Soft-delete a message by setting its deleted_at field.

    Args:
        session (Session): The database session.
        message (Message): The Message object to soft-delete.

    Returns:
        Message: The soft-deleted Message object. (No commit here)
    """
    message.deleted_at = datetime.now(timezone.utc)
    message.updated_at = datetime.now(timezone.utc)
    return message



# ======================= AnalysisData =======================

def create_analysis_data(
    session: Session, 
    convo_id: int,
    field: str, 
    content: str
    ) -> AnalysisData:
    """
    Create a new row in the analysis_data table.
    """
    data = AnalysisData(
        convo_id=convo_id,
        field=str(field),
        content=str(content),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        deleted_at=None
    )
    session.add(data)
    return data




def get_conversation_analysis_data(
    session: Session, 
    convo_id: int, 
    include_deleted: bool = False
    ) -> List[AnalysisData]:
    """
    Fetch all analysis data for a given conversation, optionally including soft-deleted data.
    """
    stmt = select(AnalysisData).where(AnalysisData.convo_id == convo_id)
    stmt = include_deleted_records(stmt, AnalysisData, include_deleted)
    stmt = stmt.order_by(AnalysisData.updated_at.desc())
    result = session.execute(stmt)
    return result.scalars().all()


def update_analyis_data(session: Session, data: AnalysisData, **kwargs) -> AnalysisData:
    """
    Update fields on the analysis_data table.
    """
    for key, value in kwargs.items():
        setattr(data, key, value)
    data.updated_at = datetime.now(timezone.utc)
    return data


# ======================= LLM QUERIES =======================

def create_llm_query(session: Session, convo_id: int, completion: Dict, message_id: int=None, prompt_messages=None, **kwargs) -> LLMQuery:
    """
    Create a new row in the llm_queries table.
    """
    data = LLMQuery(
        convo_id=convo_id,
        message_id=message_id,
        completion=completion,
        prompt_messages=prompt_messages,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        deleted_at=None,
        **kwargs
    )
    session.add(data)
    return data

def update_llm_query(session: Session, data: LLMQuery, **kwargs) -> LLMQuery:
    """
    Update fields on the llm_queries table.
    """
    for key, value in kwargs.items():
        setattr(data, key, value)
    data.updated_at = datetime.now(timezone.utc)
    return data