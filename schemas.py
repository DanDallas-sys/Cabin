from pydantic import BaseModel, field_validator
from datetime import datetime
from typing import Optional


class TransactionIn(BaseModel):
    """Incoming transaction payload from bank provider webhook."""
    amount: float
    narration: Optional[str] = None
    reference: str
    date: datetime
    user_phone: str

    @field_validator("user_phone")
    @classmethod
    def normalise_phone(cls, v: str) -> str:
        """Strip spaces and ensure leading + for international format."""
        v = v.strip().replace(" ", "")
        if not v.startswith("+"):
            v = "+" + v
        return v


class TransactionOut(BaseModel):
    id: int
    amount: float
    narration: Optional[str]
    cleaned_narration: Optional[str]
    category: Optional[str]
    type: str
    status: str
    confidence: float
    date: datetime

    model_config = {"from_attributes": True}


class WhatsAppWebhookIn(BaseModel):
    """Twilio sends form data; FastAPI will parse it from form fields."""
    From: str
    Body: str


class ReportOut(BaseModel):
    user_id: int
    file_path: str
    total_transactions: int


class MonoWebhookEvent(BaseModel):
    """Mono webhook event envelope."""
    event: str
    data: dict
