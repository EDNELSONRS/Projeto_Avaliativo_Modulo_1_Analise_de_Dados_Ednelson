"""Confere as camadas do projeto sem modificar o banco de dados."""
from __future__ import annotations

import sys
from contextlib import closing

import psycopg2
from psycopg2 import sql

from banco import conectar

ENTIDADES = ("viagem", "pagamento", "passagem", "trecho")
OBJETOS_GOLD = (
    "gold_resumo_viagem", "gold_resumo_viagem_vw",
    "gold_pagamento_tipo_vw", "gold_transporte_vw",
    "gold_destino_uf_vw", "gold_orgao_pagador_vw",
)


def conferir() -> list[str]:
    """Usa uma transação somente de leitura para validar contagens e totais."""
    mensagens = []
    with closing(conectar()) as conn:
        conn.set_session(readonly=True)
        with conn:
            with conn.cursor() as cursor:
                tabelas = [
                    f"{camada}_{entidade}"
                    for camada in ("raw", "silver")
                    for entidade in ENTIDADES
                ]
                for objeto in tabelas + list(OBJETOS_GOLD):
                    cursor.execute("SELECT to_regclass(%s)", (objeto,))
                    if cursor.fetchone()[0] is None:
                        raise ValueError(
                            f"Objeto ausente: {objeto}. Execute as etapas "
                            "0, 1, 2 e o notebook nesta ordem."
                        )
                contagens = {}
                for tabela in tabelas:
                    cursor.execute(sql.SQL("SELECT COUNT(*) FROM {}").format(
                        sql.Identifier(tabela)
                    ))
                    contagens[tabela] = cursor.fetchone()[0]
                for entidade in ENTIDADES:
                    raw = contagens[f"raw_{entidade}"]
                    silver = contagens[f"silver_{entidade}"]
                    if raw == 0 or raw != silver:
                        raise ValueError(
                            f"Contagens não conciliadas em {entidade}: "
                            f"Raw={raw}, Silver={silver}."
                        )
                    mensagens.append(
                        f"{entidade}: Raw={raw:,} / Silver={silver:,}"
                    )
                cursor.execute("""
                    SELECT
                        (SELECT COUNT(*) FROM gold_resumo_viagem) =
                        (SELECT COUNT(*) FROM silver_viagem),
                        (SELECT COUNT(DISTINCT id_viagem)
                         FROM gold_resumo_viagem) =
                        (SELECT COUNT(*) FROM gold_resumo_viagem),
                        (SELECT SUM(valor_total) FROM gold_resumo_viagem) =
                        (SELECT SUM(valor_total) FROM silver_viagem),
                        (SELECT SUM(valor_pago) FROM gold_resumo_viagem) =
                        (SELECT SUM(valor) FROM silver_pagamento),
                        (SELECT SUM(quantidade_trechos)
                         FROM gold_resumo_viagem) =
                        (SELECT COUNT(*) FROM silver_trecho)
                """)
                if not all(cursor.fetchone()):
                    raise ValueError("Falha de reconciliação na camada Gold.")
                for entidade in ("pagamento", "passagem"):
                    cursor.execute(sql.SQL("""
                        SELECT COALESCE(SUM(quantidade - 1), 0)::BIGINT
                        FROM (
                            SELECT COUNT(*) AS quantidade
                            FROM {} r
                            GROUP BY r
                            HAVING COUNT(*) > 1
                        ) grupos
                    """).format(sql.Identifier(f"raw_{entidade}")))
                    repeticoes = cursor.fetchone()[0]
                    if repeticoes:
                        mensagens.append(
                            f"Aviso de qualidade: {entidade} possui "
                            f"{repeticoes:,} ocorrências excedentes com todos "
                            "os campos iguais na fonte. Preservadas por não "
                            "haver ID único ou regra para excluir eventos."
                        )
    mensagens.append("Gold: viagens únicas, contagens e totais conciliados.")
    return mensagens


def main() -> int:
    try:
        mensagens = conferir()
    except (RuntimeError, ValueError, psycopg2.Error) as exc:
        print(f"Verificação não concluída: {exc}", file=sys.stderr)
        return 1
    for mensagem in mensagens:
        print(mensagem)
    print("Verificação concluída sem alterar os dados.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
