import os
from pathlib import Path

from dotenv import load_dotenv


# Load environment variables from backend/.env
BASE_DIR = Path(__file__).resolve().parents[1]
ENV_FILE = BASE_DIR / ".env"

load_dotenv(ENV_FILE)


class Settings:
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

    GROQ_MODEL = os.getenv(
        "GROQ_MODEL",
        "openai/gpt-oss-20b"
    )

    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "sqlite:///./backend/purchasing.db"
    )


settings = Settings()