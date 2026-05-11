"""
Wrapper da API Oficial do Clash Royale â€” Royle Metrics
Centraliza a criaÃ§Ã£o do cliente para reutilizaÃ§Ã£o em todo o projeto.
DocumentaÃ§Ã£o: https://clashroyale.readthedocs.io/en/latest/api.html
"""
import logging

import clashroyale

from app.config import get_settings

# Logger do mÃ³dulo para rastrear conexÃµes e erros
logger = logging.getLogger(__name__)


def get_client() -> clashroyale.OfficialAPI:
    """
    Retorna um cliente configurado da API Oficial do Clash Royale.

    Utiliza o proxy pÃºblico (proxy.royaleapi.dev) para contornar a
    restriÃ§Ã£o de IP fixo da API oficial â€” essencial em ambientes
    escolares com IP dinÃ¢mico (DHCP).

    O token Ã© lido da variÃ¡vel de ambiente CLASH_API_TOKEN via .env.

    Retorna:
        clashroyale.OfficialAPI: cliente pronto para fazer requisiÃ§Ãµes.
    """
    settings = get_settings()

    logger.info("Inicializando cliente da API Clash Royale via proxy pÃºblico.")

    return clashroyale.OfficialAPI(
        token=settings.CLASH_API_TOKEN,
        url=settings.CLASH_API_URL,   # proxy.royaleapi.dev para IP dinÃ¢mico
        is_async=False,               # modo sÃ­ncrono (compatÃ­vel com APScheduler)
    )

