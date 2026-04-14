"""
Router de Torneios — Royle Metrics
Retorna análise dos torneios escolares com gráfico de participação.
"""
import logging
from typing import Any, Dict

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..services.analise import gerar_analise_torneios

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/torneios", tags=["Torneios"])


@router.get(
    "",
    summary="Torneios escolares",
    description=(
        "Retorna os torneios escolares registrados manualmente no sistema. "
        "Gera um gráfico de barras com o número de participantes por torneio "
        "e destaca o campeão de cada edição (barra dourada). "
        "Torneios em andamento aparecem em azul."
    ),
)
def get_torneios(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Busca e retorna análise dos torneios escolares.

    Cores do gráfico:
        - Dourado (#e8c94a): torneio com campeão definido
        - Azul (#4a9eff): torneio em andamento

    Args:
        db: Sessão do banco injetada pelo FastAPI.

    Retorna:
        dict: Objeto com 'data' e 'layout' compatíveis com Plotly.js.
    """
    logger.info("Gerando análise de torneios escolares...")
    grafico = gerar_analise_torneios(db)
    return grafico
