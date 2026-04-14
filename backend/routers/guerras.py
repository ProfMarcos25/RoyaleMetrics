"""
Router de Guerras — Royle Metrics
Retorna histórico de guerras e previsão de resultado via ML.
"""
import logging
from typing import Any, Dict

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..services.analise import gerar_historico_guerras
from ..services.modelo import prever_resultado_guerra

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/guerras", tags=["Guerras"])


@router.get(
    "",
    summary="Histórico de guerras",
    description=(
        "Retorna o histórico de River Races dos clãs monitorados. "
        "Gera um gráfico de linhas com a evolução da pontuação (Fame) "
        "por temporada para cada clã."
    ),
)
def get_guerras(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Retorna o histórico de guerras com gráfico de linhas por clã.

    Args:
        db: Sessão do banco injetada pelo FastAPI.

    Retorna:
        dict: Objeto com 'data' e 'layout' compatíveis com Plotly.js.
    """
    logger.info("Gerando histórico de guerras...")
    grafico = gerar_historico_guerras(db)
    return grafico


@router.get(
    "/previsao",
    summary="Prever resultado da próxima guerra",
    description=(
        "Treina um modelo Random Forest com o histórico de guerras "
        "e prevê se o clã vai ganhar ou perder a próxima guerra. "
        "Retorna a previsão, confiança do modelo e variáveis mais importantes — "
        "ideal para aulas de Machine Learning no curso técnico."
    ),
)
def get_previsao_guerra(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Usa Machine Learning para prever o resultado da próxima guerra.

    O modelo RandomForestClassifier é treinado com:
    - batalhas_ganhas, batalhas_perdidas, pontuacao
    - media_fame_membros, media_vitorias_membros

    Target: colocação ≤ 3 → vitória | colocação > 3 → derrota

    Args:
        db: Sessão do banco injetada pelo FastAPI.

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
