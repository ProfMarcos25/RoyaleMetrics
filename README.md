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


<img width="526" height="597" alt="image" src="https://github.com/user-attachments/assets/a650186c-5d7f-4bfc-aa0d-f07d1388dcf6" />






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

### Criar banco de dados


--> No PostegreSql , Abra o pgadmin
1. Procure PgAdmin no Computador

<img width="865" height="757" alt="image" src="https://github.com/user-attachments/assets/60715683-6f2b-435d-867a-9f6f1f606a9e" />


1.1 
<img width="749" height="595" alt="image" src="https://github.com/user-attachments/assets/f44364b4-8911-45a8-9c51-194cd4dd117f" />



2. Acesse o Postegree recente a senha de acesso é 1234

   <img width="545" height="399" alt="image" src="https://github.com/user-attachments/assets/fe86c4c6-49f0-4932-b8fc-d6998dce5c0e" />

2.1 clique com o Botao direito em Database


   <img width="638" height="377" alt="image" src="https://github.com/user-attachments/assets/62061b60-2cbd-49ff-98b2-f1d043e11f5d" />

   
2.2 Insira o nome do seu Database


   <img width="696" height="550" alt="image" src="https://github.com/user-attachments/assets/b95ea6fd-6112-490c-8301-d194cf949cb5" />

   
2.2 Clique em Save


   <img width="698" height="552" alt="image" src="https://github.com/user-attachments/assets/1144808f-394d-42c4-9e41-a82883f7d965" />

   
3. Clique no Database Criado com o botao direito:


<img width="495" height="498" alt="image" src="https://github.com/user-attachments/assets/eba19eae-3018-4632-9540-bcfa390dacdd" />


3.1 Clique no Database Criado com o botao direito e selecione QueryTols:

   <img width="413" height="486" alt="image" src="https://github.com/user-attachments/assets/2b56cb1a-6711-4f28-8e47-f2738072c6cc" />

3.2 Adicione os Scripts do arquivo schema.sql
```bash
CREATE TABLE IF NOT EXISTS clans (
    id            SERIAL PRIMARY KEY,
    tag           VARCHAR(20)  UNIQUE NOT NULL,
    nome          VARCHAR(100) NOT NULL,
    descricao     TEXT,
    trofeus       INTEGER      DEFAULT 0,
    membros       INTEGER      DEFAULT 0,
    atualizado_em TIMESTAMP    DEFAULT NOW()
);

-- ---------------------------------------------------------
-- Tabela: jogadores
-- Membros dos clãs coletados via API
-- ---------------------------------------------------------
CREATE TABLE IF NOT EXISTS jogadores (
    id              SERIAL PRIMARY KEY,
    tag             VARCHAR(20)  UNIQUE NOT NULL,
    nickname        VARCHAR(50)  NOT NULL,
    nivel           INTEGER,
    trofeus         INTEGER      DEFAULT 0,
    trofeus_recorde INTEGER      DEFAULT 0,
    arena           VARCHAR(50),
    clan_id         INTEGER      REFERENCES clans(id) ON DELETE SET NULL,
    ultima_batalha  TIMESTAMP,
    criado_em       TIMESTAMP    DEFAULT NOW()
);

-- ---------------------------------------------------------
-- Tabela: cartas
-- Todas as cartas do jogo (populado via GET /cards)
-- ---------------------------------------------------------
CREATE TABLE IF NOT EXISTS cartas (
    id        SERIAL PRIMARY KEY,
    card_id   INTEGER UNIQUE,             -- ID original da API oficial
    nome      VARCHAR(100) NOT NULL,
    tipo      VARCHAR(30),                -- troop, spell, building
    raridade  VARCHAR(20),                -- Common, Rare, Epic, Legendary
    elixir    INTEGER,
    max_nivel INTEGER,
    url_icon  TEXT                        -- link da imagem via royaleapi assets
);

-- ---------------------------------------------------------
-- Tabela: torneios
-- Torneios escolares (declarada antes de batalhas por dependência)
-- ---------------------------------------------------------
CREATE TABLE IF NOT EXISTS torneios (
    id         SERIAL PRIMARY KEY,
    nome       VARCHAR(100) NOT NULL,
    data       DATE,
    formato    VARCHAR(50),               -- eliminatoria, pontos_corridos
    descricao  TEXT,
    campeao_id INTEGER REFERENCES jogadores(id) ON DELETE SET NULL
);

-- ---------------------------------------------------------
-- Tabela: batalhas
-- Batalhas coletadas via API (log do jogador)
-- ---------------------------------------------------------
CREATE TABLE IF NOT EXISTS batalhas (
    id               SERIAL PRIMARY KEY,
    battle_id        VARCHAR(100) UNIQUE,  -- hash único: tag + battleTime
    jogador_id       INTEGER REFERENCES jogadores(id) ON DELETE CASCADE,
    tipo             VARCHAR(30),           -- PvP, clanWar, riverRacePvP, etc.
    resultado        VARCHAR(10),           -- vitoria, derrota, empate
    trofeus_ganhos   INTEGER DEFAULT 0,
    time_trofeus     INTEGER,
    oponente_tag     VARCHAR(20),
    oponente_trofeus INTEGER,
    data_batalha     TIMESTAMP,
    torneio_id       INTEGER REFERENCES torneios(id) ON DELETE SET NULL
);

-- ---------------------------------------------------------
-- Tabela: batalha_cartas
-- Cartas usadas em cada batalha (deck do jogador)
-- ---------------------------------------------------------
CREATE TABLE IF NOT EXISTS batalha_cartas (
    batalha_id INTEGER REFERENCES batalhas(id) ON DELETE CASCADE,
    carta_id   INTEGER REFERENCES cartas(id) ON DELETE CASCADE,
    nivel      INTEGER,
    PRIMARY KEY (batalha_id, carta_id)
);

-- ---------------------------------------------------------
-- Tabela: guerras
-- River Race e guerras de clã
-- ---------------------------------------------------------
CREATE TABLE IF NOT EXISTS guerras (
    id                SERIAL PRIMARY KEY,
    clan_id           INTEGER REFERENCES clans(id) ON DELETE CASCADE,
    temporada         VARCHAR(20),           -- ex: "2024-03"
    tipo              VARCHAR(30),           -- riverRace, classicWarDay
    batalhas_ganhas   INTEGER DEFAULT 0,
    batalhas_perdidas INTEGER DEFAULT 0,
    pontuacao         INTEGER DEFAULT 0,
    colocacao         INTEGER,
    data_inicio       DATE,
    data_fim          DATE
);

-- ---------------------------------------------------------
-- Tabela: contribuicoes_guerra
-- Contribuição individual de cada jogador por guerra
-- ---------------------------------------------------------
CREATE TABLE IF NOT EXISTS contribuicoes_guerra (
    id         SERIAL PRIMARY KEY,
    guerra_id  INTEGER REFERENCES guerras(id) ON DELETE CASCADE,
    jogador_id INTEGER REFERENCES jogadores(id) ON DELETE CASCADE,
    batalhas   INTEGER DEFAULT 0,
    vitorias   INTEGER DEFAULT 0,
    fame       INTEGER DEFAULT 0            -- métrica principal do River Race
);

-- ---------------------------------------------------------
-- Tabela: partidas_torneio
-- Partidas individuais dos torneios escolares
-- ---------------------------------------------------------
CREATE TABLE IF NOT EXISTS partidas_torneio (
    id           SERIAL PRIMARY KEY,
    torneio_id   INTEGER REFERENCES torneios(id) ON DELETE CASCADE,
    jogador_a_id INTEGER REFERENCES jogadores(id) ON DELETE CASCADE,
    jogador_b_id INTEGER REFERENCES jogadores(id) ON DELETE CASCADE,
    vencedor_id  INTEGER REFERENCES jogadores(id) ON DELETE SET NULL,
    placar_a     INTEGER DEFAULT 0,
    placar_b     INTEGER DEFAULT 0,
    data_partida TIMESTAMP
);

-- ---------------------------------------------------------
-- Índices para performance nas queries de análise
-- ---------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_jogadores_clan   ON jogadores(clan_id);
CREATE INDEX IF NOT EXISTS idx_batalhas_jogador ON batalhas(jogador_id);
CREATE INDEX IF NOT EXISTS idx_batalhas_data    ON batalhas(data_batalha);
CREATE INDEX IF NOT EXISTS idx_batalhas_tipo    ON batalhas(tipo);
CREATE INDEX IF NOT EXISTS idx_guerras_clan     ON guerras(clan_id);
CREATE INDEX IF NOT EXISTS idx_contrib_guerra   ON contribuicoes_guerra(guerra_id);
CREATE INDEX IF NOT EXISTS idx_contrib_jogador  ON contribuicoes_guerra(jogador_id);
CREATE INDEX IF NOT EXISTS idx_partidas_torneio ON partidas_torneio(torneio_id);
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
