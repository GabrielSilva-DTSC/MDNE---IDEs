"""Adaptador opcional para classificação de sentimento via Hugging Face Transformers.

Não substitui silenciosamente o classificador da Etapa 1: erros de modelo/dependência são
reportados para que resultados incompletos não sejam confundidos com previsões reais.
"""
import logging

import pandas as pd

logger = logging.getLogger("transformers_sentimento")
MODELO_PADRAO = "lxyuan/distilbert-base-multilingual-cased-sentiments-student"
MAPA_ROTULOS = {
    "positive": "positivo", "pos": "positivo", "positivo": "positivo",
    "neutral": "neutro", "neu": "neutro", "neutro": "neutro",
    "negative": "negativo", "neg": "negativo", "negativo": "negativo",
}


def normalizar_rotulo(rotulo: str) -> str:
    """Mapeia rótulos conhecidos; não inventa o significado de LABEL_0 etc."""
    return MAPA_ROTULOS.get(str(rotulo).strip().lower(), "indefinido")


class ClassificadorTransformers:
    def __init__(self, modelo: str = MODELO_PADRAO, batch_size: int = 16, device: int = -1):
        self.nome_modelo = modelo
        self.batch_size = batch_size
        self.device = device
        self._pipeline = None

    def _carregar(self):
        if self._pipeline is None:
            try:
                from transformers import pipeline
            except ImportError as erro:
                raise RuntimeError(
                    "Classificação Transformers requer requirements-etapa2.txt."
                ) from erro
            try:
                self._pipeline = pipeline(
                    "text-classification", model=self.nome_modelo, tokenizer=self.nome_modelo,
                    device=self.device,
                )
            except Exception as erro:
                raise RuntimeError(f"Não foi possível carregar o modelo {self.nome_modelo}: {erro}") from erro
        return self._pipeline

    def classificar(self, textos):
        textos = [str(t) if t is not None else "" for t in textos]
        if not textos:
            return []
        pipe = self._carregar()
        saidas = []
        for inicio in range(0, len(textos), self.batch_size):
            lote = textos[inicio:inicio + self.batch_size]
            previsoes = pipe(lote, truncation=True, batch_size=self.batch_size)
            if previsoes and isinstance(previsoes[0], dict):
                previsoes = [[p] for p in previsoes]
            saidas.extend(previsoes)
        resultado = []
        for predicoes in saidas:
            scores = {normalizar_rotulo(p["label"]): float(p["score"]) for p in predicoes}
            validos = {k: v for k, v in scores.items() if k != "indefinido"}
            if not validos:
                resultado.append({"sentimento_transformer": "indefinido", "score_transformer": 0.0,
                                  "p_pos_transformer": 0.0, "p_neu_transformer": 0.0,
                                  "p_neg_transformer": 0.0})
                continue
            rotulo = max(validos, key=validos.get)
            resultado.append({
                "sentimento_transformer": rotulo, "score_transformer": validos[rotulo],
                "p_pos_transformer": scores.get("positivo", 0.0),
                "p_neu_transformer": scores.get("neutro", 0.0),
                "p_neg_transformer": scores.get("negativo", 0.0),
            })
        return resultado

    def aplicar(self, df: pd.DataFrame, coluna_texto: str) -> pd.DataFrame:
        if coluna_texto not in df.columns:
            raise KeyError(f"Coluna de texto ausente: {coluna_texto}")
        resultado = df.copy()
        previsoes = self.classificar(resultado[coluna_texto].fillna("").tolist())
        for coluna in ("sentimento_transformer", "score_transformer", "p_pos_transformer",
                       "p_neu_transformer", "p_neg_transformer"):
            resultado[coluna] = [p[coluna] for p in previsoes]
        resultado["modelo_transformer"] = self.nome_modelo
        return resultado
