"""Classificação de sentimento (positivo/neutro/negativo) para comentários em português.

Modelo principal: pysentimiento (BERTweet em português). TextBlob NÃO serve: é para inglês.
Se o modelo não puder ser baixado, usa-se um léxico mínimo e a coluna `metodo_sentimento`
deixa isso explícito — não apresente esse resultado como análise final.
"""
import logging
import re

import pandas as pd

logger = logging.getLogger("sentimentos")
ROTULOS = {"POS": "positivo", "NEU": "neutro", "NEG": "negativo"}

_POS = re.compile(r"\b(ótim\w+|excelente|bom|boa|melhor|parabéns|obrigad\w+|amei|adorei|"
                  r"incrível|top|show|útil|claro|didático)\b", re.I)
_NEG = re.compile(r"\b(péssim\w+|ruim|pior|horrível|odiei|chato|confus\w+|lixo|decepcion\w+|"
                  r"inútil|erro|errado|enganoso)\b", re.I)


class AnalisadorSentimento:
    def __init__(self, usar_modelo: bool = True):
        self.modelo = None
        if usar_modelo:
            try:
                from pysentimiento import create_analyzer
                self.modelo = create_analyzer(task="sentiment", lang="pt")
            except Exception as erro:  # noqa: BLE001 — qualquer falha de download/import
                logger.warning("pysentimiento indisponível (%s). Usando léxico de reserva.", erro)

    @property
    def metodo(self) -> str:
        return "pysentimiento" if self.modelo else "lexico_reserva"

    def _classificar_modelo(self, textos):
        saidas = self.modelo.predict(textos)
        return [(ROTULOS[s.output], s.probas["POS"], s.probas["NEU"], s.probas["NEG"]) for s in saidas]

    @staticmethod
    def _classificar_lexico(textos):
        resultado = []
        for t in textos:
            saldo = len(_POS.findall(t)) - len(_NEG.findall(t))
            rotulo = "positivo" if saldo > 0 else "negativo" if saldo < 0 else "neutro"
            p_pos, p_neg = (0.8, 0.1) if saldo > 0 else (0.1, 0.8) if saldo < 0 else (0.1, 0.1)
            resultado.append((rotulo, p_pos, 1 - p_pos - p_neg, p_neg))
        return resultado

    def aplicar(self, df: pd.DataFrame, coluna: str) -> pd.DataFrame:
        df = df.copy()
        textos = df[coluna].tolist()
        res = self._classificar_modelo(textos) if self.modelo else self._classificar_lexico(textos)
        df["sentimento"], df["p_pos"], df["p_neu"], df["p_neg"] = zip(*res) if res else ([], [], [], [])
        df["score"] = df["p_pos"] - df["p_neg"]           # de -1 (negativo) a +1 (positivo)
        df["metodo_sentimento"] = self.metodo
        return df
