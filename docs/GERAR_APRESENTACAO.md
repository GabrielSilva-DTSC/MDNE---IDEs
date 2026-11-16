# Gerar a apresentação PowerPoint da Etapa 2 localmente

O repositório contém o script gerador; o arquivo binário `.pptx` é criado no seu computador e não precisa ser versionado.

## Windows (PowerShell)

Na raiz do repositório e com a branch `feature/etapa2-analise-semantica` atualizada:

```powershell
python -m pip install -r requirements-apresentacao.txt
python scripts/gerar_apresentacao_etapa2.py
```

Isso cria `apresentacao_etapa2.pptx` na raiz do projeto. Para escolher outro destino:

```powershell
python scripts/gerar_apresentacao_etapa2.py --saida saida/apresentacao_etapa2.pptx
```

Abra o `.pptx` no Microsoft PowerPoint ou no LibreOffice Impress. Para produzir PDF no PowerPoint, use **Arquivo > Exportar > Criar documento PDF/XPS** ou **Arquivo > Salvar como > PDF**. No LibreOffice Impress, use **Arquivo > Exportar como > Exportar como PDF**.

## Apresentar com os dados do projeto

O arquivo de slides apresenta o pipeline, os resultados observados e as limitações. Para demonstrar o painel interativo com os dados locais, gere os arquivos da Etapa 2 e inicie o app:

```powershell
python etapa2.py --embeddings --transformer
streamlit run app_etapa2.py
```

A execução completa requer também as dependências em `requirements-etapa2.txt`. Rode-a antes da apresentação e mantenha o Streamlit aberto durante a demonstração.

## Conteúdo dos slides

A apresentação inclui contexto da Etapa 1, pipeline spaCy, embeddings (incluindo o resultado observado de 1.958 × 384), classificador Transformer, novo painel, roteiro de demonstração, impacto e limitações. Diagramas e vetores ilustrativos estão identificados como conceituais; não são apresentados como resultados medidos. O mapa semântico exibido durante a demonstração é produzido pelo app com os dados locais.

Se o ambiente `python` do terminal não for o da `.venv`, ative o ambiente antes de instalar e gerar o arquivo. O script requer apenas `python-pptx`; não precisa carregar os modelos de NLP para criar a apresentação.
