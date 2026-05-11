"""
Router de Torneios â€” Royle Metrics
Retorna anÃ¡lise dos torneios escolares com grÃ¡fico de participaÃ§Ã£o.
"""
import logging
from typing import Any, Dict

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.models.database import get_db
from app.models.services.analise import gerar_analise_torneios

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/torneios", tags=["Torneios"])


@router.get(
    "",
    summary="Torneios escolares",
    description=(
        "Retorna os torneios escolares registrados manualmente no sistema. "
        "Gera um grÃ¡fico de barras com o nÃºmero de participantes por torneio "
        "e destaca o campeÃ£o de cada ediÃ§Ã£o (barra dourada). "
        "Torneios em andamento aparecem em azul."
    ),
)
def get_torneios(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Busca e retorna anÃ¡lise dos torneios escolares.

    Cores do grÃ¡fico:
        - Dourado (#e8c94a): torneio com campeÃ£o definido
        - Azul (#4a9eff): torneio em andamento

    Args:
        db: SessÃ£o do banco injetada pelo FastAPI.

    Retorna:
        dict: Objeto com 'data' e 'layout' compatÃ­veis com Plotly.js.
    """
    logger.info("Gerando anÃ¡lise de torneios escolares...")
    grafico = gerar_analise_torneios(db)
    return grafico

