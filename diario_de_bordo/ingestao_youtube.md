# Ingestão de comentários do YouTube

## Decisões do recorte

- Objetivo: analisar o sentimento geral dos comentários de cada vídeo.
- Vídeos: `qD3zyh7-hpw` e `40QyA5f3Qo0`.
- Fonte: YouTube Data API v3, consultando dados públicos com uma chave de API.
- Recorte inicial: até 500 registros por vídeo, incluindo os comentários principais e suas respostas. Na coleta executada, o limite de registros foi removido para buscar o máximo disponível dentro da parcela de cota de cada vídeo.
- Orçamento: teto de 10.000 unidades por execução, dividido em até 5.000 requisições por vídeo. Metadados e novas tentativas também são contados. O teto local deve ser ajustado se a cota diária do projeto já tiver sido usada.
- Ordem: comentários principais mais recentes primeiro; respostas na ordem retornada pela API.
- Amostragem: cada principal é seguido de suas respostas até atingir o limite. Essa amostra não corresponde aos 500 textos mais recentes de toda a conversa.
- Armazenamento: JSON com metadados e CSV com uma linha por registro, em uma pasta por execução.
- Preparação: texto preservado como retornado pela API, sem limpeza ou classificação de sentimentos nesta etapa.

## Implementação e validação

O código está em `dados/brutos/bronze.py`. A ingestão utiliza a biblioteca padrão do Python e não exige instalação de pacotes adicionais. Foram validados com dados simulados a paginação, o limite total, os vínculos entre principais e respostas, a deduplicação por ID, os formatos JSON/CSV e o tratamento de falhas.

A primeira tentativa foi bloqueada pela rede do ambiente de desenvolvimento. O resultado dessa tentativa registra `status=erro` e `motivo=falhaConexao`.

Depois de implementar o orçamento dividido entre os vídeos, a execução com acesso à API foi autorizada e concluída em 2026-10-07. Os dados reais foram salvos em `dados/brutos/youtube/20261007T061129_708025Z/`.

| Vídeo | Principais | Respostas | Total | Requisições |
| --- | ---: | ---: | ---: | ---: |
| `qD3zyh7-hpw` | 35 | 21 | 56 | 10 |
| `40QyA5f3Qo0` | 115 | 22 | 137 | 17 |
| Total | 150 | 43 | 193 | 27 |

Ambas as coletas terminaram com `status=concluido` e `encerramento=api_esgotada`: todas as páginas disponibilizadas pela API naquele momento foram percorridas. Nenhum dos tetos de 5.000 requisições por vídeo foi atingido.

Os 13 testes com dados simulados passaram. Os arquivos reais JSON e CSV foram conferidos: contagens iguais, IDs sem duplicatas, respostas vinculadas a comentários principais e textos preservados entre os dois formatos. A chave de API não aparece nos arquivos de saída.

Para iniciar a coleta no terminal da raiz do projeto:

```bash
source .venv/bin/activate
python dados/brutos/bronze.py
```

Para repetir o recorte da coleta máxima com divisão de cota, execute:

```bash
python dados/brutos/bronze.py --limite 0 --orcamento 10000
```

Após uma execução com sucesso, registre neste diário a data, as quantidades de principais e respostas por vídeo e o campo `encerramento` de cada JSON.
