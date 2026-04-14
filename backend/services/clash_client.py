"""
Wrapper da API Oficial do Clash Royale — Royle Metrics
Centraliza a criação do cliente para reutilização em todo o projeto.
Documentação: https://clashroyale.readthedocs.io/en/latest/api.html
"""
import logging

import clashroyale

from ..database import get_settings

# Logger do módulo para rastrear conexões e erros
logger = logging.getLogger(__name__)


def get_client() -> clashroyale.OfficialAPI:
    """
    Retorna um cliente configurado da API Oficial do Clash Royale.

    Utiliza o proxy público (proxy.royaleapi.dev) para contornar a
    restrição de IP fixo da API oficial — essencial em ambientes
    escolares com IP dinâmico (DHCP).

    O token é lido da variável de ambiente CLASH_API_TOKEN via .env.

    Retorna:
        clashroyale.OfficialAPI: cliente pronto para fazer requisições.
    """
    settings = get_settings()

    logger.info("Inicializando cliente da API Clash Royale via proxy público.")

    return clashroyale.OfficialAPI(
        token=settings.CLASH_API_TOKEN,
        url=settings.CLASH_API_URL,   # proxy.royaleapi.dev para IP dinâmico
        is_async=False,               # modo síncrono (compatível com APScheduler)
    )
