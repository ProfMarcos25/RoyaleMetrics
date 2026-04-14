"""
Agendador de Coleta Automática — Royle Metrics
Usa APScheduler para sincronizar dados dos clãs a cada 6 horas,
sem intervenção manual. Roda em background junto com o servidor FastAPI.
"""
import json
import logging
import os

from apscheduler.schedulers.background import BackgroundScheduler

from .database import SessionLocal
from .services.coleta import sincronizar_cartas, sincronizar_clan

logger = logging.getLogger(__name__)


def _ler_tags_clans() -> list[str]:
    """
    Lê as tags dos clãs monitorados do arquivo JSON de configuração.
    Retorna lista vazia se o arquivo não existir ou estiver malformado.

    Retorna:
        list[str]: Lista de tags dos clãs (ex: ['#ABC123', '#XYZ789']).
    """
    caminho = os.path.join(os.path.dirname(__file__), "..", "data", "tags_clas.json")
    caminho = os.path.normpath(caminho)

    if not os.path.exists(caminho):
        logger.warning(f"Arquivo de configuração não encontrado: {caminho}")
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
    Lê as tags dos clãs do arquivo de configuração e sincroniza
    dados de todos eles: jogadores, batalhas, warlog e River Race.

    Esta função é o coração da coleta automática do Royle Metrics.
    """
    tags = _ler_tags_clans()

    if not tags:
        logger.warning("Nenhuma tag de clã configurada. Sincronização pulada.")
        return

    logger.info(f"Iniciando sincronização automática de {len(tags)} clãs...")

    db = SessionLocal()
    try:
        # Atualiza o catálogo de cartas (raramente muda, mas garante consistência)
        sincronizar_cartas(db)

        # Sincroniza cada clã individualmente
        for tag in tags:
            try:
                logger.info(f"Sincronizando clã {tag}...")
                sincronizar_clan(tag, db)
            except Exception as e:
                # Um clã com erro não deve parar a sincronização dos outros
                logger.error(f"Falha ao sincronizar clã {tag}: {e}", exc_info=True)

    except Exception as e:
        logger.error(f"Erro crítico no job de sincronização: {e}", exc_info=True)
    finally:
        # Sempre fecha a sessão, mesmo em caso de erro
        db.close()

    logger.info("Sincronização automática concluída.")


def iniciar_scheduler() -> BackgroundScheduler:
    """
    Cria e inicia o agendador de coleta automática.
    O job é executado imediatamente na inicialização e depois
    a cada SYNC_INTERVAL_HOURS horas (padrão: 6 horas).

    O scheduler roda em uma thread separada e não bloqueia o servidor.

    Retorna:
        BackgroundScheduler: Instância do agendador em execução.
    """
    from .database import get_settings
    settings = get_settings()
    intervalo_horas = settings.SYNC_INTERVAL_HOURS

    scheduler = BackgroundScheduler(timezone="America/Sao_Paulo")

    # Job principal de sincronização
    scheduler.add_job(
        func=job_sincronizar_todos,
        trigger="interval",
        hours=intervalo_horas,
        id="sync_clans",
        name="Sincronização automática dos clãs",
        replace_existing=True,
        misfire_grace_time=300,  # tolera até 5 min de atraso antes de pular
    )

    scheduler.start()
    logger.info(
        f"Agendador iniciado. Sincronização automática a cada {intervalo_horas}h."
    )
    return scheduler
