"""Estatísticas descritivas do sentimento por vídeo."""
from collections import Counter
from math import sqrt

import pandas as pd

from ..preprocessamento.emojis import extrair_emojis

ORDEM = ["positivo", "neutro", "negativo"]


def intervalo_wilson(k: int, n: int, z: float = 1.96):
    """IC de 95% para uma proporção. Com poucos comentários o intervalo é largo — mostre isso."""
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    centro = (p + z * z / (2 * n)) / (1 + z * z / n)
    margem = z * sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return (max(0.0, centro - margem), min(1.0, centro + margem))


def resumo_por_video(df: pd.DataFrame, coluna_grupo: str = "video_id") -> pd.DataFrame:
    linhas = []
    for chave, g in df.groupby(coluna_grupo):
        n = len(g)
        linha = {coluna_grupo: chave, "titulo": g["titulo_video"].iloc[0], "n": n,
                 "score_medio": g["score"].mean(), "score_mediano": g["score"].median(),
                 "curtidas_total": int(g["curtidas"].sum())}
        for rotulo in ORDEM:
            k = int((g["sentimento"] == rotulo).sum())
            baixo, alto = intervalo_wilson(k, n)
            linha.update({f"n_{rotulo}": k, f"pct_{rotulo}": 100 * k / n,
                          f"ic_{rotulo}_inf": 100 * baixo, f"ic_{rotulo}_sup": 100 * alto})
        linhas.append(linha)
    return pd.DataFrame(linhas)


def resumo_por_tipo(df: pd.DataFrame) -> pd.DataFrame:
    """Comentários principais x respostas."""
    tab = pd.crosstab(df["tipo"], df["sentimento"], normalize="index") * 100
    tab = tab.reindex(columns=ORDEM, fill_value=0)
    tab["n"] = df.groupby("tipo").size()
    return tab.reset_index()


def termos_por_sentimento(df: pd.DataFrame, n: int = 15, min_freq: int = 2) -> pd.DataFrame:
    linhas = []
    for rotulo in ORDEM:
        cont = Counter(w for lemas in df.loc[df["sentimento"] == rotulo, "lemas"] for w in lemas.split())
        linhas += [{"sentimento": rotulo, "termo": t, "frequencia": f}
                   for t, f in cont.most_common(n) if f >= min_freq]
    return pd.DataFrame(linhas, columns=["sentimento", "termo", "frequencia"])


def top_emojis(df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    cont = Counter(e for texto in df["texto"] for e in extrair_emojis(texto))
    return pd.DataFrame(cont.most_common(n), columns=["emoji", "frequencia"])


def top_entidades(df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    cont = Counter(e for ents in df["entidades"].fillna("") for e in ents.split(";") if e)
    linhas = [{"entidade": e.rsplit("|", 1)[0], "tipo": e.rsplit("|", 1)[1], "frequencia": f}
              for e, f in cont.most_common(n)]
    return pd.DataFrame(linhas, columns=["entidade", "tipo", "frequencia"])
