import httpx
import sys

URL = "http://localhost:8000/whatsapp/test-chat"

MODELS = [
    "xiaomi/mimo-v2-flash",
    "minimax/minimax-m2.7",
    "deepseek/deepseek-v3.2",
    "qwen/qwen3.5-flash-02-23",
    "google/gemini-3.1-flash-lite-preview",
    "z-ai/glm-4.7-flash",
    "openai/gpt-5.4-nano",
]

def select_model():
    print("\n[ Select LLM Model for Testing ]")
    for i, model in enumerate(MODELS, 1):
        print(f"  {i}. {model}")
    print(f"  0. (Default) Gunakan OPENROUTER_CHATBOT_MODEL dari .env")

    while True:
        try:
            choice = input("\nPilih angka model (0-7): ").strip()
            if not choice:
                return None
            idx = int(choice)
            if idx == 0:
                return None
            if 1 <= idx <= len(MODELS):
                return MODELS[idx - 1]
            print("Pilihan tidak valid.")
        except ValueError:
            print("Masukkan angka.")

def main():
    print("========================================")
    print("🌿 FitMate Bot CLI Tester 🌿")
    print("========================================")

    selected_model = select_model()
    model_display = selected_model if selected_model else "Default Config (.env)"

    print("\n========================================")
    print(f"✅ Active Model: {model_display}")
    print("Ketik pesan dan tekan Enter.")
    print("Ketik 'quit' atau 'exit' untuk berhenti.")
    print("Pastikan server FastAPI berjalan di terminal lain!")
    print("========================================\n")

    sender = "cli_test_user_v2"

    while True:
        try:
            user_msg = input("\n[Kamu]: ")
            if user_msg.lower() in ("quit", "exit"):
                break
            if not user_msg.strip():
                continue

            print(f"⏳ Evaluasi menggunakan {model_display}...")

            payload = {"sender": sender, "message": user_msg}
            if selected_model:
                payload["model"] = selected_model

            response = httpx.post(
                URL, 
                json=payload,
                timeout=45.0
            )

            if response.status_code == 200:
                data = response.json()
                reply = data.get("reply", "")
                welcome = data.get("welcome_message", "")

                if welcome:
                    print(f"\n[FitMate]:\n{welcome}\n")

                print(f"[FitMate]: {reply}")

                ext = data.get('ingredient_extracted')
                ingredient_display = ext if ext else "None"
                print(f"\n  (🤖 Debug: Intent='{data.get('intent')}' | Ingredient='{ingredient_display}')")
            else:
                print(f"\n[Error]: Server respond with status code {response.status_code}")
                print(response.text)

        except httpx.RequestError as e:
            print(f"\n[Error]: Cannot connect to backend.")
            print("Make sure your FastAPI server is running! (e.g. 'uvicorn main:app --reload')")
        except KeyboardInterrupt:
            print("\nBot tester closed. Goodbye! 👋")
            break

if __name__ == "__main__":
    main()
