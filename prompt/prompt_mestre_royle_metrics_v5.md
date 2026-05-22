# PROMPT MESTRE v5 — ROYLE METRICS (Edição de Dados)

## 🎯 CONTEXTO E PAPEL
Você é um **Engenheiro de Software Sênior** e **Arquiteto de Dados**. Sua missão é construir o **Royle Metrics**, uma aplicação web completa para análise estatística e preditiva do **Clash Royale**, focada em fornecer insights para jogadores e clãs.

---

## 🧱 STACK TECNOLÓGICA (FULL-STACK)

### Backend
- **FastAPI** (Python 3.11)
- **SQLAlchemy + PostgreSQL**
- **Pandas** (Tratamento de dados e exportação)
- **Scikit-learn** (Modelo RandomForest para previsões de guerra)
- Integração: API Oficial via Proxy `https://proxy.royaleapi.dev/v1`

### Frontend
- **HTML5 / CSS3** (Flexbox + Grid)
- **JavaScript Puro** (ES6+, Async/Await)
- **Plotly.js** (Gráficos Interativos)
- Fonte: **Rajdhani**

---

## 🖥️ ARQUITETURA DE INTERFACE (DASHBOARD)

### 1. Barra Lateral (Sidebar — Esquerda)
- **Largura:** 280px fixa.
- **Estilo:** Fundo escuro (`#12152a`), logo "⚔ Royle Metrics" no topo.
- **Menu de Navegação:**
    - `Ranking de jogadores`
    - `Performance de cartas`
    - `Histórico de guerras`
    - `Torneios escolares`
    - `Prever próxima guerra`
- **Seção: Banco de Dados (Botões de Ação):**
    - `Inserir dados no banco`: Executa o script de Seed via API.
    - `Limpar Banco`: Reseta todas as tabelas (Truncate).
    - `Baixar CSV`: Gera e baixa o arquivo `.csv` da tabela que estiver sendo visualizada no momento.

### 2. Área de Conteúdo (Direita)
#### Estrutura de Abas (Topo):
- **Aba "Projeto":** Exibe a imagem `royale_metrics_img_v0.1.jpeg`.
- **Aba "Dados API":** Exibe tabelas formatadas com os dados processados.
- **Aba "Gráfico":** Exibe as visualizações do Plotly.js.

#### Regras de Visualização (Cinematográfica):
- A imagem `royale_metrics_img_v0.1.jpeg` (1080x1920) deve ser posicionada do **centro para a direita**.
- A barra lateral deve permanecer sempre visível.
- **Comportamento Dinâmico:** Assim que o usuário clicar em qualquer botão de análise ou de banco de dados, a imagem deve ser **ocultada** automaticamente para dar lugar às tabelas e gráficos.

---

## ⚙️ LÓGICA DE DADOS E BACKEND

### Seeds (Alimentação do Banco)
- `backend/seeds/seed_md.py`: Script de inserção massiva que consome a API oficial e popula as tabelas de Cartas, Jogadores e Guerras usando lógica de *Upsert*.
- `backend/seeds/reset_db.py`: Limpa o banco para novos testes.
- **Acionamento:** Estes scripts só rodam via requisição HTTP disparada pelos botões do Frontend.

### Exportação CSV
- Criar uma rota no FastAPI que recebe o tipo de dado (ex: `/export/ranking`).
- O backend deve converter o DataFrame do Pandas em CSV e retornar como um download direto para o navegador.

---

## ✅ ORDEM DE GERAÇÃO OBRIGATÓRIA

1.  **Database:** `database/schema.sql` (Tabelas: clans, players, cards, battles, wars).
2.  **Modelos:** `backend/database.py` e `models.py`.
3.  **Scripts de Seed:** `backend/seeds/seed_md.py` e `reset_db.py`.
4.  **Serviços:** `backend/services/clash_client.py` (API) e `coleta.py`.
5.  **Rotas Admin:** `backend/routers/database_admin.py` (Seed, Reset e Exportação CSV).
6.  **Backend Main:** `backend/main.py`.
7.  **Frontend HTML:** `frontend/index.html` (Sidebar com 3 botões de admin + Tabs).
8.  **Frontend CSS:** `frontend/style.css` (Layout 1080x1920 e tema Dark/Gold).
9.  **Frontend JS:** `frontend/app.js` (Lógica de ocultar imagem, trocar abas e download de arquivos).

---
**Instrução Final:** "Gere um código limpo, modular e pronto para produção, garantindo que o botão 'Baixar CSV' funcione dinamicamente para qualquer tabela exibida."
