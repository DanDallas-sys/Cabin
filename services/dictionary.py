"""
Pattern dictionary for fast, zero-cost transaction classification.
Patterns are checked BEFORE the AI classifier to save API calls.
Add new patterns here as you encounter them.
"""

# Format: "keyword_in_narration_lowercase": "category"
KNOWN_PATTERNS: dict[str, str] = {
    # ── Transfers / P2P ───────────────────────────────────
    "opay": "transfer",
    "kuda": "transfer",
    "palmpay": "transfer",
    "piggytech": "savings_and_investment",
    "cowrywise": "savings_and_investment",
    "bamboo": "savings_and_investment",
    "chaka": "savings_and_investment",
    "risevest": "savings_and_investment",
    "nip transfer": "transfer",
    "instant payment": "transfer",
    "interbank": "transfer",

    # ── Transport ────────────────────────────────────────
    "uber": "transport",
    "bolt": "transport",
    "taxify": "transport",
    "rida": "transport",
    "indriver": "transport",
    "fuel": "transport",
    "petrol": "transport",
    "total energies": "transport",
    "ardova": "transport",
    "oando": "transport",
    "air peace": "transport",
    "arik": "transport",
    "dana air": "transport",
    "max.ng": "transport",
    "gokada": "transport",

    # ── Food & Dining ─────────────────────────────────────
    "jumia food": "food_and_dining",
    "chowdeck": "food_and_dining",
    "glovo": "food_and_dining",
    "dominos": "food_and_dining",
    "chicken republic": "food_and_dining",
    "tastee": "food_and_dining",
    "mr biggs": "food_and_dining",
    "shoprite": "food_and_dining",
    "spar": "food_and_dining",

    # ── Utilities ────────────────────────────────────────
    "dstv": "utilities",
    "gotv": "utilities",
    "startimes": "utilities",
    "phcn": "utilities",
    "nepa": "utilities",
    "ikedc": "utilities",
    "ekedc": "utilities",
    "aedc": "utilities",
    "phedc": "utilities",
    "lawma": "utilities",
    "rccg": "utilities",

    # ── Subscriptions ────────────────────────────────────
    "netflix": "subscriptions",
    "spotify": "subscriptions",
    "apple.com": "subscriptions",
    "google one": "subscriptions",
    "youtube premium": "subscriptions",
    "showmax": "subscriptions",
    "boomplay": "subscriptions",

    # ── Shopping ─────────────────────────────────────────
    "jumia": "shopping",
    "konga": "shopping",
    "jiji": "shopping",
    "payporte": "shopping",

    # ── Airtime & Data ───────────────────────────────────
    "mtn": "airtime_and_data",
    "airtel": "airtime_and_data",
    "glo": "airtime_and_data",
    "9mobile": "airtime_and_data",
    "etisalat": "airtime_and_data",
    "vtpass": "airtime_and_data",
    "buypower": "utilities",

    # ── Health ───────────────────────────────────────────
    "pharmacy": "health",
    "hospital": "health",
    "clinic": "health",
    "medplus": "health",
    "reliance hmo": "health",
    "hygeia": "health",

    # ── Education ───────────────────────────────────────
    "udemy": "education",
    "coursera": "education",
    "school fees": "education",
    "tuition": "education",

    # ── Salary / Income ──────────────────────────────────
    "salary": "salary_or_income",
    "payroll": "salary_or_income",
    "dividend": "salary_or_income",
    "interest credit": "salary_or_income",
}


def match_pattern(narration: str) -> str | None:
    """
    Return a category if any known keyword is found in the narration.
    Returns None if no match is found.
    """
    if not narration:
        return None

    lowered = narration.lower()
    for keyword, category in KNOWN_PATTERNS.items():
        if keyword in lowered:
            return category

    return None
