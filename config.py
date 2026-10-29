"""Caminhos, layout dos CSVs e configuração local do projeto."""

from __future__ import annotations

from pathlib import Path

from dotenv import dotenv_values

ROOT_DIR = Path(__file__).resolve().parent
ENV_PATH = ROOT_DIR / ".env"
DATA_DIR = ROOT_DIR / "data"
DATASET_ZIP = DATA_DIR / "viagens_2025_6meses.zip"

# O arquivo desta pasta é a fonte de configuração. Variáveis antigas do
# terminal e arquivos .env de outros projetos não substituem estes valores.
# A interpolação é desativada para preservar senhas com caracteres como ${}.
_AMBIENTE = dotenv_values(
    ENV_PATH,
    encoding="utf-8-sig",
    interpolate=False,
)


def _valor_local(nome: str, padrao: str) -> str:
    """Leia uma opção do .env local sem consultar o ambiente do terminal."""
    valor = _AMBIENTE.get(nome)
    return padrao if valor is None else valor


def _porta_local() -> int:
    """Valide a porta sem abrir uma conexão com o PostgreSQL."""
    try:
        porta = int(_valor_local("POSTGRES_PORT", "5432"))
    except ValueError as erro:
        raise ValueError(
            "POSTGRES_PORT no .env deve ser um número, por exemplo 5432."
        ) from erro
    if not 1 <= porta <= 65535:
        raise ValueError("POSTGRES_PORT no .env deve estar entre 1 e 65535.")
    return porta


POSTGRES_CONFIG = {
    "host": _valor_local("POSTGRES_HOST", "localhost"),
    "port": _porta_local(),
    "user": _valor_local("POSTGRES_USER", "postgres"),
    "password": _valor_local("POSTGRES_PASSWORD", ""),
    "dbname": _valor_local("POSTGRES_DATABASE", "transparencia_viagens"),
}
DRIVE_FILE_ID = _valor_local(
    "DRIVE_FILE_ID", "1pQjKacyHdIsyteknQbwKGM5_4hL5V4RV"
).strip()
TAMANHO_BLOCO = 50_000

ARQUIVOS = {
    "2025_Viagem.csv": {
        "tabela_raw": "raw_viagem",
        "colunas_raw": [
            "id_viagem", "num_proposta", "situacao", "viagem_urgente",
            "justificativa_urgencia_viagem", "cod_orgao_superior",
            "nome_orgao_superior", "cod_orgao_solicitante",
            "nome_orgao_solicitante", "cpf_viajante", "nome_viajante",
            "cargo", "funcao", "descricao_funcao", "data_inicio", "data_fim",
            "destinos", "motivo", "valor_diarias", "valor_passagens",
            "valor_devolucao", "valor_outros_gastos",
        ],
        "cabecalho_csv": [
            "Identificador do processo de viagem", "Número da Proposta (PCDP)",
            "Situação", "Viagem Urgente", "Justificativa Urgência Viagem",
            "Código do órgão superior", "Nome do órgão superior",
            "Código órgão solicitante", "Nome órgão solicitante",
            "CPF viajante",
            "Nome", "Cargo", "Função", "Descrição Função",
            "Período - Data de início", "Período - Data de fim", "Destinos",
            "Motivo", "Valor diárias", "Valor passagens", "Valor devolução",
            "Valor outros gastos",
        ],
    },
    "2025_Pagamento.csv": {
        "tabela_raw": "raw_pagamento",
        "colunas_raw": [
            "id_viagem", "num_proposta", "cod_orgao_superior",
            "nome_orgao_superior", "codigo_orgao_pagador",
            "nome_orgao_pagador", "codigo_ug_pagadora", "nome_ug_pagadora",
            "tipo_pagamento", "valor",
        ],
        "cabecalho_csv": [
            "Identificador do processo de viagem", "Número da Proposta (PCDP)",
            "Código do órgão superior", "Nome do órgão superior",
            "Codigo do órgão pagador", "Nome do órgao pagador",
            "Código da unidade gestora pagadora",
            "Nome da unidade gestora pagadora", "Tipo de pagamento", "Valor",
        ],
    },
    "2025_Passagem.csv": {
        "tabela_raw": "raw_passagem",
        "colunas_raw": [
            "id_viagem", "num_proposta", "meio_transporte", "pais_origem_ida",
            "uf_origem_ida", "cidade_origem_ida", "pais_destino_ida",
            "uf_destino_ida", "cidade_destino_ida", "pais_origem_volta",
            "uf_origem_volta", "cidade_origem_volta", "pais_destino_volta",
            "uf_destino_volta", "cidade_destino_volta", "valor_passagem",
            "taxa_servico", "data_emissao", "hora_emissao",
        ],
        "cabecalho_csv": [
            "Identificador do processo de viagem", "Número da Proposta (PCDP)",
            "Meio de transporte", "País - Origem ida", "UF - Origem ida",
            "Cidade - Origem ida", "País - Destino ida", "UF - Destino ida",
            "Cidade - Destino ida", "País - Origem volta", "UF - Origem volta",
            "Cidade - Origem volta", "Pais - Destino volta",
            "UF - Destino volta",
            "Cidade - Destino volta", "Valor da passagem", "Taxa de serviço",
            "Data da emissão/compra", "Hora da emissão/compra",
        ],
    },
    "2025_Trecho.csv": {
        "tabela_raw": "raw_trecho",
        "colunas_raw": [
            "id_viagem", "num_proposta", "sequencia_trecho", "origem_data",
            "origem_pais", "origem_uf", "origem_cidade", "destino_data",
            "destino_pais", "destino_uf", "destino_cidade", "meio_transporte",
            "numero_diarias", "missao",
        ],
        "cabecalho_csv": [
            "Identificador do processo de viagem", "Número da Proposta (PCDP)",
            "Sequência Trecho", "Origem - Data", "Origem - País",
            "Origem - UF", "Origem - Cidade", "Destino - Data",
            "Destino - País", "Destino - UF", "Destino - Cidade",
            "Meio de transporte", "Número Diárias", "Missao?",
        ],
    },
}
