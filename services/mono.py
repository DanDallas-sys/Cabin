"""
Mono API client — fetches transactions after receiving account_updated webhook.
Docs: https://docs.mono.co/reference/get-transactions
"""
import httpx
from datetime import datetime
from config import get_settings

settings = get_settings()

MONO_BASE_URL = "https://api.withmono.com/v2"


def fetch_mono_transactions(account_id: str) -> list[dict]:
    """
    Fetch transactions for an account from Mono API.
    Returns a list of raw transaction dicts.
    """
    headers = {
        "mono-sec-key": settings.mono_secret_key,
        "Content-Type": "application/json",
    }

    try:
        with httpx.Client(timeout=30) as client:
            response = client.get(
                f"{MONO_BASE_URL}/accounts/{account_id}/transactions",
                headers=headers,
                params={"limit": 100, "paginate": "false"},
            )
            response.raise_for_status()
            data = response.json()
            txs = data.get("data", [])
            print(f"[Mono] Fetched {len(txs)} transactions for account {account_id}")
            if txs:
                print(f"[Mono] Sample transaction structure: {txs[0]}")
            return txs

    except httpx.HTTPError as e:
        print(f"[Mono] Failed to fetch transactions for {account_id}: {e}")
        return []
