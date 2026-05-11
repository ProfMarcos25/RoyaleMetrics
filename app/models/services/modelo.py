"""
Modelo Preditivo de Guerras — Royle Metrics
Usa RandomForestClassifier do Scikit-learn para prever se
o clã vai vencer a próxima guerra com base no histórico.
"""
import logging
from typing import Any, Dict, List

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# Mínimo de guerras no histórico para treinar o modelo
MIN_GUERRAS_TREINO = 5


def _buscar_dados_treino(db: Session) -> pd.DataFrame:
    """
    Busca os dados históricos de guerras e contribuições individuais
    para construir as features do modelo preditivo.

    Retorna um DataFrame com uma linha por guerra por clã, contendo:
    - batalhas_ganhas, batalhas_perdidas, pontuacao (da guerra)
    - media_fame_membros (média de fame individual dos participantes)
    - colocacao (target: ≤3 = vitória, >3 = derrota)

    Args:
        db: Sessão ativa do banco de dados.

    Retorna:
        pd.DataFrame: Dados para treino e predição.
    """
    sql = text("""
        SELECT
            g.id                          AS guerra_id,
            g.batalhas_ganhas,
            g.batalhas_perdidas,
            g.pontuacao,
            g.colocacao,
            COALESCE(AVG(cg.fame), 0)     AS media_fame_membros,
            COALESCE(AVG(cg.vitorias), 0) AS media_vitorias_membros,
            COALESCE(SUM(cg.batalhas), 0) AS total_batalhas_membros
        FROM guerras g
        LEFT JOIN contribuicoes_guerra cg ON cg.guerra_id = g.id
        WHERE g.colocacao IS NOT NULL
        GROUP BY g.id, g.batalhas_ganhas, g.batalhas_perdidas, g.pontuacao, g.colocacao
        ORDER BY g.id DESC
        LIMIT 100
    """)

    resultado = db.execute(sql)
    df = pd.DataFrame(resultado.fetchall(), columns=resultado.keys())
    return df


def _preparar_features(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    """
    Transforma o DataFrame em features (X) e target (y) para o modelo.

    Target binário:
        - 1 (vitória): colocação ≤ 3
        - 0 (derrota): colocação > 3

    Args:
        df: DataFrame com dados históricos.

    Retorna:
        tuple: (DataFrame de features X, Series de target y)
    """
    colunas_features = [
        "batalhas_ganhas",
        "batalhas_perdidas",
        "pontuacao",
        "media_fame_membros",
        "media_vitorias_membros",
        "total_batalhas_membros",
    ]

    X = df[colunas_features].fillna(0)

    # Converte colocação em target binário
    y = (df["colocacao"] <= 3).astype(int)

    return X, y


def prever_resultado_guerra(db: Session) -> Dict[str, Any]:
    """
    Treina o modelo RandomForest com o histórico de guerras
    e retorna a previsão para a próxima guerra do clã.

    O modelo usa as últimas 5 guerras para contextualizar a predição.
    As features mais importantes são retornadas para fins didáticos
    (importante para ensinar ciência de dados aos alunos).

    Args:
        db: Sessão ativa do banco de dados.

    Retorna:
        dict: {
            "previsao": "vitoria" | "derrota",
            "confianca": float (0 a 1),
            "top_features": dict com importância de cada variável,
            "historico_recente": lista das últimas guerras,
            "mensagem": texto explicativo para o aluno
        }

    Erros:
        - Menos de MIN_GUERRAS_TREINO no banco: retorna mensagem educativa.
    """
    try:
        df = _buscar_dados_treino(db)
    except Exception as e:
        logger.error(f"Erro ao buscar dados para o modelo: {e}")
        return _resposta_sem_dados("Erro ao acessar o banco de dados.")

    if len(df) < MIN_GUERRAS_TREINO:
        return _resposta_sem_dados(
            f"São necessárias ao menos {MIN_GUERRAS_TREINO} guerras no histórico "
            f"para treinar o modelo. Atualmente há {len(df)}."
        )

    X, y = _preparar_features(df)

    # Verifica se há exemplos de ambas as classes (vitória e derrota)
    if y.nunique() < 2:
        return _resposta_sem_dados(
            "O modelo precisa de exemplos de vitórias E derrotas para funcionar. "
            "Aguarde mais guerras serem registradas."
        )

    # Treina o modelo com validação — usa 80% para treino
    if len(df) >= 10:
        X_treino, _, y_treino, _ = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
    else:
        # Poucos dados: treina com tudo (aceitável para demonstração)
        X_treino, y_treino = X, y

    modelo = RandomForestClassifier(
        n_estimators=100,       # 100 árvores de decisão
        max_depth=5,            # limita profundidade para evitar overfitting
        random_state=42,        # reprodutibilidade dos resultados
        class_weight="balanced", # corrige desequilíbrio entre classes
    )
    modelo.fit(X_treino, y_treino)  

    # Usa a média das últimas 5 guerras como "próxima guerra projetada"
    ultimas_5 = X.head(5).mean().to_frame().T
    probabilidades = modelo.predict_proba(ultimas_5)[0]
    classe_prevista = modelo.predict(ultimas_5)[0]

    # Confiança: probabilidade da classe prevista
    confianca = float(max(probabilidades))
    previsao = "vitoria" if classe_prevista == 1 else "derrota"

    # Importância das features (para fins didáticos)
    top_features = dict(
        sorted(
            zip(X.columns.tolist(), modelo.feature_importances_.tolist()),
            key=lambda x: x[1],
            reverse=True,
        )
    )

    # Histórico recente para exibir no front-end
    historico_recente = df[["batalhas_ganhas", "batalhas_perdidas", "pontuacao", "colocacao"]].head(5).to_dict(orient="records")

    mensagem = _gerar_mensagem_educativa(previsao, confianca, top_features)

    return {
        "previsao": previsao,
        "confianca": round(confianca, 4),
        "top_features": {k: round(v, 4) for k, v in top_features.items()},
        "historico_recente": historico_recente,
        "mensagem": mensagem,
        "amostras_treino": len(X_treino),
    }


def _gerar_mensagem_educativa(
    previsao: str, confianca: float, top_features: Dict[str, float]
) -> str:
    """
    Gera uma mensagem explicativa sobre a previsão para fins didáticos.
    Explica ao aluno quais variáveis mais influenciaram o resultado.

    Args:
        previsao: 'vitoria' ou 'derrota'.
        confianca: Probabilidade da classe prevista (0.0 a 1.0).
        top_features: Dicionário de importância das variáveis.

    Retorna:
        str: Texto explicativo em português.
    """
    percentual = round(confianca * 100, 1)
    icone = "🏆" if previsao == "vitoria" else "⚠️"
    resultado_texto = "VITÓRIA" if previsao == "vitoria" else "DERROTA"

    # Feature mais importante
    feature_principal = list(top_features.keys())[0]
    nomes_amigaveis = {
        "batalhas_ganhas": "número de batalhas ganhas",
        "batalhas_perdidas": "número de batalhas perdidas",
        "pontuacao": "pontuação total (Fame)",
        "media_fame_membros": "média de Fame individual",
        "media_vitorias_membros": "média de vitórias por membro",
        "total_batalhas_membros": "total de batalhas jogadas",
    }
    nome_principal = nomes_amigaveis.get(feature_principal, feature_principal)

    return (
        f"{icone} O modelo prevê {resultado_texto} na próxima guerra "
        f"com {percentual}% de confiança. "
        f"A variável mais importante foi o {nome_principal}. "
        f"Este modelo usa Random Forest com {100} árvores de decisão — "
        f"algoritmo de ensemble aprendido no Curso Técnico em Ciência de Dados!"
    )


def _resposta_sem_dados(mensagem: str) -> Dict[str, Any]:
    """
    Retorna uma resposta padrão quando não há dados suficientes
    para treinar o modelo preditivo.

    Args:
        mensagem: Texto explicativo do motivo.

    Retorna:
        dict: Resposta com status de erro informativo.
    """
    return {
        "previsao": None,
        "confianca": None,
        "top_features": {},
        "historico_recente": [],
        "mensagem": mensagem,
        "amostras_treino": 0,
    }
