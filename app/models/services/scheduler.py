"""
Agendador de Coleta AutomÃ¡tica â€” Royle Metrics
Usa APScheduler para sincronizar dados dos clÃ£s a cada 6 horas,
sem intervenÃ§Ã£o manual. Roda em background junto com o servidor FastAPI.
"""
import json
import logging
import os

from apscheduler.schedulers.background import BackgroundScheduler

from app.models.database import SessionLocal
from app.models.services.coleta import sincronizar_cartas, sincronizar_clan

logger = logging.getLogger(__name__)


def _ler_tags_clans() -> list[str]:
    """
    LÃª as tags dos clÃ£s monitorados do arquivo JSON de configuraÃ§Ã£o.
    Retorna lista vazia se o arquivo nÃ£o existir ou estiver malformado.

    Retorna:
        list[str]: Lista de tags dos clÃ£s (ex: ['#ABC123', '#XYZ789']).
    """
    caminho = os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "tags_clas.json")
    caminho = os.path.normpath(caminho)

    if not os.path.exists(caminho):
        logger.warning(f"Arquivo de configuraÃ§Ã£o nÃ£o encontrado: {caminho}")
        return []

    try:
        with open(caminho, encoding="utf-8") as f:
            dados = json.load(f)
        return dados.get("clans", [])
    except json.JSONDecodeError as e:
        logger.error(f"Erro ao ler tags_clas.json: {e}")
        return []


def job_sincronizar_todos() -> None:
    """
    Job executado automaticamente pelo APScheduler a cada 6 horas.
    LÃª as tags dos clÃ£s do arquivo de configuraÃ§Ã£o e sincroniza
    dados de todos eles: jogadores, batalhas, warlog e River Race.

    Esta funÃ§Ã£o Ã© o coraÃ§Ã£o da coleta automÃ¡tica do Royle Metrics.
    """
    tags = _ler_tags_clans()

    if not tags:
        logger.warning("Nenhuma tag de clÃ£ configurada. SincronizaÃ§Ã£o pulada.")
        return

    logger.info(f"Iniciando sincronizaÃ§Ã£o automÃ¡tica de {len(tags)} clÃ£s...")

    db = SessionLocal()
    try:
        # Atualiza o catÃ¡logo de cartas (raramente muda, mas garante consistÃªncia)
        sincronizar_cartas(db)

        # Sincroniza cada clÃ£ individualmente
        for tag in tags:
            try:
                logger.info(f"Sincronizando clÃ£ {tag}...")
                sincronizar_clan(tag, db)
            except Exception as e:
                # Um clÃ£ com erro nÃ£o deve parar a sincronizaÃ§Ã£o dos outros
                logger.error(f"Falha ao sincronizar clÃ£ {tag}: {e}", exc_info=True)

    except Exception as e:
        logger.error(f"Erro crÃ­tico no job de sincronizaÃ§Ã£o: {e}", exc_info=True)
    finally:
        # Sempre fecha a sessÃ£o, mesmo em caso de erro
        db.close()

    logger.info("SincronizaÃ§Ã£o automÃ¡tica concluÃ­da.")


def iniciar_scheduler() -> BackgroundScheduler:
    """
    Cria e inicia o agendador de coleta automÃ¡tica.
    O job Ã© executado imediatamente na inicializaÃ§Ã£o e depois
    a cada SYNC_INTERVAL_HOURS horas (padrÃ£o: 6 horas).

    O scheduler roda em uma thread separada e nÃ£o bloqueia o servidor.

    Retorna:
        BackgroundScheduler: InstÃ¢ncia do agendador em execuÃ§Ã£o.
    """
    from app.config import get_settings
    settings = get_settings()
    intervalo_horas = settings.SYNC_INTERVAL_HOURS

    scheduler = BackgroundScheduler(timezone="America/Sao_Paulo")

    # Job principal de sincronizaÃ§Ã£o
    scheduler.add_job(
        func=job_sincronizar_todos,
        trigger="interval",
        hours=intervalo_horas,
        id="sync_clans",
        name="SincronizaÃ§Ã£o automÃ¡tica dos clÃ£s",
        replace_existing=True,
        misfire_grace_time=300,  # tolera atÃ© 5 min de atraso antes de pular
    )

    scheduler.start()
    logger.info(
        f"Agendador iniciado. SincronizaÃ§Ã£o automÃ¡tica a cada {intervalo_horas}h."
    )
    return scheduler

