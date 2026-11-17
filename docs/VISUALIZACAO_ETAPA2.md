# Visualização da Etapa 2

O painel de visualização foi separado do painel original da Etapa 1 para manter a visualização anterior intacta. Execute após gerar `comentarios_etapa2.csv` e `comentarios_etapa2_embeddings.npz`:

```powershell
python etapa2.py --embeddings --transformer
streamlit run app_etapa2.py
```

Para abrir os dois painéis na mesma aplicação, execute `streamlit run app.py` e selecione a Etapa 2 na navegação lateral. O comando direto acima continua disponível para abrir somente esse painel.

O painel oferece:

- **Mapa semântico:** projeção PCA 2D dos embeddings, pontos coloridos por sentimento e texto disponível no hover.
- **Conteúdo:** frequência dos lemas/termos do spaCy, entidades reconhecidas e comentários para inspeção.
- **Comparação de sentimentos:** matriz de concordância entre o classificador principal e o Transformer, mais distribuição das classes.
- **Busca semântica:** digite uma frase e recupere os comentários com embeddings mais semelhantes.
- **Filtros:** sentimento e busca textual, compartilhados pelas visualizações.

O arquivo `app_etapa2.py` usa os resultados locais; não coleta novos comentários. A busca semântica carrega o mesmo modelo Sentence Transformers identificado no NPZ. O mapa PCA é exploratório: os eixos não correspondem a tópicos interpretáveis e proximidade não substitui validação. O painel deixa explícito que o clustering automático de tópicos ainda não está implementado.

Se não houver NPZ, gere-o com `python etapa2.py --embeddings`. A comparação de classificadores só aparece quando o CSV foi produzido com `--transformer`.
