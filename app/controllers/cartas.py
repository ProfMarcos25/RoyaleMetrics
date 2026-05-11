"""
Router de Cartas â€” Royle Metrics
Retorna anÃ¡lise de performance das cartas mais usadas nas batalhas.
"""
import logging
from typing import Any, Dict

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.models.database import get_db
from app.models.services.analise import gerar_analise_cartas

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/cartas", tags=["Cartas"])


@router.get(
    "",
    summary="Performance de cartas",
    description=(
        "Analisa as cartas mais usadas nas batalhas registradas. "
        "Retorna um scatter plot com frequÃªncia no eixo X, "
        "taxa de vitÃ³ria no eixo Y, tamanho proporcional ao elixir "
        "e cor por raridade. Apenas cartas com ao menos 5 usos sÃ£o exibidas."
    ),
)
def get_cartas(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Analisa e retorna a performance das cartas nas batalhas.

    Cartas com alta taxa de vitÃ³ria E alta frequÃªncia sÃ£o
    candidatas a compor o deck ideal dos jogadores do clÃ£.

    Args:
        db: SessÃ£o do banco injetada pelo FastAPI.

    Retorna:
        dict: Objeto com 'data' e 'layout' compatÃ­veis com Plotly.js.
    """
    logger.info("Gerando anÃ¡lise de performance de cartas...")
    grafico = gerar_analise_cartas(db)
    return grafico

