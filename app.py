"""Painel — IDEs mais citadas e sentimento sobre cada IDE nos comentários do YouTube.

Uso (na raiz do projeto, depois de rodar `python etapa1.py`):
    streamlit run app.py

O painel só lê dados/processados/*.csv e recalcula as estatísticas conforme os filtros.
"""
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.analise import estatisticas as est, ides as an_ides

RAIZ = Path(__file__).resolve().parent
PROC = RAIZ / "dados" / "processados"
CORES = {"positivo": "#2a9d8f", "neutro": "#bdbdbd", "negativo": "#e76f51"}
COR_BASE = "#264653"
ORDENS = {"Saldo (% positivo − % negativo)": "saldo", "% positivo": "pct_positivo",
          "% negativo": "pct_negativo", "Nº de comentários": "n_comentarios"}

st.set_page_config(page_title="IDEs nos comentários do YouTube", page_icon="🧑‍💻", layout="wide")


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


def figura(fig: go.Figure, altura: int = None) -> go.Figure:
    fig.update_layout(margin=dict(l=10, r=10, t=50, b=10), height=altura,
                      legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0))
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
st.title("🧑‍💻 O que dizem os comentários sobre cada IDE")
st.caption("Comentários públicos de vídeos do YouTube sobre IDEs. Cada menção é um comentário que cita a IDE; "
           "o sentimento é o do trecho que fala dela.")
if metodo != "pysentimiento":
    st.warning("O modelo pysentimiento não foi usado (léxico de reserva). Não apresente estes resultados como finais.")
if m.empty:
    st.info("Nenhuma menção com os filtros atuais. Ajuste a barra lateral.")
    st.stop()

r = resumo(m, min_mencoes)
ok = r[r["amostra_suficiente"]]

k1, k2, k3, k4 = st.columns(4)
k1.metric("Comentários classificados", f"{len(comentarios):,}".replace(",", "."), border=True)
n_citam = m["comentario_id"].nunique()
k2.metric("Citam alguma IDE", f"{n_citam:,}".replace(",", "."),
          f"{100 * n_citam / len(comentarios):.0f}% do total", delta_color="off", border=True)
k3.metric("IDEs na análise", f"{r['ide'].nunique()}", f"{len(ok)} com {min_mencoes}+ comentários",
          delta_color="off", border=True)
saldo_geral = 100 * ((m["sentimento"] == "positivo").mean() - (m["sentimento"] == "negativo").mean())
k4.metric("Saldo geral das menções", f"{saldo_geral:+.0f} p.p.",
          help="% positivo − % negativo, juntando todas as menções filtradas.", border=True)

aba_geral, aba_sent, aba_porque, aba_video, aba_explorar, aba_sobre = st.tabs(
    ["📊 Mais citadas", "🎭 Sentimento por IDE", "🔍 Por quê?", "🎬 IDE × vídeo", "💬 Comentários", "ℹ️ Sobre"])

# ---------------------------------------------------------------- 1. mais citadas
with aba_geral:
    top = r.head(15)
    c1, c2, c3 = st.columns(3)
    c1.metric("IDE mais citada", top.iloc[0]["ide"], f"{top.iloc[0]['n_comentarios']} comentários", delta_color="off",
              border=True)
    if len(ok):
        melhor, pior = ok.loc[ok["saldo"].idxmax()], ok.loc[ok["saldo"].idxmin()]
        c2.metric("Melhor saldo", melhor["ide"], f"{melhor['saldo']:+.0f} p.p. (n={melhor['n_comentarios']})",
                  border=True)
        c3.metric("Pior saldo", pior["ide"], f"{pior['saldo']:+.0f} p.p. (n={pior['n_comentarios']})", border=True)
    fig = go.Figure(go.Bar(
        y=top["ide"], x=top["n_comentarios"], orientation="h", marker_color=COR_BASE,
        text=[f"{n} ({p:.0f}%)" for n, p in zip(top["n_comentarios"], top["pct_das_mencoes"])],
        textposition="outside", cliponaxis=False,
        customdata=top[["n_videos", "curtidas_total"]],
        hovertemplate="<b>%{y}</b><br>%{x} comentários<br>%{customdata[0]} vídeos<br>"
                      "%{customdata[1]} curtidas nos comentários<extra></extra>"))
    fig.update_yaxes(autorange="reversed")
    fig.update_xaxes(title="comentários que citam a IDE", range=[0, top["n_comentarios"].max() * 1.2])
    fig.update_layout(title="IDEs mais citadas (entre parênteses: % das menções)")
    st.plotly_chart(figura(fig, 120 + 38 * len(top)), width="stretch")

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
                hovertemplate="<b>%{y}</b><br>" + s + ": %{x:.1f}%<extra></extra>"))
        fig.update_layout(barmode="stack", title="Sentimento sobre cada IDE")
        fig.update_yaxes(autorange="reversed")
        fig.update_xaxes(title="% dos comentários que citam a IDE", range=[0, 100])
        st.plotly_chart(figura(fig, 160 + 36 * len(o)), width="stretch")

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
                         autorange="reversed")
        fig.update_xaxes(title="% de comentários positivos", range=[0, 100])
        st.plotly_chart(figura(fig, 160 + 44 * len(d)), width="stretch")

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
