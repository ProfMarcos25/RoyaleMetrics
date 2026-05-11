"""
Router de SincronizaÃ§Ã£o Manual â€” Royle Metrics
Permite ao professor acionar a coleta de dados da API durante a aula,
sem precisar esperar o agendador automÃ¡tico de 6 horas.
"""
import json
import logging
import os
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.models.database import get_db
from app.models.services.coleta import sincronizar_cartas, sincronizar_clan

logger = logging.getLogger(__name__)

# Prefixo e tag para organizaÃ§Ã£o da documentaÃ§Ã£o automÃ¡tica do FastAPI
router = APIRouter(prefix="/api/sync", tags=["SincronizaÃ§Ã£o"])


def _ler_tags_clans() -> List[str]:
    """
    LÃª as tags dos clÃ£s monitorados do arquivo JSON de configuraÃ§Ã£o.
    O arquivo fica em data/tags_clas.json relativo Ã  raiz do projeto.

    Retorna:
        list[str]: Lista de tags de clÃ£s a sincronizar.
    """
    caminho = os.path.join(os.path.dirname(__file__), "..", "..", "data", "tags_clas.json")
    caminho = os.path.normpath(caminho)

    if not os.path.exists(caminho):
        logger.warning(f"Arquivo de tags nÃ£o encontrado: {caminho}")
        return []

    with open(caminho, encoding="utf-8") as f:
        dados = json.load(f)

    return dados.get("clans", [])


@router.get(
    "",
    summary="SincronizaÃ§Ã£o manual de dados",
    description=(
        "Aciona a coleta imediata de dados da API do Clash Royale "
        "para todos os clÃ£s cadastrados em data/tags_clas.json. "
        "Use este endpoint durante a aula para atualizar os dados antes da anÃ¡lise."
    ),
)
def sincronizar_manual(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Endpoint de sincronizaÃ§Ã£o manual â€” para uso do professor em sala de aula.
    Sincroniza cartas (catÃ¡logo geral) e todos os clÃ£s cadastrados.

    Retorna:
        dict: Status da operaÃ§Ã£o e lista de clÃ£s processados.
    """
    tags = _ler_tags_clans()

    if not tags:
        raise HTTPException(
            status_code=404,
            detail=(
                "Nenhuma tag de clÃ£ encontrada em data/tags_clas.json. "
                "Adicione as tags dos clÃ£s do alunos e tente novamente."
            ),
        )

    logger.info(f"SincronizaÃ§Ã£o manual iniciada para {len(tags)} clÃ£s.")

    # Sincroniza o catÃ¡logo de cartas primeiro
    qtd_cartas = sincronizar_cartas(db)

    # Sincroniza cada clÃ£
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
            logger.error(f"Erro ao sincronizar clÃ£ {tag}: {e}")
            erros.append(tag)
            resultados.append({"tag": tag, "nome": None, "status": f"erro: {str(e)}"})

    return {
        "status": "ok" if not erros else "parcial",
        "mensagem": (
            f"SincronizaÃ§Ã£o concluÃ­da. "
            f"{len(resultados) - len(erros)}/{len(resultados)} clÃ£s atualizados. "
            f"{qtd_cartas} cartas no catÃ¡logo."
        ),
        "clans": resultados,
        "erros": erros,
        "cartas_sincronizadas": qtd_cartas,
    }

