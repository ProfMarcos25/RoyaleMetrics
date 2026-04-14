"""
Router de Sincronização Manual — Royle Metrics
Permite ao professor acionar a coleta de dados da API durante a aula,
sem precisar esperar o agendador automático de 6 horas.
"""
import json
import logging
import os
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..services.coleta import sincronizar_cartas, sincronizar_clan

logger = logging.getLogger(__name__)

# Prefixo e tag para organização da documentação automática do FastAPI
router = APIRouter(prefix="/api/sync", tags=["Sincronização"])


def _ler_tags_clans() -> List[str]:
    """
    Lê as tags dos clãs monitorados do arquivo JSON de configuração.
    O arquivo fica em data/tags_clas.json relativo à raiz do projeto.

    Retorna:
        list[str]: Lista de tags de clãs a sincronizar.
    """
    caminho = os.path.join(os.path.dirname(__file__), "..", "..", "data", "tags_clas.json")
    caminho = os.path.normpath(caminho)

    if not os.path.exists(caminho):
        logger.warning(f"Arquivo de tags não encontrado: {caminho}")
        return []

    with open(caminho, encoding="utf-8") as f:
        dados = json.load(f)

    return dados.get("clans", [])


@router.get(
    "",
    summary="Sincronização manual de dados",
    description=(
        "Aciona a coleta imediata de dados da API do Clash Royale "
        "para todos os clãs cadastrados em data/tags_clas.json. "
        "Use este endpoint durante a aula para atualizar os dados antes da análise."
    ),
)
def sincronizar_manual(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Endpoint de sincronização manual — para uso do professor em sala de aula.
    Sincroniza cartas (catálogo geral) e todos os clãs cadastrados.

    Retorna:
        dict: Status da operação e lista de clãs processados.
    """
    tags = _ler_tags_clans()

    if not tags:
        raise HTTPException(
            status_code=404,
            detail=(
                "Nenhuma tag de clã encontrada em data/tags_clas.json. "
                "Adicione as tags dos clãs do alunos e tente novamente."
            ),
        )

    logger.info(f"Sincronização manual iniciada para {len(tags)} clãs.")

    # Sincroniza o catálogo de cartas primeiro
    qtd_cartas = sincronizar_cartas(db)

    # Sincroniza cada clã
    resultados: List[Dict[str, Any]] = []
    erros: List[str] = []

    for tag in tags:
        try:
            clan = sincronizar_clan(tag, db)
            if clan:
                resultados.append({"tag": tag, "nome": clan.nome, "status": "ok"})
            else:
                erros.append(tag)
                resultados.append({"tag": tag, "nome": None, "status": "erro"})
        except Exception as e:
            logger.error(f"Erro ao sincronizar clã {tag}: {e}")
            erros.append(tag)
            resultados.append({"tag": tag, "nome": None, "status": f"erro: {str(e)}"})

    return {
        "status": "ok" if not erros else "parcial",
        "mensagem": (
            f"Sincronização concluída. "
            f"{len(resultados) - len(erros)}/{len(resultados)} clãs atualizados. "
            f"{qtd_cartas} cartas no catálogo."
        ),
        "clans": resultados,
        "erros": erros,
        "cartas_sincronizadas": qtd_cartas,
    }
