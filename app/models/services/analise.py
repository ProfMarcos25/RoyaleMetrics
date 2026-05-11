"""
Serviço de Análise de Dados — Royle Metrics
Realiza consultas SQL e processa os resultados com Pandas,
gerando gráficos interativos com Plotly para o front-end.
"""
import logging
from typing import Any, Dict

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# Paleta de cores por raridade para gráficos de cartas
CORES_RARIDADE: Dict[str, str] = {
    "Common": "#8892a4",
    "Rare": "#4a9eff",
    "Epic": "#a855f7",
    "Legendary": "#e8c94a",
    "Champion": "#ef4444",
}

# Paleta de cores para clãs (até 8 clãs distintos)
PALETA_CLANS: list[str] = [
    "#e8c94a", "#4a9eff", "#34d399", "#f87171",
    "#a78bfa", "#fb923c", "#38bdf8", "#f472b6",
]

# Layout padrão dos gráficos (tema escuro do projeto)
LAYOUT_PADRAO: Dict[str, Any] = {
    "paper_bgcolor": "rgba(0,0,0,0)",
    "plot_bgcolor": "rgba(0,0,0,0)",
    "font": {"color": "#e2e8f0", "family": "Rajdhani, sans-serif"},
    "margin": {"l": 20, "r": 20, "t": 60, "b": 20},
    "legend": {
        "bgcolor": "rgba(18,21,42,0.8)",
        "bordercolor": "#e8c94a",
        "borderwidth": 1,
    },
}

# Mensagem padrão quando não há dados
MENSAGEM_SEM_DADOS: Dict[str, Any] = {
    "data": [],
    "layout": {
        **LAYOUT_PADRAO,
        "title": {
            "text": "⚔ Sem dados ainda. Clique em <b>Atualizar dados</b> para sincronizar.",
            "font": {"size": 16, "color": "#8892a4"},
            "x": 0.5,
            "xanchor": "center",
        },
        "xaxis": {"visible": False},
        "yaxis": {"visible": False},
    },
}


def gerar_ranking(db: Session) -> Dict[str, Any]:
    """
    Gera o ranking dos 20 melhores jogadores por troféus.
    Produz um gráfico de barras horizontais colorido por clã.

    Args:
        db: Sessão ativa do banco de dados.

    Retorna:
        dict: Objeto Plotly serializável com 'data' e 'layout'.
    """
    sql = text("""
        SELECT
            j.nickname,
            j.trofeus,
            j.trofeus_recorde,
            j.arena,
            COALESCE(c.nome, 'Sem clã') AS clan
        FROM jogadores j
        LEFT JOIN clans c ON j.clan_id = c.id
        ORDER BY j.trofeus DESC
        LIMIT 20
    """)

    try:
        resultado = db.execute(sql)
        df = pd.DataFrame(resultado.fetchall(), columns=resultado.keys())
    except Exception as e:
        logger.error(f"Erro ao gerar ranking: {e}")
        return MENSAGEM_SEM_DADOS

    if df.empty:
        return MENSAGEM_SEM_DADOS

    # Mapeia cores por clã
    clans_unicos = df["clan"].unique().tolist()
    mapa_cores = {clan: PALETA_CLANS[i % len(PALETA_CLANS)] for i, clan in enumerate(clans_unicos)}

    # Cria um trace por clã para exibir legenda por cor
    traces = []
    for clan in clans_unicos:
        df_clan = df[df["clan"] == clan]
        trace = go.Bar(
            x=df_clan["trofeus"],
            y=df_clan["nickname"],
            orientation="h",
            name=clan,
            marker_color=mapa_cores[clan],
            text=df_clan["trofeus"].apply(lambda v: f"🏆 {v:,}"),
            textposition="inside",
            hovertemplate=(
                "<b>%{y}</b><br>"
                "Troféus: %{x:,}<br>"
                "Clã: " + clan + "<extra></extra>"
            ),
        )
        traces.append(trace)

    layout = {
        **LAYOUT_PADRAO,
        "title": {
            "text": "⚔ Ranking de Jogadores — Top 20",
            "font": {"size": 20, "color": "#e8c94a"},
            "x": 0.5,
            "xanchor": "center",
        },
        "xaxis": {
            "title": "Troféus",
            "gridcolor": "#1a1f38",
            "tickformat": ",",
        },
        "yaxis": {
            "autorange": "reversed",
            "gridcolor": "#1a1f38",
        },
        "barmode": "stack",
        "height": max(400, len(df) * 35),
    }

    return {"data": [t.to_plotly_json() for t in traces], "layout": layout}


def gerar_analise_cartas(db: Session) -> Dict[str, Any]:
    """
    Analisa performance das cartas mais usadas nas batalhas.
    Gera um scatter plot: frequência × taxa de vitória,
    com tamanho proporcional ao custo de elixir e cor por raridade.

    Args:
        db: Sessão ativa do banco de dados.

    Retorna:
        dict: Objeto Plotly serializável com 'data' e 'layout'.
    """
    sql = text("""
        SELECT
            ca.nome,
            ca.raridade,
            ca.elixir,
            COUNT(bc.batalha_id)                                           AS frequencia,
            ROUND(
                SUM(CASE WHEN b.resultado = 'vitoria' THEN 1 ELSE 0 END)::numeric
                / NULLIF(COUNT(bc.batalha_id), 0) * 100, 1
            )                                                               AS taxa_vitoria
        FROM cartas ca
        JOIN batalha_cartas bc ON ca.id = bc.carta_id
        JOIN batalhas b        ON bc.batalha_id = b.id
        GROUP BY ca.nome, ca.raridade, ca.elixir
        HAVING COUNT(bc.batalha_id) >= 5
        ORDER BY taxa_vitoria DESC
    """)

    try:
        resultado = db.execute(sql)
        df = pd.DataFrame(resultado.fetchall(), columns=resultado.keys())
    except Exception as e:
        logger.error(f"Erro ao gerar análise de cartas: {e}")
        return MENSAGEM_SEM_DADOS

    if df.empty:
        return MENSAGEM_SEM_DADOS

    # Tamanho proporcional ao elixir (mínimo para visibilidade)
    df["tamanho"] = df["elixir"].fillna(3) * 8 + 10
    df["raridade"] = df["raridade"].fillna("Common")

    traces = []
    for raridade, cor in CORES_RARIDADE.items():
        df_r = df[df["raridade"] == raridade]
        if df_r.empty:
            continue

        trace = go.Scatter(
            x=df_r["frequencia"],
            y=df_r["taxa_vitoria"],
            mode="markers+text",
            name=raridade,
            text=df_r["nome"],
            textposition="top center",
            textfont={"size": 9, "color": "#e2e8f0"},
            marker=dict(
                size=df_r["tamanho"],
                color=cor,
                opacity=0.85,
                line=dict(width=1, color="#0a0c14"),
            ),
            hovertemplate=(
                "<b>%{text}</b><br>"
                "Frequência: %{x}<br>"
                "Taxa de vitória: %{y}%<br>"
                "Raridade: " + raridade + "<extra></extra>"
            ),
        )
        traces.append(trace)

    # Linha de referência em 50% de taxa de vitória
    forma_linha_50 = dict(
        type="line",
        x0=0, x1=1, xref="paper",
        y0=50, y1=50, yref="y",
        line=dict(color="#8892a4", width=1, dash="dot"),
    )

    layout = {
        **LAYOUT_PADRAO,
        "title": {
            "text": "⚔ Performance de Cartas — Frequência × Taxa de Vitória",
            "font": {"size": 18, "color": "#e8c94a"},
            "x": 0.5,
            "xanchor": "center",
        },
        "xaxis": {
            "title": "Frequência (nº de batalhas)",
            "gridcolor": "#1a1f38",
        },
        "yaxis": {
            "title": "Taxa de Vitória (%)",
            "gridcolor": "#1a1f38",
            "range": [0, 105],
        },
        "shapes": [forma_linha_50],
        "annotations": [{
            "x": 1, "y": 50, "xref": "paper", "yref": "y",
            "text": "50% vitória", "showarrow": False,
            "font": {"color": "#8892a4", "size": 10},
            "xanchor": "right",
        }],
        "height": 550,
    }

    return {"data": [t.to_plotly_json() for t in traces], "layout": layout}


def gerar_historico_guerras(db: Session) -> Dict[str, Any]:
    """
    Gera um gráfico de linhas com a evolução da pontuação dos clãs
    ao longo das temporadas de guerra.

    Args:
        db: Sessão ativa do banco de dados.

    Retorna:
        dict: Objeto Plotly serializável com 'data' e 'layout'.
    """
    sql = text("""
        SELECT
            g.temporada,
            COALESCE(c.nome, 'Clã desconhecido') AS clan,
            g.batalhas_ganhas,
            g.batalhas_perdidas,
            g.pontuacao,
            g.colocacao
        FROM guerras g
        JOIN clans c ON g.clan_id = c.id
        ORDER BY g.data_inicio DESC
        LIMIT 200
    """)

    try:
        resultado = db.execute(sql)
        df = pd.DataFrame(resultado.fetchall(), columns=resultado.keys())
    except Exception as e:
        logger.error(f"Erro ao gerar histórico de guerras: {e}")
        return MENSAGEM_SEM_DADOS

    if df.empty:
        return MENSAGEM_SEM_DADOS

    # Inverte para ordem cronológica
    df = df.iloc[::-1].reset_index(drop=True)

    clans_unicos = df["clan"].unique().tolist()
    traces = []

    for i, clan in enumerate(clans_unicos):
        df_clan = df[df["clan"] == clan]
        cor = PALETA_CLANS[i % len(PALETA_CLANS)]

        trace = go.Scatter(
            x=df_clan["temporada"],
            y=df_clan["pontuacao"],
            mode="lines+markers",
            name=clan,
            line=dict(color=cor, width=2),
            marker=dict(size=8, color=cor),
            hovertemplate=(
                "<b>%{x}</b><br>"
                "Clã: " + clan + "<br>"
                "Pontuação: %{y:,}<br>"
                "<extra></extra>"
            ),
        )
        traces.append(trace)

    layout = {
        **LAYOUT_PADRAO,
        "title": {
            "text": "⚔ Histórico de Guerras — Evolução da Pontuação",
            "font": {"size": 18, "color": "#e8c94a"},
            "x": 0.5,
            "xanchor": "center",
        },
        "xaxis": {
            "title": "Temporada",
            "gridcolor": "#1a1f38",
        },
        "yaxis": {
            "title": "Pontuação (Fame)",
            "gridcolor": "#1a1f38",
            "tickformat": ",",
        },
        "height": 450,
    }

    return {"data": [t.to_plotly_json() for t in traces], "layout": layout}


def gerar_analise_torneios(db: Session) -> Dict[str, Any]:
    """
    Gera um gráfico de barras com os torneios escolares,
    destacando o número de participantes e o campeão de cada torneio.

    Args:
        db: Sessão ativa do banco de dados.

    Retorna:
        dict: Objeto Plotly serializável com 'data' e 'layout'.
    """
    sql = text("""
        SELECT
            t.nome                   AS torneio,
            t.data,
            t.formato,
            COUNT(DISTINCT pt.jogador_a_id) + COUNT(DISTINCT pt.jogador_b_id) AS participantes,
            COALESCE(j.nickname, 'Em andamento') AS campeao
        FROM torneios t
        LEFT JOIN partidas_torneio pt ON pt.torneio_id = t.id
        LEFT JOIN jogadores j         ON j.id = t.campeao_id
        GROUP BY t.id, t.nome, t.data, t.formato, j.nickname
        ORDER BY t.data DESC
    """)

    try:
        resultado = db.execute(sql)
        df = pd.DataFrame(resultado.fetchall(), columns=resultado.keys())
    except Exception as e:
        logger.error(f"Erro ao gerar análise de torneios: {e}")
        return MENSAGEM_SEM_DADOS

    if df.empty:
        return MENSAGEM_SEM_DADOS

    # Cor dourada para torneios com campeão definido
    cores = [
        "#e8c94a" if c != "Em andamento" else "#4a9eff"
        for c in df["campeao"]
    ]

    trace = go.Bar(
        x=df["torneio"],
        y=df["participantes"],
        marker_color=cores,
        text=df["campeao"].apply(lambda c: f"🏆 {c}" if c != "Em andamento" else "⏳ Em andamento"),
        textposition="outside",
        hovertemplate=(
            "<b>%{x}</b><br>"
            "Participantes: %{y}<br>"
            "Campeão: %{text}<extra></extra>"
        ),
    )

    layout = {
        **LAYOUT_PADRAO,
        "title": {
            "text": "⚔ Torneios Escolares — Participação e Campeões",
            "font": {"size": 18, "color": "#e8c94a"},
            "x": 0.5,
            "xanchor": "center",
        },
        "xaxis": {"title": "Torneio", "gridcolor": "#1a1f38"},
        "yaxis": {"title": "Nº de Participantes", "gridcolor": "#1a1f38"},
        "height": 450,
        "showlegend": False,
    }

    return {"data": [trace.to_plotly_json()], "layout": layout}
