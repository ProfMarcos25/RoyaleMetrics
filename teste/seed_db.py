"""
seed_db.py — Royle Metrics
Popula o banco de dados PostgreSQL com dados reais da API do Clash Royale.
Executa em sequência:
  1. Cartas     → tabela `cartas`
  2. Clã        → tabela `clans`
  3. Jogadores  → tabela `jogadores`
  4. Batalhas   → tabelas `batalhas` + `batalha_cartas`
  5. Guerras    → tabelas `guerras` + `contribuicoes_guerra`

Execute:
    python teste/seed_db.py
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from datetime import datetime
from typing import List, Optional

# ── Raiz do projeto no path para imports do backend ──────────────────────────
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import clashroyale
from dotenv import load_dotenv
from sqlalchemy.orm import Session

load_dotenv(os.path.join(ROOT, ".env"))

from app.models.database import SessionLocal
from app.models.entities import (
    Batalha,
    BatalhaCartas,
    Carta,
    Clan,
    ContribuicaoGuerra,
    Guerra,
    Jogador,
)
from seed_md import separador, testar_conexao

# ── Configuração ──────────────────────────────────────────────────────────────
TOKEN    = os.getenv("CLASH_API_TOKEN", "")
PROXY    = os.getenv("CLASH_API_URL", "https://proxy.royaleapi.dev/v1")

TAGS_FILE = os.path.join(ROOT, "data", "tags_clas.json")
with open(TAGS_FILE, encoding="utf-8") as _f:
    _tags = json.load(_f)
TAGS_CLAS: List[str] = _tags.get("clans", [])


# =============================================================================
# Helpers
# =============================================================================

def _normalizar_tag(tag: str) -> str:
    tag = tag.strip().upper()
    return tag if tag.startswith("#") else "#" + tag


def _gerar_battle_id(player_tag: str, battle_time: str) -> str:
    chave = f"{player_tag}|{battle_time}"
    return hashlib.sha256(chave.encode()).hexdigest()[:32]


def _url_icone(nome: str) -> str:
    return (
        "https://royaleapi.github.io/cr-api-assets/cards/"
        + nome.lower().replace(" ", "-").replace(".", "") + ".png"
    )


def _parse_data(battle_time: str) -> Optional[datetime]:
    """Converte '20260510T212914.000Z' → datetime."""
    try:
        return datetime.strptime(battle_time[:15], "%Y%m%dT%H%M%S")
    except (ValueError, TypeError):
        return None


def _pausar(segundos: float = 0.35) -> None:
    """Pequena pausa para respeitar o rate-limit da API."""
    time.sleep(segundos)


# =============================================================================
# 1. Popular cartas
# =============================================================================

def popular_cartas(client: clashroyale.OfficialAPI, db: Session) -> int:
    """
    Busca todas as cartas do jogo e faz upsert na tabela `cartas`.
    Retorna o total de cartas processadas.
    """
    separador("POPULANDO → cartas")
    try:
        cartas_api = client.get_all_cards()
    except Exception as erro:
        print(f"  ❌ Erro ao buscar cartas: {erro}")
        return 0

    total = 0
    for c in cartas_api:
        card_id = getattr(c, "id", None)
        carta = db.query(Carta).filter(Carta.card_id == card_id).first()
        if carta is None:
            carta = Carta(card_id=card_id)
            db.add(carta)
        carta.nome      = getattr(c, "name", "Desconhecida")
        carta.tipo      = getattr(c, "type", None)
        carta.raridade  = getattr(c, "rarity", None)
        carta.elixir    = getattr(c, "elixir_cost", None)
        carta.max_nivel = getattr(c, "max_level", None)
        carta.url_icon  = _url_icone(getattr(c, "name", ""))
        total += 1

    db.commit()
    print(f"  ✅ {total} cartas salvas no banco.")
    return total


# =============================================================================
# 2. Popular clã
# =============================================================================

def popular_clan(
    client: clashroyale.OfficialAPI, db: Session, tag: str
) -> Optional[Clan]:
    """
    Busca dados do clã e faz upsert na tabela `clans`.
    Retorna o objeto Clan persistido.
    """
    tag = _normalizar_tag(tag)
    separador(f"POPULANDO → clans  [{tag}]")
    try:
        clan_api = client.get_clan(tag)
    except clashroyale.errors.NotFoundError:
        print(f"  ❌ Clã {tag} não encontrado.")
        return None
    except clashroyale.errors.RatelimitError:
        print("  ⚠️ Rate limit — aguarde e tente novamente.")
        return None
    except Exception as erro:
        print(f"  ❌ Erro: {erro}")
        return None

    clan = db.query(Clan).filter(Clan.tag == tag).first()
    if clan is None:
        clan = Clan(tag=tag)
        db.add(clan)

    clan.nome         = getattr(clan_api, "name", "Sem nome")
    clan.descricao    = getattr(clan_api, "description", None)
    clan.trofeus      = getattr(clan_api, "clan_score", 0) or 0
    clan.membros      = getattr(clan_api, "members", 0) or 0
    clan.atualizado_em = datetime.utcnow()
    db.flush()
    db.commit()
    print(f"  ✅ Clã '{clan.nome}' salvo (id={clan.id}).")
    return clan


# =============================================================================
# 3. Popular jogadores
# =============================================================================

def popular_jogadores(
    client: clashroyale.OfficialAPI, db: Session, clan: Clan
) -> List[Jogador]:
    """
    Busca membros do clã e faz upsert na tabela `jogadores`.
    Retorna lista de objetos Jogador persistidos.
    """
    separador(f"POPULANDO → jogadores  [clã: {clan.tag}]")
    try:
        clan_api  = client.get_clan(clan.tag)
        membros   = getattr(clan_api, "member_list", []) or []
    except Exception as erro:
        print(f"  ❌ Erro ao buscar membros: {erro}")
        return []

    jogadores_salvos: List[Jogador] = []
    for m in membros:
        tag_m = getattr(m, "tag", None)
        if not tag_m:
            continue

        jogador = db.query(Jogador).filter(Jogador.tag == tag_m).first()
        if jogador is None:
            jogador = Jogador(tag=tag_m)
            db.add(jogador)

        jogador.nickname        = getattr(m, "name", "?")
        jogador.nivel           = getattr(m, "exp_level", None)
        jogador.trofeus         = getattr(m, "trophies", 0)
        jogador.trofeus_recorde = getattr(m, "best_trophies", 0) or 0
        arena                   = getattr(m, "arena", None)
        jogador.arena           = getattr(arena, "name", None) if arena else None
        jogador.clan_id         = clan.id
        db.flush()
        jogadores_salvos.append(jogador)
        print(f"   👤 {jogador.nickname:<22} | Troféus: {jogador.trofeus}")

    db.commit()
    print(f"  ✅ {len(jogadores_salvos)} jogadores salvos.")
    return jogadores_salvos


# =============================================================================
# 4. Popular batalhas + batalha_cartas
# =============================================================================

def popular_batalhas_jogador(
    client: clashroyale.OfficialAPI, db: Session, jogador: Jogador
) -> int:
    """
    Busca batalhas recentes de um jogador e persiste em `batalhas`
    e `batalha_cartas`. Usa battle_id (hash) para evitar duplicatas.
    Retorna o número de novas batalhas inseridas.
    """
    _pausar()
    try:
        batalhas_api = client.get_player_battles(jogador.tag)
    except clashroyale.errors.NotFoundError:
        print(f"    ⚠️ Jogador {jogador.tag} não encontrado na API.")
        return 0
    except clashroyale.errors.RatelimitError:
        print(f"    ⚠️ Rate limit ao buscar batalhas de {jogador.tag}.")
        return 0
    except Exception as erro:
        print(f"    ❌ Erro batalhas {jogador.tag}: {erro}")
        return 0

    novas = 0
    for b in batalhas_api:
        battle_time = str(getattr(b, "battle_time", ""))
        battle_id   = _gerar_battle_id(jogador.tag, battle_time)

        if db.query(Batalha).filter(Batalha.battle_id == battle_id).first():
            continue  # já existe — pular

        # Resultado
        try:
            ct = b.team[0].crowns
            co = b.opponent[0].crowns
            resultado = "vitoria" if ct > co else ("derrota" if ct < co else "empate")
        except (AttributeError, IndexError):
            resultado = "empate"

        # Oponente
        oponente_tag    = None
        oponente_trofeus = None
        time_trofeus     = None
        try:
            oponente_tag     = getattr(b.opponent[0], "tag", None)
            oponente_trofeus = getattr(b.opponent[0], "starting_trophies", None)
            time_trofeus     = getattr(b.team[0], "starting_trophies", None)
        except (AttributeError, IndexError):
            pass

        batalha = Batalha(
            battle_id        = battle_id,
            jogador_id       = jogador.id,
            tipo             = getattr(b, "type", "PvP"),
            resultado        = resultado,
            trofeus_ganhos   = getattr(b, "trophy_change", 0) or 0,
            time_trofeus     = time_trofeus,
            oponente_tag     = oponente_tag,
            oponente_trofeus = oponente_trofeus,
            data_batalha     = _parse_data(battle_time),
        )
        db.add(batalha)
        db.flush()  # precisa do batalha.id antes de inserir cartas

        # Deck do jogador → batalha_cartas
        try:
            for carta_api in (b.team[0].cards or []):
                cid = getattr(carta_api, "id", None)
                if cid is None:
                    continue
                carta = db.query(Carta).filter(Carta.card_id == cid).first()
                if carta is None:
                    # insere carta desconhecida para não perder o registro
                    carta = Carta(
                        card_id  = cid,
                        nome     = getattr(carta_api, "name", f"Carta_{cid}"),
                        raridade = getattr(carta_api, "rarity", None),
                        elixir   = getattr(carta_api, "elixir_cost", None),
                        url_icon = _url_icone(getattr(carta_api, "name", "")),
                    )
                    db.add(carta)
                    db.flush()

                # evita duplicata na chave composta
                existe_bc = (
                    db.query(BatalhaCartas)
                    .filter(
                        BatalhaCartas.batalha_id == batalha.id,
                        BatalhaCartas.carta_id   == carta.id,
                    )
                    .first()
                )
                if not existe_bc:
                    db.add(BatalhaCartas(
                        batalha_id = batalha.id,
                        carta_id   = carta.id,
                        nivel      = getattr(carta_api, "level", None),
                    ))
        except (AttributeError, IndexError):
            pass  # deck indisponível para este tipo de batalha

        # Atualiza última batalha do jogador
        data_b = _parse_data(battle_time)
        if data_b and (not jogador.ultima_batalha or data_b > jogador.ultima_batalha):
            jogador.ultima_batalha = data_b

        novas += 1

    db.commit()
    return novas


def popular_batalhas_todos(
    client: clashroyale.OfficialAPI, db: Session, jogadores: List[Jogador]
) -> None:
    separador("POPULANDO → batalhas + batalha_cartas")
    total = 0
    for jogador in jogadores:
        n = popular_batalhas_jogador(client, db, jogador)
        total += n
        print(f"   ⚔️  {jogador.nickname:<22} → {n} nova(s) batalha(s)")
    print(f"  ✅ {total} batalhas novas salvas no banco.")


# =============================================================================
# 5. Popular guerras + contribuições
# =============================================================================

def popular_guerras(
    client: clashroyale.OfficialAPI, db: Session, clan: Clan
) -> int:
    """
    Busca o warlog do clã e popula `guerras` + `contribuicoes_guerra`.
    Retorna o número de guerras processadas.
    """
    separador(f"POPULANDO → guerras  [clã: {clan.tag}]")
    try:
        warlog = client.get_clan_war_log(clan.tag)
    except clashroyale.errors.NotFoundError:
        print(f"  ⚠️ Warlog não disponível para {clan.tag} (clã pode ser privado).")
        return 0
    except Exception as erro:
        print(f"  ❌ Erro warlog: {erro}")
        return 0

    if not warlog:
        print("  ℹ️ Sem histórico de guerras.")
        return 0

    processadas = 0
    for war in warlog:
        temporada = str(getattr(war, "season_id", "") or "")

        guerra = (
            db.query(Guerra)
            .filter(Guerra.clan_id == clan.id, Guerra.temporada == temporada)
            .first()
        )
        if guerra is None:
            guerra = Guerra(clan_id=clan.id, temporada=temporada, tipo="riverRace")
            db.add(guerra)

        # Localiza dados do clã nos standings
        standings = getattr(war, "standings", []) or []
        for pos, standing in enumerate(standings, 1):
            clan_st = getattr(standing, "clan", None)
            if clan_st and getattr(clan_st, "tag", "") == clan.tag:
                guerra.colocacao        = pos
                guerra.batalhas_ganhas  = getattr(clan_st, "battles_played", 0) or 0
                guerra.pontuacao        = getattr(clan_st, "fame", 0) or 0
                break

        db.flush()

        # Contribuições individuais
        participantes = getattr(war, "participants", []) or []
        for p in participantes:
            p_tag = getattr(p, "tag", None)
            if not p_tag:
                continue
            jogador = db.query(Jogador).filter(Jogador.tag == p_tag).first()
            if jogador is None:
                continue

            contrib = (
                db.query(ContribuicaoGuerra)
                .filter(
                    ContribuicaoGuerra.guerra_id  == guerra.id,
                    ContribuicaoGuerra.jogador_id == jogador.id,
                )
                .first()
            )
            if contrib is None:
                contrib = ContribuicaoGuerra(guerra_id=guerra.id, jogador_id=jogador.id)
                db.add(contrib)

            contrib.batalhas = getattr(p, "battles_played", 0) or 0
            contrib.vitorias = getattr(p, "wins", 0) or 0
            contrib.fame     = getattr(p, "fame", 0) or 0

        processadas += 1
        print(f"   🏆 Temporada {temporada} | Colocação: {guerra.colocacao} | Fame: {guerra.pontuacao}")

    db.commit()
    print(f"  ✅ {processadas} guerra(s) salvas no banco.")
    return processadas


# =============================================================================
# EXECUÇÃO PRINCIPAL
# =============================================================================

if __name__ == "__main__":
    print("\n⚔️  ROYLE METRICS — Popular Banco de Dados via API")
    print(f"   Proxy : {PROXY}")
    print(f"   Token : {'configurado ✅' if TOKEN else 'NÃO ENCONTRADO ❌'}")
    print(f"   Clãs  : {TAGS_CLAS}")

    client = clashroyale.OfficialAPI(token=TOKEN, url=PROXY)

    # Verifica conexão antes de abrir sessão do banco
    if not testar_conexao(client):
        print("\n❌ Falha na conexão com a API. Abortando.")
        sys.exit(1)

    db = SessionLocal()
    try:
        # 1. Cartas (global — independe de clã)
        popular_cartas(client, db)

        for tag in TAGS_CLAS:
            # 2. Clã
            clan = popular_clan(client, db, tag)
            if clan is None:
                continue

            # 3. Jogadores
            jogadores = popular_jogadores(client, db, clan)

            # 4. Batalhas de todos os membros
            popular_batalhas_todos(client, db, jogadores)

            # 5. Histórico de guerras
            popular_guerras(client, db, clan)

    except KeyboardInterrupt:
        print("\n\n⚠️  Interrompido pelo usuário. Dados parciais foram salvos.")
    except Exception as erro:
        db.rollback()
        print(f"\n❌ Erro inesperado: {erro}")
        raise
    finally:
        db.close()

    separador("RESULTADO FINAL")
    print("✅ Banco populado com dados reais da API do Clash Royale!")
    print()
