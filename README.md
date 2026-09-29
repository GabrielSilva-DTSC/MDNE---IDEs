# Reddit-IDE

Projeto de modelagem de dados não estruturados com dados do Reddit.

## Estrutura

- `dados/brutos/`: dados coletados sem alterações.
- `dados/intermediarios/`: dados após etapas parciais de tratamento.
- `dados/processados/`: dados prontos para análise e modelagem.
- `src/coleta/reddit.py`: coleta de dados da API do Reddit.
- `src/preprocessamento/`: limpeza de texto, identificação de idioma e tratamento de emojis.
- `src/modelagem/sentimentos.py`: modelagem de sentimentos.
- `src/analise/estatisticas.py`: análises estatísticas.
- `diario_de_bordo/`: registros do andamento do projeto.
- `relatorio/`: resultados e relatório final.
- `notebooks/`: análises exploratórias em Jupyter.

Os arquivos em `src/` são pontos de partida. As etapas de coleta, tratamento e modelagem ainda precisam ser implementadas.

## Configuração

1. Ative o ambiente virtual existente: `source .venv/bin/activate`.
2. Instale as dependências após defini-las em `requirements.txt`: `pip install -r requirements.txt`.
3. Preencha `REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET` e `REDDIT_USER_AGENT` no arquivo `.env`. Use `.env.example` como referência. O `.env` não é versionado.
