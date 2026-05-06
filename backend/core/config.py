import os
import warnings
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):

    MONGODB_URL: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "fitmate_db"

    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_WHATSAPP_FROM: str = "+14155238886"

    OPENROUTER_OCR_API_KEY: str = ""
    OPENROUTER_OCR_MODEL: str = "google/gemini-3.1-flash-lite-preview"

    OPENROUTER_CHATBOT_API_KEY: str = ""
    OPENROUTER_CHATBOT_MODEL: str = "google/gemini-3.1-flash-lite-preview"

    JWT_SECRET_KEY: str = "change-me-in-production-min-32-chars"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_HOURS: int = 8
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD_HASH: str = ""

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

        if not self.OPENROUTER_OCR_API_KEY:
            print("⚠️  [CONFIG] WARNING: OPENROUTER_OCR_API_KEY is not set — OCR will fail.")

        if not self.OPENROUTER_CHATBOT_API_KEY:
            print("⚠️  [CONFIG] WARNING: OPENROUTER_CHATBOT_API_KEY is not set — chatbot will fail.")

settings = Settings()

settings.validate_security()
