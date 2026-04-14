"""
Router de Cartas — Royle Metrics
Retorna análise de performance das cartas mais usadas nas batalhas.
"""
import logging
from typing import Any, Dict

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..services.analise import gerar_analise_cartas

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/cartas", tags=["Cartas"])


@router.get(
    "",
    summary="Performance de cartas",
    description=(
        "Analisa as cartas mais usadas nas batalhas registradas. "
        "Retorna um scatter plot com frequência no eixo X, "
        "taxa de vitória no eixo Y, tamanho proporcional ao elixir "
        "e cor por raridade. Apenas cartas com ao menos 5 usos são exibidas."
    ),
)
def get_cartas(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Analisa e retorna a performance das cartas nas batalhas.

    Cartas com alta taxa de vitória E alta frequência são
    candidatas a compor o deck ideal dos jogadores do clã.

    Args:
        db: Sessão do banco injetada pelo FastAPI.

    Retorna:
        dict: Objeto com 'data' e 'layout' compatíveis com Plotly.js.
    """
    logger.info("Gerando análise de performance de cartas...")
    grafico = gerar_analise_cartas(db)
    return grafico
