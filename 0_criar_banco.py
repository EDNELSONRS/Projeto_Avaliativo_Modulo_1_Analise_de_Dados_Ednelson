"""Recria o banco e inicializa as tabelas definidas no arquivo SQL."""
from __future__ import annotations

import re
import sys
from contextlib import closing
from pathlib import Path

import psycopg2
from psycopg2.errors import ObjectInUse

from banco import settings as obter_configuracao
from config import POSTGRES_CONFIG, ROOT_DIR


def ler_script(arquivo: Path, banco: str) -> tuple[list[str], str]:
    """Valida e separa a administração do banco da criação das tabelas."""
    if not re.fullmatch(r"[a-z_][a-z0-9_]{0,62}", banco):
        raise ValueError("O nome do banco deve ser um identificador simples.")
    if banco in {"postgres", "template0", "template1"}:
        raise ValueError("Configure um banco dedicado para este projeto.")

    conteudo = arquivo.read_text(encoding="utf-8-sig")
    conexoes = list(re.finditer(
        r"(?m)^\\connect[ \t]+([a-z_][a-z0-9_]*)[ \t]*$", conteudo
    ))
    if len(conexoes) != 1:
        raise ValueError("O SQL deve conter um único comando \\connect.")
    conexao = conexoes[0]
    if conexao.group(1) != banco:
        raise ValueError(
            "O nome do banco no SQL deve ser igual a POSTGRES_DATABASE "
            "no arquivo .env."
        )

    linhas = []
    for linha in conteudo[:conexao.start()].splitlines():
        linha = linha.strip()
        if not linha or linha.startswith("--"):
            continue
        if linha == r"\set ON_ERROR_STOP on":
            continue
        linhas.append(linha)
    comandos = [
        " ".join(parte.split())
        for parte in "\n".join(linhas).split(";") if parte.strip()
    ]
    esperados = [
        f"DROP DATABASE IF EXISTS {banco}",
        f"CREATE DATABASE {banco} TEMPLATE template0",
    ]
    normalizados = [comando.casefold() for comando in comandos]
    if normalizados != [comando.casefold() for comando in esperados]:
        raise ValueError(
            "O início do SQL deve conter somente DROP DATABASE IF EXISTS "
            "e CREATE DATABASE, usando o mesmo nome de banco."
        )
    tabelas = conteudo[conexao.end():].strip()
    if not tabelas or any(
        linha.lstrip().startswith("\\") for linha in tabelas.splitlines()
    ):
        raise ValueError("Bloco de criação das tabelas ausente ou inválido.")
    return comandos, tabelas


def main() -> int:
    banco = POSTGRES_CONFIG["dbname"]
    try:
        comandos, tabelas = ler_script(ROOT_DIR / "0_criar_banco.sql", banco)
        settings = obter_configuracao()
        settings.pop("dbname")
        # template1 permite administrar mesmo quando o banco postgres não existe.
        # O SQL cria o banco a partir de template0; esta conexão usa autocommit.
        with closing(psycopg2.connect(
            dbname="template1", **settings, connect_timeout=10
        )) as admin:
            admin.autocommit = True
            with admin.cursor() as cursor:
                for comando in comandos:
                    cursor.execute(comando)

        with closing(psycopg2.connect(
            dbname=banco, **settings, connect_timeout=10
        )) as conn:
            with conn:
                with conn.cursor() as cursor:
                    cursor.execute(tabelas)
    except ObjectInUse:
        print(
            f"O banco {banco!r} está em uso. Encerre o kernel do notebook "
            "e feche as conexões do pgAdmin ou psql antes de repetir.",
            file=sys.stderr,
        )
        return 1
    except (OSError, ValueError, RuntimeError, psycopg2.Error) as exc:
        print(f"Falha na criação do banco: {exc}", file=sys.stderr)
        return 1

    print(f"Banco {banco!r} recriado com as tabelas Raw e Silver.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
