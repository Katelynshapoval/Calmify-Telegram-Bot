import os
import base64
import asyncio
import requests

# ---------------- CONFIG ----------------

VISION_BACKEND = os.getenv("VISION_BACKEND", "ollama")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_MODEL = "google/gemma-3-27b-it:free"


# ---------------- HELPERS ----------------

def image_to_base64(path: str) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


# ---------------- OLLAMA ----------------

def _ollama_vision_sync(system_prompt, user_message, image_path):
    image_b64 = image_to_base64(image_path)

    response = requests.post(
        "http://localhost:11434/api/chat",
        json={
            "model": "gemma3",
            "stream": False,
            "messages": [
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": user_message,
                    "images": [image_b64],
                },
            ],
        },
        timeout=None,
    )
    response.raise_for_status()
    return response.json()["message"]["content"]


# ---------------- OPENROUTER ----------------

def _openrouter_vision_sync(system_prompt, user_message, image_path):
    image_b64 = image_to_base64(image_path)

    response = requests.post(
        OPENROUTER_URL,
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": OPENROUTER_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": user_message},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_b64}"
                            },
                        },
                    ],
                },
            ],
        },
        timeout=60,
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]


# ---------------- PUBLIC API ----------------

async def generate_vision_response(system_prompt, user_message, image_path):
    if VISION_BACKEND == "openrouter":
        return await asyncio.to_thread(
            _openrouter_vision_sync,
            system_prompt,
            user_message,
            image_path,
        )

    # default: ollama
    return await asyncio.to_thread(
        _ollama_vision_sync,
        system_prompt,
        user_message,
        image_path,
    )
