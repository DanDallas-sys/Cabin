from sqlalchemy import (
    Column, Integer, String, Float, DateTime,
    ForeignKey, Enum, Index
)
from sqlalchemy.orm import relationship
from database import Base
import datetime
import enum


class TransactionStatus(str, enum.Enum):
    pending = "pending"
    processed = "processed"
    low_confidence = "low_confidence"
    uncategorized = "uncategorized"
    reversal = "reversal"
    internal_transfer = "internal_transfer"


class TransactionType(str, enum.Enum):
    credit = "credit"
    debit = "debit"
    reversal = "reversal"
    internal_transfer = "internal_transfer"


class ClarificationStatus(str, enum.Enum):
    pending = "pending"
    nudged = "nudged"
    resolved = "resolved"
    abandoned = "abandoned"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    phone = Column(String, unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    transactions = relationship("Transaction", back_populates="user")
    clarification_requests = relationship("ClarificationRequest", back_populates="user")


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    amount = Column(Float, nullable=False)
    narration = Column(String, nullable=True)
    cleaned_narration = Column(String, nullable=True)

    category = Column(String, nullable=True)
    type = Column(
        Enum(TransactionType, name="transaction_type"),
        nullable=False,
        default=TransactionType.debit
    )

    reference = Column(String, unique=True, nullable=False, index=True)

    status = Column(
        Enum(TransactionStatus, name="transaction_status"),
        nullable=False,
        default=TransactionStatus.pending
    )
    confidence = Column(Float, default=0.0)

    date = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="transactions")
    clarification_requests = relationship("ClarificationRequest", back_populates="transaction")

    __table_args__ = (
        Index("ix_transactions_user_date", "user_id", "date"),
    )


class ClarificationRequest(Base):
    __tablename__ = "clarification_requests"

    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(Integer, ForeignKey("transactions.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    status = Column(
        Enum(ClarificationStatus, name="clarification_status"),
        nullable=False,
        default=ClarificationStatus.pending
    )

    prompt_sent_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    nudge_sent_at = Column(DateTime, nullable=True)
    resolved_at = Column(DateTime, nullable=True)

    transaction = relationship("Transaction", back_populates="clarification_requests")
    user = relationship("User", back_populates="clarification_requests")
