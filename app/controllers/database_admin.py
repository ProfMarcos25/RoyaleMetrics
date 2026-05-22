"""
Router de Administração do Banco de Dados — Royle Metrics
Endpoints para:
  - Executar seed (popular banco via API do Clash Royale)
  - Resetar banco (truncar todas as tabelas)
  - Exportar CSV (download de qualquer tabela)
"""
import csv
import io
import json
import logging
import os
from typing import Any, Dict, List

from fastapi import APIRouter, BackgroundTasks, Depends
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy import inspect, text
from sqlalchemy.orm import Session

from app.models.database import SessionLocal, get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin", tags=["Administração"])

# Estado global do seed (para polling do frontend)
_seed_status: Dict[str, Any] = {"rodando": False, "resultado": None}


# =====================================================================
# SEED — Popular banco via API
# =====================================================================

def _executar_seed() -> None:
    """
    Executa o seed completo em background.
    Importa as funções do seed_db.py e roda a sequência completa.
    """
    global _seed_status
    _seed_status = {"rodando": True, "resultado": None}

    try:
        import clashroyale
        from dotenv import load_dotenv

        ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        load_dotenv(os.path.join(ROOT, ".env"))

        TOKEN = os.getenv("CLASH_API_TOKEN", "")
        PROXY = os.getenv("CLASH_API_URL", "https://proxy.royaleapi.dev/v1")

        TAGS_FILE = os.path.join(ROOT, "data", "tags_clas.json")
        with open(TAGS_FILE, encoding="utf-8") as f:
            tags_data = json.load(f)
        TAGS_CLAS: List[str] = tags_data.get("clans", [])

        client = clashroyale.OfficialAPI(token=TOKEN, url=PROXY)

        # Importa funções do seed
        import sys
        sys.path.insert(0, os.path.join(ROOT, "teste"))
        from seed_db import (
            popular_cartas,
            popular_clan,
            popular_jogadores,
            popular_batalhas_todos,
            popular_guerras,
        )

        db = SessionLocal()
        resumo = {
            "cartas": 0,
            "clans": 0,
            "jogadores": 0,
            "batalhas": "processadas",
            "guerras": 0,
        }

        try:
            resumo["cartas"] = popular_cartas(client, db)

            for tag in TAGS_CLAS:
                clan = popular_clan(client, db, tag)
                if clan is None:
                    continue
                resumo["clans"] += 1

                jogadores = popular_jogadores(client, db, clan)
                resumo["jogadores"] += len(jogadores)

                popular_batalhas_todos(client, db, jogadores)
                resumo["guerras"] += popular_guerras(client, db, clan)
        finally:
            db.close()

        _seed_status = {
            "rodando": False,
            "resultado": {"status": "ok", "mensagem": "✅ Banco populado com sucesso!", "resumo": resumo},
        }
        logger.info(f"Seed concluído: {resumo}")

    except Exception as e:
        logger.error(f"Erro no seed: {e}")
        _seed_status = {
            "rodando": False,
            "resultado": {"status": "erro", "mensagem": f"❌ Erro no seed: {str(e)}"},
        }


@router.post("/seed", summary="Popular banco de dados via API")
def iniciar_seed(background_tasks: BackgroundTasks):
    """
    Inicia o processo de seed em background.
    Retorna imediatamente e o frontend pode consultar /api/admin/seed/status.
    """
    if _seed_status["rodando"]:
        return JSONResponse(status_code=409, content={
            "status": "em_andamento",
            "mensagem": "⏳ O seed já está em execução. Aguarde.",
        })

    background_tasks.add_task(_executar_seed)
    return JSONResponse(content={
        "status": "iniciado",
        "mensagem": "🚀 Seed iniciado em background. Consulte /api/admin/seed/status.",
    })


@router.get("/seed/status", summary="Status do seed em andamento")
def status_seed():
    """Retorna o status atual do processo de seed."""
    if _seed_status["rodando"]:
        return JSONResponse(content={"status": "rodando", "mensagem": "⏳ Seed em execução..."})
    if _seed_status["resultado"]:
        return JSONResponse(content=_seed_status["resultado"])
    return JSONResponse(content={"status": "idle", "mensagem": "Nenhum seed executado ainda."})


# =====================================================================
# RESET — Limpar todas as tabelas
# =====================================================================

# Ordem de truncate respeitando as foreign keys
TABELAS_RESET = [
    "contribuicoes_guerra",
    "batalha_cartas",
    "batalhas",
    "guerras",
    "jogadores",
    "clans",
    "cartas",
    "torneios",
]


@router.post("/reset", summary="Limpar banco de dados (Truncate)")
def resetar_banco(db: Session = Depends(get_db)):
    """
    Executa TRUNCATE CASCADE em todas as tabelas na ordem correta.
    ⚠️ Esta ação é irreversível!
    """
    try:
        inspector = inspect(db.get_bind())
        tabelas_existentes = inspector.get_table_names()

        truncadas: List[str] = []
        for tabela in TABELAS_RESET:
            if tabela in tabelas_existentes:
                db.execute(text(f'TRUNCATE TABLE "{tabela}" CASCADE'))
                truncadas.append(tabela)

        db.commit()
        logger.info(f"Banco resetado. Tabelas truncadas: {truncadas}")

        return JSONResponse(content={
            "status": "ok",
            "mensagem": f"🗑️ {len(truncadas)} tabela(s) limpas com sucesso!",
            "tabelas": truncadas,
        })
    except Exception as e:
        db.rollback()
        logger.error(f"Erro ao resetar banco: {e}")
        return JSONResponse(status_code=500, content={
            "status": "erro",
            "mensagem": f"❌ Erro ao limpar banco: {str(e)}",
        })


# =====================================================================
# EXPORTAR CSV — Download de qualquer tabela
# =====================================================================

@router.get("/export/{nome_tabela}", summary="Exportar tabela como CSV")
def exportar_csv(nome_tabela: str, db: Session = Depends(get_db)):
    """
    Gera um arquivo CSV da tabela informada e retorna como download.
    """
    try:
        inspector = inspect(db.get_bind())
        tabelas_validas = inspector.get_table_names()
    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "erro", "mensagem": str(e)})

    if nome_tabela not in tabelas_validas:
        return JSONResponse(status_code=404, content={
            "status": "erro",
            "mensagem": f"Tabela '{nome_tabela}' não encontrada.",
        })

    try:
        resultado = db.execute(text(f'SELECT * FROM "{nome_tabela}"'))
        colunas = list(resultado.keys())
        linhas = resultado.fetchall()

        # Gera CSV em memória
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(colunas)
        for linha in linhas:
            writer.writerow([str(v) if v is not None else "" for v in linha])

        output.seek(0)

        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={
                "Content-Disposition": f'attachment; filename="{nome_tabela}.csv"',
            },
        )
    except Exception as e:
        return JSONResponse(status_code=500, content={
            "status": "erro",
            "mensagem": f"❌ Erro ao exportar: {str(e)}",
        })
