# Passo a passo do projeto

## 1. Preparar a pasta

Extraia todos os arquivos do pacote em uma pasta nova, por exemplo:

```text
D:\PROJETOS FEITO PELO GPT\Projeto_Viagens_Entrega_2026
```

Os arquivos `README.md`, `requirements.txt` e `0_criar_banco.py` devem ficar
diretamente nessa pasta. Abra essa pasta no VS Code usando **Arquivo >
Abrir Pasta**. A pasta nova tem somente o código; dados e credenciais são
configurados nas próximas etapas.

## 2. Criar o ambiente Python

No VS Code, abra **Terminal > Novo Terminal** e execute:

```powershell
Set-Location "D:\PROJETOS FEITO PELO GPT\Projeto_Viagens_Entrega_2026"
py -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

O terminal deve mostrar `(.venv)`. A política de execução acima vale apenas
para o processo atual do PowerShell.

## 3. Configurar a conexão

```powershell
Copy-Item .env.example .env
```

Abra `.env` no VS Code. Substitua somente o marcador
`COLE_SUA_SENHA_AQUI` pela senha do seu PostgreSQL e salve. Se a senha
contiver `#` ou espaços, coloque o valor entre aspas simples.

O banco deve continuar com o nome `transparencia_viagens`. O ID do Drive
já está preenchido para permitir o download automático.

Para conferir a configuração e a conexão administrativa com `template1`:

```powershell
python -c "from banco import conectar; c=conectar('template1'); print('Conexao administrativa OK'); c.close()"
```

Se houver falha, confirme a senha, a porta, o serviço PostgreSQL e as
permissões do usuário. A senha salva no `.env` deve ser a mesma aceita
pelo PostgreSQL. Nunca envie a senha ao GitHub ou ao chat.

## 4. Recriar o banco do projeto

**Executar esta etapa apaga o banco `transparencia_viagens` inteiro.**
Feche o kernel de notebooks antigos e desconecte sessões do pgAdmin ou
psql que estejam usando esse banco. Faça cópia de segurança se precisar
guardar outros dados existentes nele.

```powershell
python 0_criar_banco.py
```

O resultado esperado informa que o banco foi recriado com as tabelas Raw
e Silver. Se o banco estiver em uso, o programa informa quais conexões
devem ser fechadas. Depois prossiga às cargas.

## 5. Baixar e carregar os dados Raw

```powershell
python 1_extrair.py
```

Na primeira execução, o ZIP é baixado automaticamente. Aguarde até o
programa informar as quatro cargas concluídas:

```text
2025_Viagem.csv: 341,860 linhas carregadas
2025_Pagamento.csv: 606,916 linhas carregadas
2025_Passagem.csv: 167,260 linhas carregadas
2025_Trecho.csv: 763,349 linhas carregadas
```

Se você já possui o arquivo correto, pode copiá-lo manualmente para
`data/viagens_2025_6meses.zip`. O script confere o ZIP antes de carregar.

## 6. Transformar para Silver

```powershell
python 2_transformar.py
```

As quatro tabelas Silver devem ter as mesmas contagens da etapa anterior.
As mensagens de conclusão são exibidas somente após confirmar a transação.

## 7. Executar a análise no VS Code

1. Abra `3_analise.ipynb`.
2. Clique em **Selecionar Kernel** e escolha **Ambientes do Python**.
3. Selecione o Python `.venv\Scripts\python.exe` dentro da pasta nova.
4. Use **Reiniciar Kernel e Executar Tudo**.
5. Aguarde as sete respostas, tabelas, gráficos e verificações finais.
6. Salve com **Ctrl+S** para manter as saídas no arquivo entregue.

Caso o ambiente não apareça, use **Python: Selecionar Interpretador** na
paleta de comandos e informe este caminho:

```text
D:\PROJETOS FEITO PELO GPT\Projeto_Viagens_Entrega_2026\.venv\Scripts\python.exe
```

Depois selecione esse mesmo ambiente no notebook.

O arquivo `gerar_notebook.py` é opcional. Executá-lo recria o notebook sem
resultados salvos; nesse caso, execute novamente todas as células e salve.

## 8. Conferir o pipeline

```powershell
python verificar_projeto.py
```

O resultado esperado informa as quatro contagens conciliadas e confirma
a Gold. Esse comando apenas lê o banco. Repetir extração, transformação e
notebook deve manter as mesmas contagens. A etapa 0 é usada para recriar
todo o banco; repita-a somente quando desejar reinicializar o projeto.

## 9. Criar o histórico Git da pasta nova

Faça esta etapa após executar, conferir e salvar o notebook. Execute um
bloco por vez. As mensagens dos commits descrevem os arquivos adicionados.
O PDF não estabelece uma quantidade mínima de commits.

```powershell
git init -b main
git config user.name (Read-Host "Seu nome para os commits")
git config user.email (Read-Host "Seu email do GitHub ou noreply")
git add .gitignore .env.example requirements.txt config.py banco.py
git commit -m "configura ambiente e conexao PostgreSQL"
```

Banco:

```powershell
git switch -c feature-banco
git add 0_criar_banco.sql 0_criar_banco.py
git commit -m "implementa recriacao do banco e tabelas"
git switch main
git merge --no-ff feature-banco -m "integra criacao do banco"
```

Extração:

```powershell
git switch -c feature-extracao
git add 1_extrair.py
git commit -m "implementa download e carga Raw"
git switch main
git merge --no-ff feature-extracao -m "integra extracao"
```

Transformação:

```powershell
git switch -c feature-transformacao
git add 2_transformar.py
git commit -m "implementa transformacao para Silver"
git switch main
git merge --no-ff feature-transformacao -m "integra transformacao"
```

Análise:

```powershell
git switch -c feature-analise
git add 3_analise.ipynb gerar_notebook.py verificar_projeto.py
git commit -m "adiciona Gold analises e verificacao"
git switch main
git merge --no-ff feature-analise -m "integra analises"
```

Documentação:

```powershell
git switch -c feature-documentacao
git add README.md GUIA_EXECUCAO.md
git commit -m "documenta configuracao execucao e entrega"
git switch main
git merge --no-ff feature-documentacao -m "integra documentacao"
git status --short
git --no-pager log --oneline --graph --all
```

O `git status --short` deve ficar sem saída. O gráfico deve mostrar as
branches e os commits correspondentes. `.env`, `.venv`, CSVs e ZIPs são
ignorados pelo `.gitignore`.

## 10. Publicar e entregar

Crie um repositório vazio no GitHub, copie sua URL HTTPS e execute:

```powershell
$urlRepositorio = Read-Host "Cole a URL HTTPS do novo repositorio GitHub"
git remote add origin $urlRepositorio
git push -u origin main
git push origin feature-banco feature-extracao feature-transformacao feature-analise feature-documentacao
git status --short
```

Abra o repositório no navegador e confira os scripts, SQL, README, notebook
com resultados e branches. Envie o link desse repositório no AVA, na
atividade **Módulo 1 - Projeto Avaliativo**, até **03/11/2026 às 22h**.
Depois da entrega, mantenha o repositório sem alterações até a correção.
