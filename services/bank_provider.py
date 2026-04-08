"""
Bank provider integration — Mono only.
Handles incoming Mono webhooks and normalises them
into our internal TransactionIn schema.
"""
import hmac
import hashlib
from datetime import datetime
from schemas import TransactionIn
from config import get_settings

settings = get_settings()


def verify_mono_signature(payload: bytes, signature: str) -> bool:
    """Verify Mono webhook HMAC-SHA512 signature."""
    expected = hmac.new(
        settings.mono_secret_key.encode(),
        payload,
        hashlib.sha512
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


def parse_mono_transaction(event_data: dict, user_phone: str) -> "TransactionIn | None":
    """
    Parse a Mono transaction event into our internal schema.
    Mono sends amounts in kobo (smallest unit) so we divide by 100.
    Docs: https://docs.mono.co/reference/transaction-sync
    """
    try:
        tx = event_data.get("transaction", event_data)
        return TransactionIn(
            amount=float(tx["amount"]) / 100,
            narration=tx.get("narration") or tx.get("description"),
            reference=tx["_id"],
            date=datetime.fromisoformat(tx["date"].replace("Z", "+00:00")),
            user_phone=user_phone,
        )
    except (KeyError, ValueError, TypeError) as e:
        print(f"[Mono] Failed to parse transaction: {e}")
        return None
