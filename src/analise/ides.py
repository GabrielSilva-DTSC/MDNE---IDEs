"""Estatísticas por IDE: quais são mais citadas e qual o sentimento dos comentários sobre cada uma."""
from collections import Counter

import pandas as pd

from ..preprocessamento import ides as detector
from . import estatisticas as est

MIN_MENCOES_PADRAO = 10     # abaixo disso o percentual de sentimento é instável demais para comparar


def resumo_por_ide(mencoes: pd.DataFrame, min_mencoes: int = MIN_MENCOES_PADRAO,
                   n_boot: int = 2000) -> pd.DataFrame:
    """Uma linha por IDE, da mais citada para a menos citada.

    n_comentarios = comentários que citam a IDE (cada comentário conta uma vez por IDE).
    pct_das_mencoes = fatia da IDE no total de menções. saldo = %positivo − %negativo.
    pct_isoladas = % das menções cujo trecho cita só essa IDE (o resto é comparação/lista).
    amostra_suficiente = tem ao menos `min_mencoes` menções (só essas entram nos gráficos de sentimento).
    """
    base = est.resumo_por_dimensao(mencoes, "ide", incluir_total=False, n_boot=n_boot)
    extra = mencoes.groupby("ide").agg(
        curtidas_total=("curtidas", "sum"),
        pct_isoladas=("isolada", lambda s: 100 * s.mean()))
    base = base.merge(extra, left_on="ide", right_index=True)
    base["pct_das_mencoes"] = 100 * base["n_comentarios"] / base["n_comentarios"].sum()
    base["saldo"] = base["pct_positivo"] - base["pct_negativo"]
    base["amostra_suficiente"] = base["n_comentarios"] >= min_mencoes
    return base.sort_values(["n_comentarios", "n_videos"], ascending=False).reset_index(drop=True)


def termos_por_ide(mencoes: pd.DataFrame, ides: list, n: int = 8, min_freq: int = 2) -> pd.DataFrame:
    """Palavras mais frequentes nas menções de cada IDE, separadas por sentimento (o 'porquê').

    Tira o próprio nome da IDE e palavras genéricas (ide, editor, visual, studio...).
    """
    linhas = []
    for ide in ides:
        sub = mencoes[mencoes["ide"] == ide]
        for rotulo in est.ORDEM:
            cont = Counter(
                w for lemas in sub.loc[sub["sentimento"] == rotulo, "lemas"].fillna("")
                for w in lemas.split()
                if w not in detector.TERMOS_GENERICOS and not detector.eh_nome_de_ide(w))
            linhas += [{"ide": ide, "sentimento": rotulo, "termo": t, "frequencia": f}
                       for t, f in cont.most_common(n) if f >= min_freq]
    return pd.DataFrame(linhas, columns=["ide", "sentimento", "termo", "frequencia"])


def exemplos_por_ide(mencoes: pd.DataFrame, ides: list, por_sentimento: int = 2) -> pd.DataFrame:
    """Menções mais curtidas de cada IDE em cada sentimento (para slides e para conferir o modelo)."""
    partes = []
    for ide in ides:
        for rotulo in ("positivo", "negativo"):
            sub = mencoes[(mencoes["ide"] == ide) & (mencoes["sentimento"] == rotulo)]
            partes.append(sub.nlargest(por_sentimento, "curtidas"))
    colunas = ["ide", "sentimento", "curtidas", "score", "escopo_texto", "nome_video", "texto_mencao"]
    if not partes:
        return pd.DataFrame(columns=colunas)
    return pd.concat(partes)[colunas].reset_index(drop=True)
