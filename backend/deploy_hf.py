import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from huggingface_hub import HfApi
from dotenv import load_dotenv
load_dotenv()
TOKEN = os.getenv("HF_TOKEN", "")
if not TOKEN:
    print("[ERROR] HF_TOKEN not set. Add HF_TOKEN=hf_... to backend/.env before deploying.")
    sys.exit(1)
REPO_ID = "benedictpepper/fitmate-api"

print("[INFO] Inisialisasi HuggingFace API...")
try:
    api = HfApi(token=TOKEN)
except Exception as e:
    print(f"[ERROR] Gagal menginisialisasi HfApi: {e}")
    sys.exit(1)

print(f"\n[UPLOAD] Sedang mengupload folder backend ke Space: {REPO_ID}")
print("Ini akan memakan waktu beberapa detik...\n")
backend_dir = os.path.dirname(os.path.abspath(__file__))
try:
    api.upload_folder(
        folder_path=backend_dir,
        repo_id=REPO_ID,
        repo_type="space",
        ignore_patterns=[
            ".env", 
            ".env.example", 
            "credentials/**",
            "credentials",
            "secrets/**",
            "*.key",
            "*.pem",
            "venv/**", 
            ".venv/**",
            "__pycache__/**", 
            "*.pyc", 
            "evaluasi_model*", 
            "*.csv", 
            "*.log",
            "deploy_hf.py",
            ".dockerignore"
        ],
        commit_message="Automated deployment backend API by VS Code AI"
    )
    print("[OK] Semua file dan kode berhasil di-upload ke Hugging Face Spaces!")
except Exception as e:
    print(f"[ERROR] Error saat upload folder: {e}")

print("\n[SECRET] Sedang menginjeksi rahasia (Environment Secrets) dari .env ke server...")
env_path = os.path.join(backend_dir, ".env")
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

                if "YOUR-PASSWORD" in val or "huggingspace token" in line or key == "HF_TOKEN":
                    continue
                try:
                    if len(val) > 0:
                        api.add_space_secret(repo_id=REPO_ID, key=key, value=val)
                        print(f" - [OK] Secret tersimpan: {key}")
                except Exception as e:
                    print(f" - [ERROR] Error setting secret {key}: {e}")
else:
    print("[WARN] File .env tidak ditemukan, melewati tahap set rahasia.")

print("\n[SUCCESS] DEPLOYMENT SELESAI!")
print("Server Backend-mu sekarang sedang di-Build secara live di Docker HuggingFace.")
