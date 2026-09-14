import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")
    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "sqlite:///./purchasing.db"
    )


settings = Settings()