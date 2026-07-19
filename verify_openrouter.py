import os

import requests
from dotenv import load_dotenv


def verify_openrouter():
    load_dotenv()
    api_key = os.getenv("OPENROUTER_API_KEY") or os.getenv("open_router_api_key")
    base_url = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1/chat/completions")
    model = os.getenv("OPENROUTER_MODEL", "google/gemini-2.5-flash")

    if not api_key:
        print("OPENROUTER_API_KEY not found in .env")
        return

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    payload = {
        "messages": [
            {"role": "user", "content": "Reply ONLY with:\n\nOK"}
        ],
        "model": model,
        "temperature": 0,
        "max_tokens": 100
    }

    try:
        response = requests.post(base_url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        print("OpenRouter API response:", data['choices'][0]['message']['content'].strip())
    except Exception as e:
        print("Error calling OpenRouter:", str(e))
        if hasattr(e, 'response') and e.response is not None:
            print("Response:", e.response.text)

if __name__ == "__main__":
    verify_openrouter()
