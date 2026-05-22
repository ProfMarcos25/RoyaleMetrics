/**
 * app.js — Royle Metrics Frontend
 * Layout: Sidebar + Abas (Gráfico / Dados API) + Imagem Cinematográfica
 *
 * Padrões:
 *   - async/await
 *   - event listeners (sem onclick inline)
 *   - Funções nomeadas e comentadas em português
 */

// URL base da API
const API_BASE = "http://localhost:8000";

// Layout padrão injetado nos gráficos para manter o tema escuro
const LAYOUT_TEMA = {
  paper_bgcolor: "rgba(0,0,0,0)",
  plot_bgcolor:  "rgba(0,0,0,0)",
  font: { color: "#e2e8f0", family: "Rajdhani, sans-serif" },
};

// Config padrão do Plotly
const CONFIG_PLOTLY = {
  displaylogo: false,
  responsive:  true,
  modeBarButtonsToRemove: ["select2d", "lasso2d", "autoScale2d"],
};

// ============================================================
// REFERÊNCIAS AO DOM
// ============================================================
const elStatusDot     = document.getElementById("status-dot");
const elStatusText    = document.getElementById("status-text");
const elBtnSync       = document.getElementById("btn-sync");
const elLoading       = document.getElementById("loading");
const elErroCard      = document.getElementById("erro-card");
const elErroMsg       = document.getElementById("erro-mensagem");
const elGrafico       = document.getElementById("grafico-container");
const elPrevisao      = document.getElementById("previsao-card");
const elDadosApi      = document.getElementById("dados-api-container");
const elContentTitulo = document.getElementById("content-titulo");
const elPainelBanco   = document.getElementById("painel-banco");
const elSidebar       = document.getElementById("sidebar");
const elOverlay       = document.getElementById("sidebar-overlay");

// Abas
const elTabProjeto    = document.getElementById("tab-projeto");
const elTabGrafico    = document.getElementById("tab-grafico");
const elTabDados      = document.getElementById("tab-dados");
const elTabProjetoBtn = document.getElementById("tab-projeto-btn");
const elTabGraficoBtn = document.getElementById("tab-grafico-btn");
const elTabDadosBtn   = document.getElementById("tab-dados-btn");

// Cache dos últimos dados recebidos (para troca de aba instantânea)
let ultimosDados      = null;
let ultimoEndpoint    = null;
let ultimoLabel       = null;
let ultimaTabela      = null;  // tabela exibida no momento (para CSV)

// ============================================================
// STATUS DA API
// ============================================================
async function verificarStatus() {
  try {
    const res = await fetch(`${API_BASE}/health`, { signal: AbortSignal.timeout(5000) });
    if (res.ok) {
      elStatusDot.className = "status-dot conectado";
      elStatusText.textContent = "API conectada";
    } else {
      throw new Error();
    }
  } catch {
    elStatusDot.className = "status-dot desconectado";
    elStatusText.textContent = "API desconectada";
  }
}

// ============================================================
// UI — Loading, erro, sidebar
// ============================================================
function mostrarLoading() {
  elLoading.hidden = false;
  elGrafico.hidden = true;
  elPrevisao.hidden = true;
  elErroCard.hidden = true;
}

function ocultarLoading() {
  elLoading.hidden = true;
  elGrafico.hidden = false;
}

function exibirErro(mensagem) {
  elErroMsg.textContent = mensagem;
  elErroCard.hidden = false;
  elGrafico.innerHTML = "";
  elPrevisao.hidden = true;
}

function fecharErro() {
  elErroCard.hidden = true;
}

/** Destaca o item ativo na sidebar */
function destacarNavItem(endpointAtivo) {
  document.querySelectorAll(".nav-item").forEach((item) => {
    const ep = item.dataset.endpoint;
    item.classList.toggle("ativo", ep === endpointAtivo);
  });
}

/** Toggle da sidebar no mobile */
function toggleSidebar() {
  elSidebar.classList.toggle("aberta");
  elOverlay.classList.toggle("visivel");
}

function fecharSidebar() {
  elSidebar.classList.remove("aberta");
  elOverlay.classList.remove("visivel");
}

// ============================================================
// SISTEMA DE ABAS — Gráfico / Dados API
// ============================================================
function trocarAba(aba) {
  // Esconde todos os painéis
  elTabProjeto.hidden = true;
  elTabGrafico.hidden = true;
  elTabDados.hidden = true;
  elTabProjetoBtn.classList.remove("ativo");
  elTabGraficoBtn.classList.remove("ativo");
  elTabDadosBtn.classList.remove("ativo");

  if (aba === "projeto") {
    elTabProjeto.hidden = false;
    elTabProjetoBtn.classList.add("ativo");
  } else if (aba === "grafico") {
    elTabGrafico.hidden = false;
    elTabGraficoBtn.classList.add("ativo");
  } else {
    elTabDados.hidden = false;
    elTabDadosBtn.classList.add("ativo");
  }

  // Esconde painel do banco ao trocar aba
  elPainelBanco.hidden = true;
}

// ============================================================
// BUSCA E RENDERIZAÇÃO
// ============================================================

/**
 * Busca dados de um endpoint e renderiza simultaneamente:
 *   - Aba Gráfico: gráfico Plotly ou card de previsão
 *   - Aba Dados API: tabela com dados brutos
 */
async function buscarGrafico(endpoint, label) {
  mostrarLoading();
  destacarNavItem(endpoint);
  elContentTitulo.textContent = label;
  elPainelBanco.hidden = true;

  // Mostra aba gráfico por padrão
  trocarAba("grafico");

  try {
    const res = await fetch(`${API_BASE}${endpoint}`);
    if (!res.ok) throw new Error(`Erro ${res.status}: ${res.statusText}`);

    const data = await res.json();

    // Armazena para troca de aba instantânea
    ultimosDados = data;
    ultimoEndpoint = endpoint;
    ultimoLabel = label;

    if (endpoint.includes("previsao")) {
      exibirPrevisao(data);
      renderizarDadosApi(data, label);
    } else {
      renderizarGrafico(data);
      renderizarDadosApi(data, label);
    }
  } catch (err) {
    exibirErro(`Não foi possível carregar "${label}". ${err.message}`);
    elDadosApi.innerHTML = `<div class="placeholder">
      <span class="placeholder-icon">⚠️</span>
      <p class="placeholder-texto">Erro ao carregar dados.</p>
    </div>`;
  } finally {
    ocultarLoading();
  }
}

/**
 * Renderiza o gráfico Plotly.
 */
function renderizarGrafico(graficoData) {
  elGrafico.hidden = false;
  elPrevisao.hidden = true;
  elErroCard.hidden = true;

  // Remove placeholder
  const ph = elGrafico.querySelector(".placeholder");
  if (ph) ph.remove();

  const layoutFinal = {
    ...graficoData.layout,
    ...LAYOUT_TEMA,
    font: {
      ...LAYOUT_TEMA.font,
      ...(graficoData.layout?.font || {}),
      color: "#e2e8f0",
    },
  };

  Plotly.newPlot(elGrafico, graficoData.data || [], layoutFinal, CONFIG_PLOTLY);
}

/**
 * Renderiza os dados brutos na aba "Dados API".
 * Extrai os dados dos traces do Plotly para montar uma tabela.
 */
function renderizarDadosApi(data, label) {
  // Se for previsão, mostra o JSON formatado
  if (ultimoEndpoint && ultimoEndpoint.includes("previsao")) {
    elDadosApi.innerHTML = `
      <p class="dados-info">📋 Dados brutos de <strong>${label}</strong></p>
      <pre style="color: var(--text-primary); font-size: 0.85rem; white-space: pre-wrap; 
                  background: var(--bg-primary); padding: 16px; border-radius: var(--radius);
                  border: 1px solid var(--border-color); overflow-x: auto;">
${JSON.stringify(data, null, 2)}</pre>`;
    return;
  }

  // Para gráficos, extrair dados dos traces
  const traces = data.data || [];
  if (!traces.length) {
    elDadosApi.innerHTML = `<div class="placeholder">
      <span class="placeholder-icon">📋</span>
      <p class="placeholder-texto">Sem dados para exibir.</p>
    </div>`;
    return;
  }

  // Monta linhas a partir dos traces
  let linhas = [];
  for (const trace of traces) {
    const xArr = trace.x || [];
    const yArr = trace.y || [];
    const textArr = trace.text || [];
    const name = trace.name || "";
    const customdata = trace.customdata || [];

    for (let i = 0; i < Math.max(xArr.length, yArr.length); i++) {
      const row = {};
      if (name) row["Grupo"] = name;
      if (yArr[i] !== undefined) row["Nome"] = yArr[i];
      if (xArr[i] !== undefined) row["Valor"] = typeof xArr[i] === "number" ? xArr[i].toLocaleString("pt-BR") : xArr[i];
      if (textArr[i] !== undefined) row["Info"] = textArr[i];
      if (customdata[i]) {
        customdata[i].forEach((v, j) => {
          row[`Extra ${j + 1}`] = v;
        });
      }
      linhas.push(row);
    }
  }

  if (!linhas.length) {
    elDadosApi.innerHTML = `<div class="placeholder">
      <span class="placeholder-icon">📋</span>
      <p class="placeholder-texto">Sem dados tabulares para exibir.</p>
    </div>`;
    return;
  }

  const colunas = Object.keys(linhas[0]);
  const cabecalho = colunas.map(c => `<th>${c}</th>`).join("");
  const corpo = linhas.map(row =>
    `<tr>${colunas.map(c => `<td>${row[c] ?? "—"}</td>`).join("")}</tr>`
  ).join("");

  elDadosApi.innerHTML = `
    <p class="dados-info">📋 <strong>${linhas.length}</strong> registros de <strong>${label}</strong></p>
    <div style="overflow-x: auto;">
      <table class="dados-tabela">
        <thead><tr>${cabecalho}</tr></thead>
        <tbody>${corpo}</tbody>
      </table>
    </div>`;
}

// ============================================================
// PREVISÃO ML
// ============================================================
function exibirPrevisao(dados) {
  elGrafico.innerHTML = "";
  elGrafico.hidden = true;
  elPrevisao.hidden = false;
  elErroCard.hidden = true;

  elPrevisao.classList.remove("vitoria", "derrota", "sem-dados");

  const badge = document.getElementById("previsao-badge");

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

  const isVitoria = dados.previsao === "vitoria";
  elPrevisao.classList.add(isVitoria ? "vitoria" : "derrota");

  badge.className = `previsao-badge ${dados.previsao}`;
  badge.textContent = isVitoria ? "🏆 Vitória prevista" : "⚠️ Derrota prevista";

  document.getElementById("previsao-resultado-texto").textContent =
    isVitoria ? "✅ Vitória" : "❌ Derrota";

  const pct = ((dados.confianca || 0) * 100).toFixed(1);
  document.getElementById("previsao-confianca").textContent = `${pct}%`;
  document.getElementById("previsao-amostras").textContent = dados.amostras_treino ?? "—";
  document.getElementById("previsao-mensagem-texto").textContent = dados.mensagem || "Modelo treinado com sucesso.";

  renderizarFeatures(dados.top_features || {});
  renderizarHistorico(dados.historico_recente || []);
}

function renderizarFeatures(features) {
  const container = document.getElementById("previsao-features-lista");

  const nomesAmigaveis = {
    batalhas_ganhas:        "Batalhas ganhas",
    batalhas_perdidas:      "Batalhas perdidas",
    pontuacao:              "Pontuação total (Fame)",
    media_fame_membros:     "Média de Fame por membro",
    media_vitorias_membros: "Média de vitórias por membro",
    total_batalhas_membros: "Total de batalhas jogadas",
  };

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
        </div>`;
    })
    .join("");
}

function renderizarHistorico(historico) {
  const container = document.getElementById("previsao-historico-tabela");

  if (!historico.length) {
    container.innerHTML = `<p style="color: var(--text-muted); font-size: 0.9rem;">Sem histórico disponível.</p>`;
    return;
  }

  const linhas = historico
    .map((g) => {
      const colocacao = g.colocacao ?? "—";
      const icone = typeof g.colocacao === "number" && g.colocacao <= 3 ? "🏆" : (g.colocacao ? "⚠️" : "—");
      return `
        <tr>
          <td>${g.batalhas_ganhas ?? 0}</td>
          <td>${g.batalhas_perdidas ?? 0}</td>
          <td>${(g.pontuacao ?? 0).toLocaleString("pt-BR")}</td>
          <td>${icone} ${colocacao}</td>
        </tr>`;
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
    </table>`;
}

// ============================================================
// SINCRONIZAÇÃO MANUAL
// ============================================================
async function sincronizar() {
  elBtnSync.disabled = true;
  const iconEl = document.getElementById("sync-icon");
  const textoEl = document.getElementById("sync-text");
  iconEl.textContent = "⏳";
  textoEl.textContent = "Sincronizando...";

  try {
    const res = await fetch(`${API_BASE}/api/sync`);
    const data = await res.json();

    if (res.ok) {
      iconEl.textContent = "✅";
      textoEl.textContent = "Atualizado!";
    } else {
      throw new Error(data.detail || `Erro ${res.status}`);
    }
  } catch (err) {
    iconEl.textContent = "❌";
    textoEl.textContent = "Erro!";
    exibirErro(`Falha na sincronização: ${err.message}`);
  } finally {
    setTimeout(() => {
      elBtnSync.disabled = false;
      iconEl.textContent = "🔄";
      textoEl.textContent = "Atualizar dados";
    }, 3000);
  }
}

// ============================================================
// PAINEL DO BANCO DE DADOS
// ============================================================
async function abrirPainelBanco() {
  destacarNavItem(null);
  document.getElementById("btn-banco").classList.add("ativo");

  // Esconde abas e mostra painel
  elTabGrafico.hidden = true;
  elTabDados.hidden = true;
  document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("ativo"));
  elPainelBanco.hidden = false;
  elContentTitulo.textContent = "Banco de Dados";

  fecharSidebar();
  await carregarTabelasBanco();
}

function fecharPainelBanco() {
  elPainelBanco.hidden = true;
  trocarAba("grafico");
  destacarNavItem(null);
  elContentTitulo.textContent = "Dashboard";
}

async function testarConexaoBanco() {
  const elMsg = document.getElementById("banco-status-msg");
  elMsg.textContent = "⏳ Testando conexão...";
  elMsg.className = "banco-status-msg";

  try {
    const res  = await fetch(`${API_BASE}/api/db/status`);
    const data = await res.json();
    const conectado = res.ok && data.status === "conectado";

    elMsg.textContent = data.mensagem;
    elMsg.className   = `banco-status-msg ${conectado ? "ok" : "erro"}`;
    elStatusDot.className  = `status-dot ${conectado ? "conectado" : "desconectado"}`;
    elStatusText.textContent = conectado ? "API + Banco conectados" : "Banco desconectado";
  } catch (err) {
    elMsg.textContent = `❌ Erro de rede: ${err.message}`;
    elMsg.className   = "banco-status-msg erro";
    elStatusDot.className = "status-dot desconectado";
    elStatusText.textContent = "Banco desconectado";
  }
}

async function carregarTabelasBanco() {
  const select = document.getElementById("banco-select-tabela");

  try {
    const res  = await fetch(`${API_BASE}/api/db/tabelas`);
    const data = await res.json();
    if (!res.ok) throw new Error(data.mensagem || "Erro ao listar tabelas");

    select.innerHTML = `<option value="">— selecione —</option>`;
    (data.tabelas || []).forEach((t) => {
      const opt = document.createElement("option");
      opt.value = t;
      opt.textContent = t;
      select.appendChild(opt);
    });

    const elMsg = document.getElementById("banco-status-msg");
    elMsg.textContent = `✅ Conectado — ${data.total} tabela(s) encontrada(s)`;
    elMsg.className = "banco-status-msg ok";
  } catch (err) {
    const elMsg = document.getElementById("banco-status-msg");
    elMsg.textContent = `❌ Falha ao carregar tabelas: ${err.message}`;
    elMsg.className = "banco-status-msg erro";
  }
}

async function selecionarTabela() {
  const select = document.getElementById("banco-select-tabela");
  const limite = document.getElementById("banco-limite").value || 20;
  const tabela = select.value;
  const elRes  = document.getElementById("banco-resultado");

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
      elRes.innerHTML = `<p class="banco-placeholder">
        ℹ️ A tabela <strong>${tabela}</strong> existe mas não tem registros ainda.
      </p>`;
      return;
    }

    const cabecalho = data.colunas.map(c => `<th>${c}</th>`).join("");
    const linhas = data.linhas
      .map(linha => `<tr>${data.colunas.map(c => `<td>${linha[c] ?? "—"}</td>`).join("")}</tr>`)
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
      </div>`;
  } catch (err) {
    elRes.innerHTML = `<p class="banco-placeholder erro">❌ ${err.message}</p>`;
  }
}

// ============================================================
// ADMINISTRAÇÃO — Seed, Reset, CSV
// ============================================================

/**
 * Inicia o seed do banco via API e faz polling do status.
 */
async function executarSeed() {
  if (!confirm("📥 Deseja popular o banco com dados da API do Clash Royale?\nIsso pode levar alguns minutos.")) return;

  trocarAba("dados");
  elContentTitulo.textContent = "Inserindo dados...";
  elDadosApi.innerHTML = `<div class="placeholder">
    <span class="placeholder-icon">⏳</span>
    <p class="placeholder-texto">Populando banco de dados via API...</p>
    <p class="placeholder-sub">Aguarde, isso pode levar alguns minutos.</p>
  </div>`;

  try {
    const res = await fetch(`${API_BASE}/api/admin/seed`, { method: "POST" });
    const data = await res.json();

    if (res.status === 409) {
      exibirErro(data.mensagem);
      return;
    }

    // Polling do status
    const intervalo = setInterval(async () => {
      try {
        const statusRes = await fetch(`${API_BASE}/api/admin/seed/status`);
        const statusData = await statusRes.json();

        if (statusData.status !== "rodando") {
          clearInterval(intervalo);
          elContentTitulo.textContent = "Seed concluído";

          if (statusData.status === "ok") {
            const r = statusData.resumo || {};
            elDadosApi.innerHTML = `<div class="placeholder">
              <span class="placeholder-icon">✅</span>
              <p class="placeholder-texto">${statusData.mensagem}</p>
              <p class="placeholder-sub">
                Cartas: ${r.cartas || 0} | Clãs: ${r.clans || 0} | 
                Jogadores: ${r.jogadores || 0} | Guerras: ${r.guerras || 0}
              </p>
            </div>`;
          } else {
            elDadosApi.innerHTML = `<div class="placeholder">
              <span class="placeholder-icon">❌</span>
              <p class="placeholder-texto">${statusData.mensagem}</p>
            </div>`;
          }
        }
      } catch { /* polling silencioso */ }
    }, 3000);
  } catch (err) {
    exibirErro(`Falha ao iniciar seed: ${err.message}`);
  }
}

/**
 * Reseta o banco (TRUNCATE em todas as tabelas).
 */
async function resetarBanco() {
  if (!confirm("🗑️ ATENÇÃO: Isso vai APAGAR TODOS os dados do banco!\n\nDeseja continuar?")) return;
  if (!confirm("⚠️ Última confirmação: tem certeza que quer LIMPAR o banco?")) return;

  trocarAba("dados");
  elContentTitulo.textContent = "Limpando banco...";

  try {
    const res = await fetch(`${API_BASE}/api/admin/reset`, { method: "POST" });
    const data = await res.json();

    elContentTitulo.textContent = "Banco de dados";
    elDadosApi.innerHTML = `<div class="placeholder">
      <span class="placeholder-icon">${data.status === "ok" ? "🗑️" : "❌"}</span>
      <p class="placeholder-texto">${data.mensagem}</p>
      ${data.tabelas ? `<p class="placeholder-sub">Tabelas: ${data.tabelas.join(", ")}</p>` : ""}
    </div>`;
  } catch (err) {
    exibirErro(`Falha ao limpar banco: ${err.message}`);
  }
}

/**
 * Baixa o CSV da tabela atualmente selecionada no painel de banco,
 * ou da análise ativa (ranking → jogadores, cartas → cartas, etc.)
 */
async function baixarCSV() {
  // Determina qual tabela exportar
  let tabela = null;

  // 1. Se o painel de banco está aberto e tem tabela selecionada
  const selectTabela = document.getElementById("banco-select-tabela");
  if (selectTabela && selectTabela.value) {
    tabela = selectTabela.value;
  }

  // 2. Se há uma análise ativa, mapeia para tabela
  if (!tabela && ultimoEndpoint) {
    const mapa = {
      "/api/ranking": "jogadores",
      "/api/cartas": "cartas",
      "/api/guerras": "guerras",
      "/api/torneios": "torneios",
    };
    tabela = mapa[ultimoEndpoint];
  }

  if (!tabela) {
    exibirErro("Selecione uma tabela no painel de banco ou uma análise para exportar.");
    return;
  }

  try {
    const res = await fetch(`${API_BASE}/api/admin/export/${tabela}`);
    if (!res.ok) {
      const err = await res.json();
      exibirErro(err.mensagem || "Erro ao exportar CSV.");
      return;
    }

    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${tabela}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  } catch (err) {
    exibirErro(`Erro ao baixar CSV: ${err.message}`);
  }
}

// ============================================================
// INICIALIZAÇÃO
// ============================================================
document.addEventListener("DOMContentLoaded", async () => {
  await verificarStatus();

  // Navegação da sidebar — clique nos itens de análise
  document.querySelectorAll(".nav-item[data-endpoint]").forEach((item) => {
    item.addEventListener("click", () => {
      const endpoint = item.dataset.endpoint;
      const label    = item.dataset.label || endpoint;
      fecharSidebar();
      buscarGrafico(endpoint, label);
    });
  });

  // Banco de dados
  document.getElementById("btn-banco").addEventListener("click", () => {
    fecharSidebar();
    abrirPainelBanco();
  });

  // Abas
  elTabProjetoBtn.addEventListener("click", () => trocarAba("projeto"));
  elTabGraficoBtn.addEventListener("click", () => trocarAba("grafico"));
  elTabDadosBtn.addEventListener("click", () => trocarAba("dados"));

  // Sync
  elBtnSync.addEventListener("click", sincronizar);

  // Fechar erro
  document.getElementById("btn-fechar-erro").addEventListener("click", fecharErro);

  // Banco — fechar, testar, executar
  document.getElementById("btn-fechar-banco").addEventListener("click", fecharPainelBanco);
  document.getElementById("btn-testar-conexao").addEventListener("click", testarConexaoBanco);
  document.getElementById("btn-executar-select").addEventListener("click", selecionarTabela);

  // Admin
  document.getElementById("btn-seed").addEventListener("click", () => { fecharSidebar(); executarSeed(); });
  document.getElementById("btn-reset").addEventListener("click", () => { fecharSidebar(); resetarBanco(); });
  document.getElementById("btn-csv").addEventListener("click", () => { fecharSidebar(); baixarCSV(); });

  // Sidebar toggle (mobile)
  document.getElementById("sidebar-toggle").addEventListener("click", toggleSidebar);
  elOverlay.addEventListener("click", fecharSidebar);
});
