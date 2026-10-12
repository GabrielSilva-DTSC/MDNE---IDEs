"""Gráficos da Etapa 1, salvos em relatorio/assets/ para entrar nos slides."""
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from wordcloud import WordCloud

from ..comum import ASSETS
from .estatisticas import ORDEM

CORES = {"positivo": "#2a9d8f", "neutro": "#bdbdbd", "negativo": "#e76f51"}


def _salvar(nome: str):
    plt.tight_layout()
    plt.savefig(ASSETS / nome, dpi=200, bbox_inches="tight")
    plt.close()


def _curto(texto: str, tam: int = 42) -> str:
    return texto if len(texto) <= tam else texto[: tam - 1] + "…"


def _barras_empilhadas(rotulos, resumo: pd.DataFrame, altura: float, titulo: str, arquivo: str):
    base = [0.0] * len(resumo)
    plt.figure(figsize=(10, altura))
    for r in ORDEM:
        valores = resumo[f"pct_{r}"].tolist()
        plt.barh(rotulos, valores, left=base, color=CORES[r], label=r)
        base = [b + v for b, v in zip(base, valores)]
    plt.gca().invert_yaxis()
    plt.xlabel("% dos comentários"); plt.xlim(0, 100); plt.title(titulo)
    plt.legend(ncol=3, loc="lower center", bbox_to_anchor=(0.5, 1.08))
    _salvar(arquivo)


def sentimento_por_dimensao(resumo: pd.DataFrame, coluna: str, titulo: str, arquivo: str):
    """Barras empilhadas para 'Todos' e cada categoria de `coluna`, com n de comentários e vídeos."""
    rotulos = [f"{nome}\n(n={n}, {v} vídeos)" for nome, n, v in
               zip(resumo[coluna], resumo["n_comentarios"], resumo["n_videos"])]
    _barras_empilhadas(rotulos, resumo, 1.4 + 0.9 * len(resumo), titulo, arquivo)


def sentimento_por_video(resumo: pd.DataFrame):
    resumo = resumo.sort_values("pct_positivo", ascending=False)
    rotulos = [f"{_curto(t)} (n={n})" + (f" [{g}]" if "grupo" in resumo else "")
               for t, n, g in zip(resumo["titulo"], resumo["n"],
                                  resumo["grupo"] if "grupo" in resumo else [""] * len(resumo))]
    _barras_empilhadas(rotulos, resumo, 1.5 + 0.38 * len(resumo),
                       "Sentimento por vídeo (ordenado por % positivo)", "sentimento_por_video.png")


def intervalos_positivos(resumo: pd.DataFrame, coluna: str, arquivo: str):
    """% de positivos com IC de 95% (Wilson e, quando há vídeos suficientes, bootstrap de vídeos)."""
    r = resumo.reset_index(drop=True)
    plt.figure(figsize=(8, 1.5 + 0.8 * len(r)))
    for i, linha in r.iterrows():
        plt.plot([linha["ic_positivo_inf"], linha["ic_positivo_sup"]], [i + 0.12] * 2,
                 color="#264653", lw=3, label="IC por comentário (Wilson)" if i == 0 else None)
        if pd.notna(linha["ic_video_positivo_inf"]):
            plt.plot([linha["ic_video_positivo_inf"], linha["ic_video_positivo_sup"]], [i - 0.12] * 2,
                     color="#e9c46a", lw=3, label="IC por vídeo (bootstrap)")
        plt.plot(linha["pct_positivo"], i, "o", color="#2a9d8f", ms=9)
    plt.yticks(range(len(r)), [f"{n} (n={c})" for n, c in zip(r[coluna], r["n_comentarios"])])
    plt.gca().invert_yaxis()
    handles, rotulos = plt.gca().get_legend_handles_labels()
    plt.legend(dict(zip(rotulos, handles)).values(), dict(zip(rotulos, handles)).keys(),
               loc="lower center", bbox_to_anchor=(0.5, 1.02), ncol=2)
    plt.xlabel("% de comentários positivos"); plt.xlim(0, 100)
    _salvar(arquivo)


def distribuicao_score(df: pd.DataFrame, coluna: str = None, titulo: str = "Distribuição do score"):
    """Histograma do score (−1 a +1). Com `coluna`, uma curva por categoria."""
    plt.figure(figsize=(9, 4.5))
    sns.histplot(data=df, x="score", hue=coluna, bins=20, element="step", stat="density",
                 common_norm=False)
    plt.xlabel("score = P(positivo) − P(negativo)"); plt.xlim(-1, 1)
    plt.title(titulo)
    _salvar("distribuicao_score.png")


def termos(tab: pd.DataFrame):
    rotulos = [r for r in ("positivo", "negativo") if (tab["sentimento"] == r).any()]
    if not rotulos:
        return
    fig, eixos = plt.subplots(1, len(rotulos), figsize=(6 * len(rotulos), 5), squeeze=False)
    for eixo, r in zip(eixos[0], rotulos):
        dados = tab[tab["sentimento"] == r].head(10)
        sns.barplot(x="frequencia", y="termo", data=dados, color=CORES[r], ax=eixo)
        eixo.set_title(f"Termos em comentários {r}s"); eixo.set_ylabel("")
    _salvar("termos_por_sentimento.png")


def nuvem(df: pd.DataFrame, nome: str, titulo: str = ""):
    texto = " ".join(df["lemas"].dropna())
    if not texto.strip():
        return
    img = WordCloud(width=1200, height=600, background_color="white").generate(texto)
    plt.figure(figsize=(10, 5)); plt.imshow(img, interpolation="bilinear"); plt.axis("off")
    if titulo:
        plt.title(titulo)
    _salvar(f"nuvem_{nome}.png")


def entidades(tab: pd.DataFrame):
    if tab.empty:
        return
    nomes = [f"{e} ({t})" for e, t in zip(tab["entidade"], tab["tipo"])]
    plt.figure(figsize=(8, 5))
    sns.barplot(x=tab["frequencia"].tolist(), y=nomes, hue=nomes, palette="magma", legend=False)
    plt.title("Entidades nomeadas mais frequentes (spaCy NER)")
    _salvar("entidades.png")


def ides_mais_citadas(resumo: pd.DataFrame, n: int = 15, arquivo: str = "ides_mais_citadas.png"):
    """Barras com o nº de comentários que citam cada IDE (as `n` mais citadas)."""
    top = resumo.head(n)
    plt.figure(figsize=(9, 1.2 + 0.45 * len(top)))
    plt.barh(top["ide"], top["n_comentarios"], color="#264653")
    plt.gca().invert_yaxis()
    margem = top["n_comentarios"].max() * 0.01
    for i, (n_com, pct, vids) in enumerate(zip(top["n_comentarios"], top["pct_das_mencoes"], top["n_videos"])):
        plt.text(n_com + margem, i, f"{n_com} ({pct:.0f}%) · {vids} vídeos", va="center", fontsize=9)
    plt.xlim(0, top["n_comentarios"].max() * 1.35)
    plt.xlabel("comentários que citam a IDE"); plt.title("IDEs mais citadas nos comentários")
    _salvar(arquivo)
