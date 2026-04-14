-- =============================================================
--  Royle Metrics — Schema do Banco de Dados PostgreSQL
--  Projeto: Análise de desempenho no Clash Royale
--  Curso Técnico em Ciência de Dados
-- =============================================================

-- Habilitar extensão para geração de UUIDs (opcional, futuro)
-- CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ---------------------------------------------------------
-- Tabela: clans
-- Armazena os clãs monitorados pelo projeto
-- ---------------------------------------------------------
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
