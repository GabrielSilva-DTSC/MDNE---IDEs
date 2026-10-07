# Análise de sentimentos no YouTube

Projeto de modelagem de dados não estruturados a partir de comentários públicos de vídeos do YouTube. A ingestão usa a YouTube Data API v3. O objetivo inicial é analisar o sentimento geral dos comentários de cada vídeo.

## Estrutura

- `dados/brutos/`: dados coletados sem alterações.
- `dados/intermediarios/`: dados após etapas parciais de tratamento.
- `dados/processados/`: dados prontos para análise e modelagem.
- `dados/brutos/bronze.py`: coletor de comentários pela YouTube Data API v3.
- `src/preprocessamento/`: limpeza de texto, identificação de idioma e tratamento de emojis.
- `src/modelagem/sentimentos.py`: modelagem de sentimentos.
- `src/analise/estatisticas.py`: análises estatísticas.
- `diario_de_bordo/`: registros do andamento do projeto.
- `relatorio/`: resultados e relatório final.
- `notebooks/`: análises exploratórias em Jupyter e o notebook `estrutura_projeto.ipynb` com as etapas do projeto.

O coletor está implementado. Os módulos de pré-processamento, modelagem e análise ainda são esboços. Os arquivos `__init__.py` permitem organizar os módulos como pacotes Python para importá-los a partir da raiz do projeto.

O fluxo previsto é: vídeos selecionados → coleta de comentários → `dados/brutos/` → pré-processamento → `dados/processados/` → classificação de sentimentos → estatísticas e relatório. O código da coleta está em `dados/brutos/bronze.py`; os módulos das demais etapas estão em `src/`. As saídas da coleta ficam em `dados/brutos/youtube/`.

## Configuração

1. Após clonar o projeto, crie o ambiente virtual com `python -m venv .venv` e ative-o com `source .venv/bin/activate`. Se o ambiente já existir, basta ativá-lo.
2. A coleta usa apenas a biblioteca padrão do Python e não exige instalação de pacotes. O `requirements.txt` contém dependências para as próximas etapas do projeto.
3. No Google Cloud Console, ative a YouTube Data API v3 e crie uma chave de API restrita a esse serviço. Consulte o [guia oficial de credenciais](https://developers.google.com/youtube/registering_an_application).
4. Preencha `YOUTUBE_API_KEY` no arquivo `.env` da raiz:

   ```env
   YOUTUBE_API_KEY=sua_chave_aqui
   ```

   O `.env` é ignorado pelo Git. O coletor lê apenas a variável `YOUTUBE_API_KEY`; você também pode defini-la no ambiente do processo. A chave é enviada em um cabeçalho HTTPS e não aparece nos arquivos de saída.

## Executar a primeira coleta

Na raiz do projeto, com o ambiente virtual ativo:

```bash
python dados/brutos/bronze.py
```

O comando já usa os vídeos `qD3zyh7-hpw` e `40QyA5f3Qo0`, com **até 500 registros por vídeo, incluindo respostas**. Os comentários principais são consultados dos mais recentes para os mais antigos. Depois de cada principal, o coletor busca suas respostas até esgotá-las ou atingir o limite total. A ordem das respostas é a retornada pela API.

Esse recorte não equivale aos 500 textos mais recentes de toda a conversa. Um tópico com muitas respostas pode ocupar boa parte da amostra. Registre essa escolha na metodologia da análise de sentimentos.

Outros exemplos:

```bash
# Coleta pequena para estudar o funcionamento.
python dados/brutos/bronze.py --limite 20

# Apenas comentários principais, de outro vídeo.
python dados/brutos/bronze.py --videos "https://www.youtube.com/watch?v=qD3zyh7-hpw" --limite 100 --sem-respostas
```

`--limite 0` remove o limite local de registros e tenta obter todos os registros disponíveis pela API, respeitando o orçamento de requisições. `--ordem relevance` troca a ordem dos comentários principais para relevância. Essas opções alteram o recorte e o consumo de cota.

## Orçamento de requisições

A cota padrão para os endpoints usados aqui é de 10.000 unidades diárias, compartilhadas pelo projeto. `videos.list`, `commentThreads.list` e `comments.list` custam 1 unidade por requisição. Consulte a [documentação de cotas](https://developers.google.com/youtube/v3/getting-started).

O coletor aceita `--orcamento` de 1 a 10.000 unidades por execução. O padrão é 10.000, dividido igualmente entre os vídeos selecionados: com os dois vídeos deste projeto, o teto é de 5.000 requisições por vídeo. Os metadados e as novas tentativas também entram na conta. Ao atingir sua parcela, o coletor salva os registros obtidos com `encerramento=orcamento_atingido`.

Para buscar o máximo disponível dentro dessas parcelas:

```bash
python dados/brutos/bronze.py --limite 0 --orcamento 10000
```

Esse é um teto, não uma meta de consumo: a coleta termina antes se não houver mais páginas. Um vídeo com mais respostas pode consumir mais requisições por registro do que outro; dividir a cota igualmente não garante a mesma quantidade de comentários por vídeo.

O orçamento é local a cada execução e não consulta o saldo diário no Google Cloud. Se parte da cota já tiver sido usada no projeto, ajuste `--orcamento` ao saldo disponível. Ao receber `quotaExceeded` ou `dailyLimitExceeded`, o programa salva o resultado parcial e encerra a execução. Uma nova execução tem um novo contador local, mas usa a mesma cota diária do projeto.

## Arquivos gerados

Cada execução cria uma pasta própria, com o horário UTC no nome:

```text
dados/brutos/youtube/<execucao>/
├── qD3zyh7-hpw.json
├── qD3zyh7-hpw.csv
├── 40QyA5f3Qo0.json
├── 40QyA5f3Qo0.csv
└── manifesto.json
```

O JSON reúne metadados do vídeo, informações da coleta e os comentários. O CSV contém uma linha por registro e as colunas `video_id`, `comentario_id`, `comentario_pai_id`, `tipo`, `texto`, `curtidas`, `publicado_em` e `atualizado_em`. O manifesto registra quais vídeos foram tentados, os arquivos gerados e o número de requisições. Falhas gerais de chave, rede ou cota podem encerrar a execução antes do segundo vídeo; isso fica registrado no manifesto.

Os textos são preservados como entregues pela API em `plainText`, com acentos, emojis e quebras de linha. Ainda não há limpeza nem classificação de sentimentos. O JSON contém campos selecionados da API, não uma cópia integral de sua resposta. Nomes, fotos e canais dos autores dos comentários não são solicitados. As coletas ficam fora do Git.

No JSON, `status` pode ser `concluido`, `parcial` ou `erro`. O campo `encerramento` distingue `api_esgotada`, `limite_atingido`, `orcamento_atingido` e `erro`. Atingir 500 registros ou o orçamento não significa ter obtido todos os comentários do vídeo. Vídeo indisponível ou comentários desativados são falhas explícitas, não coletas vazias bem-sucedidas.

## Como o código funciona

1. `carregar_chave()` lê a chave do `.env`, sem executar o arquivo ou carregar as outras credenciais.
2. `extrair_id_video()` transforma a URL em um ID e rejeita endereços inválidos.
3. `ClienteYouTube.consultar()` envia uma requisição GET e transforma a resposta JSON em um dicionário Python. Essa função também trata erros sem exibir a chave.
4. `coletar_video()` consulta o título e os metadados do vídeo. Depois usa `commentThreads` para os principais e `comments` para as respostas. Cada endpoint retorna até 100 registros por página; `nextPageToken` permite pedir a página seguinte.
5. `montar_registro()` seleciona os campos do comentário e identifica seu vínculo com o principal. Um conjunto de IDs evita duplicatas durante a coleta.
6. `salvar_coleta()` escreve JSON e CSV. O `main()` divide o orçamento entre os vídeos, repete o processo e salva o manifesto com o consumo de cada coleta.

Para conferir a paginação, os limites, os formatos e os erros com dados simulados, sem gastar cota:

```bash
python -m unittest discover -s tests -v
```

Referências: [comentários principais e paginação](https://developers.google.com/youtube/v3/docs/commentThreads/list), [busca das respostas](https://developers.google.com/youtube/v3/docs/comments/list) e [campos de texto do comentário](https://developers.google.com/youtube/v3/docs/comments). O texto público em `textDisplay` pode diferir do original digitado pelo autor, conforme a documentação da API.

## Primeira coleta concluída

A coleta real de 2026-10-07 buscou o máximo disponível com `--limite 0 --orcamento 10000`. A API esgotou suas páginas antes de atingir os tetos de requisições.

| Vídeo | Principais | Respostas | Total | Requisições |
| --- | ---: | ---: | ---: | ---: |
| `qD3zyh7-hpw` | 35 | 21 | 56 | 10 |
| `40QyA5f3Qo0` | 115 | 22 | 137 | 17 |

São 193 registros e 27 requisições no total. Os JSONs, CSVs e o manifesto estão em `dados/brutos/youtube/20261007T061129_708025Z/`. Os dois resultados têm `status=concluido` e `encerramento=api_esgotada`. Consulte também `diario_de_bordo/ingestao_youtube.md` para as decisões do recorte e a validação.
