import warnings

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    APP_ENV: str = "development"
    FRONTEND_URL: str = ""
    ALLOWED_ORIGINS: str = ""
    PUBLIC_BASE_URL: str = ""
    ENABLE_TEST_ENDPOINTS: bool = False
    TRUSTED_PROXIES: str = ""
    MOCK_VISION_API: bool = False

    MONGODB_URL: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "fitmate_db"

    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_WHATSAPP_FROM: str = "+14155238886"

    OPENROUTER_API_KEY: str = ""
    OPENROUTER_OCR_API_KEY: str = ""
    OPENROUTER_OCR_MODEL: str = "google/gemini-2.5-flash"

    OPENROUTER_CHATBOT_API_KEY: str = ""
    OPENROUTER_CHATBOT_MODEL: str = "google/gemini-2.5-flash"

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

    @property
    def effective_ocr_key(self) -> str:
        return self.OPENROUTER_OCR_API_KEY or self.OPENROUTER_API_KEY

    @property
    def effective_chatbot_key(self) -> str:
        return self.OPENROUTER_CHATBOT_API_KEY or self.OPENROUTER_API_KEY

    def validate_security(self) -> None:
        """
        Enforces fail-closed JWT secret validation in production and warns
        loudly about insecure defaults in non-production environments.
        Call this once at startup.
        """
        _INSECURE_JWT_DEFAULTS = {
            "change-me-in-production-min-32-chars",
            "fitmate-dev-secret-key-change-in-production-32chars",
            "secret",
        }
        is_weak_jwt = (
            self.JWT_SECRET_KEY in _INSECURE_JWT_DEFAULTS
            or len(self.JWT_SECRET_KEY) < 32
        )
        if is_weak_jwt:
            if self.APP_ENV.lower() == "production":
                raise RuntimeError(
                    "[SECURITY] Refusing to start in production with an insecure or "
                    "short (<32 chars) JWT_SECRET_KEY. Set a strong random secret."
                )
            warnings.warn(
                "[SECURITY] JWT_SECRET_KEY is set to a known insecure default or is <32 chars! "
                "Set a strong, random secret in backend/.env before deploying to production.",
                stacklevel=2,
            )
            print("[SECURITY] WARNING: JWT_SECRET_KEY is using an insecure default or short value!")

        if not self.ADMIN_PASSWORD_HASH:
            print("[SECURITY] WARNING: ADMIN_PASSWORD_HASH is not set - admin login is disabled.")

        if not self.effective_ocr_key:
            print("[CONFIG] WARNING: OPENROUTER_OCR_API_KEY / OPENROUTER_API_KEY is not set - OCR will fail.")

        if not self.effective_chatbot_key:
            print("[CONFIG] WARNING: OPENROUTER_CHATBOT_API_KEY / OPENROUTER_API_KEY is not set - chatbot will fail.")


settings = Settings()

settings.validate_security()
