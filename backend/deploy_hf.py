import os
import sys
from huggingface_hub import HfApi

import os
from dotenv import load_dotenv
load_dotenv()
TOKEN = os.getenv("HF_TOKEN", "")
if not TOKEN:
    print("❌ HF_TOKEN not set. Add HF_TOKEN=hf_... to backend/.env before deploying.")
    sys.exit(1)
REPO_ID = "benedictpepper/fitmate-api"

print("🔥 Inisialisasi HuggingFace API...")
try:
    api = HfApi(token=TOKEN)
except Exception as e:
    print(f"Gagal menginisialisasi HfApi: {e}")
    sys.exit(1)

print(f"\n🚀 Sedang mengupload folder backend ke Space: {REPO_ID}")
print("Ini akan memakan waktu beberapa detik...\n")
try:
    api.upload_folder(
        folder_path=r"C:\Users\Benny Pepper\Documents\GitHub\FitMate-Project\backend",
        repo_id=REPO_ID,
        repo_type="space",
        ignore_patterns=[
            ".env", 
            ".env.example", 
            "venv/**", 
            "__pycache__/**", 
            "*.pyc", 
            "evaluasi_model*", 
            "*.csv", 
            "*.log",
            "deploy_hf.py"
        ],
        commit_message="🚀 Automated deployment backend API by VS Code AI"
    )
    print("✅ Semua file dan kode berhasil di-upload ke Hugging Face Spaces!")
except Exception as e:
    print(f"❌ Error saat upload folder: {e}")

print("\n🔐 Sedang menginjeksi rahasia (Environment Secrets) dari .env ke server...")
env_path = r"C:\Users\Benny Pepper\Documents\GitHub\FitMate-Project\backend\.env"
if os.path.exists(env_path):
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, val = line.split("=", 1)
                key = key.strip()
                val = val.strip()
                # Hindari upload error jika user tidak hapus pesan error
                if "YOUR-PASSWORD" in val or "huggingspace token" in line:
                    continue
                try:
                    if len(val) > 0:
                        api.add_space_secret(repo_id=REPO_ID, key=key, value=val)
                        print(f" - ✅ Secret tersimpan: {key}")
                except Exception as e:
                    print(f" - ❌ Error setting secret {key}: {e}")
else:
    print("❌ File .env tidak ditemukan, melewati tahap set rahasia.")

print("\n🎉 DEPLOYMENT SELESAI!")
print("Server Backend-mu sekarang sedang di-Build secara live di Docker HuggingFace.")
