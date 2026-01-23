import os
import requests
import asyncio
from dotenv import load_dotenv

# Load .env once
load_dotenv()

# Read API key once at import time
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
if not OPENROUTER_API_KEY:
    raise RuntimeError("OPENROUTER_API_KEY not found in .env file")

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

# ✅ SINGLE SOURCE OF TRUTH FOR MODEL
DEFAULT_MODEL = "google/gemma-3-27b-it:free"


# DEFAULT_MODEL = "meta-llama/llama-3.1-405b-instruct:free"


def _post_chat(payload: dict) -> dict:
    response = requests.post(
        OPENROUTER_URL,
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=60,
    )
    response.raise_for_status()
    return response.json()


async def generate_response(
        prompt: str,
        *,
        reasoning_enabled: bool = False,
) -> str:
    payload = {
        "model": DEFAULT_MODEL,  # ✅ model is fixed here
        "messages": [
            {"role": "user", "content": prompt},
        ],
    }

    if reasoning_enabled:
        payload["reasoning"] = {"enabled": True}

    # Run blocking HTTP call in a thread
    data = await asyncio.to_thread(_post_chat, payload)

    return data["choices"][0]["message"].get("content", "")
