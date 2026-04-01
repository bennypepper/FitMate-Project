import base64
import json
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

img_path = r'C:\Users\Benny Pepper\OneDrive - Ma Chung University\College Docs\PKM\assets\test_tcm\golden_throat_lozenges_golden_th.jpg'
with open(img_path, 'rb') as f:
    b64 = base64.b64encode(f.read()).decode('utf-8')

prompt = (
    "You are a TCM (Traditional Chinese Medicine) ingredient extractor. "
    "Look at this product label image and extract ALL ingredient names listed. "
    "1. Prioritize extracting from the formal 'composition' or 'ingredients' section if visible. "
    "2. IF NO composition section exists (e.g. it is just the front cover of a box), "
    "extract the main product name or prominent herbal names visible (e.g. 'Tian Wang Bu Xin Dan' or 'Golden Throat Lozenges'). "
    "Include Chinese (Hanzi), Pinyin, Latin, Indonesian, and English names if visible. "
    "Return ONLY a JSON array of strings — one extracted text per string. "
    "Example: [\"Ginseng\", \"当归\", \"Radix Astragali\", \"Golden Throat\"] "
    "If you cannot find any text at all, return an empty array: [] "
    "Do NOT include markdown code fences, do NOT include any explanation."
)

payload = {
    'model': 'google/gemini-3.1-flash-lite-preview',
    'messages': [
        {'role': 'user', 'content': [{'type': 'text', 'text': prompt}, {'type': 'image_url', 'image_url': {'url': f'data:image/jpeg;base64,{b64}'}}]},
    ],
    'temperature': 0.1,
}
api_key = os.getenv('OPENROUTER_OCR_API_KEY', '')
headers = {'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'}
print(httpx.post('https://openrouter.ai/api/v1/chat/completions', headers=headers, json=payload, timeout=20.0).json()['choices'][0]['message']['content'])
