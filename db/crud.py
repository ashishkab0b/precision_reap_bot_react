# db/crud.py

from typing import Optional, List, Dict
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta
from sqlalchemy.sql import or_, and_
from db.models import (
    User, 
    Conversation, 
    Message, 
    Donation, 
    Support,
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
        model: The model class (e.g., User, Conversation).
        include_deleted: Whether to include soft-deleted records.

    Returns:
        The modified query.
    """
    if not include_deleted:
        query = query.where(model.deleted_at.is_(None))
    return query


# ======================= USERS =======================
def get_user_by_id(
    session: Session, 
    user_id: int, 
    include_deleted: bool = False
) -> Optional[User]:
    """
    Fetch user by ID, optionally including soft-deleted users.

    Args:
        session (Session): The database session.
        user_id (int): The ID of the user to fetch.
        include_deleted (bool): Whether to include soft-deleted users.

    Returns:
        Optional[User]: The User object if found, else None.
    """
    stmt = select(User).where(User.id == user_id)
    stmt = include_deleted_records(stmt, User, include_deleted)
    result = session.execute(stmt)
    return result.scalar_one_or_none()


def get_user_by_email(
    session: Session, 
    email: str, 
    include_deleted: bool = False
) -> Optional[User]:
    """
    Fetch user by email, optionally including soft-deleted users.

    Args:
        session (Session): The database session.
        email (str): The email of the user to fetch.
        include_deleted (bool): Whether to include soft-deleted users.

    Returns:
        Optional[User]: The User object if found, else None.
    """
    stmt = select(User).where(User.email == email)
    stmt = include_deleted_records(stmt, User, include_deleted)
    result = session.execute(stmt)
    return result.scalar_one_or_none()


def create_user(
    session: Session,
    email: str,
    password_hash: str,
    **kwargs
) -> User:
    """
    Create a new User record.
    
    Args:
        session (Session): The database session.
        email (str): The email of the user.
        password_hash (str): The hashed password for the user.
        
    Keyword Args:
        utm_source (Optional[str]): UTM source parameter.
        utm_medium (Optional[str]): UTM medium parameter.
        utm_campaign (Optional[str]): UTM campaign parameter.
        utm_term (Optional[str]): UTM term parameter.
        utm_content (Optional[str]): UTM content parameter.

    Returns:
        User: The newly created user object. (No commit here)
    """
    otp = secrets.token_hex(16)
    otp_expiry_ts = datetime.now(timezone.utc) + timedelta(minutes=current_app.config['NEW_USER_OTP_EXPIRY_MIN'])
    
    user = User(
        email=email,
        password_hash=password_hash,
        otp=otp,
        otp_expiry_ts=otp_expiry_ts,
        **kwargs,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        deleted_at=None
    )
    session.add(user)
    return user


def update_user(
    session: Session,
    user: User,
    **kwargs
) -> User:
    """
    Update an existing User record with provided keyword arguments.

    Args:
        session (Session): The database session.
        user (User): The User object to update.
        **kwargs: Fields to be updated

    Returns:
        User: The updated User object. (No commit here)
    """
    for key, value in kwargs.items():
        setattr(user, key, value)
    user.updated_at = datetime.now(timezone.utc)
    return user


def soft_delete_user(
    session: Session,
    user: User
) -> User:
    """
    Soft-delete a user by setting its deleted_at field.
    
    Args:
        session (Session): The database session.
        user (User): The User object to soft-delete.

    Returns:
        User: The soft-deleted user object. (No commit here)
    """
    user.deleted_at = datetime.now(timezone.utc)
    user.updated_at = datetime.now(timezone.utc)
    return user


# ======================= CONVERSATIONS =======================
def get_conversation_by_id(
    session: Session,
    conversation_id: int,
    include_deleted: bool = False
) -> Optional[Conversation]:
    """
    Fetch a Conversation by its ID, optionally including soft-deleted conversations.

    Args:
        session (Session): The database session.
        conversation_id (int): The ID of the conversation to fetch.
        include_deleted (bool): Whether to include soft-deleted conversations.

    Returns:
        Optional[Conversation]: The Conversation object if found, else None.
    """
    stmt = select(Conversation).where(Conversation.id == conversation_id)
    stmt = include_deleted_records(stmt, Conversation, include_deleted)
    result = session.execute(stmt)
    return result.scalar_one_or_none()


def get_user_conversations(
    session: Session,
    user_id: int,
    include_deleted: bool = False
) -> List[Conversation]:
    """
    Fetch all conversations for a given user, optionally including soft-deleted conversations.

    Args:
        session (Session): The database session.
        user_id (int): The ID of the user whose conversations to fetch.
        include_deleted (bool): Whether to include soft-deleted conversations.

    Returns:
        List[Conversation]: A list of Conversation objects.
    """
    stmt = select(Conversation).where(Conversation.user_id == user_id)
    stmt = include_deleted_records(stmt, Conversation, include_deleted)
    stmt = stmt.order_by(Conversation.updated_at.desc())
    result = session.execute(stmt)
    return result.scalars().all()


def create_conversation(
    session: Session,
    user_id: int
) -> Conversation:
    """
    Create a new Conversation record for a given user.

    Args:
        session (Session): The database session.
        user_id (int): The ID of the user for whom to create the conversation.

    Returns:
        Conversation: The newly created conversation object. (No commit here)
    """
    conversation = Conversation(
        user_id=user_id,
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
        **kwargs: Fields to be updated, e.g., user_id=123.

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
    conversation_id: int,
    include_deleted: bool = False
) -> List[Message]:
    """
    Fetch all messages for a given conversation, optionally including soft-deleted messages.

    Args:
        session (Session): The database session.
        conversation_id (int): The ID of the conversation.
        include_deleted (bool): Whether to include soft-deleted messages.

    Returns:
        List[Message]: A list of Message objects.
    """
    stmt = select(Message).where(Message.conversation_id == conversation_id)
    stmt = include_deleted_records(stmt, Message, include_deleted)
    result = session.execute(stmt)
    return result.scalars().all()


def get_user_messages(
    session: Session,
    user_id: int,
    include_deleted: bool = False
) -> List[Message]:
    """
    Fetch all messages for a given user, optionally including soft-deleted messages.

    Args:
        session (Session): The database session.
        user_id (int): The ID of the user.
        include_deleted (bool): Whether to include soft-deleted messages.

    Returns:
        List[Message]: A list of Message objects.
    """
    stmt = select(Message).where(Message.user_id == user_id)
    stmt = include_deleted_records(stmt, Message, include_deleted)
    result = session.execute(stmt)
    return result.scalars().all()


def create_message(
    session: Session,
    user_id: int,
    conversation_id: int,
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
        user_id (int): The ID of the user creating the message.
        conversation_id (int): The ID of the conversation to which the message belongs.
        content (str): The message content.
        state (ConvoStateEnum): The state of the conversation.
        role (RoleEnum): The role of the message sender.
        response_type (ResponseTypeEnum): The type of response (e.g., text, image).

    Returns:
        Message: The newly created message object. 
    """
    conversation = get_conversation_by_id(session, conversation_id)
    if conversation:
        conversation.last_active_at = datetime.now(timezone.utc)
        conversation.state = state
    msg = Message(
        user_id=user_id,
        conversation_id=conversation_id,
        content=content,
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


# ======================= DONATIONS =======================
def get_donation_by_id(
    session: Session,
    donation_id: int,
    include_deleted: bool = False
) -> Optional[Donation]:
    """
    Fetch a Donation by its ID, optionally including soft-deleted donations.

    Args:
        session (Session): The database session.
        donation_id (int): The ID of the donation to fetch.
        include_deleted (bool): Whether to include soft-deleted donations.

    Returns:
        Optional[Donation]: The Donation object if found, else None.
    """
    stmt = select(Donation).where(Donation.id == donation_id)
    stmt = include_deleted_records(stmt, Donation, include_deleted)
    result = session.execute(stmt)
    return result.scalar_one_or_none()


def get_user_donations(
    session: Session,
    user_id: int,
    include_deleted: bool = False
) -> List[Donation]:
    """
    Fetch all donations for a given user, optionally including soft-deleted donations.

    Args:
        session (Session): The database session.
        user_id (int): The ID of the user whose donations to fetch.
        include_deleted (bool): Whether to include soft-deleted donations.

    Returns:
        List[Donation]: A list of Donation objects.
    """
    stmt = select(Donation).where(Donation.user_id == user_id)
    stmt = include_deleted_records(stmt, Donation, include_deleted)
    result = session.execute(stmt)
    return result.scalars().all()


def create_donation(
    session: Session,
    user_id: int,
    amount: float
) -> Donation:
    """
    Create a new Donation record.

    Args:
        session (Session): The database session.
        user_id (int): The ID of the user making the donation.
        amount (float): The donation amount.

    Returns:
        Donation: The newly created Donation object. (No commit here)
    """
    donation = Donation(
        user_id=user_id,
        amount=amount,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        deleted_at=None
    )
    session.add(donation)
    return donation


def update_donation(
    session: Session,
    donation: Donation,
    **kwargs
) -> Donation:
    """
    Update an existing Donation record with provided keyword arguments.

    Args:
        session (Session): The database session.
        donation (Donation): The Donation object to update.
        **kwargs: Fields to be updated, e.g., amount=99.99.

    Returns:
        Donation: The updated Donation object. (No commit here)
    """
    for key, value in kwargs.items():
        setattr(donation, key, value)
    donation.updated_at = datetime.now(timezone.utc)
    return donation


def soft_delete_donation(
    session: Session,
    donation: Donation
) -> Donation:
    """
    Soft-delete a donation by setting its deleted_at field.

    Args:
        session (Session): The database session.
        donation (Donation): The Donation object to soft-delete.

    Returns:
        Donation: The soft-deleted Donation object. (No commit here)
    """
    donation.deleted_at = datetime.now(timezone.utc)
    donation.updated_at = datetime.now(timezone.utc)
    return donation


# ======================= SUPPORT =======================
def get_support_by_id(
    session: Session,
    support_id: int,
    include_deleted: bool = False
) -> Optional[Support]:
    """
    Fetch a Support record by its ID, optionally including soft-deleted records.

    Args:
        session (Session): The database session.
        support_id (int): The ID of the support record to fetch.
        include_deleted (bool): Whether to include soft-deleted records.

    Returns:
        Optional[Support]: The Support object if found, else None.
    """
    stmt = select(Support).where(Support.id == support_id)
    stmt = include_deleted_records(stmt, Support, include_deleted)
    result = session.execute(stmt)
    return result.scalar_one_or_none()


def get_user_support_queries(
    session: Session,
    user_id: int,
    include_deleted: bool = False
) -> List[Support]:
    """
    Fetch all Support records for a given user, optionally including soft-deleted records.

    Args:
        session (Session): The database session.
        user_id (int): The ID of the user whose support records to fetch.
        include_deleted (bool): Whether to include soft-deleted records.

    Returns:
        List[Support]: A list of Support objects.
    """
    stmt = select(Support).where(Support.user_id == user_id)
    stmt = include_deleted_records(stmt, Support, include_deleted)
    result = session.execute(stmt)
    return result.scalars().all()


def create_support_query(
    session: Session,
    user_id: int,
    query_type: str,
    is_urgent: bool,
    is_resolved: bool,
    query: str,
    messages: Optional[Dict] = None,
    notes: Optional[str] = None
) -> Support:
    """
    Create a new Support record.

    Args:
        session (Session): The database session.
        user_id (int): The ID of the user.
        query_type (str): The type of the query (e.g., 'bug', 'feature', etc.).
        is_urgent (bool): Whether the issue is urgent.
        is_resolved (bool): Whether the issue is resolved at creation time.
        query (str): The main query text.
        messages (Optional[Dict]): Additional messages or attachments in a JSON structure.
        notes (Optional[str]): Internal notes about this support query.

    Returns:
        Support: The newly created Support object. (No commit here)
    """
    support_record = Support(
        user_id=user_id,
        query_type=query_type,
        is_urgent=is_urgent,
        is_resolved=is_resolved,
        query=query,
        messages=messages,
        notes=notes,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        deleted_at=None
    )
    session.add(support_record)
    return support_record


def update_support_query(
    session: Session,
    support_record: Support,
    **kwargs
) -> Support:
    """
    Update an existing Support record with provided keyword arguments.

    Args:
        session (Session): The database session.
        support_record (Support): The Support object to update.
        **kwargs: Fields to be updated, e.g., is_resolved=True, notes="Issue resolved".

    Returns:
        Support: The updated Support object. (No commit here)
    """
    for key, value in kwargs.items():
        setattr(support_record, key, value)
    support_record.updated_at = datetime.now(timezone.utc)
    return support_record


def soft_delete_support_query(
    session: Session,
    support_record: Support
) -> Support:
    """
    Soft-delete a Support record by setting its deleted_at field.

    Args:
        session (Session): The database session.
        support_record (Support): The Support object to soft-delete.

    Returns:
        Support: The soft-deleted Support object. (No commit here)
    """
    support_record.deleted_at = datetime.now(timezone.utc)
    support_record.updated_at = datetime.now(timezone.utc)
    return support_record


# ======================= AnalysisData =======================

def create_analysis_data(
    session: Session, 
    user_id: int,
    conversation_id: int,
    field: str, 
    content: str
    ) -> AnalysisData:
    """
    Create a new row in the analysis_data table.
    """
    data = AnalysisData(
        user_id=user_id,
        conversation_id=conversation_id,
        field=field,
        content=content,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        deleted_at=None
    )
    session.add(data)
    return data

def get_user_analysis_data(
    session: Session, 
    user_id: int, 
    include_deleted: bool = False
    ) -> List[AnalysisData]:
    """
    Fetch all analysis data for a given user, optionally including soft-deleted data.
    """
    stmt = select(AnalysisData).where(AnalysisData.user_id == user_id)
    stmt = include_deleted_records(stmt, AnalysisData, include_deleted)
    stmt = stmt.order_by(AnalysisData.updated_at.desc())
    result = session.execute(stmt)
    return result.scalars().all()


def get_conversation_analysis_data(
    session: Session, 
    conversation_id: int, 
    include_deleted: bool = False
    ) -> List[AnalysisData]:
    """
    Fetch all analysis data for a given conversation, optionally including soft-deleted data.
    """
    stmt = select(AnalysisData).where(AnalysisData.conversation_id == conversation_id)
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

def create_llm_query(session: Session, user_id: int, completion: Dict, message_id: int=None, **kwargs) -> LLMQuery:
    """
    Create a new row in the llm_queries table.
    """
    data = LLMQuery(
        user_id=user_id,
        message_id=message_id,
        completion=completion,
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