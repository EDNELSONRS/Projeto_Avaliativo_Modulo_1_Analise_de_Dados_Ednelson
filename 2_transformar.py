"""Converte as strings Raw em registros Silver tipados e preserva nulos."""

from __future__ import annotations

import sys
from contextlib import closing

import psycopg2
from psycopg2 import sql

from banco import conectar

TABELAS_SILVER = (
    "silver_viagem",
    "silver_pagamento",
    "silver_passagem",
    "silver_trecho",
)


def num(col: str) -> str:
    """Converte decimal brasileiro; campo vazio continua NULL."""
    return (
        f"NULLIF(REPLACE(REPLACE(BTRIM({col}), '.', ''),\n"
        "        ',', '.'), '')::NUMERIC(12, 2)"
    )


def data(col: str) -> str:
    """Converte a data DD/MM/AAAA; campo vazio continua NULL."""
    return f"TO_DATE(NULLIF(BTRIM({col}), ''), 'DD/MM/YYYY')"


SQL = f"""
TRUNCATE TABLE
    silver_trecho,
    silver_passagem,
    silver_pagamento,
    silver_viagem
RESTART IDENTITY CASCADE;

INSERT INTO silver_viagem (
    id_viagem,
    num_proposta,
    situacao,
    viagem_urgente,
    cod_orgao_superior,
    nome_orgao_superior,
    nome_viajante,
    cargo,
    data_inicio,
    data_fim,
    destinos,
    motivo,
    valor_diarias,
    valor_passagens,
    valor_devolucao,
    valor_outros_gastos,
    valor_total,
    duracao_dias
)
SELECT
    NULLIF(BTRIM(id_viagem), ''),
    NULLIF(BTRIM(num_proposta), ''),
    NULLIF(BTRIM(situacao), ''),
    NULLIF(BTRIM(viagem_urgente), ''),
    NULLIF(BTRIM(cod_orgao_superior), ''),
    NULLIF(BTRIM(nome_orgao_superior), ''),
    NULLIF(BTRIM(nome_viajante), ''),
    NULLIF(BTRIM(cargo), ''),
    {data('data_inicio')},
    {data('data_fim')},
    NULLIF(BTRIM(destinos), ''),
    NULLIF(BTRIM(motivo), ''),
    {num('valor_diarias')},
    {num('valor_passagens')},
    {num('valor_devolucao')},
    {num('valor_outros_gastos')},
    COALESCE(
        {num('valor_diarias')}, 0
    )
    + COALESCE(
        {num('valor_passagens')}, 0
    )
    + COALESCE(
        {num('valor_outros_gastos')}, 0
    )
    - COALESCE(
        {num('valor_devolucao')}, 0
    ),
    CASE
        WHEN {data('data_inicio')} IS NOT NULL
            AND {data('data_fim')} IS NOT NULL
        THEN
            {data('data_fim')}
            - {data('data_inicio')}
    END
FROM raw_viagem
WHERE NULLIF(BTRIM(id_viagem), '') IS NOT NULL;

INSERT INTO silver_pagamento (
    id_viagem,
    num_proposta,
    nome_orgao_pagador,
    nome_ug_pagadora,
    tipo_pagamento,
    valor
)
SELECT
    r.id_viagem,
    NULLIF(BTRIM(r.num_proposta), ''),
    NULLIF(BTRIM(r.nome_orgao_pagador), ''),
    NULLIF(BTRIM(r.nome_ug_pagadora), ''),
    NULLIF(BTRIM(r.tipo_pagamento), ''),
    {num('r.valor')}
FROM raw_pagamento r
JOIN silver_viagem v ON v.id_viagem = r.id_viagem
WHERE NULLIF(BTRIM(r.tipo_pagamento), '') IS NOT NULL;

INSERT INTO silver_passagem (
    id_viagem,
    meio_transporte,
    pais_origem_ida,
    uf_origem_ida,
    cidade_origem_ida,
    pais_destino_ida,
    uf_destino_ida,
    cidade_destino_ida,
    valor_passagem,
    taxa_servico,
    data_emissao
)
SELECT
    r.id_viagem,
    NULLIF(BTRIM(r.meio_transporte), ''),
    NULLIF(BTRIM(r.pais_origem_ida), ''),
    NULLIF(BTRIM(r.uf_origem_ida), ''),
    NULLIF(BTRIM(r.cidade_origem_ida), ''),
    NULLIF(BTRIM(r.pais_destino_ida), ''),
    NULLIF(BTRIM(r.uf_destino_ida), ''),
    NULLIF(BTRIM(r.cidade_destino_ida), ''),
    {num('r.valor_passagem')},
    {num('r.taxa_servico')},
    {data('r.data_emissao')}
FROM raw_passagem r
JOIN silver_viagem v ON v.id_viagem = r.id_viagem;

INSERT INTO silver_trecho (
    id_viagem,
    sequencia_trecho,
    origem_data,
    origem_uf,
    origem_cidade,
    destino_data,
    destino_uf,
    destino_cidade,
    meio_transporte,
    numero_diarias
)
SELECT
    r.id_viagem,
    NULLIF(BTRIM(r.sequencia_trecho), '')::INTEGER,
    {data('r.origem_data')},
    NULLIF(BTRIM(r.origem_uf), ''),
    NULLIF(BTRIM(r.origem_cidade), ''),
    {data('r.destino_data')},
    NULLIF(BTRIM(r.destino_uf), ''),
    NULLIF(BTRIM(r.destino_cidade), ''),
    NULLIF(BTRIM(r.meio_transporte), ''),
    {num('r.numero_diarias')}
FROM raw_trecho r
JOIN silver_viagem v ON v.id_viagem = r.id_viagem;
"""


def transformar_silver() -> dict[str, int]:
    """Recria as quatro Silver em uma transação e fecha a conexão."""
    contagens = {}
    with closing(conectar()) as conn:
        with conn:
            with conn.cursor() as cur:
                cur.execute(SQL)
                for tabela in TABELAS_SILVER:
                    cur.execute(
                        sql.SQL("SELECT COUNT(*) FROM {}").format(
                            sql.Identifier(tabela)
                        )
                    )
                    contagens[tabela] = cur.fetchone()[0]
    return contagens


def main() -> int:
    """Mostra as contagens somente depois da confirmação da transação."""
    try:
        contagens = transformar_silver()
    except (psycopg2.Error, UnicodeError, OSError, ValueError, RuntimeError) as exc:
        print(f"Falha na transformação: {exc}", file=sys.stderr)
        return 1
    for tabela, quantidade in contagens.items():
        print(f"{tabela}: {quantidade:,} linhas")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
