import os
import warnings
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # MongoDB
    MONGODB_URL: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "fitmate_db"

    # Twilio WhatsApp Sandbox
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_WHATSAPP_FROM: str = "+14155238886"  # Shared sandbox number

    # OpenRouter (gemini-2.5-flash-lite for multimodal/medical context support)
    OPENROUTER_API_KEY: str = ""
    OPENROUTER_MODEL: str = "google/gemini-2.5-flash-lite"

    # JWT Admin Authentication
    JWT_SECRET_KEY: str = "change-me-in-production-min-32-chars"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_HOURS: int = 8
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD_HASH: str = ""  # bcrypt hash — set in .env, never plaintext

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    def validate_security(self) -> None:
        """
        Warns loudly if insecure defaults are detected.
        Call this once at startup.
        """
        _INSECURE_JWT_DEFAULTS = {
            "change-me-in-production-min-32-chars",
            "fitmate-dev-secret-key-change-in-production-32chars",
            "secret",
        }
        if self.JWT_SECRET_KEY in _INSECURE_JWT_DEFAULTS:
            warnings.warn(
                "⚠️  [SECURITY] JWT_SECRET_KEY is set to a known insecure default! "
                "Set a strong, random secret in backend/.env before deploying to production.",
                stacklevel=2,
            )
            print("⚠️  [SECURITY] WARNING: JWT_SECRET_KEY is using an insecure default value!")

        if not self.ADMIN_PASSWORD_HASH:
            print("⚠️  [SECURITY] WARNING: ADMIN_PASSWORD_HASH is not set — admin login is disabled.")

        if not self.OPENROUTER_API_KEY:
            print("⚠️  [CONFIG] WARNING: OPENROUTER_API_KEY is not set — chatbot and OCR will fail.")


settings = Settings()
# Run security checks at import time so they appear in server startup logs
settings.validate_security()
