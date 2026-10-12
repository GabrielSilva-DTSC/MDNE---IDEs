"""Estatísticas descritivas do sentimento (por vídeo, grupo, escopo e formato)."""
from collections import Counter
from math import sqrt

import numpy as np
import pandas as pd

from ..preprocessamento.emojis import extrair_emojis

ORDEM = ["positivo", "neutro", "negativo"]
MIN_VIDEOS_BOOTSTRAP = 5


def intervalo_wilson(k: int, n: int, z: float = 1.96):
    """IC de 95% para uma proporção, tratando cada comentário como independente."""
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    centro = (p + z * z / (2 * n)) / (1 + z * z / n)
    margem = z * sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return (max(0.0, centro - margem), min(1.0, centro + margem))


def ic_bootstrap_por_video(df: pd.DataFrame, rotulo: str, n_boot: int = 2000, semente: int = 0):
    """IC de 95% (em %) sorteando VÍDEOS com reposição. Mais honesto que o de Wilson quando os
    comentários de um mesmo vídeo se parecem entre si (mesmo criador, mesmo público)."""
    por_video = df.groupby("video_id")["sentimento"].agg(
        k=lambda s: int((s == rotulo).sum()), n="size")
    k, n = por_video["k"].to_numpy(), por_video["n"].to_numpy()
    sorteio = np.random.default_rng(semente).integers(0, len(k), size=(n_boot, len(k)))
    pct = 100 * k[sorteio].sum(axis=1) / n[sorteio].sum(axis=1)
    inf, sup = np.percentile(pct, [2.5, 97.5])
    return float(inf), float(sup)


def sobrepoe(a_inf, a_sup, b_inf, b_sup):
    """True se os dois intervalos se sobrepõem (não dá para afirmar diferença)."""
    if any(pd.isna(v) for v in (a_inf, a_sup, b_inf, b_sup)):
        return None
    return not (a_sup < b_inf or b_sup < a_inf)


def resumo_por_video(df: pd.DataFrame) -> pd.DataFrame:
    extras = [c for c in ("nome_video", "grupo", "escopo", "formato_video", "nome_canal") if c in df.columns]
    linhas = []
    for video_id, g in df.groupby("video_id"):
        n = len(g)
        linha = {"video_id": video_id, "titulo": g["titulo_video"].iloc[0], "n": n,
                 **{c: g[c].iloc[0] for c in extras},
                 "score_medio": g["score"].mean(), "score_mediano": g["score"].median(),
                 "curtidas_total": int(g["curtidas"].sum())}
        for rotulo in ORDEM:
            k = int((g["sentimento"] == rotulo).sum())
            baixo, alto = intervalo_wilson(k, n)
            linha.update({f"n_{rotulo}": k, f"pct_{rotulo}": 100 * k / n,
                          f"ic_{rotulo}_inf": 100 * baixo, f"ic_{rotulo}_sup": 100 * alto})
        linhas.append(linha)
    return pd.DataFrame(linhas)


def resumo_por_dimensao(df: pd.DataFrame, coluna: str, incluir_total: bool = True,
                        n_boot: int = 2000) -> pd.DataFrame:
    """Uma linha por categoria de `coluna` (e uma linha 'Todos'). Traz:
    - pct_* e ic_* (Wilson, por comentário);
    - media_videos_*: média das % de cada vídeo (cada vídeo pesa igual, vídeos grandes não dominam);
    - ic_video_*: IC por bootstrap de vídeos (só com ao menos 5 vídeos no grupo)."""
    partes = [("Todos", df)] if incluir_total else []
    partes += [(str(nome), g) for nome, g in df.groupby(coluna, sort=True)]
    linhas = []
    for nome, g in partes:
        n, n_videos = len(g), g["video_id"].nunique()
        linha = {coluna: nome, "n_comentarios": n, "n_videos": n_videos,
                 "score_medio": g["score"].mean()}
        for rotulo in ORDEM:
            k = int((g["sentimento"] == rotulo).sum())
            baixo, alto = intervalo_wilson(k, n)
            linha.update({f"pct_{rotulo}": 100 * k / n, f"ic_{rotulo}_inf": 100 * baixo,
                          f"ic_{rotulo}_sup": 100 * alto})
            linha[f"media_videos_{rotulo}"] = g.groupby("video_id")["sentimento"].apply(
                lambda s, r=rotulo: 100 * (s == r).mean()).mean()
            if n_videos >= MIN_VIDEOS_BOOTSTRAP:
                inf, sup = ic_bootstrap_por_video(g, rotulo, n_boot)
            else:
                inf = sup = np.nan
            linha[f"ic_video_{rotulo}_inf"], linha[f"ic_video_{rotulo}_sup"] = inf, sup
        linhas.append(linha)
    return pd.DataFrame(linhas)


def comparar_grupos(df: pd.DataFrame, coluna: str, a: str, b: str) -> pd.DataFrame:
    """Compara dois grupos: se os ICs se sobrepõem em todas as categorias, juntá-los é razoável."""
    resumo = resumo_por_dimensao(df[df[coluna].isin([a, b])], coluna, incluir_total=False)
    ra = resumo[resumo[coluna] == a].iloc[0]
    rb = resumo[resumo[coluna] == b].iloc[0]
    linhas = []
    for r in ORDEM:
        linhas.append({
            "sentimento": r, "grupo_a": a, "grupo_b": b,
            "n_a": int(ra["n_comentarios"]), "n_b": int(rb["n_comentarios"]),
            "pct_a": ra[f"pct_{r}"], "ic_a_inf": ra[f"ic_{r}_inf"], "ic_a_sup": ra[f"ic_{r}_sup"],
            "pct_b": rb[f"pct_{r}"], "ic_b_inf": rb[f"ic_{r}_inf"], "ic_b_sup": rb[f"ic_{r}_sup"],
            "sobrepoe_ic_comentarios": sobrepoe(ra[f"ic_{r}_inf"], ra[f"ic_{r}_sup"],
                                                rb[f"ic_{r}_inf"], rb[f"ic_{r}_sup"]),
            "sobrepoe_ic_videos": sobrepoe(ra[f"ic_video_{r}_inf"], ra[f"ic_video_{r}_sup"],
                                           rb[f"ic_video_{r}_inf"], rb[f"ic_video_{r}_sup"]),
        })
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
        cont = Counter(w for lemas in df.loc[df["sentimento"] == rotulo, "lemas"].fillna("")
                       for w in lemas.split())
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
