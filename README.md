# Análise de sentimentos e semântica em comentários do YouTube

Projeto acadêmico de modelagem de dados não estruturados a partir de comentários públicos de vídeos do YouTube. A coleta usa a YouTube Data API v3. A Etapa 1 realiza limpeza, identificação de idioma, processamento spaCy, análise de sentimento e análise de menções a IDEs. A Etapa 2 amplia o fluxo com análise semântica, embeddings e classificação opcional com Transformers.

## Estrutura do projeto

- `dados/brutos/`: dados coletados sem alterações; coletas não devem ser incluídas no Git.
- `dados/intermediarios/`: resultados de etapas parciais de tratamento.
- `dados/processados/`: dados prontos para análise e modelagem.
- `dados/brutos/bronze.py`: coletor de comentários pela YouTube Data API v3.
- `src/preprocessamento/`: limpeza, detecção de idioma, tratamento de emojis, spaCy e análise semântica.
- `src/modelagem/`: análise de sentimento, embeddings e integração com Transformers.
- `src/analise/`: estatísticas, análises por IDE e gráficos.
- `etapa1.py`: fluxo original da primeira etapa.
- `etapa2.py`: fluxo semântico da segunda etapa.
- `app.py`: painel Streamlit para explorar resultados da Etapa 1.
- `docs/ETAPA2.md`: guia detalhado da Etapa 2.
- `tests/`: testes automatizados, incluindo fixtures simuladas sem uso da API.

## Requisitos e instalação

Recomenda-se Python 3.10 ou superior. Crie e ative um ambiente virtual:

```bash
python -m venv .venv
# Linux/macOS
source .venv/bin/activate
# Windows PowerShell
.venv\Scripts\Activate.ps1
```

Instale os pacotes da aplicação e o modelo português do spaCy:

```bash
python -m pip install -r requirements.txt
python -m spacy download pt_core_news_sm
```

Para a coleta real, configure uma chave da YouTube Data API v3 no arquivo `.env` na raiz do projeto ou na variável de ambiente `YOUTUBE_API_KEY`:

```env
YOUTUBE_API_KEY=sua_chave_aqui
```

Não compartilhe nem faça commit da chave. O arquivo `.env` é ignorado pelo Git.

## Coleta de comentários

A coleta é executada a partir da raiz do projeto:

```bash
python dados/brutos/bronze.py
```

Para processar uma lista de vídeos, configure `dados/brutos/videos.csv` conforme as opções aceitas pelo coletor e use, por exemplo:

```bash
python dados/brutos/bronze.py --arquivo-videos dados/brutos/videos.csv --limite 0 --orcamento 10000
```

Uma amostra pequena para validar o fluxo:

```bash
python dados/brutos/bronze.py --limite 20
```

O limite e o orçamento restringem a quantidade de dados/requisições por execução; `--limite 0` tenta obter todos os comentários disponíveis dentro do orçamento. Cada execução cria uma pasta em `dados/brutos/youtube/<execucao>/`, com arquivos JSON e CSV por vídeo e um manifesto. A API pode retornar respostas junto aos comentários principais; o recorte coletado não deve ser interpretado automaticamente como os comentários mais recentes de toda a conversa. Consulte a documentação do coletor e o manifesto para verificar o status e o encerramento da coleta.

## Etapa 1 — sentimento e análise por IDE

Execute o processamento padrão sobre as coletas disponíveis:

```bash
python etapa1.py
```

Para processar apenas uma execução:

```bash
python etapa1.py --entrada dados/brutos/youtube/<execucao>
```

A opção `--sem-modelo` ativa um léxico de reserva para testes; esses resultados não devem ser apresentados como classificação final. Para uma execução de teste com dados fictícios:

```bash
python etapa1.py --entrada tests/fixtures/execucao_exemplo --sem-modelo
```

O fluxo da Etapa 1 associa metadados, limpa comentários, identifica idioma, processa texto com spaCy, classifica sentimento e extrai menções a IDEs. O catálogo de nomes e aliases está em `src/preprocessamento/ides.py`. Entre os resultados ficam `dados/processados/comentarios_sentimento.csv`, `dados/processados/mencoes_ides.csv`, tabelas e gráficos em `relatorio/`.

O painel pode ser iniciado após gerar os dados:

```bash
streamlit run app.py
```

## Etapa 2 — análise semântica, embeddings e Transformers

A Etapa 2 preserva o fluxo e os resultados existentes da Etapa 1. Ela grava um resultado separado em `dados/processados/comentarios_etapa2.csv`.

### Instalação opcional de embeddings e Transformers

O pipeline linguístico spaCy e o classificador de sentimento já usados pelo projeto usam `requirements.txt`. Embeddings e classificação adicional via Hugging Face são opcionais e podem exigir bastante espaço em disco para PyTorch e os modelos:

```bash
python -m pip install -r requirements-etapa2.txt
```

Os modelos são baixados na primeira execução que os solicita. Para ambientes sem rede, baixe os modelos previamente e configure um caminho local quando aplicável.

### Executar a Etapa 2

```bash
# spaCy semântico e sentimento principal
python etapa2.py

# Gerar embeddings semânticos; arquivo NPZ separado do CSV
python etapa2.py --embeddings

# Acrescentar previsões do classificador Transformers
python etapa2.py --transformer

# Pipeline completo
python etapa2.py --embeddings --transformer
```

Para usar uma única execução e um caminho de saída específico:

```bash
python etapa2.py --entrada dados/brutos/youtube/<execucao> \
  --saida dados/processados/etapa2.csv --embeddings --transformer
```

Para executar com a fixture sem carregar o modelo principal de sentimento:

```bash
python etapa2.py --entrada tests/fixtures/execucao_exemplo --sem-modelo-sentimento
```

### Saídas e interpretação

- `sentencas`, `termos_semanticos`, `entidades_semanticas` e `relacoes_sintaticas` são dados JSON serializados em colunas do CSV. As relações sujeito/verbo/complemento são pistas sintáticas aproximadas, não fatos validados.
- As colunas de sentimento sem sufixo `_transformer` correspondem ao classificador principal existente. Comentários fora do recorte de idioma ficam sem classificação.
- `--transformer` acrescenta colunas como `sentimento_transformer` e `score_transformer`; esta previsão é adicional e não substitui silenciosamente o resultado da Etapa 1.
- `--embeddings` cria um arquivo NPZ ao lado do CSV, contendo IDs dos comentários, vetores normalizados e identificação do modelo. Como os vetores estão normalizados, o produto escalar entre dois vetores equivale à similaridade cosseno.
- Probabilidades/confianças de modelos diferentes não são necessariamente calibradas nem diretamente comparáveis. Valide os resultados com amostras rotuladas antes de tirar conclusões.

Detalhes de implementação, opções e exemplos de leitura do NPZ estão em [`docs/ETAPA2.md`](docs/ETAPA2.md).

## Testes

Os testes usam dados simulados e não precisam da chave da YouTube API:

```bash
python -m unittest discover -s tests -v
```

Os testes da Etapa 2 simulam o processamento spaCy e não baixam modelos. A validação ponta a ponta da etapa requer instalar o modelo `pt_core_news_sm`; os recursos de embeddings e Transformers também precisam de suas dependências opcionais e dos modelos correspondentes.

## Limitações metodológicas

- A análise por IDE depende do catálogo de nomes/aliases, e comentários sem menções explícitas a nomes reconhecidos não entram na análise por IDE.
- Classificadores de sentimento podem errar em ironia, negação, comparações, gírias e comentários curtos. Leia os resultados como estimativas e valide uma amostra manualmente.
- Embeddings representam similaridade semântica aproximada; não são rótulos nem evidência causal.
- A coleta da API é uma amostra sujeita a disponibilidade de comentários, ordenação, paginação, orçamento e limites definidos na execução.
- Consulte o manifesto de cada coleta e registre os parâmetros de amostragem usados na metodologia do trabalho.

## Referências

- [YouTube Data API — commentThreads.list](https://developers.google.com/youtube/v3/docs/commentThreads/list)
- [YouTube Data API — comments.list](https://developers.google.com/youtube/v3/docs/comments/list)
- [Documentação do spaCy](https://spacy.io/usage)
- [Sentence Transformers](https://www.sbert.net/)
- [Transformers — Hugging Face](https://huggingface.co/docs/transformers)
