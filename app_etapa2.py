"""Painel Streamlit da Etapa 2: semântica, embeddings e comparação de sentimento.

Execute após `python etapa2.py --embeddings --transformer`:
    streamlit run app_etapa2.py
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

RAIZ = Path(__file__).resolve().parent
PROC = RAIZ / "dados" / "processados"
CSV = PROC / "comentarios_etapa2.csv"
NPZ = PROC / "comentarios_etapa2_embeddings.npz"
CORES = {"positivo": "#2a9d8f", "neutro": "#9aa0a6", "negativo": "#e76f51", "indefinido": "#7b61a8"}

st.set_page_config(page_title="Etapa 2 — análise semântica", page_icon="🧠", layout="wide")
st.title("🧠 Etapa 2 — além do sentimento")
st.caption("Explore termos, entidades, previsões de sentimento e proximidade semântica dos comentários.")

if not CSV.exists():
    st.error("CSV da Etapa 2 não encontrado. Rode `python etapa2.py` primeiro.")
    st.stop()

assinatura = (CSV.stat().st_mtime_ns, NPZ.stat().st_mtime_ns if NPZ.exists() else None)

@st.cache_data(show_spinner="Carregando resultados da Etapa 2...")
def carregar_dados(_assinatura):
    dados = pd.read_csv(CSV, encoding="utf-8-sig")
    if "comentario_id" not in dados or "texto" not in dados:
        raise ValueError("CSV precisa conter as colunas comentario_id e texto.")
    dados["comentario_id"] = dados["comentario_id"].fillna("").astype(str)
    dados["texto"] = dados["texto"].fillna("").astype(str)
    vetores, ids, modelo = None, None, None
    if NPZ.exists():
        arquivo = np.load(NPZ, allow_pickle=False)
        ids = arquivo["ids"].astype(str)
        vetores = np.asarray(arquivo["embeddings"], dtype=np.float32)
        modelo = str(arquivo["modelo"].item()) if "modelo" in arquivo.files else "Modelo não registrado"
        if len(ids) != len(vetores):
            raise ValueError("NPZ inválido: quantidade de IDs difere da quantidade de vetores.")
    return dados, ids, vetores, modelo

try:
    df, ids_npz, embeddings, nome_modelo = carregar_dados(assinatura)
except Exception as erro:
    st.error(f"Não foi possível carregar os dados: {erro}")
    st.stop()

if "sentimento" not in df:
    df["sentimento"] = "indefinido"
df["sentimento"] = df["sentimento"].fillna("sem classificação").astype(str)
if "score" not in df:
    df["score"] = np.nan

# Alinha embeddings com linhas do CSV por ID, sem presumir que a ordem dos arquivos é igual.
if embeddings is not None:
    posicoes = {ident: i for i, ident in enumerate(ids_npz)}
    indices_csv = df["comentario_id"].map(posicoes)
    validos = indices_csv.notna().to_numpy()
    df_emb = df.loc[validos].reset_index(drop=True)
    E = embeddings[indices_csv[validos].astype(int).to_numpy()]
else:
    df_emb, E = df.iloc[0:0].copy(), None

with st.sidebar:
    st.header("Filtros")
    sentimentos = sorted(df["sentimento"].unique().tolist())
    sentimentos_sel = st.multiselect("Sentimentos", sentimentos, default=sentimentos)
    texto_filtro = st.text_input("Buscar texto ou IDE", placeholder="ex.: VS Code, extensão, lento")
    max_pontos = st.slider("Máximo de pontos no mapa", 200, 2000, 1200, step=100)
    if embeddings is not None:
        st.caption(f"Embedding: `{nome_modelo}` · {embeddings.shape[1]} dimensões")
    else:
        st.warning("NPZ de embeddings não encontrado. Rode `python etapa2.py --embeddings` para habilitar o mapa e a busca semântica.")

filtrado = df[df["sentimento"].isin(sentimentos_sel)].copy()
if texto_filtro.strip():
    filtrado = filtrado[filtrado["texto"].str.contains(texto_filtro.strip(), case=False, regex=False, na=False)]

n1, n2, n3, n4 = st.columns(4)
n1.metric("Comentários processados", f"{len(df):,}".replace(",", "."))
n2.metric("Com embedding", f"{len(df_emb):,}".replace(",", "."))
n3.metric("Termos semânticos", "spaCy" if "termos_semanticos" in df else "Indisponível")
n4.metric("Modelo de sentimento", "2 modelos" if "sentimento_transformer" in df else "Principal")

aba_mapa, aba_conteudo, aba_comparacao, aba_busca, aba_metodo = st.tabs(
    ["🗺️ Mapa semântico", "🧩 O que aparece nos comentários?", "⚖️ Comparar sentimentos", "🔎 Busca semântica", "ℹ️ Como interpretar"]
)

@st.cache_data(show_spinner="Calculando projeção 2D dos embeddings...")
def projetar_pca(vetores):
    x = np.asarray(vetores, dtype=np.float32)
    if len(x) < 2:
        return np.zeros((len(x), 2), dtype=np.float32)
    x = x - x.mean(axis=0, keepdims=True)
    # PCA por matriz de covariância; não requer scikit-learn.
    cov = (x.T @ x) / max(len(x) - 1, 1)
    valores, vetores_eixos = np.linalg.eigh(cov)
    eixos = vetores_eixos[:, np.argsort(valores)[-2:][::-1]]
    return x @ eixos

with aba_mapa:
    st.subheader("Cada ponto representa um comentário")
    st.caption("Pontos próximos têm embeddings mais semelhantes. A projeção PCA reduz 384 dimensões para 2; os eixos não são tópicos nomeados.")
    if E is None or len(E) < 2:
        st.info("Gere embeddings para visualizar o mapa semântico.")
    else:
        mapa = df_emb.copy()
        coords = projetar_pca(E)
        mapa["PCA 1"], mapa["PCA 2"] = coords[:, 0], coords[:, 1]
        if "sentimento_transformer" in mapa:
            mapa["cor_mapa"] = mapa["sentimento_transformer"].fillna(mapa["sentimento"])
        else:
            mapa["cor_mapa"] = mapa["sentimento"]
        if sentimentos_sel:
            mapa = mapa[mapa["sentimento"].isin(sentimentos_sel)]
        if texto_filtro.strip():
            mapa = mapa[mapa["texto"].str.contains(texto_filtro.strip(), case=False, regex=False, na=False)]
        if len(mapa) > max_pontos:
            mapa = mapa.sample(max_pontos, random_state=17)
        fig = px.scatter(mapa, x="PCA 1", y="PCA 2", color="cor_mapa", color_discrete_map=CORES,
                         hover_data={"texto": True, "sentimento": True, "score": ":.3f",
                                     "nome_video": True if "nome_video" in mapa else False,
                                     "PCA 1": False, "PCA 2": False}, opacity=0.75,
                         title="Projeção PCA dos embeddings, colorida por sentimento")
        fig.update_traces(marker={"size": 8})
        st.plotly_chart(fig, use_container_width=True)
        st.caption(f"Mostrando {len(mapa):,} pontos. A cor usa o sentimento Transformer quando disponível; o hover exibe também o sentimento principal.")


def ler_json(celula):
    if not isinstance(celula, str) or not celula.strip():
        return []
    try:
        valor = json.loads(celula)
        return valor if isinstance(valor, list) else []
    except (ValueError, TypeError):
        return []

with aba_conteudo:
    st.subheader("Termos e entidades extraídos pelo spaCy")
    a, b = st.columns(2)
    if "termos_semanticos" in df:
        freq = {}
        for celula in filtrado["termos_semanticos"].dropna():
            for item in ler_json(celula):
                termo = str(item.get("lema", "")).strip().lower()
                if termo:
                    freq[termo] = freq.get(termo, 0) + 1
        top_termos = pd.DataFrame(sorted(freq.items(), key=lambda item: item[1], reverse=True)[:20],
                                  columns=["Lema", "Frequência"])
        with a:
            st.markdown("**Lemas mais frequentes**")
            if top_termos.empty:
                st.info("Nenhum termo disponível com os filtros atuais.")
            else:
                fig = px.bar(top_termos.sort_values("Frequência"), x="Frequência", y="Lema", orientation="h")
                st.plotly_chart(fig, use_container_width=True)
    else:
        a.info("Coluna termos_semanticos não encontrada no CSV.")
    if "entidades_semanticas" in df:
        freq_ent = {}
        for celula in filtrado["entidades_semanticas"].dropna():
            for item in ler_json(celula):
                chave = (str(item.get("texto", "")).strip(), str(item.get("tipo", "")).strip())
                if chave[0]:
                    freq_ent[chave] = freq_ent.get(chave, 0) + 1
        entidades = pd.DataFrame([{"Entidade": t, "Tipo": tipo, "Frequência": n}
                                  for (t, tipo), n in sorted(freq_ent.items(), key=lambda item: item[1], reverse=True)[:20]])
        with b:
            st.markdown("**Entidades reconhecidas**")
            if entidades.empty:
                st.info("Nenhuma entidade reconhecida com os filtros atuais.")
            else:
                st.dataframe(entidades, hide_index=True, use_container_width=True)
    else:
        b.info("Coluna entidades_semanticas não encontrada no CSV.")
    st.markdown("**Comentários para conferir a interpretação**")
    colunas = [c for c in ["sentimento", "sentimento_transformer", "texto", "nome_video"] if c in filtrado]
    st.dataframe(filtrado[colunas].head(100), hide_index=True, use_container_width=True)

with aba_comparacao:
    st.subheader("Sentimento principal × previsão Transformer")
    if "sentimento_transformer" not in df:
        st.info("Não há colunas do Transformer. Gere o CSV com `python etapa2.py --transformer`.")
    else:
        comparavel = filtrado.dropna(subset=["sentimento", "sentimento_transformer"])
        tabela = pd.crosstab(comparavel["sentimento"], comparavel["sentimento_transformer"])
        if tabela.empty:
            st.info("Sem previsões disponíveis para os filtros atuais.")
        else:
            fig = px.imshow(tabela, text_auto=True, aspect="auto", color_continuous_scale="Blues",
                            labels={"x": "Transformer", "y": "Sentimento principal", "color": "Comentários"},
                            title="Matriz de concordância entre classificadores")
            st.plotly_chart(fig, use_container_width=True)
            n = len(comparavel)
            acordo = (comparavel["sentimento"] == comparavel["sentimento_transformer"]).mean()
            st.metric("Concordância simples", f"{100 * acordo:.1f}%", f"{n:,} comentários comparáveis")
            st.warning("Concordância não mede acurácia. Para dizer qual modelo é melhor, compare ambos com uma amostra rotulada manualmente.")
            dist = pd.concat([
                comparavel["sentimento"].value_counts().rename_axis("Classe").rename("Quantidade").reset_index().assign(Modelo="Principal"),
                comparavel["sentimento_transformer"].value_counts().rename_axis("Classe").rename("Quantidade").reset_index().assign(Modelo="Transformer")
            ], ignore_index=True)
            st.plotly_chart(px.bar(dist, x="Classe", y="Quantidade", color="Modelo", barmode="group"), use_container_width=True)

with aba_busca:
    st.subheader("Encontrar comentários semanticamente parecidos")
    st.caption("Escreva uma ideia ou frase. O modelo compara sua representação vetorial com as dos comentários processados.")
    consulta = st.text_input("Consulta semântica", placeholder="ex.: problemas de desempenho e lentidão da IDE")
    if not consulta.strip():
        st.info("Digite uma consulta para buscar comentários próximos pelo embedding.")
    elif E is None:
        st.warning("A busca semântica requer o arquivo NPZ. Rode a Etapa 2 com `--embeddings`.")
    else:
        @st.cache_resource
        def carregar_modelo_embedding(nome):
            from sentence_transformers import SentenceTransformer
            return SentenceTransformer(nome)
        try:
            modelo = carregar_modelo_embedding(nome_modelo)
            q = modelo.encode([consulta], convert_to_numpy=True, normalize_embeddings=True)[0]
            similaridades = E @ q
            ordem = np.argsort(similaridades)[::-1][:10]
            resultados = df_emb.iloc[ordem].copy()
            resultados.insert(0, "similaridade cosseno", similaridades[ordem])
            st.dataframe(resultados[[c for c in ["similaridade cosseno", "sentimento", "sentimento_transformer", "texto", "nome_video"] if c in resultados]],
                         hide_index=True, use_container_width=True)
        except Exception as erro:
            st.error(f"Não foi possível carregar o modelo de embeddings para a consulta: {erro}")

with aba_metodo:
    st.markdown("""
    **Como ler o painel**

    - O mapa é uma projeção PCA dos embeddings. Proximidade representa similaridade aproximada no espaço vetorial; não significa causalidade nem garante que os comentários pertençam ao mesmo tópico.
    - Lemas e entidades são extrações automáticas do spaCy e podem conter erros, especialmente com gírias, nomes de IDEs e frases curtas.
    - A matriz compara dois classificadores. A diagonal mostra quantas previsões coincidem, mas não permite concluir acurácia sem rótulos humanos.
    - A busca semântica ranqueia comentários pela similaridade cosseno com a frase digitada.
    - A implementação atual não executa clustering/rotulagem automática de tópicos. A visualização de agrupamentos seria uma extensão futura.
    """)
    st.caption("Os dados usados são os arquivos locais de `dados/processados/`; nenhuma nova coleta é feita pelo painel.")
