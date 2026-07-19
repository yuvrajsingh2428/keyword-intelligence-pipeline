import os

import requests
from dotenv import load_dotenv


def verify_grok():
    load_dotenv()
    api_key = os.getenv("GROK_API_KEY")
    if not api_key:
        print("GROK_API_KEY not found in .env")
        return

    url = "https://api.x.ai/v1/models"
    headers = {
        "Authorization": f"Bearer {api_key}"
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        print("Available models:")
        for model in data.get('data', []):
            print(f"- {model['id']}")
    except Exception as e:
        print("Error calling Grok:", str(e))
        if hasattr(e, 'response') and e.response is not None:
            print("Response:", e.response.text)

if __name__ == "__main__":
    verify_grok()
