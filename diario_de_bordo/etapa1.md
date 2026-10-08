# Diário de bordo — Etapa 1 (PLN)

## Decisões
- Entrada: JSONs de `dados/brutos/youtube/<execucao>/` (têm curtidas, datas e título; o CSV do `bronze.py` só tem 5 colunas).
- Texto vem em `plainText`, então não há HTML para limpar; a limpeza é feita com **RE**.
- Duas versões do texto: `texto_leve` (mantém emoji/maiúscula/pontuação → NER e sentimento) e `texto_limpo` (só letras minúsculas → lemas e nuvem).
- Idioma: `langdetect` com semente fixa. Só sai do recorte quem tem ≥5 palavras e é detectado com ≥95% de confiança em outro idioma; comentários curtos ficam.
- Sentimento: `pysentimiento` (pt). Score = P(positivo) − P(negativo). IC de 95% de Wilson nas proporções por vídeo.

## Erros reais e soluções (para o slide)
| Erro | Causa | Solução |
|---|---|---|
| "kkkkk" não era removido da versão limpa | A limpeza leve encolhe letras repetidas ("kkkkk"→"kk") antes de a regex de risada (3+) rodar | Remover risadas **antes** de encolher letras repetidas (o teste unitário pegou) |
| Comentários em português descartados como espanhol | `langdetect` confunde pt/es | Exigir ≥95% de confiança e **nunca excluir** línguas parecidas (es, gl, ca, it, ro, fr): o `langdetect` errou mesmo com alta confiança num comentário real em português. Só sai texto longo em idioma distante (ex.: inglês) |
| Entidades falsas ("Gostei", "Amei") | Modelo `sm` marca verbo no início da frase como entidade | Filtrar entidades cujo núcleo é VERB/AUX/INTJ/ADJ/ADV |
| Timestamps ("12:34") virando ruído | Comentário de vídeo cita minutagem | `RE_TIMESTAMP` |
| Acesso inicial bloqueado pela rede | Ambiente de desenvolvimento | Ver `ingestao_youtube.md` |
| _(acrescentem os de vocês)_ | | |

## Limitações a citar
- Poucos comentários por vídeo (ex.: 56 e 137) → intervalos largos; não generalizar para "o público do YouTube".
- A amostra são os comentários mais recentes, com respostas em ordem da API (ver README).
- Ironia/sarcasmo e gírias de programação confundem o modelo; o `pt_core_news_sm` erra NER e alguns lemas (ex.: "amei" → "ameir").
