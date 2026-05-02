"""Configuration applicative : secrets et URL issus uniquement des variables d'environnement."""

from __future__ import annotations

import json
from typing import Annotated, Any, List

from pydantic import BeforeValidator, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def _parse_allowed_origins(v: Any) -> List[str]:
    """
    Construit la liste CORS depuis une liste Python, du JSON (tableau) ou une chaîne CSV.
    Valeurs par défaut non sensibles si la variable est absente ou vide.
    """
    default: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://mmotors-frontend:3000",
    ]
    if v is None:
        return default
    if isinstance(v, list):
        out = [str(x).strip() for x in v if str(x).strip()]
        return out or default
    if isinstance(v, str):
        s = v.strip()
        if not s:
            return default
        if s.startswith("["):
            try:
                parsed = json.loads(s)
                if isinstance(parsed, list):
                    out = [str(x).strip() for x in parsed if str(x).strip()]
                    return out or default
            except json.JSONDecodeError:
                pass
        parts = [x.strip() for x in s.split(",") if x.strip()]
        return parts or default
    return default


class Settings(BaseSettings):
    """Paramètres chargés depuis l'environnement (fichier `.env` optionnel en local)."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    APP_NAME: str = "M-Motors API"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False

    DATABASE_URL: str = Field(
        ...,
        description="URL SQLAlchemy synchrone (ex. postgresql://user:pass@host:5432/db).",
    )
    SECRET_KEY: str = Field(
        ...,
        description="Secret pour signer les JWT — obligatoire (variable d'environnement uniquement).",
    )

    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24

    ALLOWED_ORIGINS: Annotated[List[str], BeforeValidator(_parse_allowed_origins)] = Field(
        default_factory=lambda: [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://mmotors-frontend:3000",
        ],
    )


# Les champs requis sont fournis par l’environnement ; mypy ne le déduit pas.
settings = Settings()  # type: ignore[call-arg]
