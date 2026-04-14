"""
Router de Ferramentas do Banco de Dados — Royle Metrics
Fornece endpoints para testar conexão e inspecionar as tabelas.
Útil em aula para demonstrar o banco de dados funcionando.
"""
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import inspect, text
from sqlalchemy.orm import Session

from ..database import get_db

router = APIRouter(prefix="/api/db", tags=["Banco de Dados"])

# Limite máximo de linhas retornadas por SELECT para não sobrecarregar
MAX_LINHAS = 50


@router.get("/status", summary="Testar conexão com o banco")
def testar_conexao(db: Session = Depends(get_db)):
    """
    Executa SELECT version() para verificar se o banco está acessível
    e retorna a versão do PostgreSQL, igual ao psycopg2.connect().
    """
    try:
        resultado = db.execute(text("SELECT version();"))
        versao = resultado.fetchone()[0]
        return JSONResponse(content={
            "status": "conectado",
            "versao": versao,
            "mensagem": f"✅ Conectado ao PostgreSQL: {versao}",
        })
    except Exception as e:
        return JSONResponse(status_code=500, content={
            "status": "erro",
            "versao": None,
            "mensagem": f"❌ Falha na conexão: {str(e)}",
        })


@router.get("/tabelas", summary="Listar tabelas do banco")
def listar_tabelas(db: Session = Depends(get_db)):
    """
    Retorna a lista de todas as tabelas do banco de dados.
    """
    try:
        inspector = inspect(db.get_bind())
        tabelas = inspector.get_table_names()
        return JSONResponse(content={
            "status": "ok",
            "tabelas": tabelas,
            "total": len(tabelas),
        })
    except Exception as e:
        return JSONResponse(status_code=500, content={
            "status": "erro",
            "mensagem": str(e),
        })


@router.get("/tabelas/{nome_tabela}", summary="Fazer SELECT em uma tabela")
def selecionar_tabela(nome_tabela: str, limite: int = MAX_LINHAS, db: Session = Depends(get_db)):
    """
    Executa SELECT * na tabela informada e retorna as colunas e linhas.
    O parâmetro 'limite' define o máximo de linhas (padrão: 50).
    """
    # Valida o nome da tabela para evitar SQL injection
    try:
        inspector = inspect(db.get_bind())
        tabelas_validas = inspector.get_table_names()
    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "erro", "mensagem": str(e)})

    if nome_tabela not in tabelas_validas:
        return JSONResponse(status_code=404, content={
            "status": "erro",
            "mensagem": f"Tabela '{nome_tabela}' não encontrada. Tabelas disponíveis: {tabelas_validas}",
        })

    # Limite seguro entre 1 e MAX_LINHAS
    limite = max(1, min(limite, MAX_LINHAS))

    try:
        resultado = db.execute(text(f'SELECT * FROM "{nome_tabela}" LIMIT :lim'), {"lim": limite})
        colunas = list(resultado.keys())
        linhas = [dict(zip(colunas, row)) for row in resultado.fetchall()]

        # Converte valores não serializáveis (datas, Decimal, etc.) para string
        for linha in linhas:
            for chave, valor in linha.items():
                if valor is not None and not isinstance(valor, (str, int, float, bool)):
                    linha[chave] = str(valor)

        return JSONResponse(content={
            "status": "ok",
            "tabela": nome_tabela,
            "colunas": colunas,
            "total_linhas": len(linhas),
            "limite": limite,
            "linhas": linhas,
        })
    except Exception as e:
        return JSONResponse(status_code=500, content={
            "status": "erro",
            "mensagem": str(e),
        })
