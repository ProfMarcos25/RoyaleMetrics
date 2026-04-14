# Pacote de serviços do Royle Metrics
# Importações centralizadas para facilitar o uso nos routers
from .analise import (
    gerar_analise_cartas,
    gerar_analise_torneios,
    gerar_historico_guerras,
    gerar_ranking,
)
from .clash_client import get_client
from .coleta import (
    sincronizar_cartas,
    sincronizar_clan,
    sincronizar_river_race,
    sincronizar_warlog,
)
from .modelo import prever_resultado_guerra

__all__ = [
    "get_client",
    "sincronizar_cartas",
    "sincronizar_clan",
    "sincronizar_river_race",
    "sincronizar_warlog",
    "gerar_ranking",
    "gerar_analise_cartas",
    "gerar_historico_guerras",
    "gerar_analise_torneios",
    "prever_resultado_guerra",
]
