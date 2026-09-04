from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    ENVIRONMENT: str = "development"
    
    # MongoDB Settings (Local or MongoDB Atlas connection string)
    MONGODB_URI: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "news_aggregator"
    
    # LLM Settings
    GROQ_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    
    # Email Settings
    EMAIL_HOST: str = "smtp.gmail.com"
    EMAIL_PORT: int = 587
    EMAIL_USER: str = ""
    EMAIL_APP_PASSWORD: str = ""
    RECIPIENT_EMAIL: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
