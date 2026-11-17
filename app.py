"""Painel — IDEs mais citadas e sentimento sobre cada IDE nos comentários do YouTube.

Uso (na raiz do projeto, depois de rodar `python etapa1.py`):
    streamlit run app.py

O painel só lê dados/processados/*.csv e recalcula as estatísticas conforme os filtros.
"""
from pathlib import Path
from html import escape

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.analise import estatisticas as est, ides as an_ides

RAIZ = Path(__file__).resolve().parent
PROC = RAIZ / "dados" / "processados"
CORES = {"positivo": "#157750", "neutro": "#f15a24", "negativo": "#e9cbd1"}
COR_BASE = "#7b1230"
COR_TEXTO_GRAFICO = "#3e1020"
ORDENS = {"Saldo (% positivo − % negativo)": "saldo", "% positivo": "pct_positivo",
          "% negativo": "pct_negativo", "Nº de comentários": "n_comentarios"}

st.set_page_config(page_title="Qual a Melhor IDE?", page_icon="🧑‍💻", layout="wide")

st.markdown("""
<style>
:root {
    --wine-950: #23040d;
    --wine-900: #310713;
    --wine-800: #4a0b1d;
    --wine-700: #79122d;
    --wine-highlight: #4b0d1d;
    --wine-sidebar-top: #390916;
    --wine-sidebar-mid: #26050e;
    --wine-sidebar-bottom: #1d030a;
    --wine-border: #713244;
    --orange: #f15a24;
    --orange-deep: #bd3b19;
    --red-deep: #b92b1d;
    --paper: #fff7f5;
    --paper-border: #ead8dc;
    --ink: #3e1020;
    --ink-muted: #765a62;
    --text-primary: #f5e9e9;
    --text-secondary: #d6c3c7;
    --text-muted: #bfa8ae;
    --orange-rgb: 241, 90, 36;
}

.stApp, [data-testid="stAppViewContainer"] {
    background: radial-gradient(ellipse at 82% 0%, var(--wine-highlight) 0, var(--wine-950) 48rem);
    color: var(--text-primary);
}
[data-testid="stMain"] { color: var(--text-primary); }
[data-testid="stMain"] h1,
[data-testid="stMain"] h2,
[data-testid="stMain"] h3,
[data-testid="stMain"] h4 { color: var(--text-primary); }
[data-testid="stMain"] [data-testid="stMarkdownContainer"],
[data-testid="stMain"] [data-testid="stWidgetLabel"] {
    color: var(--text-primary);
}
[data-testid="stMain"] [data-testid="stCaptionContainer"] {
    color: var(--text-muted);
}
[data-testid="stHeader"] { background: transparent; }
[data-testid="stSidebar"] {
    background: linear-gradient(165deg, var(--wine-sidebar-top) 0%, var(--wine-sidebar-mid) 68%,
        var(--wine-sidebar-bottom) 100%);
    border-right: 1px solid rgba(var(--orange-rgb), .28);
}
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {
    color: var(--text-primary) !important;
}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"],
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
[data-testid="stSidebar"] [data-testid="stWidgetLabel"],
[data-testid="stSidebar"] label {
    color: var(--text-primary);
}
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] {
    color: var(--text-secondary);
}
[data-testid="stSidebar"] [data-testid="stExpander"] summary,
[data-testid="stSidebar"] [data-testid="stExpander"] button {
    color: var(--text-primary);
}
.main .block-container { max-width: 1600px; padding-top: 2rem; padding-bottom: 3rem; }
[data-testid="stMetric"] {
    background: linear-gradient(145deg, rgba(117, 18, 45, .78), rgba(61, 8, 24, .88));
    border: 1px solid rgba(var(--orange-rgb), .27);
    border-radius: 15px;
    padding: 1rem 1.2rem;
    min-height: 112px;
}
[data-testid="stMetricLabel"] { color: var(--text-secondary) !important; }
[data-testid="stMetricValue"] { color: var(--text-primary) !important; }
[data-testid="stMetricDelta"] [data-testid="stMarkdownContainer"],
[data-testid="stMetricDelta"] [data-testid="stMarkdownContainer"] * {
    color: #FF5722 !important;
    font-weight: 700 !important;
}
[data-testid="stMetricDelta"] [data-testid="stMarkdownContainer"]::selection,
[data-testid="stMetricDelta"] [data-testid="stMarkdownContainer"] *::selection {
    background: #FF5722;
    color: #FFFFFF !important;
}
[data-testid="stTabs"] [role="tab"] {
    color: var(--text-secondary);
    border-radius: 10px 10px 0 0;
}
[data-testid="stTabs"] [role="tab"] [data-testid="stMarkdownContainer"] p {
    display: flex;
    align-items: center;
    gap: .4rem;
    margin: 0;
}
[data-testid="stTabs"] [role="tab"][aria-selected="true"] {
    color: var(--text-primary);
    border-bottom-color: var(--orange);
    background-color: rgba(var(--orange-rgb), .1);
}
[data-testid="stTabs"] [role="tab"]:hover,
[data-testid="stTabs"] [role="tab"]:focus-visible {
    color: var(--text-primary);
}
[data-testid="stTabs"] [role="tab"]:focus-visible {
    outline: 2px solid var(--orange);
    outline-offset: 2px;
}
[data-baseweb="select"] > div,
[data-baseweb="input"] > div {
    background-color: var(--paper);
    border-color: #b98594;
    color: var(--ink);
}
[data-baseweb="select"] input,
[data-baseweb="input"] input {
    color: var(--ink) !important;
    -webkit-text-fill-color: var(--ink);
}
[data-baseweb="select"] input::placeholder,
[data-baseweb="input"] input::placeholder {
    color: var(--ink-muted) !important;
    -webkit-text-fill-color: var(--ink-muted);
}
[data-baseweb="tag"] {
    background-color: #ead8dc;
    color: var(--ink);
}
[data-baseweb="tag"] * { color: var(--ink) !important; }
[data-testid="stSlider"] [data-testid="stThumbValue"] {
    color: var(--text-primary);
    background-color: var(--wine-700);
}
[data-baseweb="select"] > div:focus-within,
[data-baseweb="input"] > div:focus-within,
[data-baseweb="select"] input:focus-visible,
[data-baseweb="input"] input:focus-visible {
    outline: 2px solid var(--orange);
    outline-offset: 1px;
}
[data-baseweb="popover"] {
    background-color: var(--paper);
    border: 1px solid var(--paper-border);
}
[role="listbox"] { background-color: var(--paper); }
[role="option"] {
    background-color: var(--paper);
    color: var(--ink);
}
[role="option"]:hover,
[role="option"][aria-selected="true"] {
    background-color: #ead8dc;
    color: var(--ink);
}
button:disabled {
    background-color: #5a2635;
    border-color: var(--wine-border);
    color: var(--text-secondary);
    opacity: 1;
    cursor: not-allowed;
}
[data-testid="stVerticalBlockBorderWrapper"] {
    background: var(--paper);
    border-color: var(--paper-border);
    border-radius: 15px;
    color: var(--ink);
}
[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stMarkdownContainer"],
[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stCaptionContainer"],
[data-testid="stVerticalBlockBorderWrapper"] label,
[data-testid="stVerticalBlockBorderWrapper"] h1,
[data-testid="stVerticalBlockBorderWrapper"] h2,
[data-testid="stVerticalBlockBorderWrapper"] h3 {
    color: var(--ink);
}
[data-testid="stDataFrame"], [data-testid="stTable"] { color: var(--ink); }
[data-testid="stAlert"] { border-radius: 12px; }
button[kind="primary"], [data-testid="stDownloadButton"] button {
    background: linear-gradient(100deg, var(--orange-deep), var(--red-deep));
    border: 0;
    color: var(--text-primary);
    border-radius: 9px;
}
button:focus-visible,
[data-testid="stDownloadButton"] button:focus-visible {
    outline: 2px solid var(--orange);
    outline-offset: 2px;
}
.brand {
    padding: .8rem .25rem 1.1rem;
    border-bottom: 1px solid rgba(var(--orange-rgb), .28);
    margin-bottom: .5rem;
}
.brand-mark {
    display: inline-flex;
    width: 52px;
    height: 48px;
    align-items: center;
    justify-content: center;
    border: 2px solid var(--text-primary);
    border-right-color: var(--orange);
    border-radius: 13px 13px 13px 4px;
    color: var(--orange);
    font: 800 17px ui-monospace, monospace;
    margin-bottom: .8rem;
}
.brand-name { color: var(--text-primary); font: 700 1.45rem Georgia, serif; line-height: 1.1; }
.brand-name em { color: var(--orange); font: italic 800 1.6rem Arial, sans-serif; }
.brand-description { color: var(--text-secondary); font-size: .82rem; line-height: 1.5; margin-top: .7rem; }
.section-label {
    color: #ff9a72;
    font-size: .7rem;
    font-weight: 750;
    letter-spacing: .14em;
    text-transform: uppercase;
    margin-bottom: .45rem;
}
.hero {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 2rem;
    padding: .6rem 0 1.5rem;
}
.hero-copy { max-width: 760px; }
.hero h1 {
    color: var(--text-primary);
    font: 700 clamp(2.4rem, 5vw, 4.5rem)/.98 Georgia, serif;
    letter-spacing: -.04em;
    margin: .25rem 0 .9rem;
}
.hero h1 span { color: var(--orange); font: 800 .98em Arial, sans-serif; }
.hero p { color: var(--text-secondary); font-size: 1.04rem; line-height: 1.55; margin: 0; max-width: 690px; }
.hero-art {
    flex: 0 0 245px;
    min-height: 142px;
    padding: 1rem;
    border: 1px solid rgba(241, 90, 36, .4);
    border-radius: 14px;
    background: linear-gradient(145deg, rgba(116, 17, 44, .75), rgba(46, 5, 17, .85));
    box-shadow: 0 18px 40px rgba(0, 0, 0, .18);
    color: #f08a6b;
    font: .78rem/1.8 ui-monospace, SFMono-Regular, Menlo, monospace;
}
.hero-art strong { color: #fff4f0; font-weight: 500; }
.hero-art .orange { color: var(--orange); }
.panel-heading {
    color: #FFFFFF !important;
    font: 700 1.2rem Georgia, serif;
    font-weight: 700 !important;
    margin: 0 0 .2rem;
}
.panel-copy { color: var(--ink-muted); font-size: .88rem; line-height: 1.45; margin-bottom: .7rem; }
.insight {
    display: flex;
    align-items: flex-start;
    gap: .8rem;
    padding: .9rem 0;
    border-top: 1px solid #d9c3c9;
}
.insight:first-of-type { border-top: 0; }
.insight-icon {
    display: flex; flex: 0 0 40px; height: 40px; align-items: center; justify-content: center;
    border-radius: 50%; background: var(--wine-700); color: var(--text-primary);
    font-size: 1.15rem; font-weight: 700;
}
.insight:nth-of-type(3) .insight-icon { background: var(--orange); color: var(--ink); }
.insight h4 { color: #FFFFFF !important; font-size: .94rem; line-height: 1.35; margin: 0 0 .25rem; }
.insight p { color: #FFFFFF !important; font-size: .84rem; line-height: 1.5; margin: 0; }
[data-testid="stVerticalBlockBorderWrapper"]:has(.insight) {
    background: linear-gradient(145deg, var(--wine-900), var(--wine-950));
    border-color: var(--wine-border);
}
[data-testid="stVerticalBlockBorderWrapper"]:has(.insight) .panel-copy {
    color: var(--text-secondary);
}
.conclusion {
    display: flex; justify-content: space-between; align-items: center; gap: 2rem;
    padding: 1.1rem 1.35rem; border: 1px solid rgba(var(--orange-rgb), .32);
    border-radius: 14px; background: linear-gradient(110deg, var(--wine-800), #300713);
}
.conclusion strong { color: var(--text-primary); font: 700 1.1rem Georgia, serif; }
.conclusion p { color: var(--text-secondary); margin: .4rem 0 0; font-size: .9rem; }
.conclusion-tag { color: #ff9a72; font: italic 700 1.2rem Georgia, serif; max-width: 220px; }
@media (max-width: 850px) {
    .hero-art { display: none; }
    .conclusion { align-items: flex-start; flex-direction: column; gap: .8rem; }
}
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------- dados
@st.cache_data(show_spinner="Carregando dados...")
def carregar(assinatura: tuple):
    """`assinatura` (data de modificação dos arquivos) faz o cache se renovar após rodar o etapa1.py."""
    mencoes = pd.read_csv(PROC / "mencoes_ides.csv")
    mencoes["lemas"] = mencoes["lemas"].fillna("")
    comentarios = pd.read_csv(PROC / "comentarios_sentimento.csv")
    return mencoes, comentarios


@st.cache_data(show_spinner=False)
def resumo(mencoes: pd.DataFrame, min_mencoes: int) -> pd.DataFrame:
    return an_ides.resumo_por_ide(mencoes, min_mencoes, n_boot=500)


def curto(texto: str, tam: int = 48) -> str:
    texto = str(texto)
    return texto if len(texto) <= tam else texto[: tam - 1] + "…"


def figura(fig: go.Figure, altura: int = None, legenda_inferior: bool = False) -> go.Figure:
    fig.update_layout(
        template="plotly_white",
        paper_bgcolor="#fff7f5",
        plot_bgcolor="#fff7f5",
        font=dict(family="Arial, sans-serif", color=COR_TEXTO_GRAFICO),
        margin=dict(l=18, r=18, t=62, b=24),
        height=altura,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0,
                    font=dict(color=COR_TEXTO_GRAFICO)),
    )
    if legenda_inferior:
        fig.update_layout(
            margin=dict(l=18, r=18, t=72, b=88),
            legend=dict(orientation="h", yanchor="top", y=-0.18, x=0, xanchor="left",
                        font=dict(color=COR_TEXTO_GRAFICO)),
        )
    fig.update_xaxes(gridcolor="#ead8dc", zerolinecolor="#d9c3c9")
    fig.update_yaxes(gridcolor="#ead8dc", zerolinecolor="#d9c3c9")
    return fig


arquivos = [PROC / "mencoes_ides.csv", PROC / "comentarios_sentimento.csv"]
if not all(a.exists() for a in arquivos):
    st.error("Não encontrei os dados. Rode `python etapa1.py` na raiz do projeto e recarregue esta página.")
    st.stop()
mencoes_all, comentarios = carregar(tuple(a.stat().st_mtime for a in arquivos))
if mencoes_all.empty:
    st.warning("Nenhuma IDE do catálogo foi citada nos comentários. Confira `src/preprocessamento/ides.py`.")
    st.stop()
metodo = comentarios["metodo_sentimento"].iloc[0]

# ---------------------------------------------------------------- filtros
with st.sidebar:
    st.markdown(
        '<div class="brand"><div class="brand-mark">&lt;/&gt;</div>'
        '<div class="brand-name">Qual a Melhor<br><em>IDE?</em></div>'
        '<div class="brand-description">Análise de sentimentos com dados reais da comunidade de desenvolvedores.</div>'
        '</div><div class="section-label">Explorar a pesquisa</div>',
        unsafe_allow_html=True,
    )
    st.header("Filtros")
    min_mencoes = st.slider("Mínimo de comentários por IDE", 1, 50, 10,
                            help="IDEs com menos comentários que isso ficam fora dos gráficos de sentimento: "
                                 "percentuais com poucas menções variam demais.")
    contagem = mencoes_all["ide"].value_counts()
    opcoes_ide = contagem.index.tolist()
    padrao_ide = contagem[contagem >= min_mencoes].index.tolist() or opcoes_ide[:5]
    ides_sel = st.multiselect("IDEs", opcoes_ide, default=padrao_ide,
                              format_func=lambda i: f"{i} ({contagem[i]})")
    videos = (mencoes_all.groupby("nome_video")["video_id"].size().sort_values(ascending=False))
    with st.expander("Vídeos", expanded=False):
        videos_sel = st.multiselect("Vídeos incluídos", videos.index.tolist(), default=videos.index.tolist(),
                                    format_func=curto, label_visibility="collapsed")
    so_isoladas = st.toggle("Só citações isoladas", value=False,
                            help="Tira os trechos que citam outra IDE na mesma frase (comparações e listas), "
                                 "onde o sentimento fica ambíguo.")
    st.caption(f"Método de sentimento: **{metodo}**")

mask = mencoes_all["ide"].isin(ides_sel) & mencoes_all["nome_video"].isin(videos_sel)
if so_isoladas:
    mask &= mencoes_all["isolada"]
m = mencoes_all[mask].reset_index(drop=True)

# ---------------------------------------------------------------- cabeçalho
if metodo != "pysentimiento":
    st.warning("O modelo pysentimiento não foi usado (léxico de reserva). Não apresente estes resultados como finais.")
if m.empty:
    st.info("Nenhuma menção com os filtros atuais. Ajuste a barra lateral.")
    st.stop()

r = resumo(m, min_mencoes)
ok = r[r["amostra_suficiente"]]

st.markdown(
    '<section class="hero"><div class="hero-copy">'
    '<div class="section-label">Pesquisa · comunidade · desenvolvimento</div>'
    '<h1>Qual a Melhor<br><span>IDE?</span></h1>'
    '<p>Descubra o que a comunidade realmente pensa sobre as principais IDEs, '
    'a partir da análise de sentimentos em comentários públicos do YouTube.</p>'
    '</div><div class="hero-art"><span class="orange">●</span> pesquisa.py<br>'
    '&nbsp;&nbsp;<strong>sentimentos</strong> = analisar(comentarios)<br>'
    '&nbsp;&nbsp;<span class="orange">comparar</span>(sentimentos, ides)<br>'
    '&nbsp;&nbsp;resultado: <strong>opiniões reais</strong></div></section>',
    unsafe_allow_html=True,
)

total_mencoes = len(m)
contagem_sentimentos = m["sentimento"].value_counts()
k1, k2, k3, k4 = st.columns(4)
k1.metric("Menções analisadas", f"{total_mencoes:,}".replace(",", "."),
          f"{m['comentario_id'].nunique():,} comentários únicos".replace(",", "."), delta_color="off", border=True)
for coluna, sentimento, rotulo in ((k2, "positivo", "Sentimento positivo"),
                                    (k3, "neutro", "Sentimento neutro"),
                                    (k4, "negativo", "Sentimento negativo")):
    quantidade = int(contagem_sentimentos.get(sentimento, 0))
    coluna.metric(rotulo, f"{100 * quantidade / total_mencoes:.1f}%",
                  f"{quantidade:,} menções".replace(",", "."), delta_color="off", border=True)

aba_geral, aba_sent, aba_porque, aba_video, aba_explorar, aba_sobre = st.tabs(
    [":material/bar_chart: Mais citadas", ":material/sentiment_satisfied: Sentimento por IDE",
     ":material/search: Por quê?", ":material/movie: IDE × vídeo",
     ":material/forum: Comentários", ":material/info: Sobre"])

# ---------------------------------------------------------------- 1. mais citadas
with aba_geral:
    top = r.head(10)
    c1, c2, c3 = st.columns(3)
    c1.metric("IDE mais citada", top.iloc[0]["ide"], f"{top.iloc[0]['n_comentarios']} comentários", delta_color="off",
              border=True)
    if len(ok):
        melhor, pior = ok.loc[ok["saldo"].idxmax()], ok.loc[ok["saldo"].idxmin()]
        c2.metric("Melhor saldo", melhor["ide"], f"{melhor['saldo']:+.0f} p.p. (n={melhor['n_comentarios']})",
                  border=True)
        c3.metric("Pior saldo", pior["ide"], f"{pior['saldo']:+.0f} p.p. (n={pior['n_comentarios']})", border=True)
    painel_grafico, painel_insights = st.columns([1.7, 1], gap="medium")
    with painel_grafico:
        with st.container(border=True):
            st.markdown('<div class="panel-heading">Comparativo de menções</div>'
                        '<div class="panel-copy">Veja quais ferramentas aparecem com mais frequência na conversa.</div>',
                        unsafe_allow_html=True)
            fig = go.Figure(go.Bar(
                y=top["ide"], x=top["n_comentarios"], orientation="h", marker_color=COR_BASE,
                text=[f"{n} ({p:.0f}%)" for n, p in zip(top["n_comentarios"], top["pct_das_mencoes"])],
                textposition="outside", cliponaxis=False,
                customdata=top[["n_videos", "curtidas_total"]],
                hovertemplate="<b>%{y}</b><br>%{x} comentários<br>%{customdata[0]} vídeos<br>"
                              "%{customdata[1]} curtidas nos comentários<extra></extra>"))
            fig.update_yaxes(autorange="reversed")
            fig.update_xaxes(title="Comentários que citam a IDE",
                             range=[0, top["n_comentarios"].max() * 1.2])
            fig.update_layout(title="IDEs mais citadas")
            st.plotly_chart(figura(fig, 100 + 35 * len(top)), width="stretch")

    with painel_insights:
        if len(ok):
            lider_positivo = ok.loc[ok["pct_positivo"].idxmax()]
            maior_amostra = top.iloc[0]
            lider_negativo = ok.loc[ok["pct_negativo"].idxmax()]
            itens_insight = [
                ("↗", f"{escape(str(lider_positivo['ide']))}: maior proporção positiva",
                 f"{lider_positivo['pct_positivo']:.1f}% de sentimentos positivos em "
                 f"{int(lider_positivo['n_comentarios'])} menções."),
                ("◎", f"{escape(str(maior_amostra['ide']))}: mais mencionada",
                 f"{int(maior_amostra['n_comentarios'])} comentários em {int(maior_amostra['n_videos'])} vídeos."),
                ("!", f"{escape(str(lider_negativo['ide']))}: mais avaliações negativas",
                 f"{lider_negativo['pct_negativo']:.1f}% negativas; considere o tamanho da amostra ao comparar."),
            ]
        else:
            itens_insight = [
                ("!", "Amostra insuficiente",
                 f"Nenhuma IDE atingiu o mínimo de {min_mencoes} menções para comparações de sentimento.")
            ]
        html_insights = "".join(
            f'<article class="insight"><span class="insight-icon">{icone}</span>'
            f'<div><h4>{titulo}</h4><p>{descricao}</p></div></article>'
            for icone, titulo, descricao in itens_insight
        )
        with st.container(border=True):
            st.markdown(
                '<div class="panel-heading">Insights da amostra</div>'
                '<div class="panel-copy">Sinais observados nos filtros atuais, sem extrapolar a amostra.</div>'
                + html_insights,
                unsafe_allow_html=True,
            )

    if len(ok):
        destaque = ok.loc[ok["saldo"].idxmax()]
        resumo_conclusao = (
            f"{escape(str(destaque['ide']))} apresenta o maior saldo observado "
            f"({destaque['saldo']:+.1f} pontos percentuais) entre as {len(ok)} IDEs "
            f"com pelo menos {min_mencoes} menções. Isso é um sinal descritivo, não uma prova "
            "de que as diferenças sejam estatisticamente significativas."
        )
    else:
        resumo_conclusao = (
            f"Nenhuma IDE alcançou o mínimo de {min_mencoes} menções. Reduza o limite nos filtros "
            "para explorar os resultados, sempre considerando a incerteza de amostras pequenas."
        )
    st.markdown(
        '<section class="conclusion"><div><strong>Conclusão da amostra</strong>'
        f'<p>{resumo_conclusao}</p></div>'
        '<div class="conclusion-tag">Dados que ajudam<br>a escolher melhor.</div></section>',
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------------- 2. sentimento
with aba_sent:
    if ok.empty:
        st.info(f"Nenhuma IDE chegou a {min_mencoes} comentários. Diminua o mínimo na barra lateral.")
    else:
        ordem_nome = st.radio("Ordenar por", list(ORDENS), horizontal=True)
        o = ok.sort_values(ORDENS[ordem_nome], ascending=False)
        rotulos = [f"{i}  (n={n})" for i, n in zip(o["ide"], o["n_comentarios"])]
        fig = go.Figure()
        for s in est.ORDEM:
            fig.add_trace(go.Bar(
                y=rotulos, x=o[f"pct_{s}"], name=s, orientation="h", marker_color=CORES[s],
                text=[f"{v:.0f}%" if v >= 6 else "" for v in o[f"pct_{s}"]], textposition="inside",
                textfont_color="#fff7f5" if s == "positivo" else COR_TEXTO_GRAFICO,
                hovertemplate="<b>%{y}</b><br>" + s + ": %{x:.1f}%<extra></extra>"))
        fig.update_layout(barmode="stack", title="Sentimento sobre cada IDE")
        fig.update_yaxes(autorange="reversed", automargin=True)
        fig.update_xaxes(title="% dos comentários que citam a IDE", range=[0, 100], automargin=True)
        st.plotly_chart(figura(fig, 160 + 36 * len(o), legenda_inferior=True), width="stretch")

        st.subheader("As diferenças entre IDEs são reais?")
        st.caption("Ponto = % de positivos. Barra escura = intervalo de confiança de 95% (Wilson). "
                   "Barra amarela = intervalo sorteando **vídeos** (mais conservador; só com 5+ vídeos). "
                   "**Barras que se sobrepõem: não dá para afirmar que as IDEs diferem.**")
        mostrar_video = st.toggle("Mostrar intervalo por vídeo (bootstrap)", value=True)
        d = ok.sort_values("pct_positivo", ascending=False).reset_index(drop=True)
        fig = go.Figure()
        y = list(range(len(d)))
        fig.add_trace(go.Scatter(
            x=d["pct_positivo"], y=[i + 0.12 for i in y], mode="markers", name="IC por comentário (Wilson)",
            marker=dict(color=COR_BASE, size=10),
            error_x=dict(type="data", symmetric=False, color=COR_BASE, thickness=3, width=0,
                         array=d["ic_positivo_sup"] - d["pct_positivo"],
                         arrayminus=d["pct_positivo"] - d["ic_positivo_inf"]),
            hovertemplate="%{x:.0f}% positivos<extra></extra>"))
        if mostrar_video and d["ic_video_positivo_inf"].notna().any():
            dv = d.dropna(subset=["ic_video_positivo_inf"])
            fig.add_trace(go.Scatter(
                x=dv["pct_positivo"], y=[i - 0.12 for i in dv.index], mode="markers", name="IC por vídeo (bootstrap)",
                marker=dict(color="#e9c46a", size=10),
                error_x=dict(type="data", symmetric=False, color="#e9c46a", thickness=3, width=0,
                             array=dv["ic_video_positivo_sup"] - dv["pct_positivo"],
                             arrayminus=dv["pct_positivo"] - dv["ic_video_positivo_inf"]),
                hovertemplate="%{x:.0f}% positivos<extra></extra>"))
        fig.update_yaxes(tickmode="array", tickvals=y, ticktext=[f"{i} (n={n})" for i, n in zip(d["ide"], d["n_comentarios"])],
                         autorange="reversed", automargin=True)
        fig.update_xaxes(title="% de comentários positivos", range=[0, 100])
        st.plotly_chart(figura(fig, 160 + 44 * len(d), legenda_inferior=True), width="stretch")

        st.subheader("Tabela")
        tabela = pd.DataFrame({
            "IDE": o["ide"], "Comentários": o["n_comentarios"], "Vídeos": o["n_videos"],
            "% positivo": o["pct_positivo"], "% neutro": o["pct_neutro"], "% negativo": o["pct_negativo"],
            "Saldo": o["saldo"], "Score médio": o["score_medio"], "% citações isoladas": o["pct_isoladas"],
            "IC positivos (95%)": [f"{lo:.0f}–{hi:.0f}%" for lo, hi in zip(o["ic_positivo_inf"], o["ic_positivo_sup"])]})
        st.dataframe(
            tabela, hide_index=True, width="stretch",
            column_config={
                "% positivo": st.column_config.ProgressColumn(format="%.0f%%", min_value=0, max_value=100),
                "% neutro": st.column_config.NumberColumn(format="%.0f%%"),
                "% negativo": st.column_config.NumberColumn(format="%.0f%%"),
                "Saldo": st.column_config.NumberColumn(format="%+.0f"),
                "Score médio": st.column_config.NumberColumn(format="%.2f"),
                "% citações isoladas": st.column_config.NumberColumn(
                    format="%.0f%%", help="% das menções cujo trecho cita só essa IDE. Quanto menor, mais "
                                          "comparações no meio: leia o sentimento com cuidado.")})
        poucas = r[~r["amostra_suficiente"]]
        if len(poucas):
            st.caption("Fora por ter poucas menções: " + ", ".join(f"{i} ({n})" for i, n in zip(poucas["ide"], poucas["n_comentarios"])))

# ---------------------------------------------------------------- 3. por quê
with aba_porque:
    escolha = st.selectbox("Escolha uma IDE", r["ide"].tolist(),
                           format_func=lambda i: f"{i} ({int(r.loc[r['ide'] == i, 'n_comentarios'].iloc[0])} comentários)")
    sub = m[m["ide"] == escolha]
    linha = r[r["ide"] == escolha].iloc[0]
    a, b, c, d_ = st.columns(4)
    a.metric("Comentários", int(linha["n_comentarios"]), border=True)
    b.metric("Positivo", f"{linha['pct_positivo']:.0f}%", border=True)
    c.metric("Neutro", f"{linha['pct_neutro']:.0f}%", border=True)
    d_.metric("Negativo", f"{linha['pct_negativo']:.0f}%", border=True)
    if not linha["amostra_suficiente"]:
        st.warning(f"Só {int(linha['n_comentarios'])} comentários: leia com cautela.")

    freq_min = st.number_input("Frequência mínima do termo", 1, 20, 2)
    termos = an_ides.termos_por_ide(sub, [escolha], n=10, min_freq=freq_min)
    col_pos, col_neg = st.columns(2)
    for coluna, s, titulo in ((col_pos, "positivo", "👍 Palavras nos comentários positivos"),
                              (col_neg, "negativo", "👎 Palavras nos comentários negativos")):
        t = termos[termos["sentimento"] == s]
        with coluna:
            if t.empty:
                st.caption(f"{titulo}: sem termos com {freq_min}+ ocorrências.")
                continue
            fig = go.Figure(go.Bar(y=t["termo"], x=t["frequencia"], orientation="h", marker_color=CORES[s],
                                   text=t["frequencia"], textposition="outside", cliponaxis=False))
            fig.update_yaxes(autorange="reversed")
            fig.update_layout(title=titulo, showlegend=False)
            st.plotly_chart(figura(fig, 90 + 32 * len(t)), width="stretch")

    st.subheader("Comentários mais curtidos")
    ex_pos, ex_neg = st.columns(2)
    for coluna, s, titulo in ((ex_pos, "positivo", "Positivos"), (ex_neg, "negativo", "Negativos")):
        with coluna:
            st.markdown(f"**{titulo}**")
            top_ex = sub[sub["sentimento"] == s].nlargest(4, "curtidas")
            if top_ex.empty:
                st.caption("Nenhum comentário.")
            for _, l in top_ex.iterrows():
                with st.container(border=True):
                    st.write(l["texto_mencao"])
                    st.caption(f"👍 {l['curtidas']} · score {l['score']:+.2f} · {curto(l['nome_video'], 50)}"
                               + ("" if l["isolada"] else " · cita outra IDE no trecho"))

# ---------------------------------------------------------------- 4. IDE × vídeo
with aba_video:
    st.caption("Cada linha é uma IDE e cada coluna é um vídeo: onde cada IDE aparece e como é tratada.")
    metrica = st.radio("Mostrar", ["Nº de comentários", "Saldo (% positivo − % negativo)"], horizontal=True)
    base = m[m["ide"].isin(ok["ide"] if len(ok) else r["ide"])]
    nomes = base.groupby("video_id")["nome_video"].first()
    cont = base.pivot_table(index="ide", columns="video_id", values="comentario_id", aggfunc="count", fill_value=0)
    cont = cont.loc[[i for i in r["ide"] if i in cont.index]]
    cont.columns = [curto(nomes[c], 34) for c in cont.columns]
    if metrica.startswith("Nº"):
        z, escala, zmid, fmt = cont.where(cont > 0), "Blues", None, "%{z}"
        titulo = "Comentários por IDE e vídeo"
    else:
        celula_min = st.slider("Mínimo de comentários por célula", 1, 10, 3,
                               help="Células com menos comentários ficam vazias: saldo com 1 ou 2 comentários não diz nada.")
        sinal = base.assign(v=base["sentimento"].map({"positivo": 100, "neutro": 0, "negativo": -100}))
        saldo = sinal.pivot_table(index="ide", columns="video_id", values="v", aggfunc="mean")
        saldo = saldo.loc[cont.index]
        saldo.columns = cont.columns
        z, escala, zmid, fmt = saldo.where(cont >= celula_min), "RdYlGn", 0, "%{z:+.0f}"
        titulo = "Saldo por IDE e vídeo"
    fig = go.Figure(go.Heatmap(z=z.values, x=z.columns, y=z.index, colorscale=escala, zmid=zmid, xgap=2, ygap=2,
                               hovertemplate="<b>%{y}</b><br>%{x}<br>" + fmt.replace("%{z", "valor: %{z") + "<extra></extra>",
                               colorbar=dict(title="")))
    fig.update_yaxes(autorange="reversed")
    fig.update_xaxes(tickangle=-45)
    fig.update_layout(title=titulo)
    st.plotly_chart(figura(fig, 260 + 30 * len(z)), width="stretch")

# ---------------------------------------------------------------- 5. comentários
with aba_explorar:
    f1, f2, f3 = st.columns([2, 2, 3])
    sent_sel = f1.multiselect("Sentimento", est.ORDEM, default=est.ORDEM)
    ide_ex = f2.multiselect("IDE", r["ide"].tolist(), placeholder="Todas")
    busca = f3.text_input("Contém o texto", placeholder="ex.: lento, plugin, autocomplete")
    t = m[m["sentimento"].isin(sent_sel)]
    if ide_ex:
        t = t[t["ide"].isin(ide_ex)]
    if busca.strip():
        t = t[t["texto_mencao"].str.contains(busca.strip(), case=False, regex=False, na=False)]
    t = t.sort_values("curtidas", ascending=False)
    st.caption(f"{len(t)} menções")
    mostrar = t[["ide", "sentimento", "score", "curtidas", "nome_video", "texto_mencao", "escopo_texto"]].rename(columns={
        "ide": "IDE", "sentimento": "Sentimento", "score": "Score", "curtidas": "Curtidas", "nome_video": "Vídeo",
        "texto_mencao": "Trecho analisado", "escopo_texto": "Escopo"})
    st.dataframe(mostrar, hide_index=True, width="stretch",
                 column_config={"Score": st.column_config.NumberColumn(format="%+.2f"),
                                "Trecho analisado": st.column_config.TextColumn(width="large")})
    st.download_button("Baixar estas menções (CSV)", mostrar.to_csv(index=False).encode("utf-8-sig"),
                       "mencoes_filtradas.csv", "text/csv")

# ---------------------------------------------------------------- 6. sobre
with aba_sobre:
    st.subheader("Como ler")
    st.markdown(
        "- **Menção** = um comentário que cita a IDE. Se cita só uma, vale o comentário inteiro; se cita várias, "
        "vale a frase (ou o trecho entre vírgulas/\"mas\") em que ela aparece.\n"
        "- **Saldo** = % positivo − % negativo. **Intervalos que se sobrepõem** = não dá para afirmar diferença.\n"
        "- **Citação isolada** = o trecho analisado cita só aquela IDE (sem comparação).")
    st.subheader("Qualidade da detecção")
    e1, e2 = st.columns(2)
    esc = mencoes_all["escopo_texto"].value_counts()
    e1.dataframe(esc.rename_axis("Escopo do texto").rename("Menções").reset_index(), hide_index=True, width="stretch")
    e2.metric("Citações isoladas (todas as menções)", f"{100 * mencoes_all['isolada'].mean():.0f}%", border=True)
    amb = mencoes_all[mencoes_all["ide"].isin(["Cursor", "Atom", "Zed", "Rider"])]
    if len(amb):
        with st.expander("Nomes ambíguos (Cursor, Atom, Zed, Rider): confira se falam da IDE"):
            st.dataframe(amb.groupby("ide").head(5)[["ide", "texto_mencao"]], hide_index=True, width="stretch")
    st.subheader("Limitações")
    st.markdown(
        "- Só entram comentários que **citam o nome** da IDE; IDEs fora do catálogo "
        "(`src/preprocessamento/ides.py`) não aparecem.\n"
        "- O sentimento é do **trecho**, não uma opinião estruturada: reflete também tom, ironia e elogio ao criador. "
        "Em comparações (\"X é melhor que Y\"), o modelo tende a dar o mesmo rótulo às duas.\n"
        "- Poucas menções por IDE e comentários do mesmo vídeo parecidos entre si: use os intervalos de confiança.\n"
        "- Vários vídeos são dos mesmos canais; o público de cada vídeo pode favorecer certas IDEs.\n"
        "- A amostra são os comentários mais recentes de cada vídeo.")
