import base64
import json
import httpx
import sys
import os
from dotenv import load_dotenv

load_dotenv()

img_path = r'C:\Users\Benny Pepper\OneDrive - Ma Chung University\College Docs\PKM\assets\test_tcm\golden_throat_lozenges_golden_th.jpg'

def run():
    with open(img_path, 'rb') as f:
        img_bytes = f.read()
    b64 = base64.b64encode(img_bytes).decode('utf-8')

    prompt = (
        'Read all the text visible on this packaging. Transcribe it exactly.'
    )

    models = [
        'google/gemini-3.1-flash-lite-preview'
    ]

    for model in models:
        payload = {
            'model': model,
            'messages': [
                {
                    'role': 'user',
                    'content': [
                        {'type': 'text', 'text': prompt},
                        {'type': 'image_url', 'image_url': {'url': f'data:image/jpeg;base64,{b64}'}},
                    ],
                }
            ],
            'temperature': 0.1,
        }
        headers = {
            'Authorization': f'Bearer {os.getenv("OPENROUTER_OCR_API_KEY", "")}',
            'Content-Type': 'application/json',
            'HTTP-Referer': 'https://fitmate.com'
        }
        print(f"\nTesting {model}...")
        try:
            r = httpx.post('https://openrouter.ai/api/v1/chat/completions', headers=headers, json=payload, timeout=45.0)
            data = r.json()
            if 'choices' in data:
                print("Output:\n", data['choices'][0]['message']['content'])
            else:
                print("Error payload:", data)
        except Exception as e:
            print("Exception:", e)

if __name__ == "__main__":
    run()
