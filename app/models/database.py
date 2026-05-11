"""
app/models/database.py — Royle Metrics  [Model — Banco de Dados]
Gerencia a conexão com PostgreSQL via SQLAlchemy.
Expõe: engine, SessionLocal, Base, get_db()
"""
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings

settings = get_settings()

# ── Engine de conexão com PostgreSQL ─────────────────────────────────────────
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,                                    # reconecta se cair
    pool_size=10,
    max_overflow=20,
    echo=(settings.ENVIRONMENT == "development"),          # loga SQL em dev
)

# ── Fábrica de sessões ────────────────────────────────────────────────────────
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Classe base para todos os models ORM do projeto."""
    pass


# ── Dependency FastAPI ────────────────────────────────────────────────────────
def get_db() -> Generator[Session, None, None]:
    """
    Dependency injetada nos controllers via Depends(get_db).
    Garante fechamento da sessão mesmo em caso de exceção.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
