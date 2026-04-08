from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
from config import get_settings

settings = get_settings()

_client = Client(settings.twilio_account_sid, settings.twilio_auth_token)


def _whatsapp_number(phone: str) -> str:
    """Ensure phone is in whatsapp:+234XXXXXXXXXX format."""
    phone = phone.strip()
    if not phone.startswith("whatsapp:"):
        phone = f"whatsapp:{phone}"
    return phone


def send_whatsapp_message(phone: str, message: str) -> bool:
    """
    Send a WhatsApp message via Twilio.
    Returns True on success, False on failure.
    """
    try:
        msg = _client.messages.create(
            from_=settings.twilio_whatsapp_from,
            to=_whatsapp_number(phone),
            body=message,
        )
        print(f"[WhatsApp] Sent to {phone} | SID: {msg.sid}")
        return True
    except TwilioRestException as e:
        print(f"[WhatsApp] Failed to send to {phone}: {e}")
        return False


# ── Pre-built message templates ───────────────────────────────────────────────

def send_clarification_prompt(phone: str, amount: float, tx_type: str) -> bool:
    direction = "debited from" if tx_type == "debit" else "credited to"
    message = (
        f"Hi! We noticed ₦{abs(amount):,.2f} was {direction} your account "
        f"but we couldn't identify what it was for.\n\n"
        f"Could you briefly describe what this transaction was for? "
        f"(e.g. 'bought groceries', 'paid rent', 'Uber ride')"
    )
    return send_whatsapp_message(phone, message)


def send_nudge_message(phone: str, amount: float) -> bool:
    message = (
        f"Quick reminder 👋 — we still haven't been able to categorise your "
        f"₦{abs(amount):,.2f} transaction. What was it for?"
    )
    return send_whatsapp_message(phone, message)
