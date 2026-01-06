from typing import List, Union
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import PostgresDsn, field_validator


class Settings(BaseSettings):
    """Application settings"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        # ignora variaveis extra do .env por ex: POSTGRES_USER
        extra="ignore", 
    )

    # API Configuration
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Nutria Food Catalog API"
    PROJECT_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Server Configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Database Configuration
    DATABASE_URL: PostgresDsn

    # CORS Configuration - usando str para evitar JSON parsing automático
    BACKEND_CORS_ORIGINS: Union[List[str], str] = ""

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if not v:
            return []
        if isinstance(v, str):
            # separada por vírgula se for string
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, list):
            return v
        raise ValueError(f"Invalid CORS origins: {v}")


settings = Settings()
