from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Meta / WhatsApp Cloud API
    WHATSAPP_TOKEN: str = ""
    WHATSAPP_PHONE_NUMBER_ID: str = ""
    WHATSAPP_VERIFY_TOKEN: str = "fitmate_webhook_hub_secret"
    
    # Gemini API
    GEMINI_API_KEY: str = ""

    # JWT Admin Authentication
    JWT_SECRET_KEY: str = "change-me-in-production-min-32-chars"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_HOURS: int = 8
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD_HASH: str = ""  # bcrypt hash — set in .env, never plaintext

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
