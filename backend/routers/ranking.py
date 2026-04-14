"""
Router de Ranking — Royle Metrics
Retorna o ranking dos 20 melhores jogadores com gráfico Plotly.
"""
import logging
from typing import Any, Dict

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..services.analise import gerar_ranking

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ranking", tags=["Ranking"])


@router.get(
    "",
    summary="Ranking de jogadores",
    description=(
        "Retorna os 20 melhores jogadores ordenados por troféus. "
        "Inclui um gráfico de barras horizontais colorido por clã "
        "pronto para ser renderizado com Plotly.js no front-end."
    ),
)
def get_ranking(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Busca e retorna o ranking dos 20 melhores jogadores.

    O gráfico gerado tem barras horizontais agrupadas por clã,
    com troféus como valor e cores distintas por clã.

    Args:
        db: Sessão do banco injetada pelo FastAPI (Depends).

    Retorna:
        dict: Objeto com 'data' e 'layout' compatíveis com Plotly.js.
    """
    logger.info("Gerando ranking de jogadores...")
    grafico = gerar_ranking(db)
    return grafico
