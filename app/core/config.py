"""
Configuration de l'application
Gère toutes les variables d'environnement et paramètres
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional, Union
from pydantic import field_validator
import secrets
import json


class Settings(BaseSettings):
    """Configuration principale de l'application"""

    # Informations de base
    PROJECT_NAME: str = "Commercia API"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "production"  # development, staging, production

    # Sécurité
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 jours
    ALGORITHM: str = "HS256"

    # Database PostgreSQL (Supabase)
    DATABASE_URL: str
    DATABASE_POOL_SIZE: int = 3  # Réduit pour plan starter Render
    DATABASE_MAX_OVERFLOW: int = 2
    DATABASE_POOL_TIMEOUT: int = 30
    DATABASE_POOL_RECYCLE: int = 1800

    # CORS
    BACKEND_CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8000",
    ]
    
    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS origins from JSON string or return as-is if already a list"""
        if isinstance(v, str):
            # Si c'est "*", autoriser toutes les origines
            if v.strip() == "*":
                return ["*"]
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                # Si c'est une seule URL, la retourner dans une liste
                return [v]
        return v

    # Supabase (optionnel si besoin du client Supabase)
    #SUPABASE_URL: Optional[str] = None
    #SUPABASE_KEY: Optional[str] = None

    # Email (pour notifications futures)
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: Optional[int] = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAILS_FROM_EMAIL: Optional[str] = None
    EMAILS_FROM_NAME: Optional[str] = None

    # Storage (pour upload fichiers)
    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB

    # Pagination
    DEFAULT_PAGE_SIZE: int = 50
    MAX_PAGE_SIZE: int = 1000

    # Loyalty Program
    LOYALTY_POINTS_RATE: int = 1000  # 1 point par 1000 XOF
    LOYALTY_POINTS_VALUE: int = 100  # 1 point = 100 XOF

    # Rate Limiting (pour future implémentation)
    RATE_LIMIT_PER_MINUTE: int = 60

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )

    def get_database_url(self) -> str:
        """Retourne l'URL de la base de données formatée pour asyncpg"""
        if self.DATABASE_URL.startswith("postgres://"):
            return self.DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)
        elif self.DATABASE_URL.startswith("postgresql://"):
            return self.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
        return self.DATABASE_URL


# Instance unique des settings
settings = Settings()
