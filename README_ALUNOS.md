# 🎓 Royale Metrics para Alunos (2º Ano)

Este guia foi feito para quem está começando. A ideia é explicar o projeto de um jeito simples, como se fosse uma aula.

---

## 🕹️ O que é esse projeto?

O **Royale Metrics** pega dados do Clash Royale e transforma em gráficos para analisar:
- Quem está melhor no clã
- Quais cartas têm melhor desempenho
- Como o clã foi nas guerras

Também existe uma parte de **Inteligência Artificial** que tenta prever o resultado da próxima guerra.

---

## 🧠 Entendendo em linguagem fácil

Pense assim:
- **Model** = onde ficam os dados e as regras
- **Controller** = os “caminhos” da API (rotas)
- **View** = a tela que você vê no navegador

No projeto:
- `app/models/` → dados e lógica
- `app/controllers/` → endpoints da API
- `app/views/` → página web

---

## 🧰 O que você precisa ter no PC

Antes de rodar, precisa de:
- Python 3.11 ou superior
- PostgreSQL instalado
- Token da API do Clash Royale

Se não tiver tudo isso, peça ajuda ao professor.

---

## 🚀 Como rodar o projeto (passo a passo)

### 1) Ativar ambiente virtual

Abra o terminal na pasta do projeto e rode:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 2) Instalar bibliotecas

```powershell
pip install -r requirements.txt
```

### 3) Criar o arquivo `.env`

```powershell
Copy-Item .env.example .env
```

Depois edite o `.env` e coloque seu token.

Exemplo:

```env
CLASH_API_TOKEN=seu_token_aqui
CLASH_API_URL=https://proxy.royaleapi.dev/v1
DATABASE_URL=postgresql://postgres:senha@localhost:5432/royale_metrics
ENVIRONMENT=development
SYNC_INTERVAL_HOURS=6
```

### 4) Configurar os clãs

No arquivo `data/tags_clas.json`, coloque as tags dos clãs:

```json
{
  "clans": ["#GGRU2GCJ"],
  "jogadores": []
}
```

### 5) Iniciar o servidor

```powershell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Se deu certo, abra:
- Front-end: `http://localhost:8000`
- Documentação da API: `http://localhost:8000/docs`

---

## 🌐 Endpoints mais usados (explicação simples)

- `/api/sync` → atualiza dados do Clash Royale
- `/api/ranking` → mostra ranking dos jogadores
- `/api/cartas` → mostra desempenho das cartas
- `/api/guerras` → mostra histórico de guerras
- `/api/guerras/previsao` → previsão da próxima guerra (IA)
- `/api/torneios` → dados de torneios escolares

---

## 📊 Como usar na aula

Sugestão prática:
1. Rodar `/api/sync` para atualizar dados
2. Abrir ranking e discutir média, máximo, mínimo
3. Ver cartas e discutir “frequência x vitória”
4. Ver previsão de guerra e conversar sobre IA

---

## ❓ Erros comuns (e como resolver)

- **Erro de token**: confira `CLASH_API_TOKEN` no `.env`
- **Porta ocupada**: troque para outra porta, ex.: `--port 8001`
- **Banco não conecta**: revise `DATABASE_URL` e se o PostgreSQL está ligado
- **Comando não funciona**: confirme se `.venv` está ativado

---

## ✅ Resumo rápido

Você vai:
1. Instalar dependências
2. Configurar `.env`
3. Rodar o servidor
4. Abrir o navegador
5. Analisar dados reais do jogo

Pronto! 🎉
