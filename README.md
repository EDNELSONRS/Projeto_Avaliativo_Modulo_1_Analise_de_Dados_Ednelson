# Análise de despesas com viagens a serviço

Projeto avaliativo de Análise de Dados com Python. O objetivo é transformar
dados de viagens a serviço do Governo Federal em informações sobre custos,
destinos, duração, pagamentos e meios de transporte.

O pipeline usa PostgreSQL e a arquitetura Medallion: Raw, Silver e Gold.
O guia [GUIA_EXECUCAO.md](GUIA_EXECUCAO.md) apresenta a execução no Windows
e o versionamento por funcionalidades.

## Tecnologias

Python 3.10 ou superior; PostgreSQL 13 ou superior; psycopg2, SQLAlchemy,
python-dotenv, gdown, pandas, Matplotlib, Seaborn, ipykernel e nbformat.
O notebook pode ser executado pelas extensões Python e Jupyter do VS Code.
Não é necessário instalar o JupyterLab para essa forma de execução.

## Dados de origem

A base da atividade contém viagens iniciadas entre janeiro e junho de 2025.
Algumas viagens terminam em 2026; essas datas são preservadas.

[Baixar a base fornecida no Google Drive](https://drive.google.com/file/d/1pQjKacyHdIsyteknQbwKGM5_4hL5V4RV/view).

O ID público do arquivo é `1pQjKacyHdIsyteknQbwKGM5_4hL5V4RV` e já está
preenchido no modelo de configuração. O ZIP contém:

- `2025_Viagem.csv`;
- `2025_Pagamento.csv`;
- `2025_Passagem.csv`;
- `2025_Trecho.csv`.

Os CSVs usam codificação Latin-1, separador `;`, vírgula decimal e datas
no formato `DD/MM/AAAA`. O download requer acesso público ao arquivo.

## Arquivos

| Arquivo | Função |
|---|---|
| `0_criar_banco.sql` | Remove e cria o banco nomeado e suas oito tabelas. |
| `0_criar_banco.py` | Executa as etapas do SQL nas conexões correspondentes. |
| `1_extrair.py` | Baixa e valida o ZIP e carrega as quatro tabelas Raw. |
| `2_transformar.py` | Converte os dados e popula as quatro tabelas Silver. |
| `3_analise.ipynb` | Responde às sete perguntas e constrói a camada Gold. |
| `config.py` | Define caminhos, configuração e o layout dos CSVs. |
| `banco.py` | Valida as credenciais e centraliza as conexões. |
| `verificar_projeto.py` | Confere contagens e totais sem modificar os dados. |
| `gerar_notebook.py` | Recria o notebook sem suas saídas; uso opcional. |
| `.env.example` | Modelo de configuração sem senha real. |
| `requirements.txt` | Dependências Python. |
| `GUIA_EXECUCAO.md` | Passo a passo de instalação, execução e Git. |

## Configuração

Abra a pasta do projeto no VS Code. No PowerShell, dentro dessa pasta:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Edite o `.env`, substituindo `COLE_SUA_SENHA_AQUI` pela senha do seu
PostgreSQL. A configuração padrão é:

```dotenv
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=COLE_SUA_SENHA_AQUI
POSTGRES_DATABASE=transparencia_viagens
DRIVE_FILE_ID=1pQjKacyHdIsyteknQbwKGM5_4hL5V4RV
```

As credenciais são lidas somente do `.env` da pasta deste projeto.
Cada pessoa usa a senha do próprio PostgreSQL. O nome do banco deve
corresponder ao nome explícito no SQL: `transparencia_viagens`.

O serviço PostgreSQL deve estar ativo. O usuário precisa de permissão para
criar bancos e ser proprietário de `transparencia_viagens` quando ele existe.

## Execução

### 0. Criar o banco e as tabelas

**Esta etapa remove todo o banco `transparencia_viagens` e seus dados.**
Use um banco dedicado ao projeto. Feche conexões de notebooks, pgAdmin e
psql com esse banco antes de executá-la.

```powershell
python 0_criar_banco.py
```

O SQL contém `DROP DATABASE IF EXISTS transparencia_viagens`,
`CREATE DATABASE transparencia_viagens TEMPLATE template0`, a troca de
conexão e os oito `CREATE TABLE`. Os antigos DROP VIEW e DROP TABLE foram
retirados dessa etapa conforme a orientação do professor.

O Python executa DROP e CREATE separadamente em uma conexão administrativa
com `template1`, em autocommit. Assim, não depende da existência do banco
administrativo `postgres`. Depois abre uma conexão no banco criado e
executa a criação das tabelas em uma transação. A remoção do banco não pode
ser desfeita por rollback. [Documentação do PostgreSQL](https://www.postgresql.org/docs/18/sql-dropdatabase.html).

Para executar o SQL diretamente pelo psql no Windows:

```powershell
& "C:\Program Files\PostgreSQL\18\bin\psql.exe" -X -h localhost -p 5432 -U postgres -d template1 -W -f .\0_criar_banco.sql
```

As linhas `\set ON_ERROR_STOP on` e `\connect transparencia_viagens`
são comandos do psql: interrompem o script em caso de erro e mudam para
o banco recém-criado. No Query Tool do pgAdmin, execute DROP e CREATE
separadamente na conexão com `template1`; depois abra uma conexão com
`transparencia_viagens` e execute somente o bloco CREATE TABLE/CREATE INDEX.

### 1. Extrair para Raw

```powershell
python 1_extrair.py
```

Sem o ZIP local, o script faz o download automático pelo ID do Drive.
O download é temporário e só é publicado em
`data/viagens_2025_6meses.zip` após validar integridade, membros e cabeçalhos.
O ZIP local também é validado antes de conectar ao banco.

As quatro Raw mantêm todas as colunas originais como `VARCHAR`, sem
restrições. COPY transmite o conteúdo progressivamente, sem carregar o
CSV inteiro em memória. Os quatro TRUNCATE/COPY usam uma única transação.
Uma falha reverte a carga e retorna código de saída diferente de zero.

### 2. Transformar para Silver

```powershell
python 2_transformar.py
```

São convertidos textos, datas, inteiros e decimais. Silver possui chaves
primárias, estrangeiras e as restrições adicionais do enunciado.

```text
valor_total = valor_diarias + valor_passagens + valor_outros_gastos - valor_devolucao
duracao_dias = data_fim - data_inicio
```

Somente na composição do total, componentes ausentes contam como zero.
Os campos individuais continuam nulos quando não informados. A duração
não acrescenta um dia à diferença entre as datas.

A transformação ignora viagens sem identificador, pagamentos sem tipo e
registros filhos sem viagem correspondente. A conferência de contagens
permite detectar essas exclusões em uma fonte diferente da fornecida.
Todos os TRUNCATE/INSERT são executados em uma única transação.

### 3. Executar o notebook

Abra `3_analise.ipynb`, selecione o Python de `.venv`, reinicie o kernel
e use **Executar Tudo**. Salve o notebook com as tabelas e gráficos.
O notebook constrói Gold a partir de Silver; não recarrega Raw ou Silver.

As três primeiras perguntas consultam Silver. A tabela
`gold_resumo_viagem` e sua view têm uma linha por viagem; pagamentos,
passagens e trechos são agregados antes das junções para evitar
multiplicação de valores. Quatro views Gold agrupam pagamentos por tipo,
transporte, UF e órgão pagador. As perguntas 4 a 7 consultam essas views.

### 4. Conferir o resultado

```powershell
python verificar_projeto.py
```

A verificação usa uma transação somente de leitura. Compara Raw e Silver,
confere os seis objetos Gold, a unicidade das viagens e os totais agregados.

## Perguntas de negócio

1. Quais são os cinco órgãos superiores com maior custo total?
2. Quais são os três destinos com maior custo médio por viagem?
3. Qual foi a viagem de maior duração e qual foi seu custo total?
4. Qual tipo de pagamento apresenta o maior valor médio?
5. Qual meio de transporte aparece mais nos trechos?
6. Qual UF de destino aparece em mais trechos?
7. Qual órgão pagador apresenta o maior total pago?

## Resultados da base fornecida

| Entidade | Raw | Silver |
|---|---:|---:|
| Viagem | 341.860 | 341.860 |
| Pagamento | 606.916 | 606.916 |
| Passagem | 167.260 | 167.260 |
| Trecho | 763.349 | 763.349 |

São 1.879.385 registros em cada camada e 341.860 viagens na tabela de
resumo Gold. As sete respostas são apresentadas nas tabelas do notebook.

| Indicador | Resultado |
|---|---|
| Maior custo por órgão superior | Ministério da Justiça e Segurança Pública: R$ 486.933.121,65. |
| Maior custo médio por roteiro | Abu Dabi/Emirados Árabes, Riad/Arábia Saudita, Rio de Janeiro/RJ: R$ 245.852,80, uma viagem. |
| Maior duração | Processo 0000000000020699856: 383 dias; custo registrado de R$ 0,00. |
| Maior média por tipo de pagamento | DIÁRIAS: R$ 2.078,28 por registro. |
| Transporte mais frequente | Veículo Oficial: 386.424 trechos. |
| UF de destino mais frequente | São Paulo: 82.722 ocorrências em trechos. |
| Maior total por órgão pagador | Fundo Nacional de Segurança Pública: R$ 278.481.047,89. |

## Interpretação e limites

O custo por órgão superior mede custos líquidos das viagens. O total por
órgão pagador mede os registros de pagamento: são medidas diferentes e não
devem ser somadas entre si. Os rankings isolados não demonstram eficiência
ou causalidade.

Na pergunta 2, destino corresponde ao texto completo do roteiro; o custo
não é repartido entre cidades. Cada um dos três roteiros vencedores tem
uma viagem, o que limita a generalização da média. Os códigos Roteiro 1,
2 e 3 no gráfico correspondem aos textos completos da tabela.

O custo zero da viagem mais longa é um valor registrado na fonte e não
comprova ausência de despesas. Duração e custo são exibidos separadamente,
com unidades próprias. Campos opcionais vazios são preservados como
ausentes; a categoria de transporte `Inválido` é mantida nas contagens.

## Melhorias futuras

- Retentativas controladas para falhas transitórias no download.
- Logs persistentes com duração das etapas e registros rejeitados.
- Normalização dos destinos para análises por cidade.
- Comparações mensais e análise de custos considerando volume de viagens.

## Versionamento e entrega

Versione os scripts, SQL, notebook com saídas, documentação, dependências,
`.env.example` e `.gitignore`. As pastas de dados e ambiente virtual,
o `.env` e os ZIPs ficam fora do Git. O guia apresenta branches por
funcionalidade e commits com mensagens específicas.

A entrega solicitada é o link do repositório GitHub na atividade
**Módulo 1 - Projeto Avaliativo**, no AVA, até **03/11/2026 às 22h**.
Depois de entregar, mantenha o repositório sem alterações até a correção.
