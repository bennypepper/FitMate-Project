from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Twilio WhatsApp Sandbox
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_WHATSAPP_FROM: str = "+14155238886"  # Shared sandbox number
    
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
