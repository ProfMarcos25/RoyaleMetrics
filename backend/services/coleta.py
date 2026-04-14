"""
Serviço de Coleta de Dados — Royle Metrics
Responsável por buscar dados na API do Clash Royale e
persistir no banco PostgreSQL de forma idempotente (sem duplicatas).
"""
import hashlib
import logging
from datetime import datetime
from typing import Optional

import clashroyale
from sqlalchemy.orm import Session

from ..models import (
    Batalha,
    BatalhaCartas,
    Carta,
    Clan,
    ContribuicaoGuerra,
    Guerra,
    Jogador,
)
from .clash_client import get_client

logger = logging.getLogger(__name__)


# =============================================================
# Funções auxiliares internas
# =============================================================

def _normalizar_tag(tag: str) -> str:
    """
    Garante que a tag começa com '#' e está em maiúsculas.
    A API do Clash Royale aceita tags com ou sem '#'.
    """
    tag = tag.strip().upper()
    if not tag.startswith("#"):
        tag = "#" + tag
    return tag


def _gerar_battle_id(player_tag: str, battle_time: str) -> str:
    """
    Gera um identificador único para cada batalha combinando
    a tag do jogador com o horário da batalha via SHA-256.
    Evita inserções duplicadas mesmo em coletas repetidas.

    Args:
        player_tag: Tag do jogador (ex: '#ABC123').
        battle_time: Horário da batalha no formato da API.

    Retorna:
        str: Hash hexadecimal com 32 caracteres.
    """
    chave = f"{player_tag}|{battle_time}"
    return hashlib.sha256(chave.encode()).hexdigest()[:32]


def _determinar_resultado(battle: object) -> str:
    """
    Determina o resultado de uma batalha comparando coroas.
    A API retorna 'team' e 'opponent' como listas de participantes.

    Args:
        battle: Objeto de batalha retornado pela API.

    Retorna:
        str: 'vitoria', 'derrota' ou 'empate'.
    """
    try:
        coroas_time = battle.team[0].crowns
        coroas_oponente = battle.opponent[0].crowns
        if coroas_time > coroas_oponente:
            return "vitoria"
        elif coroas_time < coroas_oponente:
            return "derrota"
        else:
            return "empate"
    except (AttributeError, IndexError):
        return "empate"


def _url_icone_carta(nome: str) -> str:
    """
    Monta a URL do ícone da carta usando o repositório público
    de assets do RoyaleAPI no GitHub.

    Args:
        nome: Nome da carta (ex: 'Fireball').

    Retorna:
        str: URL completa da imagem PNG da carta.
    """
    # Converte espaços em hifens e coloca em minúsculas (padrão dos assets)
    nome_formatado = nome.lower().replace(" ", "-")
    return f"https://royaleapi.github.io/cr-api-assets/cards/{nome_formatado}.png"


# =============================================================
# Funções principais de sincronização
# =============================================================

def sincronizar_cartas(db: Session) -> int:
    """
    Busca todas as cartas do jogo via API e persiste no banco.
    Realiza upsert: atualiza se existir, insere se não existir.
    Essa função deve ser executada na primeira inicialização do projeto.

    Args:
        db: Sessão ativa do banco de dados SQLAlchemy.

    Retorna:
        int: Número de cartas sincronizadas.

    Erros tratados:
        - NotFoundError: endpoint inválido (raro para /cards).
        - RatelimitError: muitas requisições — aguarda próximo ciclo.
    """
    client = get_client()
    logger.info("Iniciando sincronização de cartas...")

    try:
        cartas_api = client.get_cards()
    except clashroyale.errors.NotFoundError:
        logger.error("Endpoint de cartas não encontrado na API.")
        return 0
    except clashroyale.errors.RatelimitError:
        logger.warning("Rate limit atingido ao buscar cartas. Tente novamente mais tarde.")
        return 0

    contador = 0

    for carta_api in cartas_api:
        # Tenta localizar carta existente pelo ID da API
        carta = db.query(Carta).filter(Carta.card_id == carta_api.id).first()

        if carta is None:
            # Insere nova carta
            carta = Carta(
                card_id=carta_api.id,
                nome=getattr(carta_api, "name", "Desconhecida"),
                tipo=getattr(carta_api, "type", None),
                raridade=getattr(carta_api, "rarity", None),
                elixir=getattr(carta_api, "elixir_cost", None),
                max_nivel=getattr(carta_api, "max_level", None),
                url_icon=_url_icone_carta(getattr(carta_api, "name", "")),
            )
            db.add(carta)
        else:
            # Atualiza dados da carta existente
            carta.nome = getattr(carta_api, "name", carta.nome)
            carta.tipo = getattr(carta_api, "type", carta.tipo)
            carta.raridade = getattr(carta_api, "rarity", carta.raridade)
            carta.elixir = getattr(carta_api, "elixir_cost", carta.elixir)
            carta.max_nivel = getattr(carta_api, "max_level", carta.max_nivel)

        contador += 1

    db.commit()
    logger.info(f"Sincronização de cartas concluída: {contador} cartas processadas.")
    return contador


def sincronizar_clan(tag: str, db: Session) -> Optional[Clan]:
    """
    Sincroniza todos os dados de um clã:
    - Dados gerais do clã (nome, descrição, troféus)
    - Lista de membros (jogadores)
    - Batalhas de cada membro

    Args:
        tag: Tag do clã (ex: '#ABC123').
        db: Sessão ativa do banco de dados.

    Retorna:
        Clan: Objeto do clã sincronizado, ou None em caso de erro.

    Erros tratados:
        - NotFoundError: clã não encontrado (tag inválida).
        - RatelimitError: aguarda próximo ciclo de coleta.
    """
    client = get_client()
    tag = _normalizar_tag(tag)
    logger.info(f"Sincronizando clã {tag}...")

    try:
        clan_api = client.get_clan(tag)
    except clashroyale.errors.NotFoundError:
        logger.error(f"Clã {tag} não encontrado na API. Verifique a tag.")
        return None
    except clashroyale.errors.RatelimitError:
        logger.warning(f"Rate limit ao buscar clã {tag}.")
        return None

    # Upsert do clã
    clan = db.query(Clan).filter(Clan.tag == tag).first()
    if clan is None:
        clan = Clan(tag=tag)
        db.add(clan)

    clan.nome = getattr(clan_api, "name", clan.nome or "Sem nome")
    clan.descricao = getattr(clan_api, "description", clan.descricao)
    clan.trofeus = getattr(clan_api, "clan_score", 0) or getattr(clan_api, "clanScore", 0)
    clan.membros = getattr(clan_api, "members", 0)
    clan.atualizado_em = datetime.utcnow()
    db.flush()  # garante que clan.id esteja disponível

    # Sincroniza cada membro do clã
    membros_api = getattr(clan_api, "member_list", []) or []
    for membro_api in membros_api:
        membro_tag = getattr(membro_api, "tag", None)
        if not membro_tag:
            continue

        jogador = db.query(Jogador).filter(Jogador.tag == membro_tag).first()
        if jogador is None:
            jogador = Jogador(tag=membro_tag)
            db.add(jogador)

        jogador.nickname = getattr(membro_api, "name", jogador.nickname or "Desconhecido")
        jogador.nivel = getattr(membro_api, "exp_level", jogador.nivel)
        jogador.trofeus = getattr(membro_api, "trophies", jogador.trofeus)
        jogador.trofeus_recorde = getattr(membro_api, "best_trophies", jogador.trofeus_recorde)
        jogador.arena = getattr(
            getattr(membro_api, "arena", None), "name", jogador.arena
        )
        jogador.clan_id = clan.id
        db.flush()

        # Sincroniza batalhas do membro
        sincronizar_batalhas_jogador(membro_tag, db)

    db.commit()
    logger.info(f"Clã {tag} sincronizado com {len(membros_api)} membros.")
    return clan


def sincronizar_batalhas_jogador(tag: str, db: Session) -> int:
    """
    Busca as batalhas recentes de um jogador e persiste no banco.
    Usa o campo battle_id (hash) para evitar duplicatas.
    Registra também as cartas usadas em cada batalha (deck).

    Args:
        tag: Tag do jogador (ex: '#XYZ456').
        db: Sessão ativa do banco de dados.

    Retorna:
        int: Número de novas batalhas inseridas.

    Erros tratados:
        - NotFoundError: jogador não encontrado.
        - RatelimitError: aguarda próximo ciclo.
    """
    client = get_client()
    tag = _normalizar_tag(tag)

    jogador = db.query(Jogador).filter(Jogador.tag == tag).first()
    if jogador is None:
        logger.warning(f"Jogador {tag} não encontrado no banco. Pulando batalhas.")
        return 0

    try:
        batalhas_api = client.get_player_battles(tag)
    except clashroyale.errors.NotFoundError:
        logger.error(f"Jogador {tag} não encontrado na API.")
        return 0
    except clashroyale.errors.RatelimitError:
        logger.warning(f"Rate limit ao buscar batalhas de {tag}.")
        return 0

    novas = 0

    for battle_api in batalhas_api:
        battle_time = str(getattr(battle_api, "battle_time", ""))
        battle_id = _gerar_battle_id(tag, battle_time)

        # Verifica se a batalha já foi registrada (evita duplicata)
        if db.query(Batalha).filter(Batalha.battle_id == battle_id).first():
            continue

        resultado = _determinar_resultado(battle_api)

        # Extrai troféus ganhos (pode ser 0 em guerras/torneios)
        trofeus_ganhos = getattr(battle_api, "trophy_change", 0) or 0

        # Troféus do time e do oponente
        time_trofeus = None
        oponente_tag = None
        oponente_trofeus = None
        try:
            time_trofeus = getattr(battle_api.team[0], "starting_trophies", None)
            oponente_tag = getattr(battle_api.opponent[0], "tag", None)
            oponente_trofeus = getattr(battle_api.opponent[0], "starting_trophies", None)
        except (AttributeError, IndexError):
            pass

        # Converte data da batalha (formato: "20230115T120000.000Z")
        data_batalha = None
        if battle_time:
            try:
                data_batalha = datetime.strptime(battle_time[:15], "%Y%m%dT%H%M%S")
            except ValueError:
                data_batalha = None

        batalha = Batalha(
            battle_id=battle_id,
            jogador_id=jogador.id,
            tipo=getattr(battle_api, "type", "PvP"),
            resultado=resultado,
            trofeus_ganhos=trofeus_ganhos,
            time_trofeus=time_trofeus,
            oponente_tag=oponente_tag,
            oponente_trofeus=oponente_trofeus,
            data_batalha=data_batalha,
        )
        db.add(batalha)
        db.flush()  # precisa do batalha.id para as cartas

        # Registra cartas do deck do jogador nessa batalha
        try:
            cartas_deck = battle_api.team[0].cards or []
            for carta_api in cartas_deck:
                carta_id_api = getattr(carta_api, "id", None)
                if carta_id_api is None:
                    continue

                carta = db.query(Carta).filter(Carta.card_id == carta_id_api).first()
                if carta is None:
                    # Insere carta desconhecida para não perder o registro
                    carta = Carta(
                        card_id=carta_id_api,
                        nome=getattr(carta_api, "name", f"Carta_{carta_id_api}"),
                        raridade=getattr(carta_api, "rarity", None),
                        elixir=getattr(carta_api, "elixir_cost", None),
                        max_nivel=getattr(carta_api, "max_level", None),
                        url_icon=_url_icone_carta(getattr(carta_api, "name", "")),
                    )
                    db.add(carta)
                    db.flush()

                bc = BatalhaCartas(
                    batalha_id=batalha.id,
                    carta_id=carta.id,
                    nivel=getattr(carta_api, "level", None),
                )
                db.add(bc)
        except (AttributeError, IndexError):
            pass  # deck indisponível para este tipo de batalha

        # Atualiza timestamp da última batalha do jogador
        if data_batalha and (
            jogador.ultima_batalha is None or data_batalha > jogador.ultima_batalha
        ):
            jogador.ultima_batalha = data_batalha

        novas += 1

    db.commit()
    logger.info(f"Batalhas de {tag}: {novas} novas batalhas registradas.")
    return novas


def sincronizar_warlog(tag: str, db: Session) -> int:
    """
    Busca o histórico de guerras do clã e persiste no banco.
    Inclui desempenho individual dos membros (contribuições).

    Args:
        tag: Tag do clã (ex: '#ABC123').
        db: Sessão ativa do banco de dados.

    Retorna:
        int: Número de guerras processadas.

    Erros tratados:
        - NotFoundError: clã não encontrado.
        - RatelimitError: aguarda próximo ciclo.
    """
    client = get_client()
    tag = _normalizar_tag(tag)

    clan = db.query(Clan).filter(Clan.tag == tag).first()
    if clan is None:
        logger.warning(f"Clã {tag} não encontrado no banco. Execute sincronizar_clan primeiro.")
        return 0

    try:
        warlog_api = client.get_clan_warlog(tag)
    except clashroyale.errors.NotFoundError:
        logger.error(f"Clã {tag} não encontrado na API (warlog).")
        return 0
    except clashroyale.errors.RatelimitError:
        logger.warning(f"Rate limit ao buscar warlog de {tag}.")
        return 0

    processadas = 0

    for war_api in warlog_api:
        temporada = str(getattr(war_api, "season_id", "") or "")

        # Verifica se essa guerra já foi registrada
        guerra = db.query(Guerra).filter(
            Guerra.clan_id == clan.id,
            Guerra.temporada == temporada,
        ).first()

        if guerra is None:
            guerra = Guerra(clan_id=clan.id, temporada=temporada)
            db.add(guerra)

        # Encontra a posição do clã nos standings
        standings = getattr(war_api, "standings", []) or []
        colocacao = None
        batalhas_ganhas = 0
        batalhas_perdidas = 0
        pontuacao = 0

        for i, standing in enumerate(standings):
            clan_info = getattr(standing, "clan", None)
            if clan_info and getattr(clan_info, "tag", "") == tag:
                colocacao = i + 1
                batalhas_ganhas = getattr(clan_info, "battles_played", 0) or 0
                pontuacao = getattr(clan_info, "fame", 0) or 0
                break

        guerra.tipo = "riverRace"
        guerra.colocacao = colocacao
        guerra.batalhas_ganhas = batalhas_ganhas
        guerra.batalhas_perdidas = batalhas_perdidas
        guerra.pontuacao = pontuacao
        db.flush()

        # Registra contribuições individuais
        participantes = getattr(war_api, "participants", []) or []
        for p in participantes:
            p_tag = getattr(p, "tag", None)
            if not p_tag:
                continue

            jogador = db.query(Jogador).filter(Jogador.tag == p_tag).first()
            if jogador is None:
                continue

            contrib = db.query(ContribuicaoGuerra).filter(
                ContribuicaoGuerra.guerra_id == guerra.id,
                ContribuicaoGuerra.jogador_id == jogador.id,
            ).first()

            if contrib is None:
                contrib = ContribuicaoGuerra(
                    guerra_id=guerra.id, jogador_id=jogador.id
                )
                db.add(contrib)

            contrib.batalhas = getattr(p, "battles_played", 0) or 0
            contrib.vitorias = getattr(p, "wins", 0) or 0
            contrib.fame = getattr(p, "fame", 0) or 0

        processadas += 1

    db.commit()
    logger.info(f"Warlog do clã {tag}: {processadas} guerras processadas.")
    return processadas


def sincronizar_river_race(tag: str, db: Session) -> Optional[Guerra]:
    """
    Busca a guerra atual (River Race em andamento) e persiste no banco.
    Diferente do warlog, esta função captura dados da guerra ativa,
    que ainda não foi concluída.

    Args:
        tag: Tag do clã (ex: '#ABC123').
        db: Sessão ativa do banco de dados.

    Retorna:
        Guerra: Objeto da guerra atual, ou None em caso de erro.

    Erros tratados:
        - NotFoundError: clã sem guerra ativa no momento.
        - RatelimitError: aguarda próximo ciclo.
    """
    client = get_client()
    tag = _normalizar_tag(tag)

    clan = db.query(Clan).filter(Clan.tag == tag).first()
    if clan is None:
        logger.warning(f"Clã {tag} não encontrado no banco.")
        return None

    try:
        race_api = client.get_clan_current_river_race(tag)
    except clashroyale.errors.NotFoundError:
        logger.warning(f"Clã {tag} não está em uma guerra ativa no momento.")
        return None
    except clashroyale.errors.RatelimitError:
        logger.warning(f"Rate limit ao buscar river race de {tag}.")
        return None

    # A temporada ativa usa "em_andamento" como identificador
    temporada = str(getattr(race_api, "season_id", "em_andamento"))

    guerra = db.query(Guerra).filter(
        Guerra.clan_id == clan.id,
        Guerra.temporada == temporada,
    ).first()

    if guerra is None:
        guerra = Guerra(clan_id=clan.id, temporada=temporada, tipo="riverRace")
        db.add(guerra)
        db.flush()

    # Atualiza dados gerais da guerra ativa
    clan_api_data = getattr(race_api, "clan", None)
    if clan_api_data:
        guerra.pontuacao = getattr(clan_api_data, "fame", 0) or 0
        guerra.batalhas_ganhas = getattr(clan_api_data, "wins", 0) or 0

    db.flush()

    # Processa participantes e suas contribuições
    participantes = getattr(race_api, "clan", None)
    participantes_lista = getattr(participantes, "participants", []) if participantes else []

    for p in participantes_lista:
        p_tag = getattr(p, "tag", None)
        if not p_tag:
            continue

        jogador = db.query(Jogador).filter(Jogador.tag == p_tag).first()
        if jogador is None:
            continue

        contrib = db.query(ContribuicaoGuerra).filter(
            ContribuicaoGuerra.guerra_id == guerra.id,
            ContribuicaoGuerra.jogador_id == jogador.id,
        ).first()

        if contrib is None:
            contrib = ContribuicaoGuerra(
                guerra_id=guerra.id, jogador_id=jogador.id
            )
            db.add(contrib)

        contrib.batalhas = getattr(p, "battles_played", 0) or 0
        contrib.vitorias = getattr(p, "wins", 0) or 0
        contrib.fame = getattr(p, "fame", 0) or 0

    db.commit()
    logger.info(f"River Race do clã {tag} sincronizado. Pontuação atual: {guerra.pontuacao}.")
    return guerra
