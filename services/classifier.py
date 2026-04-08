import json
import re
from openai import OpenAI, OpenAIError
from config import get_settings

settings = get_settings()

_client = OpenAI(api_key=settings.openai_api_key)

SYSTEM_PROMPT = """You are a financial transaction classifier for a Nigerian personal finance app.

Given a transaction narration, classify it into ONE of these categories:
- food_and_dining        (restaurants, food delivery, groceries)
- transport              (Uber, Bolt, fuel, BRT, flights)
- utilities              (electricity, DSTV, water, internet)
- subscriptions          (Netflix, Spotify, Apple, YouTube Premium)
- transfer               (bank transfers, OPay, Kuda, PiggyVest)
- shopping               (retail, e-commerce, Jumia, Konga)
- health                 (pharmacy, hospital, medical)
- education              (school fees, tuition, Udemy, Coursera)
- entertainment          (events, cinemas, concerts)
- salary_or_income       (salary credit, freelance income, dividends)
- airtime_and_data       (MTN, Airtel, Glo, 9mobile, data bundles)
- savings_and_investment (savings, stocks, crypto)
- uncategorized          (cannot determine)

Return ONLY a JSON object — no explanation, no markdown:
{
  "category": "<one of the categories above>",
  "confidence": <float 0.0 to 1.0>
}"""


def classify_with_ai(text: str) -> tuple[str, float]:
    """
    Classify a transaction narration using GPT-4o mini.
    Returns (category, confidence).
    Falls back to ("uncategorized", 0.0) on any error.
    """
    if not text or not text.strip():
        return "uncategorized", 0.0

    try:
        response = _client.chat.completions.create(
            model="gpt-4o-mini",
            max_tokens=100,
            temperature=0,        # deterministic — we want consistent classification
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Narration: {text.strip()}"}
            ]
        )

        raw = response.choices[0].message.content.strip()
        raw = re.sub(r"```json|```", "", raw).strip()

        result = json.loads(raw)
        category = result.get("category", "uncategorized")
        confidence = float(result.get("confidence", 0.0))

        allowed = {
            "food_and_dining", "transport", "utilities", "subscriptions",
            "transfer", "shopping", "health", "education", "entertainment",
            "salary_or_income", "airtime_and_data", "savings_and_investment",
            "uncategorized"
        }
        if category not in allowed:
            category = "uncategorized"
            confidence = 0.0

        return category, confidence

    except (json.JSONDecodeError, KeyError, OpenAIError) as e:
        print(f"[Classifier] Error classifying '{text}': {e}")
        return "uncategorized", 0.0
