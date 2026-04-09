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
        # Mono v2 API uses 'id', v1 uses '_id' — handle both
        reference = tx.get("id") or tx.get("_id")
        if not reference:
            raise KeyError("_id")
        # Amount: Mono v2 returns whole naira, v1 returns kobo
        raw_amount = float(tx["amount"])
        amount = raw_amount / 100 if raw_amount > 100000 else raw_amount
        # Type: debit is negative, credit is positive
        tx_type = tx.get("type", "debit").lower()
        if tx_type == "debit":
            amount = -abs(amount)
        else:
            amount = abs(amount)
        return TransactionIn(
            amount=amount,
            narration=tx.get("narration") or tx.get("description") or tx.get("notes"),
            reference=reference,
            date=datetime.fromisoformat(tx["date"].replace("Z", "+00:00")),
            user_phone=user_phone,
        )
    except (KeyError, ValueError, TypeError) as e:
        print(f"[Mono] Failed to parse transaction: {e}")
        return None
