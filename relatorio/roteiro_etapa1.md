# Roteiro da apresentação — Etapa 1 (≤ 5 min por integrante)
PDF para o SIGAA: `etapa1-<nome-produto>.pdf`. Mostrar o código-fonte e executar ao vivo; não ler slides; todos falam.

1. Capa: pergunta de pesquisa e vídeos analisados (título, canal, nº de comentários coletados).
2. Teoria — PLN e RE: etapas (coleta → limpeza → NLP → sentimento); o que cada regex de `limpeza.py` remove e por quê.
3. Teoria — spaCy: tokenização, lematização, POS, NER; modelo `pt_core_news_sm`; dica de onde aprender (docs do spaCy).
4. Teoria — sentimento: por que não TextBlob; pysentimiento (POS/NEU/NEG); score = P(pos) − P(neg); IC de Wilson (fórmula).
5. Implementação — coleta (`bronze.py`): endpoints, paginação, orçamento de cota, `encerramento`; recorte da amostra.
6. Implementação — limpeza e idioma (`limpeza.py`, `idioma.py`, `emojis.py`): `texto_leve` x `texto_limpo`.
7. Implementação — spaCy (`nlp_spacy.py`) e sentimento (`sentimentos.py`).
8. Implementação — estatísticas e gráficos (`estatisticas.py`, `graficos.py`).
9. **Diário de bordo** (tabela de `diario_de_bordo/etapa1.md`).
10. Demo ao vivo: `python etapa1.py` → abrir `relatorio/assets/` e `relatorio/tabelas/`.
11. Resultados por vídeo + limitações.
12. Próximas etapas: áudio e vídeo do mesmo tema.

Divisão sugerida do código (≥50 linhas por pessoa): coleta/`comum.py`; `preprocessamento/`; `modelagem/` + `analise/`.
