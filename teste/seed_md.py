"""
Funções auxiliares de teste da coleta da API do Clash Royale.

Este módulo concentra os objetos solicitados:
- testar_conexao
- testar_membros
- testar_batalhas_jogador
"""

from __future__ import annotations

from typing import List

import clashroyale


def separador(titulo: str) -> None:
    print("\n" + "=" * 55)
    print(f"  {titulo}")
    print("=" * 55)


def testar_conexao(client: clashroyale.OfficialAPI) -> bool:
    """Testa conexão com a API consultando todas as cartas."""
    separador("1. TESTE DE CONEXÃO — Lista de Cartas")
    try:
        cartas = client.get_all_cards()
        total = len(cartas)
        print(f"✔ Conexão OK! Total de cartas no jogo: {total}")
        separador("AMOSTRA DE CARTAS")
        print("\n  TODAS AS CARTAS:")
        for carta in cartas:
            elixir = getattr(carta, "elixir_cost", "?")
            raridade = getattr(carta, "rarity", "?")
            print(f" ✅ {carta.name:<40} | Elixir: {elixir} | Raridade: {raridade}")
        return True
    except clashroyale.errors.NotFoundError:
        print("❌ Erro: token inválido ou endpoint não encontrado.")
    except clashroyale.errors.RatelimitError:
        print("⚠️ Limite de requisições atingido. Aguarde alguns segundos.")
    except Exception as error:
        print(f"❌ Erro inesperado: {error}")
    return False


def testar_membros(client: clashroyale.OfficialAPI, tag: str) -> List[str]:
    """Coleta membros do clã e retorna as tags dos jogadores."""
    separador(f"3. MEMBROS DO CLÃ — {tag}")
    tags_membros: List[str] = []
    try:
        clan = client.get_clan(tag)
        membros = clan.member_list
        print(f"✔ {len(membros)} membro(s) encontrado(s):")
        for indice, membro in enumerate(membros, 1):
            tags_membros.append(membro.tag)
            arena = getattr(membro, "arena", None)
            arena_nome = getattr(arena, "name", "?") if arena else "?"
            print(
                f"   {indice:>2}. {membro.name:<20} | "
                f"Troféus: {membro.trophies:<6} | Arena: {arena_nome}"
            )
    except clashroyale.errors.NotFoundError:
        print(f"❌ Clã '{tag}' não encontrado.")
    except Exception as error:
        print(f"❌ Erro: {error}")
    return tags_membros


def testar_batalhas_jogador(client: clashroyale.OfficialAPI, tag: str, ) -> None:
    """Coleta e exibe as últimas batalhas de um jogador."""
    separador(f"4. BATALHAS DO JOGADOR — ({tag})")
    try:
        batalhas = client.get_player_battles(tag)
        print(f"✔ {len(batalhas)} batalha(s) encontrada(s):")
        for indice, batalha in enumerate(batalhas[:5], 1):
            try:
                coroas_time = batalha.team[0].crowns
                coroas_oponente = batalha.opponent[0].crowns
                if coroas_time > coroas_oponente:
                    resultado = "VITÓRIA"
                elif coroas_time < coroas_oponente:
                    resultado = "DERROTA"
                else:
                    resultado = "EMPATE"
                tipo = getattr(batalha, "type", "?")
                data = getattr(batalha, "battle_time", "?")
                print(
                    f"   {indice}. {resultado:<8} | Coroas: {coroas_time}x{coroas_oponente} "
                    f"| Tipo: {tipo} | Data: {data}"
                )
            except (AttributeError, IndexError):
                print(f"   {indice}. (batalha com formato inesperado)")
        if len(batalhas) > 5:
            print(f"   ... e mais {len(batalhas) - 5} batalha(s).")
    except clashroyale.errors.NotFoundError:
        print(f"❌ Jogador '{tag}' não encontrado.")
    except clashroyale.errors.RatelimitError:
        print("⚠️ Rate limit atingido.")
    except Exception as error:
        print(f"❌ Erro: {error}")



def testar_warlog(client: clashroyale.OfficialAPI, tag: str) -> None:
    """
    Testa a coleta do histórico de guerras (warlog) de um clã.

    Args:
        client: Cliente da API JÁ inicializado.
        tag: Tag do clã.
    """
    separador(f"5. HISTÓRICO DE GUERRAS (WARLOG) — {tag}")
    try:
        warlog = client.get_clan_war_log(tag)
        if not warlog:
            print("ℹ️  Sem histórico de guerras disponível.")
            return
        print(f"✔ {len(warlog)} guerra(s) no histórico:")
        for i, guerra in enumerate(warlog[:3], 1):
            season = getattr(guerra, "season_id", "?")
            standings = getattr(guerra, "standings", [])
            colocacao = "?"
            if standings:
                colocacao = getattr(standings[0], "rank", "?")
            print(f"   {i}. Temporada: {season} | Colocação: {colocacao}")
    except clashroyale.errors.NotFoundError:
        print(f"❌ Warlog não disponível para '{tag}' (clã pode ser privado).")
    except Exception as e:
        print(f"❌ Erro: {e}")