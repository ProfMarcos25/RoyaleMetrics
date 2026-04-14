# ⚔ Royle Metrics

> Plataforma de análise de desempenho no Clash Royale para o **Curso Técnico em Ciência de Dados**.

Combina dados reais da [API Oficial do Clash Royale](https://developer.clashroyale.com) com partidas de torneios escolares para gerar gráficos interativos, rankings e até previsões com **Machine Learning**.

---

## 📋 Índice

- [Visão Geral](#visão-geral)
- [Stack Tecnológica](#stack-tecnológica)
- [Estrutura de Pastas](#estrutura-de-pastas)
- [Configuração Inicial](#configuração-inicial)
- [Como Executar](#como-executar)
- [Endpoints da API](#endpoints-da-api)
- [Como Adicionar Clãs](#como-adicionar-clãs)
- [Modelo de Machine Learning](#modelo-de-machine-learning)
- [Dicas para a Aula](#dicas-para-a-aula)

---

## 🎮 Visão Geral

O Royle Metrics é dividido em:

| Camada | Descrição |
|---|---|
| **Back-end** | Servidor FastAPI que coleta dados da API, armazena no PostgreSQL e serve endpoints de análise |
| **Banco de dados** | PostgreSQL com tabelas para clãs, jogadores, batalhas, cartas, guerras e torneios |
| **Front-end** | Página HTML única com gráficos Plotly interativos e tema gamer escuro |
| **ML** | Modelo Random Forest que prevê o resultado de guerras com base no histórico |

---

## 🛠 Stack Tecnológica

| Tecnologia | Função |
|---|---|
| `FastAPI` | API REST assíncrona |
| `SQLAlchemy 2.0` | ORM para PostgreSQL |
| `psycopg2-binary` | Driver PostgreSQL |
| `clashroyale` | Wrapper da API oficial |
| `Pandas` | Manipulação de dados |
| `Scikit-learn` | Modelo preditivo (Random Forest) |
| `Plotly` | Gráficos interativos |
| `APScheduler` | Coleta automática a cada 6h |
| `python-dotenv` | Variáveis de ambiente |
| `Uvicorn` | Servidor ASGI |

---

## 📁 Estrutura de Pastas

```
royale-metrics/
├── backend/
│   ├── __init__.py
│   ├── main.py          ← Ponto de entrada da aplicação FastAPI
│   ├── database.py      ← Configuração do banco e sessões
│   ├── models.py        ← Modelos ORM (tabelas)
│   ├── scheduler.py     ← Agendador de coleta automática (6h)
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── sync.py      ← GET /api/sync (coleta manual)
│   │   ├── ranking.py   ← GET /api/ranking
│   │   ├── cartas.py    ← GET /api/cartas
│   │   ├── guerras.py   ← GET /api/guerras + /api/guerras/previsao
│   │   └── torneios.py  ← GET /api/torneios
│   └── services/
│       ├── __init__.py
│       ├── clash_client.py  ← Inicializa o cliente da API
│       ├── coleta.py        ← Funções de coleta e persistência
│       ├── analise.py       ← Análises Pandas + gráficos Plotly
│       └── modelo.py        ← Random Forest para previsão de guerras
├── frontend/
│   ├── index.html       ← Interface web completa
│   ├── style.css        ← Tema escuro (variáveis CSS customizáveis)
│   └── app.js           ← Lógica JS com async/await
├── database/
│   └── schema.sql       ← Schema completo do PostgreSQL
├── data/
│   └── tags_clas.json   ← Tags dos clãs monitorados
├── .env.example         ← Template das variáveis de ambiente
├── requirements.txt     ← Dependências Python
└── README.md
```

---


---
## Arquitetura 

. [ FONTES DE DADOS EXTENAS ] 
     │
     ├──> API Oficial do Clash Royale: Fornece dados reais de perfis, batalhas, guerras e cartas [1].
     │      └─ Acessada via proxy público (proxy.royaleapi.dev/v1) para contornar IPs dinâmicos [2].
     │
     └──> Torneios Escolares: Partidas locais registradas manualmente ou via formulários [1].
            │
            ▼
2. [ SERVIÇO DE COLETA (WORKERS / BACKGROUND) ]
     │
     ├──> Agendador: APScheduler configurado para coletar dados automaticamente a cada 6 horas [2].
     ├──> Cliente API: Utiliza a biblioteca oficial `clashroyale` (Python wrapper) [1, 2].
     └──> Funções de Sincronização: Extrai e processa dados de cartas, clãs, jogadores, 
          batalhas, warlogs e river races [3-5].
            │
            ▼
3. [ CAMADA DE ARMAZENAMENTO (BANCO DE DADOS) ]
     │
     └──> Banco: PostgreSQL mapeado via ORM SQLAlchemy [2].
          Esquema (Tabelas Relacionais):
          - cartas, clans, jogadores [3].
          - batalhas, batalha_cartas, guerras, contribuicoes_guerra [4, 5].
            │
            ▼
4. [ BACK-END CORE (API & PROCESSAMENTO) ]
     │
     ├──> Servidor de Aplicação: FastAPI executado pelo Uvicorn em Python 3.11+ [2].
     ├──> Endpoints (Rotas): 
     │      - /api/sync (Atualização manual) [5].
     │      - /api/ranking, /api/cartas, /api/guerras, /api/torneios (Consultas e agregação) [5, 6].
     │
     ├──> [ MÓDULO DE ANÁLISE DE DADOS E MACHINE LEARNING ]
     │      ├──> Manipulação e Gráficos: Uso de Pandas e Plotly (gera gráficos em formato JSON) [2, 6].
     │      └──> Previsão (/api/guerras/previsao): Modelo `RandomForestClassifier` do Scikit-learn 
     │           que usa o histórico de batalhas e fame para prever vitórias ou derrotas na guerra [7].
            │
            ▼
5. [ FRONT-END (INTERFACE DO USUÁRIO) ]
     │
     ├──> Tecnologias: HTML5, CSS3, JavaScript puro [2].
     ├──> Renderização: Biblioteca Plotly.js carrega o JSON do Back-end em uma <div id="grafico-container"> [2, 7].
     ├──> Interatividade: Chamadas assíncronas (async/await) aos endpoints via botões de análise [7, 8].
     └──> Estilização: Tema escuro inspirado em jogos de estratégia (com as cores primárias #0a0c14 e dourado) [9].





## ⚙️ Configuração Inicial

### 1. Pré-requisitos

- Python 3.11+
- PostgreSQL 14+ rodando localmente
- Token da API do Clash Royale ([obtido aqui](https://developer.clashroyale.com))

### 2. Clone e ambiente virtual

```bash
# Na pasta do projeto
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux/Mac
source .venv/bin/activate
```

### 3. Instale as dependências

```bash
pip install -r requirements.txt
```

### 4. Configure as variáveis de ambiente

```bash
# Crie o arquivo .env a partir do template
copy .env.example .env   # Windows
cp .env.example .env     # Linux/Mac
```

Edite o `.env` e preencha:

```env
CLASH_API_TOKEN=seu_token_da_api_aqui
DATABASE_URL=postgresql://seu_usuario:sua_senha@localhost:5432/royle_metrics
ENVIRONMENT=development
```

> **Dica para escolas:** Use `CLASH_API_URL=https://proxy.royaleapi.dev/v1` (já é o padrão) para contornar a restrição de IP fixo da API oficial.

### 5. Crie o banco de dados

```bash
# No PostgreSQL (psql)
CREATE DATABASE royle_metrics;
```

Em seguida, execute o schema:

```bash
psql -U seu_usuario -d royle_metrics -f database/schema.sql
```

Ou deixe o FastAPI criar as tabelas automaticamente na primeira execução (modo desenvolvimento).

### 6. Configure os clãs monitorados

Edite o arquivo `data/tags_clas.json` com as tags dos clãs dos alunos:

```json
{
  "clans": [
    "#ABC123",
    "#XYZ789"
  ],
  "jogadores_extras": []
}
```

---

## ▶️ Como Executar

### Iniciar o servidor back-end

```bash
# Na pasta royale-metrics/
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

- Documentação automática: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Abrir o front-end

Abra o arquivo `frontend/index.html` diretamente no navegador, ou use a extensão **Live Server** do VS Code:

1. Clique com o botão direito em `index.html`
2. Selecione "Open with Live Server"
3. O front-end abrirá em `http://127.0.0.1:5500`

### Primeira sincronização

1. Com o servidor rodando, clique em **"Atualizar dados"** no front-end
2. Aguarde a sincronização ser concluída
3. Explore as análises nos botões abaixo

---

## 🔌 Endpoints da API

| Método | Endpoint | Descrição |
|---|---|---|
| `GET` | `/` | Status da API |
| `GET` | `/health` | Health check |
| `GET` | `/api/sync` | Sincronização manual |
| `GET` | `/api/ranking` | Ranking dos 20 melhores jogadores |
| `GET` | `/api/cartas` | Performance das cartas (frequência × vitórias) |
| `GET` | `/api/guerras` | Histórico de River Races |
| `GET` | `/api/guerras/previsao` | Previsão ML da próxima guerra |
| `GET` | `/api/torneios` | Torneios escolares |
| `GET` | `/docs` | Documentação Swagger UI |

---

## 🤖 Modelo de Machine Learning

O endpoint `/api/guerras/previsao` treina um **Random Forest Classifier** com o histórico de guerras armazenado no banco.

**Features (variáveis de entrada):**
- `batalhas_ganhas` — vitórias em batalha na guerra
- `batalhas_perdidas` — derrotas em batalha
- `pontuacao` — Fame total do clã
- `media_fame_membros` — média de Fame individual
- `media_vitorias_membros` — média de vitórias por membro
- `total_batalhas_membros` — total de batalhas da guerra

**Target (saída):**
- `1` (vitória): colocação ≤ 3
- `0` (derrota): colocação > 3

> São necessárias ao menos **5 guerras** no histórico para treinar o modelo.

---


## 🛠️ Preparando o Ambiente (Setup Inicial)
Antes de começar, cada aluno deve seguir este passo:

**1. Clone o Repositório:** Faça o download do projeto para a sua máquina.

```bash
git clone [https://github.com/ProfMarcos25/RoyaleMetrics.git](https://github.com/ProfMarcos25/RoyaleMetrics.git)

```


**1. ATUALIZAÇÃO FAZER TODOD DIA ANTES DE INCIAR O DESENVOLVIMENTO:** 

```bash
git pull origin ProfSquard

```



**1.1 Identificação de Usuario** identifique seu nome de usuario ou EMAIL:


```bash

git config --global user.email <E-mail do Auno no git>


```


```bash

git config --global user.name <Login do Aluno no git>

```


## 📚 Dicas para a Aula

### Exploração dos dados
1. Use `/api/ranking` para comparar jogadores e introduzir **estatística descritiva**
2. Use `/api/cartas` para explicar **correlação** entre frequência e taxa de vitória
3. Use `/api/guerras` para mostrar **séries temporais** e tendências

### Machine Learning
1. Explique o **algoritmo Random Forest** usando o resultado de `/api/guerras/previsao`
2. O campo `top_features` mostra a **importância das variáveis** — ótimo para ensinar feature importance
3. Discuta com os alunos: _"Se quisermos melhorar a previsão, quais outros dados poderíamos coletar?"_

### Customização
- As **cores do tema** estão todas em variáveis CSS em `style.css` — peça aos alunos que personalizem
- Os alunos podem adicionar novos torneios diretamente pelo banco (tabela `torneios` e `partidas_torneio`)
- O código tem **comentários em português** em todos os trechos complexos



## 📄 Licença

Projeto educacional — Curso Técnico em Ciência de Dados.
Dados fornecidos pela API Oficial do Clash Royale (Supercell).
*This content is not affiliated with, endorsed, sponsored, or specifically approved by Supercell and Supercell is not responsible for it.*
=======
"# RoyaleMetrics" 

