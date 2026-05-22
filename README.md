# ⚔ Royle Metrics

Plataforma educacional para análise de desempenho no **Clash Royale**, usada no **Curso Técnico em Ciência de Dados**.

O projeto integra:
- Coleta de dados reais da API oficial do Clash Royale
- Armazenamento em PostgreSQL
- API FastAPI com análises e gráficos (Plotly)
- Modelo preditivo de guerras com Machine Learning

📘 Versão didática para alunos: [`README_ALUNOS.md`](README_ALUNOS.md)

---

## 📌 Arquitetura Atual (MVC)

A aplicação foi reestruturada para **MVC** em `app/`:

- **Model (`app/models/`)**: banco (`database.py`), entidades ORM (`entities.py`) e serviços de negócio (`services/`)
- **Controller (`app/controllers/`)**: rotas FastAPI (`ranking`, `cartas`, `guerras`, `torneios`, `sync`, `db_tools`)
- **View (`app/views/`)**: front-end (`templates/index.html` + `static/css` + `static/js`)

O ponto de entrada principal é:
- `app/main.py`

> A pasta `backend/` foi mantida por compatibilidade/histórico, mas o fluxo recomendado é rodar via `app.main:app`.

---

## 🧱 Estrutura de Pastas

```text
royale-metrics/
├── app/
│   ├── main.py
│   ├── config.py
│   ├── controllers/
│   │   ├── ranking.py
│   │   ├── cartas.py
│   │   ├── guerras.py
│   │   ├── torneios.py
│   │   ├── sync.py
│   │   └── db_tools.py
│   ├── models/
│   │   ├── database.py
│   │   ├── entities.py
│   │   └── services/
│   │       ├── clash_client.py
│   │       ├── coleta.py
│   │       ├── analise.py
│   │       ├── modelo.py
│   │       └── scheduler.py
│   └── views/
│       ├── templates/index.html
│       └── static/
│           ├── css/style.css
│           └── js/app.js
├── data/tags_clas.json
├── database/schema.sql
├── teste/
│   ├── seed_md.py
│   └── seed_db.py
├── requirements.txt
└── .env.example
```

---

## 🛠 Stack Tecnológica

- `FastAPI` + `Uvicorn`
- `SQLAlchemy` + `psycopg2-binary`
- `PostgreSQL`
- `clashroyale` (API wrapper)
- `Pandas`, `Plotly`
- `Scikit-learn` (Random Forest)
- `APScheduler` (sincronização automática)

---

## ⚙️ Configuração Inicial

### 1) Pré-requisitos

- Python 3.11+
- PostgreSQL 14+
- Token da API Clash Royale

### 2) Ambiente virtual e dependências

```powershell
py -m venv .venv

```
```
```powershell
.\.venv\Scripts\Activate.ps1
```

```powershell
py -m pip install -r requirements.txt
```



### 3) Configurar `.env`

```powershell
Copy-Item .env.example .env
```

Exemplo mínimo:

```env
CLASH_API_TOKEN=seu_token_aqui
CLASH_API_URL=https://proxy.royaleapi.dev/v1
DATABASE_URL=postgresql://postgres:senha@localhost:5432/royale_metrics
ENVIRONMENT=development
SYNC_INTERVAL_HOURS=6
```

### 4) Clãs monitorados

Edite `data/tags_clas.json`:

```json
{
  "clans": ["#GGRU2GCJ"],
  "jogadores": []
}
```

---

## ▶️ Como Executar

Com o ambiente virtual ativo:

```powershell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

URLs principais:
- Front-end: `http://localhost:8000`
- Swagger: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- Health: `http://localhost:8000/health`

---

## 🔌 Endpoints da API

| Método | Endpoint | Descrição |
|---|---|---|
| `GET` | `/health` | Status da aplicação |
| `GET` | `/api/sync` | Sincronização manual dos clãs configurados |
| `GET` | `/api/ranking` | Ranking dos jogadores |
| `GET` | `/api/cartas` | Análise de performance das cartas |
| `GET` | `/api/guerras` | Histórico de guerras (River Race) |
| `GET` | `/api/guerras/previsao` | Previsão da próxima guerra (ML) |
| `GET` | `/api/torneios` | Análise de torneios escolares |
| `GET` | `/api/db/status` | Status da conexão com banco |
| `GET` | `/api/db/tabelas` | Lista tabelas do banco |
| `GET` | `/api/db/tabelas/{nome_tabela}` | Consulta tabela (com limite) |

---

## 🧪 Scripts de Apoio

- `teste/seed_md.py`: testes rápidos de coleta na API (modo validação)
- `teste/seed_db.py`: população do banco com dados reais via API

Exemplo de uso:

```powershell
python .\teste\seed_db.py
```

---

## 🤖 Modelo de Machine Learning

O endpoint `GET /api/guerras/previsao` usa **RandomForestClassifier** para prever vitória/derrota com base no histórico de guerras.

Entradas principais:
- batalhas ganhas/perdidas
- pontuação (fame)
- médias por membro

Saída:
- previsão
- confiança
- variáveis mais importantes (`top_features`)

---

## 📚 Uso em Sala

Sugestões pedagógicas:
- `ranking`: estatística descritiva e comparação entre jogadores
- `cartas`: frequência × taxa de vitória (interpretação de correlação)
- `guerras/previsao`: introdução prática a classificação supervisionada

---

## 📄 Licença

Projeto educacional.

*This content is not affiliated with, endorsed, sponsored, or specifically approved by Supercell and Supercell is not responsible for it.*
