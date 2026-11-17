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
CORES = {
    "positivo": "#FF5825",
    "neutro": "#D8C8CC",
    "negativo": "#E58A9A",
    "indefinido": "#B9A6C8",
    "sem classificação": "#9A858C",
}
CORES_GRAFICO = ["#FF5825", "#E58A9A", "#D8C8CC", "#B9A6C8"]
FUNDO_PAINEL = "#310713"
VINHO_BORDA = "#713244"
TEXTO_CLARO = "#F5E9E9"
LARANJA = "#FF5825"

st.set_page_config(page_title="Etapa 2 — análise semântica", layout="wide")
st.markdown(
    """
    <style>
    :root {
        --wine-950: #23040D;
        --wine-900: #310713;
        --wine-850: #390916;
        --wine-800: #4A0B1D;
        --wine-700: #651424;
        --wine-border: #713244;
        --orange: #FF5825;
        --paper: #FFF7F5;
        --paper-border: #EAD8DC;
        --ink: #3E1020;
        --text-primary: #F5E9E9;
        --text-secondary: #D6C3C7;
        --text-muted: #C5AEB4;
    }

    .stApp, [data-testid="stAppViewContainer"] {
        background:
            radial-gradient(ellipse at 82% 0%, #4B0D1D 0, transparent 34rem),
            var(--wine-950);
        color: var(--text-primary);
    }
    [data-testid="stMain"] > div {
        max-width: 1540px;
        padding-top: 1.8rem;
        padding-bottom: 3rem;
    }
    [data-testid="stMain"] h1,
    [data-testid="stMain"] h2,
    [data-testid="stMain"] h3,
    [data-testid="stMain"] h4 {
        color: var(--text-primary);
    }
    [data-testid="stMain"] [data-testid="stMarkdownContainer"],
    [data-testid="stMain"] [data-testid="stWidgetLabel"] {
        color: var(--text-primary);
    }
    [data-testid="stMain"] [data-testid="stCaptionContainer"] {
        color: var(--text-muted);
    }
    [data-testid="stHeader"] { background: transparent; }
    [data-testid="stSidebar"] {
        background: linear-gradient(165deg, #390916 0%, #26050E 68%, #1D030A 100%);
        border-right: 1px solid rgba(255, 88, 37, .28);
    }
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"],
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
    [data-testid="stSidebar"] [data-testid="stWidgetLabel"],
    [data-testid="stSidebar"] label {
        color: var(--text-primary);
    }
    [data-testid="stSidebar"] [data-testid="stCaptionContainer"] {
        color: var(--text-secondary);
    }

    .etapa2-hero {
        position: relative;
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 2rem;
        min-height: 238px;
        padding: 1.6rem 2rem;
        margin-bottom: 1.35rem;
        overflow: hidden;
        border: 1px solid rgba(255, 88, 37, .36);
        border-radius: 20px;
        background: linear-gradient(112deg, rgba(74, 11, 29, .96), rgba(35, 4, 13, .92));
        box-shadow: 0 20px 55px rgba(0, 0, 0, .18);
    }
    .etapa2-hero-copy { position: relative; z-index: 1; max-width: 690px; }
    .etapa2-kicker {
        color: #FF9A72;
        font: 750 .72rem/1.3 Arial, sans-serif;
        letter-spacing: .16em;
        text-transform: uppercase;
    }
    .etapa2-hero h1 {
        margin: .55rem 0 .7rem;
        color: var(--text-primary);
        font: 700 clamp(2.2rem, 4vw, 3.65rem)/1 Georgia, serif;
        letter-spacing: -.035em;
    }
    .etapa2-hero h1 span { color: var(--orange); font-family: Arial, sans-serif; }
    .etapa2-hero p {
        max-width: 630px;
        margin: 0;
        color: var(--text-secondary);
        font-size: 1rem;
        line-height: 1.6;
    }
    .etapa2-signature {
        display: inline-block;
        margin-top: 1.15rem;
        color: var(--text-primary);
        font: italic 700 1rem Georgia, serif;
    }
    .etapa2-signature span { color: var(--orange); }
    .etapa2-visual { flex: 0 1 345px; width: min(37%, 345px); }
    .etapa2-visual svg { display: block; width: 100%; height: auto; }

    [data-testid="stMetric"] {
        min-height: 116px;
        padding: 1rem 1.15rem;
        border: 1px solid rgba(255, 88, 37, .3);
        border-radius: 15px;
        background: linear-gradient(145deg, rgba(101, 20, 36, .86), rgba(49, 7, 19, .94));
    }
    [data-testid="stMetricLabel"] { color: var(--text-secondary) !important; }
    [data-testid="stMetricValue"] {
        color: var(--text-primary) !important;
        font-family: Georgia, serif;
        font-weight: 700;
    }
    [data-testid="stTabs"] [role="tab"] {
        min-height: 3.1rem;
        padding-inline: .8rem;
        border-radius: 10px 10px 0 0;
        color: var(--text-secondary);
        font-weight: 650;
    }
    [data-testid="stTabs"] [role="tab"][aria-selected="true"] {
        color: var(--text-primary);
        border-bottom-color: var(--orange);
        background: rgba(255, 88, 37, .1);
    }
    [data-testid="stTabs"] [role="tab"]:hover,
    [data-testid="stTabs"] [role="tab"]:focus-visible { color: var(--text-primary); }
    [data-testid="stTabs"] [role="tab"]:focus-visible,
    [data-baseweb="select"] > div:focus-within,
    [data-baseweb="input"] > div:focus-within {
        outline: 2px solid var(--orange);
        outline-offset: 2px;
    }
    [data-baseweb="select"] > div,
    [data-baseweb="input"] > div {
        background: var(--paper);
        border-color: #B98594;
        color: var(--ink);
    }
    [data-baseweb="select"] input,
    [data-baseweb="input"] input {
        color: var(--ink) !important;
        -webkit-text-fill-color: var(--ink);
    }
    [data-baseweb="tag"] { background: #EAD8DC; color: var(--ink); }
    [data-baseweb="tag"] * { color: var(--ink) !important; }
    [data-testid="stSlider"] [data-testid="stThumbValue"] {
        color: var(--text-primary);
        background: var(--wine-700);
    }
    [data-testid="stPlotlyChart"] {
        overflow: hidden;
        border: 1px solid rgba(113, 50, 68, .68);
        border-radius: 14px;
        background: var(--wine-900);
    }
    [data-testid="stDataFrame"] {
        overflow: hidden;
        border: 1px solid var(--paper-border);
        border-radius: 12px;
        background: var(--paper);
    }
    [data-testid="stAlert"] { border-radius: 12px; }
    ::selection { background: var(--orange); color: #FFFFFF; }

    @media (max-width: 850px) {
        [data-testid="stMain"] > div { padding-top: 1rem; }
        .etapa2-hero { min-height: 0; padding: 1.4rem; }
        .etapa2-visual { flex-basis: 250px; }
    }
    @media (max-width: 600px) {
        .etapa2-hero { padding: 1.2rem; }
        .etapa2-visual { display: none; }
        .etapa2-hero h1 { font-size: 2.2rem; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <section class="etapa2-hero">
      <div class="etapa2-hero-copy">
        <div class="etapa2-kicker">Pesquisa · análise · tecnologia</div>
        <h1>Além do <span>sentimento</span></h1>
        <p>Uma leitura semântica dos comentários para explorar temas, entidades e proximidade entre ideias da comunidade de desenvolvedores.</p>
        <div class="etapa2-signature">Dados que ajudam a escolher <span>melhor.</span></div>
      </div>
      <div class="etapa2-visual" aria-hidden="true">
        <svg viewBox="0 0 350 205" role="img">
          <defs>
            <linearGradient id="card" x1="0" x2="1" y1="0" y2="1">
              <stop offset="0" stop-color="#651424"/>
              <stop offset="1" stop-color="#310713"/>
            </linearGradient>
          </defs>
          <rect x="14" y="18" width="310" height="166" rx="14" fill="url(#card)" stroke="#A94B50" stroke-opacity=".72"/>
          <path d="M14 51h310" stroke="#A94B50" stroke-opacity=".55"/>
          <circle cx="34" cy="35" r="4" fill="#FF5825"/>
          <circle cx="49" cy="35" r="4" fill="#B94A5F"/>
          <circle cx="64" cy="35" r="4" fill="#765A62"/>
          <rect x="35" y="73" width="104" height="86" rx="8" fill="#23040D" stroke="#713244"/>
          <path d="M51 137l18-20 15 10 27-34" fill="none" stroke="#FF5825" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>
          <circle cx="111" cy="93" r="4" fill="#F5E9E9"/>
          <path d="M55 147h63" stroke="#D6C3C7" stroke-opacity=".48"/>
          <rect x="158" y="75" width="135" height="12" rx="6" fill="#F5E9E9" fill-opacity=".85"/>
          <rect x="158" y="99" width="100" height="8" rx="4" fill="#D6C3C7" fill-opacity=".58"/>
          <rect x="158" y="119" width="120" height="8" rx="4" fill="#D6C3C7" fill-opacity=".38"/>
          <rect x="158" y="144" width="74" height="22" rx="11" fill="#FF5825" fill-opacity=".16" stroke="#FF5825" stroke-opacity=".75"/>
          <circle cx="171" cy="155" r="4" fill="#FF5825"/>
          <path d="M181 155h39" stroke="#F5E9E9" stroke-opacity=".82" stroke-width="4" stroke-linecap="round"/>
          <path d="M299 57v-9h9M39 184v9h-9" fill="none" stroke="#FF5825" stroke-width="2" stroke-linecap="round"/>
        </svg>
      </div>
    </section>
    """,
    unsafe_allow_html=True,
)

if not CSV.exists():
    st.error("CSV da Etapa 2 não encontrado. Rode `python etapa2.py` primeiro.")
    st.stop()

assinatura = (CSV.stat().st_mtime_ns, NPZ.stat().st_mtime_ns if NPZ.exists() else None)

@st.cache_data(show_spinner="Carregando resultados da Etapa 2...")
def carregar_dados(assinatura):
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
    st.markdown('<div class="etapa2-kicker">Explorar os resultados</div>', unsafe_allow_html=True)
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
    [
        ":material/hub: Mapa semântico",
        ":material/notes: Termos e entidades",
        ":material/compare_arrows: Comparar modelos",
        ":material/search: Busca semântica",
        ":material/menu_book: Metodologia",
    ]
)


def tema_grafico(fig, altura=None):
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor=FUNDO_PAINEL,
        plot_bgcolor=FUNDO_PAINEL,
        font=dict(family="Arial, sans-serif", color=TEXTO_CLARO, size=13),
        title=dict(font=dict(family="Georgia, serif", color=TEXTO_CLARO, size=18), x=0.02, xanchor="left"),
        margin=dict(l=58, r=34, t=76, b=58),
        height=altura,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            x=0,
            bgcolor="rgba(49, 7, 19, .72)",
            bordercolor=VINHO_BORDA,
            borderwidth=1,
            font=dict(color=TEXTO_CLARO, size=12),
        ),
        hoverlabel=dict(
            bgcolor="#FFF7F5",
            bordercolor=VINHO_BORDA,
            font=dict(color="#3E1020", family="Arial, sans-serif"),
        ),
    )
    fig.update_xaxes(
        automargin=True,
        gridcolor="#713244",
        zerolinecolor="#A56B79",
        tickfont=dict(color=TEXTO_CLARO),
        title_font=dict(color=TEXTO_CLARO),
    )
    fig.update_yaxes(
        automargin=True,
        gridcolor="#713244",
        zerolinecolor="#A56B79",
        tickfont=dict(color=TEXTO_CLARO),
        title_font=dict(color=TEXTO_CLARO),
    )
    return fig


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
        fig.update_traces(marker={"size": 8, "line": {"width": 0.6, "color": "#23040D"}})
        tema_grafico(fig, altura=560)
        st.plotly_chart(fig, width="stretch")
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
                fig.update_traces(
                    marker_color=LARANJA,
                    marker_line_color="#FF9A72",
                    marker_line_width=0.6,
                    text=top_termos.sort_values("Frequência")["Frequência"],
                    textposition="outside",
                    textfont=dict(color=TEXTO_CLARO, size=11),
                    cliponaxis=False,
                )
                tema_grafico(fig, altura=max(430, 30 * len(top_termos) + 150))
                st.plotly_chart(fig, width="stretch")
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
                st.dataframe(entidades, hide_index=True, width="stretch")
    else:
        b.info("Coluna entidades_semanticas não encontrada no CSV.")
    st.markdown("**Comentários para conferir a interpretação**")
    colunas = [c for c in ["sentimento", "sentimento_transformer", "texto", "nome_video"] if c in filtrado]
    st.dataframe(filtrado[colunas].head(100), hide_index=True, width="stretch")

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
            fig.update_traces(
                colorscale=[[0, "#4A0B1D"], [0.55, "#A93435"], [1, "#FF9A72"]],
                textfont=dict(color=TEXTO_CLARO, size=13),
                hovertemplate="Principal: %{y}<br>Transformer: %{x}<br>Comentários: %{z}<extra></extra>",
            )
            tema_grafico(fig, altura=440)
            st.plotly_chart(fig, width="stretch")
            n = len(comparavel)
            acordo = (comparavel["sentimento"] == comparavel["sentimento_transformer"]).mean()
            st.metric("Concordância simples", f"{100 * acordo:.1f}%", f"{n:,} comentários comparáveis")
            st.warning("Concordância não mede acurácia. Para dizer qual modelo é melhor, compare ambos com uma amostra rotulada manualmente.")
            dist = pd.concat([
                comparavel["sentimento"].value_counts().rename_axis("Classe").rename("Quantidade").reset_index().assign(Modelo="Principal"),
                comparavel["sentimento_transformer"].value_counts().rename_axis("Classe").rename("Quantidade").reset_index().assign(Modelo="Transformer")
            ], ignore_index=True)
            fig = px.bar(
                dist,
                x="Classe",
                y="Quantidade",
                color="Modelo",
                barmode="group",
                color_discrete_sequence=[LARANJA, "#D8C8CC"],
            )
            fig.update_traces(marker_line_color="#23040D", marker_line_width=0.5)
            tema_grafico(fig, altura=430)
            st.plotly_chart(fig, width="stretch")

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
                         hide_index=True, width="stretch")
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
