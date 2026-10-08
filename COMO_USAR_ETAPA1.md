# Etapa 1 — como rodar
Copie estes arquivos para a raiz do projeto (eles substituem os esboços de `src/preprocessamento/`, `src/modelagem/sentimentos.py` e `src/analise/estatisticas.py`).

```bash
pip install -r requirements.txt
python -m spacy download pt_core_news_sm
python -m unittest discover -s tests -v          # sem rede
python etapa1.py                                 # usa a coleta real mais recente
python etapa1.py --entrada tests/fixtures/execucao_exemplo --sem-modelo   # dados SIMULADOS
```
Saídas: `dados/intermediarios/comentarios_limpos.csv`, `dados/processados/comentarios_sentimento.csv`, `relatorio/tabelas/*.csv`, `relatorio/assets/*.png`.
Se a coluna `metodo_sentimento` mostrar `lexico_reserva`, o pysentimiento não carregou: o resultado não vale para a apresentação.
