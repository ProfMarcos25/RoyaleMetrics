/**
 * app.js — Royle Metrics Frontend
 * Gerencia a comunicação com a API FastAPI e a renderização
 * dos gráficos Plotly e do card de previsão ML.
 *
 * Padrões usados:
 *   - async/await (sem .then() encadeado)
 *   - event listeners via querySelectorAll
 *   - Funções nomeadas e comentadas em português
 */

// URL base da API — altere se hospedar em outro endereço
const API_BASE = "http://localhost:8000";

// Layout padrão injetado em todos os gráficos para manter o tema escuro
const LAYOUT_TEMA = {
  paper_bgcolor: "rgba(0,0,0,0)",
  plot_bgcolor:  "rgba(0,0,0,0)",
  font: {
    color:  "#e2e8f0",
    family: "Rajdhani, sans-serif",
  },
};

// Config padrão do Plotly (sem logo, responsivo)
const CONFIG_PLOTLY = {
  displaylogo:    false,
  responsive:     true,
  modeBarButtonsToRemove: ["select2d", "lasso2d", "autoScale2d"],
};

// Referências aos elementos do DOM (cache para performance)
const elStatusDot    = document.getElementById("status-dot");
const elStatusText   = document.getElementById("status-text");
const elBtnSync      = document.getElementById("btn-sync");
const elLoading      = document.getElementById("loading");
const elLoadingTexto = document.getElementById("loading-texto");
const elErroCard     = document.getElementById("erro-card");
const elErroMsg      = document.getElementById("erro-mensagem");
const elGrafico      = document.getElementById("grafico-container");
const elPrevisao     = document.getElementById("previsao-card");

// ============================================================
// STATUS DA API
// ============================================================

/**
 * Verifica se a API está acessível ao carregar a página.
 * Atualiza o badge de status no header com verde (conectado)
 * ou vermelho (desconectado).
 */
async function verificarStatus() {
  try {
    const res = await fetch(`${API_BASE}/health`, { signal: AbortSignal.timeout(5000) });

    if (res.ok) {
      elStatusDot.className = "status-dot conectado";
      elStatusText.textContent = "API conectada";
    } else {
      throw new Error(`Status ${res.status}`);
    }
  } catch {
    // Não exibe erro para o usuário — só atualiza o badge
    elStatusDot.className = "status-dot desconectado";
    elStatusText.textContent = "API desconectada";
  }
}

// ============================================================
// FUNÇÕES DE UI (loading, erro, limpeza)
// ============================================================

/**
 * Exibe o spinner de loading com mensagem customizável.
 * @param {string} [mensagem] - Texto exibido abaixo do spinner.
 */
function mostrarLoading(mensagem = "Carregando dados...") {
  elLoadingTexto.textContent = mensagem;
  elLoading.hidden = false;
  elGrafico.hidden = true;
  elPrevisao.hidden = true;
  elErroCard.hidden = true;
}

/** Oculta o spinner de loading. */
function ocultarLoading() {
  elLoading.hidden = true;
  elGrafico.hidden = false;
}

/**
 * Exibe o card de erro com a mensagem informada.
 * @param {string} mensagem - Descrição do erro ocorrido.
 */
function exibirErro(mensagem) {
  elErroMsg.textContent = mensagem;
  elErroCard.hidden = false;
  elGrafico.innerHTML = "";
  elPrevisao.hidden = true;
}

/** Fecha o card de erro ao clicar no botão "Fechar". */
function fecharErro() {
  elErroCard.hidden = true;
}

/**
 * Remove a classe 'ativo' de todos os botões de análise.
 * @param {string} endpointAtivo - Endpoint do botão a marcar como ativo.
 */
function destacarBotao(endpointAtivo) {
  document.querySelectorAll(".btn-analise").forEach((btn) => {
    btn.classList.toggle("ativo", btn.dataset.endpoint === endpointAtivo);
  });
}

// ============================================================
// BUSCA E RENDERIZAÇÃO DE GRÁFICOS
// ============================================================

/**
 * Busca dados de um endpoint e renderiza o gráfico ou card de previsão.
 * Chamado ao clicar em qualquer botão de análise.
 *
 * @param {string} endpoint - Caminho da API (ex: "/api/ranking").
 * @param {string} label    - Nome da análise para exibir no loading.
 */
async function buscarGrafico(endpoint, label) {
  mostrarLoading(`Carregando ${label}...`);
  destacarBotao(endpoint);

  try {
    const res = await fetch(`${API_BASE}${endpoint}`);

    if (!res.ok) {
      throw new Error(`Erro ${res.status}: ${res.statusText}`);
    }

    const data = await res.json();

    // Endpoint de previsão ML tem estrutura diferente dos gráficos
    if (endpoint.includes("previsao")) {
      exibirPrevisao(data);
    } else {
      renderizarGrafico(data);
    }
  } catch (err) {
    exibirErro(`Não foi possível carregar "${label}". ${err.message}`);
  } finally {
    ocultarLoading();
  }
}

/**
 * Renderiza um gráfico Plotly a partir dos dados retornados pela API.
 * Mescla o layout da API com o tema escuro do projeto.
 *
 * @param {{ data: object[], layout: object }} graficoData - Dados do Plotly.
 */
function renderizarGrafico(graficoData) {
  // Garante que o container esteja visível e limpo
  elGrafico.hidden = false;
  elPrevisao.hidden = true;
  elErroCard.hidden = true;

  // Mescla o layout retornado pela API com as configurações de tema
  const layoutFinal = {
    ...graficoData.layout,
    ...LAYOUT_TEMA,
    font: {
      ...LAYOUT_TEMA.font,
      ...(graficoData.layout?.font || {}),
      color: "#e2e8f0",  // força cor do texto no tema escuro
    },
  };

  Plotly.newPlot(elGrafico, graficoData.data || [], layoutFinal, CONFIG_PLOTLY);
}

// ============================================================
// EXIBIÇÃO DO CARD DE PREVISÃO ML
// ============================================================

/**
 * Exibe o card de previsão de guerra com os dados do modelo ML.
 * Preenche resultado, confiança, features e histórico recente.
 *
 * @param {object} dados - Resposta do endpoint /api/guerras/previsao.
 */
function exibirPrevisao(dados) {
  elGrafico.innerHTML = "";   // limpa gráfico anterior
  elGrafico.hidden = true;
  elPrevisao.hidden = false;
  elErroCard.hidden = true;

  // Remove classes de estado anteriores
  elPrevisao.classList.remove("vitoria", "derrota", "sem-dados");

  const badge = document.getElementById("previsao-badge");

  // Sem dados suficientes
  if (!dados.previsao) {
    elPrevisao.classList.add("sem-dados");
    badge.className = "previsao-badge";
    badge.textContent = "⚠ Dados insuficientes";
    document.getElementById("previsao-resultado-texto").textContent = "—";
    document.getElementById("previsao-confianca").textContent = "—";
    document.getElementById("previsao-amostras").textContent = "—";
    document.getElementById("previsao-mensagem-texto").textContent = dados.mensagem;
    document.getElementById("previsao-features-lista").innerHTML = "";
    document.getElementById("previsao-historico-tabela").innerHTML = "";
    return;
  }

  // Aplica classe de estilo conforme o resultado
  const isVitoria = dados.previsao === "vitoria";
  elPrevisao.classList.add(isVitoria ? "vitoria" : "derrota");

  // Badge
  badge.className = `previsao-badge ${dados.previsao}`;
  badge.textContent = isVitoria ? "🏆 Vitória prevista" : "⚠️ Derrota prevista";

  // Métricas principais
  document.getElementById("previsao-resultado-texto").textContent =
    isVitoria ? "✅ Vitória" : "❌ Derrota";

  const percentualConfianca = ((dados.confianca || 0) * 100).toFixed(1);
  document.getElementById("previsao-confianca").textContent = `${percentualConfianca}%`;
  document.getElementById("previsao-amostras").textContent =
    dados.amostras_treino ?? "—";

  // Mensagem educativa
  document.getElementById("previsao-mensagem-texto").textContent =
    dados.mensagem || "Modelo treinado com sucesso.";

  // Importância das variáveis (features)
  renderizarFeatures(dados.top_features || {});

  // Histórico recente
  renderizarHistorico(dados.historico_recente || []);
}

/**
 * Renderiza a lista de importância de variáveis como barras de progresso.
 *
 * @param {Record<string, number>} features - Objeto {nome: importância}.
 */
function renderizarFeatures(features) {
  const container = document.getElementById("previsao-features-lista");

  // Nomes amigáveis para as variáveis técnicas
  const nomesAmigaveis = {
    batalhas_ganhas:          "Batalhas ganhas",
    batalhas_perdidas:        "Batalhas perdidas",
    pontuacao:                "Pontuação total (Fame)",
    media_fame_membros:       "Média de Fame por membro",
    media_vitorias_membros:   "Média de vitórias por membro",
    total_batalhas_membros:   "Total de batalhas jogadas",
  };

  // Calcula o valor máximo para normalizar as barras
  const valores = Object.values(features);
  const maximo = Math.max(...valores, 0.001);

  container.innerHTML = Object.entries(features)
    .map(([nome, valor]) => {
      const larguraPct = ((valor / maximo) * 100).toFixed(1);
      const percentual = (valor * 100).toFixed(1);
      const nomeAmigavel = nomesAmigaveis[nome] || nome;

      return `
        <div class="feature-item">
          <span class="feature-nome">${nomeAmigavel}</span>
          <div class="feature-barra-wrapper">
            <div class="feature-barra" style="width: ${larguraPct}%"></div>
          </div>
          <span class="feature-percentual">${percentual}%</span>
        </div>
      `;
    })
    .join("");
}

/**
 * Renderiza a tabela com o histórico recente das guerras.
 *
 * @param {Array<object>} historico - Lista de objetos com dados das guerras.
 */
function renderizarHistorico(historico) {
  const container = document.getElementById("previsao-historico-tabela");

  if (!historico.length) {
    container.innerHTML = `<p style="color: var(--text-muted); font-size: 0.9rem;">
      Sem histórico disponível.
    </p>`;
    return;
  }

  const linhas = historico
    .map((g) => {
      const colocacao = g.colocacao ?? "—";
      const icone = typeof g.colocacao === "number" && g.colocacao <= 3
        ? "🏆" : (g.colocacao ? "⚠️" : "—");

      return `
        <tr>
          <td>${g.batalhas_ganhas ?? 0}</td>
          <td>${g.batalhas_perdidas ?? 0}</td>
          <td>${(g.pontuacao ?? 0).toLocaleString("pt-BR")}</td>
          <td>${icone} ${colocacao}</td>
        </tr>
      `;
    })
    .join("");

  container.innerHTML = `
    <table class="historico-tabela">
      <thead>
        <tr>
          <th>Vit. Guerras</th>
          <th>Derr. Guerras</th>
          <th>Pontuação</th>
          <th>Colocação</th>
        </tr>
      </thead>
      <tbody>${linhas}</tbody>
    </table>
  `;
}

// ============================================================
// SINCRONIZAÇÃO MANUAL
// ============================================================

/**
 * Aciona a sincronização manual dos dados via GET /api/sync.
 * Desabilita o botão durante a requisição para evitar cliques duplos.
 * Exibe o resultado brevemente na interface.
 */
async function sincronizar() {
  // Desabilita o botão e mostra feedback visual
  elBtnSync.disabled = true;
  const iconEl = document.getElementById("sync-icon");
  const textoEl = document.getElementById("sync-text");
  iconEl.textContent = "⏳";
  textoEl.textContent = "Sincronizando...";

  try {
    const res = await fetch(`${API_BASE}/api/sync`);
    const data = await res.json();

    if (res.ok) {
      // Feedback de sucesso (temporário)
      iconEl.textContent = "✅";
      textoEl.textContent = "Atualizado!";
      console.log("Sincronização concluída:", data);
    } else {
      throw new Error(data.detail || `Erro ${res.status}`);
    }
  } catch (err) {
    iconEl.textContent = "❌";
    textoEl.textContent = "Erro!";
    exibirErro(`Falha na sincronização: ${err.message}`);
  } finally {
    // Restaura o botão após 3 segundos
    setTimeout(() => {
      elBtnSync.disabled = false;
      iconEl.textContent = "🔄";
      textoEl.textContent = "Atualizar dados";
    }, 3000);
  }
}

// ============================================================
// INICIALIZAÇÃO — Event Listeners e Setup
// ============================================================

/**
 * Configura todos os event listeners ao carregar o DOM.
 * Usa querySelectorAll para registrar em todos os botões de análise.
 */
document.addEventListener("DOMContentLoaded", async () => {
  // Verifica o status da API imediatamente ao carregar
  await verificarStatus();

  // Registra listener em cada botão de análise
  document.querySelectorAll(".btn-analise").forEach((btn) => {
    btn.addEventListener("click", () => {
      const endpoint = btn.dataset.endpoint;
      const label    = btn.dataset.label || endpoint;
      buscarGrafico(endpoint, label);
    });
  });

  // Torna as funções acessíveis globalmente (chamadas pelo HTML inline)
  window.sincronizar        = sincronizar;
  window.fecharErro         = fecharErro;
  window.abrirPainelBanco   = abrirPainelBanco;
  window.fecharPainelBanco  = fecharPainelBanco;
  window.testarConexaoBanco = testarConexaoBanco;
  window.selecionarTabela   = selecionarTabela;
});

// ============================================================
// PAINEL DO BANCO DE DADOS
// ============================================================

const elPainelBanco = document.getElementById("painel-banco");

/**
 * Abre o painel do banco e carrega a lista de tabelas.
 */
async function abrirPainelBanco() {
  // Destaca o botão de banco
  document.querySelectorAll(".btn-analise").forEach((btn) => {
    btn.classList.toggle("ativo", btn.id === "btn-banco");
  });

  elPainelBanco.hidden = false;
  elPainelBanco.scrollIntoView({ behavior: "smooth", block: "start" });

  // Carrega as tabelas disponíveis no select
  await carregarTabelasBanco();
}

/** Fecha o painel do banco. */
function fecharPainelBanco() {
  elPainelBanco.hidden = true;
  document.querySelectorAll(".btn-analise").forEach((btn) => btn.classList.remove("ativo"));
}

/**
 * Testa a conexão com o banco de dados via GET /api/db/status.
 * Exibe a versão do PostgreSQL e atualiza o badge de status no header.
 */
async function testarConexaoBanco() {
  const elMsg = document.getElementById("banco-status-msg");
  elMsg.textContent = "⏳ Testando conexão...";
  elMsg.className = "banco-status-msg";

  try {
    const res  = await fetch(`${API_BASE}/api/db/status`);
    const data = await res.json();

    const conectado = res.ok && data.status === "conectado";

    // Atualiza mensagem no painel
    elMsg.textContent = data.mensagem;
    elMsg.className   = `banco-status-msg ${conectado ? "ok" : "erro"}`;

    // Atualiza o badge de status no header
    elStatusDot.className  = `status-dot ${conectado ? "conectado" : "desconectado"}`;
    elStatusText.textContent = conectado ? "API + Banco conectados" : "Banco desconectado";

  } catch (err) {
    elMsg.textContent     = `❌ Erro de rede: ${err.message}`;
    elMsg.className       = "banco-status-msg erro";
    elStatusDot.className = "status-dot desconectado";
    elStatusText.textContent = "Banco desconectado";
  }
}

/**
 * Busca as tabelas do banco e preenche o <select>.
 */
async function carregarTabelasBanco() {
  const select = document.getElementById("banco-select-tabela");

  try {
    const res  = await fetch(`${API_BASE}/api/db/tabelas`);
    const data = await res.json();

    if (!res.ok) throw new Error(data.mensagem || "Erro ao listar tabelas");

    // Reseta e preenche o select
    select.innerHTML = `<option value="">— selecione —</option>`;
    (data.tabelas || []).forEach((t) => {
      const opt = document.createElement("option");
      opt.value = t;
      opt.textContent = t;
      select.appendChild(opt);
    });

    // Atualiza status automaticamente ao carregar
    const elMsg = document.getElementById("banco-status-msg");
    elMsg.textContent = `✅ Conectado — ${data.total} tabela(s) encontrada(s)`;
    elMsg.className = "banco-status-msg ok";

  } catch (err) {
    const elMsg = document.getElementById("banco-status-msg");
    elMsg.textContent = `❌ Falha ao carregar tabelas: ${err.message}`;
    elMsg.className = "banco-status-msg erro";
  }
}

/**
 * Executa SELECT * na tabela selecionada e exibe os dados em uma tabela HTML.
 */
async function selecionarTabela() {
  const select  = document.getElementById("banco-select-tabela");
  const limite  = document.getElementById("banco-limite").value || 20;
  const tabela  = select.value;
  const elRes   = document.getElementById("banco-resultado");

  if (!tabela) {
    elRes.innerHTML = `<p class="banco-placeholder">⚠️ Selecione uma tabela antes de executar.</p>`;
    return;
  }

  elRes.innerHTML = `<p class="banco-placeholder">⏳ Executando SELECT * FROM ${tabela} LIMIT ${limite}...</p>`;

  try {
    const res  = await fetch(`${API_BASE}/api/db/tabelas/${tabela}?limite=${limite}`);
    const data = await res.json();

    if (!res.ok) throw new Error(data.mensagem || "Erro ao buscar dados");

    if (!data.linhas || data.linhas.length === 0) {
      elRes.innerHTML = `
        <p class="banco-placeholder">
          ℹ️ A tabela <strong>${tabela}</strong> existe mas não tem registros ainda.
        </p>`;
      return;
    }

    // Monta a tabela HTML
    const cabecalho = data.colunas
      .map((c) => `<th>${c}</th>`)
      .join("");

    const linhas = data.linhas
      .map((linha) =>
        `<tr>${data.colunas.map((c) => `<td>${linha[c] ?? "—"}</td>`).join("")}</tr>`
      )
      .join("");

    elRes.innerHTML = `
      <p class="banco-info">
        Tabela: <strong>${tabela}</strong> &mdash;
        Exibindo <strong>${data.total_linhas}</strong> linha(s) (limite: ${data.limite})
      </p>
      <div class="banco-tabela-wrapper">
        <table class="banco-tabela">
          <thead><tr>${cabecalho}</tr></thead>
          <tbody>${linhas}</tbody>
        </table>
      </div>
    `;

  } catch (err) {
    elRes.innerHTML = `<p class="banco-placeholder erro">❌ ${err.message}</p>`;
  }
}
