from pathlib import Path
from typing import List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
_WORKSPACE_ROOT = _BACKEND_DIR.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=[
            str(_WORKSPACE_ROOT / ".env"),
            str(_BACKEND_DIR / ".env"),
            ".env",
        ],
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    PROJECT_NAME: str = "T&P College Resume Parser API"
    VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api"

    # OpenAI configuration
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"

    MONGODB_URI: str = ""
    MONGODB_DATABASE: str = "resume_parser_db"
    MONGODB_COLLECTION: str = "resumes"
    MONGODB_COMPANY_COLLECTION: str = "companies"
    MONGODB_EVALUATION_COLLECTION: str = "evaluations"

    # File Upload limits
    MAX_UPLOAD_SIZE_MB: int = 10

    # Demo mode: allow repeated uploads and re-parsing
    DEMO_MODE: bool = True

    # CORS
    CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:3000",
    ]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            if v.startswith("[") and v.endswith("]"):
                import json
                try:
                    return json.loads(v)
                except Exception:
                    pass
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, list):
            return v
        return []


settings = Settings()
