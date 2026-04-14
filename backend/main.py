"""
Aplicação Principal — Royle Metrics
Ponto de entrada do servidor FastAPI. Registra routers, configura CORS,
inicia o agendador e cria as tabelas do banco na primeira execução.
"""
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .database import get_settings
from .routers import cartas, db_tools, guerras, ranking, sync, torneios
from .scheduler import iniciar_scheduler

# Configuração do logger da aplicação
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Gerencia o ciclo de vida da aplicação FastAPI.
    Executado na inicialização (startup) e encerramento (shutdown).

    Startup:
        1. Carrega tabelas do banco de Dados (opcional, para desenvolvimento) - OS Alunos devem criar as tabelas usando o schema.sql,
         mas esta função é útil para desenvolvimento local.
        2. Inicia o agendador de coleta automática

    Shutdown:
        1. Para o agendador graciosamente
    """
    # === STARTUP ===
    logger.info("🚀 Iniciando Royle Metrics...")

    # Cria as tabelas no banco (equivalente ao schema.sql, para desenvolvimento)
    #try:
    #    criar_tabelas()
    #    logger.info("✅ Tabelas do banco verificadas/criadas com sucesso.")
    #except Exception as e:
    #    logger.error(f"❌ Erro ao criar tabelas: {e}")

    # Inicia o agendador de coleta automática em background
    scheduler = None
    try:
        scheduler = iniciar_scheduler()
        logger.info("✅ Agendador de coleta automática iniciado.")
    except Exception as e:
        logger.error(f"❌ Erro ao iniciar agendador: {e}")

    # Armazena o scheduler no estado da app para shutdown limpo
    app.state.scheduler = scheduler

    logger.info("✅ Royle Metrics pronto! Acesse: http://localhost:8000/docs")
    yield  # A aplicação roda aqui

    # === SHUTDOWN ===
    if app.state.scheduler and app.state.scheduler.running:
        app.state.scheduler.shutdown(wait=False)
        logger.info("🛑 Agendador encerrado.")

    logger.info("🛑 Royle Metrics encerrado.")


# Instância principal da aplicação FastAPI
app = FastAPI(
    title="⚔ Royle Metrics",
    description=(
        "API de análise de desempenho no Clash Royale para o "
        "Curso Técnico em Ciência de Dados. "
        "Combina dados reais da API oficial com torneios escolares."
    ),
    version="1.0.0",
    docs_url="/docs",          # Swagger UI
    redoc_url="/redoc",        # ReDoc
    lifespan=lifespan,
)

# =============================================================
# Configuração de CORS
# Permite que o front-end (arquivo HTML local) acesse a API
# Em produção, substitua "*" pelo domínio real da escola
# =============================================================
settings = get_settings()

origens_permitidas = ["*"] if settings.ENVIRONMENT == "development" else [
    "http://localhost",
    "http://127.0.0.1",
    "http://localhost:5500",   # Live Server do VS Code
    "http://127.0.0.1:5500",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origens_permitidas,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# =============================================================
# Registro dos Routers
# Cada router gerencia um conjunto de endpoints relacionados
# =============================================================
app.include_router(sync.router)       # GET /api/sync
app.include_router(ranking.router)    # GET /api/ranking
app.include_router(cartas.router)     # GET /api/cartas
app.include_router(guerras.router)    # GET /api/guerras + /api/guerras/previsao
app.include_router(torneios.router)   # GET /api/torneios
app.include_router(db_tools.router)   # GET /api/db/status + /api/db/tabelas


# =============================================================
# Endpoints utilitários
# =============================================================

@app.get("/", tags=["Status"], summary="Status da API")
def root() -> JSONResponse:
    """
    Endpoint raiz — verifica se a API está rodando.
    Usado pelo front-end para exibir o badge 'API conectada'.
    """
    return JSONResponse(content={
        "status": "online",
        "aplicacao": "Royle Metrics",
        "versao": "1.0.0",
        "documentacao": "/docs",
        "mensagem": "⚔ API do Royle Metrics está funcionando!",
    })


@app.get("/health", tags=["Status"], summary="Health check")
def health_check() -> JSONResponse:
    """
    Health check para monitoramento — retorna status do servidor.
    Pode ser usado por ferramentas de monitoramento externas.
    """
    return JSONResponse(content={"status": "healthy"})
