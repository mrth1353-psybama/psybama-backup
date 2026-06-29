"""Quick test for Google AI Studio (Gemini) API key"""
import sys
import os
from pathlib import Path

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / '.env')

api_key = os.getenv('GEMINI_API_KEY', '')
model = os.getenv('GEMINI_MODEL', 'gemini-2.0-flash')
base_url = 'https://generativelanguage.googleapis.com/v1beta/openai/'

print(f"Key: {api_key[:12]}... (len={len(api_key)})")
print(f"Model: {model}")
print()

if len(api_key) < 10 or 'قرار_دهید' in api_key:
    print("ERROR: GEMINI_API_KEY is not set in .env")
    print("  Open psybama1\\.env and replace the placeholder with your real key")
    sys.exit(1)

try:
    from openai import OpenAI
    client = OpenAI(api_key=api_key, base_url=base_url)
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": "سلام، یک جمله کوتاه درباره فرسودگی شغلی بگو."}],
        max_tokens=100
    )
    print("SUCCESS! Response:")
    print(response.choices[0].message.content)
except Exception as e:
    print(f"FAILED: {e}")
    print()
    print("Check:")
    print("1. Your API key at aistudio.google.com")
    print("2. Make sure the key is correctly pasted in .env (no extra spaces)")
