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


def _rotulo(titulo: str, n: int, tam: int = 38) -> str:
    return (titulo if len(titulo) <= tam else titulo[: tam - 1] + "…") + f"\n(n={n})"


def sentimento_por_video(resumo: pd.DataFrame):
    rotulos = [_rotulo(t, n) for t, n in zip(resumo["titulo"], resumo["n"])]
    base = [0.0] * len(resumo)
    plt.figure(figsize=(9, 1.2 + 1.1 * len(resumo)))
    for r in ORDEM:
        valores = resumo[f"pct_{r}"].tolist()
        plt.barh(rotulos, valores, left=base, color=CORES[r], label=r)
        base = [b + v for b, v in zip(base, valores)]
    plt.xlabel("% dos comentários"); plt.xlim(0, 100); plt.legend(ncol=3, loc="lower center",
                                                                   bbox_to_anchor=(0.5, 1.0))
    _salvar("sentimento_por_video.png")


def distribuicao_score(df: pd.DataFrame):
    videos = df["video_id"].unique()
    fig, eixos = plt.subplots(1, len(videos), figsize=(5 * len(videos), 4), sharey=True, squeeze=False)
    for eixo, v in zip(eixos[0], videos):
        sns.histplot(df.loc[df["video_id"] == v, "score"], bins=20, color="#264653", ax=eixo)
        eixo.set_title(v); eixo.set_xlabel("score = P(positivo) − P(negativo)"); eixo.set_xlim(-1, 1)
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


def nuvem(df: pd.DataFrame, video_id: str):
    texto = " ".join(df.loc[df["video_id"] == video_id, "lemas"].dropna())
    if not texto.strip():
        return
    img = WordCloud(width=1200, height=600, background_color="white").generate(texto)
    plt.figure(figsize=(10, 5)); plt.imshow(img, interpolation="bilinear"); plt.axis("off")
    _salvar(f"nuvem_{video_id}.png")


def entidades(tab: pd.DataFrame):
    if tab.empty:
        return
    nomes = [f"{e} ({t})" for e, t in zip(tab["entidade"], tab["tipo"])]
    plt.figure(figsize=(8, 5))
    sns.barplot(x=tab["frequencia"].tolist(), y=nomes, hue=nomes, palette="magma", legend=False)
    plt.title("Entidades nomeadas mais frequentes (spaCy NER)")
    _salvar("entidades.png")
