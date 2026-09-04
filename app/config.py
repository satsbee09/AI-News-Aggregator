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
    
    # Search API Settings (Google Custom Search + Brave Search)
    GOOGLE_CSE_API_KEY: str = ""
    GOOGLE_CSE_ID: str = ""
    BRAVE_API_KEY: str = ""

    # Internal Authentication Secret (Express <-> FastAPI)
    INTERNAL_API_SECRET: str = "c8f5e29a4b7d16038e12f0c9751e3a649b802e5f1d7a3c9e624b80f1e5d7c3a9"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
