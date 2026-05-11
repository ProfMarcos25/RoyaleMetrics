"""
app/main.py — Royle Metrics  [Ponto de Entrada MVC]
Servidor FastAPI que integra todas as camadas:
  - Controller: routers em app/controllers/
  - Model:      lógica em app/models/
  - View:       front-end servido em app/views/

Iniciar:
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

Acesse:
    http://localhost:8000          → front-end (View)
    http://localhost:8000/docs     → documentação interativa da API
    http://localhost:8000/api/...  → endpoints JSON (Controller)
"""
import logging
import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.controllers import cartas, db_tools, guerras, ranking, sync, torneios
from app.models.services.scheduler import iniciar_scheduler

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# ── Caminhos absolutos das Views ──────────────────────────────────────────────
_HERE         = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR    = os.path.join(_HERE, "views", "static")
TEMPLATES_DIR = os.path.join(_HERE, "views", "templates")
INDEX_HTML    = os.path.join(TEMPLATES_DIR, "index.html")


# ── Ciclo de vida da aplicação ────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Startup → inicia agendador de coleta automática.
    Shutdown → encerra agendador graciosamente.
    """
    logger.info("🚀 Iniciando Royle Metrics...")

    scheduler = None
    try:
        scheduler = iniciar_scheduler()
        logger.info("✅ Agendador de coleta automática iniciado (a cada 6h).")
    except Exception as exc:
        logger.error(f"❌ Erro ao iniciar agendador: {exc}")

    app.state.scheduler = scheduler
    logger.info("✅ Royle Metrics pronto!")
    logger.info("   Front-end : http://localhost:8000")
    logger.info("   API Docs  : http://localhost:8000/docs")

    yield  # ← aplicação roda aqui

    if getattr(app.state, "scheduler", None) and app.state.scheduler.running:
        app.state.scheduler.shutdown(wait=False)
        logger.info("🛑 Agendador encerrado.")
    logger.info("🛑 Royle Metrics encerrado.")


# ── Instância FastAPI ─────────────────────────────────────────────────────────
app = FastAPI(
    title="⚔ Royle Metrics",
    description=(
        "API de análise de desempenho no Clash Royale — "
        "Curso Técnico em Ciência de Dados. "
        "Arquitetura MVC: Controllers (routers), Models (ORM + services), "
        "Views (front-end servido pelo próprio servidor)."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ─────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],      # em produção: lista os domínios específicos
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── View: arquivos estáticos (CSS, JS, imagens) ───────────────────────────────
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# ── Controllers: routers da API ───────────────────────────────────────────────
app.include_router(sync.router)
app.include_router(ranking.router)
app.include_router(cartas.router)
app.include_router(guerras.router)
app.include_router(torneios.router)
app.include_router(db_tools.router)


# ── View: rota raiz devolve o index.html (SPA) ───────────────────────────────
@app.get("/", include_in_schema=False)
def serve_frontend() -> FileResponse:
    """
    Serve o front-end (View) diretamente pelo servidor FastAPI.
    Ao acessar http://localhost:8000 o navegador recebe o index.html.
    """
    return FileResponse(INDEX_HTML)


# ── Health check ─────────────────────────────────────────────────────────────
@app.get("/health", tags=["Sistema"])
def health_check() -> JSONResponse:
    """
    Verifica se o servidor está no ar.
    Usado pelo front-end para exibir o badge de status da API.
    """
    return JSONResponse({"status": "ok", "app": "Royle Metrics", "versao": "1.0.0"})
