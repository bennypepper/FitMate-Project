from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Meta / WhatsApp Cloud API
    WHATSAPP_TOKEN: str = ""
    WHATSAPP_PHONE_NUMBER_ID: str = ""
    WHATSAPP_VERIFY_TOKEN: str = "fitmate_webhook_hub_secret"
    
    # Gemini API
    GEMINI_API_KEY: str = ""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
