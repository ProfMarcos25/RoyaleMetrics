"""
Modelos SQLAlchemy — Royle Metrics
Define as classes ORM que mapeiam as tabelas do PostgreSQL.
Cada classe corresponde a uma tabela definida em database/schema.sql.
"""
from datetime import date, datetime
from typing import List, Optional

from sqlalchemy import (
    DATE,
    INTEGER,
    TEXT,
    TIMESTAMP,
    VARCHAR,
    ForeignKey,
    Integer,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class Clan(Base):
    """
    Clãs monitorados pelo projeto Royle Metrics.
    Um clã pode ter vários jogadores e várias guerras.
    """
    __tablename__ = "clans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tag: Mapped[str] = mapped_column(VARCHAR(20), unique=True, nullable=False)
    nome: Mapped[str] = mapped_column(VARCHAR(100), nullable=False)
    descricao: Mapped[Optional[str]] = mapped_column(TEXT)
    trofeus: Mapped[int] = mapped_column(Integer, default=0)
    membros: Mapped[int] = mapped_column(Integer, default=0)
    atualizado_em: Mapped[datetime] = mapped_column(TIMESTAMP, default=func.now())

    # Relacionamentos
    jogadores: Mapped[List["Jogador"]] = relationship(
        "Jogador", back_populates="clan", cascade="all, delete-orphan"
    )
    guerras: Mapped[List["Guerra"]] = relationship(
        "Guerra", back_populates="clan", cascade="all, delete-orphan"
    )


class Jogador(Base):
    """
    Jogadores (membros dos clãs) coletados via API.
    Contém dados de perfil e referência ao clã atual.
    """
    __tablename__ = "jogadores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tag: Mapped[str] = mapped_column(VARCHAR(20), unique=True, nullable=False)
    nickname: Mapped[str] = mapped_column(VARCHAR(50), nullable=False)
    nivel: Mapped[Optional[int]] = mapped_column(Integer)
    trofeus: Mapped[int] = mapped_column(Integer, default=0)
    trofeus_recorde: Mapped[int] = mapped_column(Integer, default=0)
    arena: Mapped[Optional[str]] = mapped_column(VARCHAR(50))
    clan_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("clans.id", ondelete="SET NULL")
    )
    ultima_batalha: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP)
    criado_em: Mapped[datetime] = mapped_column(TIMESTAMP, default=func.now())

    # Relacionamentos
    clan: Mapped[Optional["Clan"]] = relationship("Clan", back_populates="jogadores")
    batalhas: Mapped[List["Batalha"]] = relationship(
        "Batalha", back_populates="jogador", cascade="all, delete-orphan"
    )
    contribuicoes: Mapped[List["ContribuicaoGuerra"]] = relationship(
        "ContribuicaoGuerra", back_populates="jogador", cascade="all, delete-orphan"
    )
    torneios_campeao: Mapped[List["Torneio"]] = relationship(
        "Torneio", back_populates="campeao", foreign_keys="Torneio.campeao_id"
    )


class Carta(Base):
    """
    Cartas do jogo Clash Royale.
    Populado via endpoint GET /cards da API oficial.
    """
    __tablename__ = "cartas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    card_id: Mapped[Optional[int]] = mapped_column(Integer, unique=True)
    nome: Mapped[str] = mapped_column(VARCHAR(100), nullable=False)
    tipo: Mapped[Optional[str]] = mapped_column(VARCHAR(30))       # troop, spell, building
    raridade: Mapped[Optional[str]] = mapped_column(VARCHAR(20))   # Common, Rare, Epic, Legendary
    elixir: Mapped[Optional[int]] = mapped_column(Integer)
    max_nivel: Mapped[Optional[int]] = mapped_column(Integer)
    url_icon: Mapped[Optional[str]] = mapped_column(TEXT)

    # Relacionamentos
    batalha_cartas: Mapped[List["BatalhaCartas"]] = relationship(
        "BatalhaCartas", back_populates="carta", cascade="all, delete-orphan"
    )


class Torneio(Base):
    """
    Torneios escolares registrados manualmente ou via formulário.
    Representa competições realizadas na unidade escolar.
    """
    __tablename__ = "torneios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(VARCHAR(100), nullable=False)
    data: Mapped[Optional[date]] = mapped_column(DATE)
    formato: Mapped[Optional[str]] = mapped_column(VARCHAR(50))   # eliminatoria, pontos_corridos
    descricao: Mapped[Optional[str]] = mapped_column(TEXT)
    campeao_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("jogadores.id", ondelete="SET NULL")
    )

    # Relacionamentos
    campeao: Mapped[Optional["Jogador"]] = relationship(
        "Jogador", back_populates="torneios_campeao", foreign_keys=[campeao_id]
    )
    partidas: Mapped[List["PartidaTorneio"]] = relationship(
        "PartidaTorneio", back_populates="torneio", cascade="all, delete-orphan"
    )
    batalhas: Mapped[List["Batalha"]] = relationship(
        "Batalha", back_populates="torneio"
    )


class Batalha(Base):
    """
    Batalhas coletadas via API do Clash Royale.
    O campo battle_id garante que batalhas duplicadas não sejam inseridas.
    """
    __tablename__ = "batalhas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    battle_id: Mapped[Optional[str]] = mapped_column(VARCHAR(100), unique=True)
    jogador_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("jogadores.id", ondelete="CASCADE")
    )
    tipo: Mapped[Optional[str]] = mapped_column(VARCHAR(30))        # PvP, clanWar, riverRacePvP
    resultado: Mapped[Optional[str]] = mapped_column(VARCHAR(10))   # vitoria, derrota, empate
    trofeus_ganhos: Mapped[int] = mapped_column(Integer, default=0)
    time_trofeus: Mapped[Optional[int]] = mapped_column(Integer)
    oponente_tag: Mapped[Optional[str]] = mapped_column(VARCHAR(20))
    oponente_trofeus: Mapped[Optional[int]] = mapped_column(Integer)
    data_batalha: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP)
    torneio_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("torneios.id", ondelete="SET NULL")
    )

    # Relacionamentos
    jogador: Mapped[Optional["Jogador"]] = relationship("Jogador", back_populates="batalhas")
    torneio: Mapped[Optional["Torneio"]] = relationship("Torneio", back_populates="batalhas")
    cartas_usadas: Mapped[List["BatalhaCartas"]] = relationship(
        "BatalhaCartas", back_populates="batalha", cascade="all, delete-orphan"
    )


class BatalhaCartas(Base):
    """
    Tabela intermediária: cartas usadas em cada batalha.
    Representa o deck do jogador em uma batalha específica.
    """
    __tablename__ = "batalha_cartas"

    batalha_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("batalhas.id", ondelete="CASCADE"), primary_key=True
    )
    carta_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("cartas.id", ondelete="CASCADE"), primary_key=True
    )
    nivel: Mapped[Optional[int]] = mapped_column(Integer)

    # Relacionamentos
    batalha: Mapped["Batalha"] = relationship("Batalha", back_populates="cartas_usadas")
    carta: Mapped["Carta"] = relationship("Carta", back_populates="batalha_cartas")


class Guerra(Base):
    """
    Registro de guerras de clã (River Race e formatos anteriores).
    Cada guerra contém o desempenho geral do clã na temporada.
    """
    __tablename__ = "guerras"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    clan_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("clans.id", ondelete="CASCADE")
    )
    temporada: Mapped[Optional[str]] = mapped_column(VARCHAR(20))   # ex: "2024-03"
    tipo: Mapped[Optional[str]] = mapped_column(VARCHAR(30))        # riverRace, classicWarDay
    batalhas_ganhas: Mapped[int] = mapped_column(Integer, default=0)
    batalhas_perdidas: Mapped[int] = mapped_column(Integer, default=0)
    pontuacao: Mapped[int] = mapped_column(Integer, default=0)
    colocacao: Mapped[Optional[int]] = mapped_column(Integer)
    data_inicio: Mapped[Optional[date]] = mapped_column(DATE)
    data_fim: Mapped[Optional[date]] = mapped_column(DATE)

    # Relacionamentos
    clan: Mapped[Optional["Clan"]] = relationship("Clan", back_populates="guerras")
    contribuicoes: Mapped[List["ContribuicaoGuerra"]] = relationship(
        "ContribuicaoGuerra", back_populates="guerra", cascade="all, delete-orphan"
    )


class ContribuicaoGuerra(Base):
    """
    Contribuição individual de cada jogador em uma guerra.
    O campo fame é a métrica principal do River Race.
    """
    __tablename__ = "contribuicoes_guerra"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    guerra_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("guerras.id", ondelete="CASCADE")
    )
    jogador_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("jogadores.id", ondelete="CASCADE")
    )
    batalhas: Mapped[int] = mapped_column(Integer, default=0)
    vitorias: Mapped[int] = mapped_column(Integer, default=0)
    fame: Mapped[int] = mapped_column(Integer, default=0)

    # Relacionamentos
    guerra: Mapped[Optional["Guerra"]] = relationship("Guerra", back_populates="contribuicoes")
    jogador: Mapped[Optional["Jogador"]] = relationship("Jogador", back_populates="contribuicoes")


class PartidaTorneio(Base):
    """
    Partidas individuais dos torneios escolares.
    Registra o confronto entre dois jogadores e o vencedor.
    """
    __tablename__ = "partidas_torneio"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    torneio_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("torneios.id", ondelete="CASCADE")
    )
    jogador_a_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("jogadores.id", ondelete="CASCADE")
    )
    jogador_b_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("jogadores.id", ondelete="CASCADE")
    )
    vencedor_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("jogadores.id", ondelete="SET NULL")
    )
    placar_a: Mapped[int] = mapped_column(Integer, default=0)
    placar_b: Mapped[int] = mapped_column(Integer, default=0)
    data_partida: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP)

    # Relacionamentos
    torneio: Mapped[Optional["Torneio"]] = relationship("Torneio", back_populates="partidas")
    jogador_a: Mapped[Optional["Jogador"]] = relationship(
        "Jogador", foreign_keys=[jogador_a_id]
    )
    jogador_b: Mapped[Optional["Jogador"]] = relationship(
        "Jogador", foreign_keys=[jogador_b_id]
    )
    vencedor: Mapped[Optional["Jogador"]] = relationship(
        "Jogador", foreign_keys=[vencedor_id]
    )
