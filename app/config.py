"""
config.py — Royle Metrics
Configurações centralizadas da aplicação lidas do arquivo .env.
Ponto único de verdade para todas as variáveis de ambiente.
"""
from functools import lru_cache

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()


class Settings(BaseSettings):
    """
    Variáveis de ambiente da aplicação.
    Cada atributo corresponde a uma linha no arquivo .env
    """

    # ── API do Clash Royale ──────────────────────────────────────
    CLASH_API_TOKEN: str = ""
    CLASH_API_URL: str = "https://proxy.royaleapi.dev/v1"

    # ── Banco de dados PostgreSQL ────────────────────────────────
    DATABASE_URL: str = ""

    # ── Configurações gerais ─────────────────────────────────────
    ENVIRONMENT: str = "development"
    SYNC_INTERVAL_HOURS: int = 6

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """
    Retorna as configurações com cache.
    O cache evita re-leitura do .env a cada chamada.
    """
    return Settings()
