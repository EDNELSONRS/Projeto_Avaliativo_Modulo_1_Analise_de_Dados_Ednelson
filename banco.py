"""Conexões PostgreSQL compartilhadas pelos scripts e pelo notebook."""

from __future__ import annotations

import psycopg2
from psycopg2.extensions import connection as Conexao
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine, URL

from config import ENV_PATH, POSTGRES_CONFIG


def settings(database: str | None = None) -> dict:
    """Valide e devolva uma cópia das opções, sem exibir a senha."""
    if not ENV_PATH.is_file():
        raise RuntimeError(
            "Arquivo .env não encontrado na pasta do projeto. Copie "
            ".env.example para .env e informe sua senha local do PostgreSQL."
        )

    configuracao = POSTGRES_CONFIG.copy()
    if database is not None:
        configuracao["dbname"] = database

    senha = configuracao["password"]
    if not senha.strip() or senha.strip() == "COLE_SUA_SENHA_AQUI":
        raise RuntimeError(
            "Defina sua senha local em POSTGRES_PASSWORD no arquivo .env. "
            "Substitua COLE_SUA_SENHA_AQUI antes de conectar. "
            "Não informe a senha no .env.example nem a envie ao GitHub."
        )

    for chave, nome in (
        ("host", "POSTGRES_HOST"),
        ("user", "POSTGRES_USER"),
        ("dbname", "POSTGRES_DATABASE"),
    ):
        if not configuracao[chave].strip():
            raise RuntimeError(f"Preencha {nome} no arquivo .env.")
    return configuracao


def conectar(database: str | None = None) -> Conexao:
    """Abra uma conexão; o chamador deve fechá-la em um bloco finally."""
    configuracao = settings(database)
    return psycopg2.connect(**configuracao, connect_timeout=10)


def motor(database: str | None = None) -> Engine:
    """Crie o motor; o chamador deve fechar conexões e chamar dispose()."""
    configuracao = settings(database)
    url = URL.create(
        "postgresql+psycopg2",
        username=configuracao["user"],
        password=configuracao["password"],
        host=configuracao["host"],
        port=configuracao["port"],
        database=configuracao["dbname"],
    )
    return create_engine(
        url,
        pool_pre_ping=True,
        connect_args={"connect_timeout": 10},
        hide_parameters=True,
    )
