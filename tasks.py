from celery_worker import celery
from database import SessionLocal
from models import ClarificationRequest, Transaction, User, ClarificationStatus, TransactionStatus
from datetime import datetime, timedelta
from services.whatsapp import send_nudge_message


@celery.task(name="tasks.check_clarifications")
def check_clarifications():
    """
    Daily job:
    - Day 2: send nudge if user hasn't replied
    - Day 4: mark transaction as uncategorized, abandon request
    """
    db = SessionLocal()
    now = datetime.utcnow()

    try:
        pending_requests = db.query(ClarificationRequest).filter(
            ClarificationRequest.status.in_([
                ClarificationStatus.pending,
                ClarificationStatus.nudged,
            ])
        ).all()

        for req in pending_requests:
            delta = now - req.prompt_sent_at

            # Look up the user's real phone number
            user = db.get(User, req.user_id)
            tx = db.get(Transaction, req.transaction_id)

            if not user or not tx:
                req.status = ClarificationStatus.abandoned
                continue

            if delta >= timedelta(days=4):
                # Abandon — mark transaction as uncategorized
                tx.status = TransactionStatus.uncategorized
                req.status = ClarificationStatus.abandoned
                print(f"[Tasks] Abandoned clarification for tx {tx.id} (user {user.phone})")

            elif delta >= timedelta(days=2) and req.status == ClarificationStatus.pending:
                # Nudge
                send_nudge_message(user.phone, tx.amount)
                req.status = ClarificationStatus.nudged
                req.nudge_sent_at = now
                print(f"[Tasks] Nudged user {user.phone} for tx {tx.id}")

        db.commit()

    except Exception as e:
        db.rollback()
        print(f"[Tasks] check_clarifications failed: {e}")
        raise

    finally:
        db.close()
