"""
Router de Ranking â€” Royle Metrics
Retorna o ranking dos 20 melhores jogadores com grÃ¡fico Plotly.
"""
import logging
from typing import Any, Dict

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.models.database import get_db
from app.models.services.analise import gerar_ranking

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ranking", tags=["Ranking"])


@router.get(
    "",
    summary="Ranking de jogadores",
    description=(
        "Retorna os 20 melhores jogadores ordenados por trofÃ©us. "
        "Inclui um grÃ¡fico de barras horizontais colorido por clÃ£ "
        "pronto para ser renderizado com Plotly.js no front-end."
    ),
)
def get_ranking(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Busca e retorna o ranking dos 20 melhores jogadores.

    O grÃ¡fico gerado tem barras horizontais agrupadas por clÃ£,
    com trofÃ©us como valor e cores distintas por clÃ£.

    Args:
        db: SessÃ£o do banco injetada pelo FastAPI (Depends).

    Retorna:
        dict: Objeto com 'data' e 'layout' compatÃ­veis com Plotly.js.
    """
    logger.info("Gerando ranking de jogadores...")
    grafico = gerar_ranking(db)
    return grafico

