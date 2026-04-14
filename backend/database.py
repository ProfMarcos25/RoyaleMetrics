"""
Configuração do banco de dados — Royle Metrics
Gerencia a conexão com PostgreSQL via SQLAlchemy.
Usa variáveis de ambiente carregadas pelo python-dotenv.
"""
from functools import lru_cache
from typing import Generator

from dotenv import load_dotenv
from pydantic_settings import BaseSettings
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

# Carrega variáveis do arquivo .env automaticamente
load_dotenv()


class Settings(BaseSettings):
    """
    Configurações da aplicação lidas a partir de variáveis de ambiente.
    Cada atributo corresponde a uma variável no arquivo .env.
    PRENCHER SOMENTE SE DER ERRO NO MOMENTO DE FAZER A CONEXÃO COM O BANCO DE DADOS, CASO CONTRÁRIO DEIXAR VAZIO PARA SER LIDO DO .env
    """

    CLASH_API_TOKEN: str = ""
    CLASH_API_URL: str = ""
    DATABASE_URL: str = ""
    ENVIRONMENT: str = ""
    SYNC_INTERVAL_HOURS: int = 6

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """
    Retorna as configurações da aplicação com cache.
    O cache evita re-leitura do .env a cada chamada.
    """
    return Settings()


# Cria o engine de conexão com o PostgreSQL
settings = get_settings()
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,        # verifica conexão antes de usar 
    pool_size=10,              # conexões simultâneas no pool
    max_overflow=20,           # conexões extras em pico
    echo=(settings.ENVIRONMENT == "development"),  # log SQL em dev
)

# Fábrica de sessões — cada requisição HTTP abre uma sessão
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """
    Classe base para todos os modelos SQLAlchemy do projeto.
    Todos os modelos em models.py herdam desta classe.
    """
    pass


def get_db() -> Generator[Session, None, None]:
    """
    Dependency do FastAPI para injeção de sessão do banco.
    Garante que a sessão seja fechada após cada requisição,
    mesmo que ocorra uma exceção.

    Uso:
        @router.get("/rota")
        def rota(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Função para criar tabelas no banco de dados

def criar_tabelas() -> None:
    """
    Cria todas as tabelas no banco de dados caso não existam.
    Chamado na inicialização da aplicação em main.py.
    Alternativa ao uso direto do schema.sql para desenvolvimento.
    """
    from . import models  # importação local para evitar circular import
    Base.metadata.create_all(bind=engine)
