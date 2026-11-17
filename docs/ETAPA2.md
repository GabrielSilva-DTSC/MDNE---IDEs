# Etapa 2 — análise semântica, embeddings e Transformers

A Etapa 2 amplia o fluxo da Etapa 1 sem alterar `etapa1.py`: mantém os dados brutos e os resultados existentes e grava os novos resultados em `dados/processados/comentarios_etapa2.csv`.

## Instalação

```bash
python -m pip install -r requirements.txt
python -m spacy download pt_core_news_sm
# Opcional: necessário somente para gerar embeddings ou ativar o classificador Hugging Face
python -m pip install -r requirements-etapa2.txt
```

As bibliotecas `sentence-transformers`, `transformers` e `torch` são opcionais para deixar o ambiente-base menor. Os modelos são baixados na primeira execução que os solicita; para execução sem rede, faça o download previamente e informe um caminho local do modelo.

## Execução

```bash
# Pipeline linguístico spaCy + sentimento pysentimiento (padrão)
python etapa2.py

# Inclui embeddings semânticos normalizados; arquivo NPZ fica ao lado do CSV
python etapa2.py --embeddings

# Inclui previsões adicionais de um classificador Transformers, sem substituir o sentimento da Etapa 1
python etapa2.py --transformer

# Pipeline completo solicitado
python etapa2.py --embeddings --transformer

# Rodar em uma execução de teste, sem carregar o modelo de sentimento
python etapa2.py --entrada tests/fixtures/execucao_exemplo --sem-modelo-sentimento
```

Para mudar caminhos/modelo:

```bash
python etapa2.py --entrada dados/brutos/youtube/EXECUCAO --saida dados/processados/etapa2.csv \
  --embeddings --modelo-embedding sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
```

## Saídas e interpretação

- `sentencas`, `termos_semanticos`, `entidades_semanticas` e `relacoes_sintaticas` são JSON serializados em células CSV. As relações sujeito/verbo/complemento são extrações sintáticas aproximadas, não fatos validados.
- `sentimento`, probabilidades e `score` seguem o classificador já usado na Etapa 1. Comentários excluídos pelo filtro de idioma ficam sem classificação.
- Com `--transformer`, colunas com sufixo `_transformer` registram a previsão adicional do modelo multilíngue. Não compare confiança entre modelos como se fosse uma escala calibrada comum.
- Com `--embeddings`, `comentarios_etapa2_embeddings.npz` (ou nome derivado de `--saida`) guarda `ids`, `embeddings` e `modelo`. Os vetores são L2-normalizados; a similaridade entre dois vetores é o produto escalar. O NPZ evita converter vetores em texto e inflar o CSV.
- spaCy continua sendo necessário para a etapa semântica. Os modelos Transformers e embeddings são carregados sob demanda e os erros de configuração não são mascarados por resultados fictícios.

Exemplo de leitura dos vetores:

```python
import numpy as np
arquivo = np.load("dados/processados/comentarios_etapa2_embeddings.npz")
ids, vetores = arquivo["ids"], arquivo["embeddings"]
# Similaridade cosseno entre os dois primeiros comentários (vetores normalizados)
print(float(vetores[0] @ vetores[1]))
```

## Testes

```bash
python -m unittest discover -s tests -v
```

Os testes unitários da Etapa 2 usam spaCy simulado e não baixam modelos. Para validar o modelo português, execute `python -m spacy download pt_core_news_sm` e rode `python etapa2.py` com uma amostra local.
