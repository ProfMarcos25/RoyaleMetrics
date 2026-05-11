"""
Router de Guerras â€” Royle Metrics
Retorna histÃ³rico de guerras e previsÃ£o de resultado via ML.
"""
import logging
from typing import Any, Dict

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.models.database import get_db
from app.models.services.analise import gerar_historico_guerras
from app.models.services.modelo import prever_resultado_guerra

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/guerras", tags=["Guerras"])


@router.get(
    "",
    summary="HistÃ³rico de guerras",
    description=(
        "Retorna o histÃ³rico de River Races dos clÃ£s monitorados. "
        "Gera um grÃ¡fico de linhas com a evoluÃ§Ã£o da pontuaÃ§Ã£o (Fame) "
        "por temporada para cada clÃ£."
    ),
)
def get_guerras(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Retorna o histÃ³rico de guerras com grÃ¡fico de linhas por clÃ£.

    Args:
        db: SessÃ£o do banco injetada pelo FastAPI.

    Retorna:
        dict: Objeto com 'data' e 'layout' compatÃ­veis com Plotly.js.
    """
    logger.info("Gerando histÃ³rico de guerras...")
    grafico = gerar_historico_guerras(db)
    return grafico


@router.get(
    "/previsao",
    summary="Prever resultado da prÃ³xima guerra",
    description=(
        "Treina um modelo Random Forest com o histÃ³rico de guerras "
        "e prevÃª se o clÃ£ vai ganhar ou perder a prÃ³xima guerra. "
        "Retorna a previsÃ£o, confianÃ§a do modelo e variÃ¡veis mais importantes â€” "
        "ideal para aulas de Machine Learning no curso tÃ©cnico."
    ),
)
def get_previsao_guerra(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Usa Machine Learning para prever o resultado da prÃ³xima guerra.

    O modelo RandomForestClassifier Ã© treinado com:
    - batalhas_ganhas, batalhas_perdidas, pontuacao
    - media_fame_membros, media_vitorias_membros

    Target: colocaÃ§Ã£o â‰¤ 3 â†’ vitÃ³ria | colocaÃ§Ã£o > 3 â†’ derrota

    Args:
        db: SessÃ£o do banco injetada pelo FastAPI.

    Retorna:
        dict: {
            previsao: str,
            confianca: float,
            top_features: dict,
            historico_recente: list,
            mensagem: str
        }
    """
    logger.info("Executando modelo preditivo de guerras...")
    resultado = prever_resultado_guerra(db)
    return resultado

