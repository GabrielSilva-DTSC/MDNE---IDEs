# Etapa 1 — como rodar (21 vídeos sobre IDEs)
Comandos para Windows (PowerShell), na raiz do projeto, com o `.venv` ativo. No Linux/macOS: `source .venv/bin/activate`.

## 1. Ambiente (uma vez)
```powershell
python -m pip install -r requirements.txt
python -m spacy download pt_core_news_sm
python -m unittest discover -s tests -v          # 32 testes, sem rede
```

## 2. Chave da API
Arquivo `.env` na raiz, uma linha só, sem aspas nem espaços: `YOUTUBE_API_KEY=sua_chave_aqui`. Nunca mostre a chave em print ou commit.

## 3. Lista de vídeos: `dados/brutos/videos.csv`
Uma linha por vídeo, com `nome_video`, `link_video`, `n_comentarios_planilha`, `nome_canal` e `formato_video` (Normal ou Shorts). As colunas `foco_ide`, `grupo` e `escopo` (linguagem; Geral x Java x Outras) podem continuar no arquivo, mas a análise **as ignora**: ela é por IDE, não por tipo de vídeo. Para incluir um vídeo, acrescente uma linha. **Dois vídeos não podem ter o mesmo link:** o coletor e o `etapa1.py` avisam se isso acontecer, e um dos vídeos ficaria de fora.

## 4. Coletar
```powershell
python dados/brutos/bronze.py --arquivo-videos dados/brutos/videos.csv --limite 0 --orcamento 10000
```
- Coleta todos os vídeos da lista numa pasta nova em `dados/brutos/youtube/<execucao>/`. O teto de 10.000 unidades é dividido igualmente (com 21 vídeos, cerca de 476 requisições por vídeo).
- Confira o `manifesto.json`: cada vídeo com `status=concluido`. Vídeo com `encerramento=orcamento_atingido` ficou parcial.
- Se algum vídeo falhar, rode de novo só ele (ex.: `--videos https://youtu.be/ID`). A Etapa 1 junta todas as execuções e usa, para cada vídeo, a coleta mais recente que tenha comentários.
- Use sempre o **link completo** em `--videos`: um ID que começa com `-` (como `-pmU-NLUYCk`) é lido como opção e dá erro.

## 5. Rodar a Etapa 1
```powershell
python etapa1.py
```
- Junta todas as coletas, associa cada vídeo ao `videos.csv`, procura as IDEs citadas em cada comentário e avisa sobre links repetidos, títulos que não batem e contagens muito diferentes da planilha. **Leia os avisos**: eles mostram links errados.
- No final, o log precisa mostrar **`método: pysentimiento`**. Com `lexico_reserva`, o modelo não carregou e o resultado não vale para a apresentação.
- Para usar só uma execução: `python etapa1.py --entrada dados/brutos/youtube/<execucao>`.

Saídas:
- `dados/intermediarios/comentarios_limpos.csv`, `dados/processados/comentarios_sentimento.csv` e **`dados/processados/mencoes_ides.csv`** (uma linha por comentário × IDE, com o trecho analisado e o sentimento)
- `relatorio/tabelas/`: **`resumo_por_ide`** (ranking de citações, sentimento, saldo, ICs), **`termos_por_ide`**, **`exemplos_por_ide`**, `resumo_geral`, `resumo_por_video`, `resumo_por_tipo`, termos, emojis e entidades
- `relatorio/assets/`: **`ides_mais_citadas`**, **`sentimento_por_ide`**, **`intervalos_positivos_ide`**, sentimento por vídeo, distribuição do score, termos, entidades e nuvem de palavras
- `--min-mencoes N` (padrão 10): mínimo de comentários por IDE para entrar nos gráficos de sentimento.

### Como a análise por IDE funciona
- O catálogo de IDEs e seus apelidos (vscode, vs code, intellij, pycharm...) está em `src/preprocessamento/ides.py`. **Para incluir uma IDE, acrescente uma linha em `CATALOGO`.** Confira os nomes que aparecem em `top_entidades.csv` para achar IDEs que faltam.
- Uma **menção** é um comentário que cita a IDE. Se o comentário cita só uma, o sentimento é o do comentário inteiro; se cita várias, é o da frase (ou do trecho entre vírgulas/"mas") em que ela aparece. A coluna `escopo_texto` mostra qual regra valeu e `isolada` diz se o trecho cita só aquela IDE.
- Comentários que não citam nenhuma IDE ficam fora das tabelas por IDE (continuam no panorama geral).

## 6. Ver os resultados
Abra `notebooks/visualizacao.ipynb`, escolha o kernel do `.venv`, clique em **Clear All Outputs** e depois em **Run All**. A primeira célula mostra o total de comentários e o método.

## Teste sem a API (dados simulados)
```powershell
python etapa1.py --entrada tests/fixtures/execucao_exemplo --sem-modelo
```
Usa comentários **inventados** (vídeos `SIMULADO...`) e o léxico de reserva; serve só para conferir que o código roda. Depois, apague os arquivos gerados antes de rodar com dados reais:
```powershell
Remove-Item relatorio\assets\*.png, relatorio\tabelas\*.csv, dados\processados\*.csv, dados\intermediarios\*.csv
```

## Problemas comuns
| Erro | O que fazer |
|---|---|
| `FileNotFoundError` em `dados/brutos/youtube` | Falta a coleta: rodar o passo 4 |
| `ModuleNotFoundError` | Passo 1, com o `.venv` ativo e `python -m pip` |
| `null bytes` ou `field larger than field limit` ao importar ou instalar o transformers | Instalação corrompida: apagar `.venv\Lib\site-packages\transformers` e `transformers-*` e rodar `python -m pip install --no-cache-dir transformers`. Se persistir, recriar o ambiente com Python 3.12 |
| `error: argument --videos: expected at least one argument` | ID de vídeo começando com `-`: use o link completo |
| Erro 403 ou de chave | Conferir o `.env` e se a YouTube Data API v3 está ativada |
| `quotaExceeded` | A cota do dia acabou; renova à meia-noite no horário do Pacífico |
| Aviso "link ... aparece em 2 linhas" | Corrigir o link errado em `dados/brutos/videos.csv` e coletar de novo |
