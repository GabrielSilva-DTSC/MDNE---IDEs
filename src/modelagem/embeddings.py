"""Geração e persistência de embeddings semânticos com Sentence Transformers.

A dependência/modelo é carregado apenas quando solicitado, evitando downloads na Etapa 1.
"""
import logging
from typing import Sequence

import numpy as np

logger = logging.getLogger("embeddings")
MODELO_PADRAO = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


class GeradorEmbeddings:
    def __init__(self, modelo: str = MODELO_PADRAO, batch_size: int = 32, device: str | None = None):
        self.nome_modelo = modelo
        self.batch_size = batch_size
        self.device = device
        self._modelo = None

    def _carregar(self):
        if self._modelo is None:
            try:
                from sentence_transformers import SentenceTransformer
            except ImportError as erro:
                raise RuntimeError(
                    "Embeddings requerem as dependências opcionais. Instale requirements-etapa2.txt."
                ) from erro
            self._modelo = SentenceTransformer(self.nome_modelo, device=self.device)
        return self._modelo

    def gerar(self, textos: Sequence[str]) -> np.ndarray:
        textos = [str(t) if t is not None else "" for t in textos]
        if not textos:
            return np.empty((0, 0), dtype=np.float32)
        modelo = self._carregar()
        vetores = modelo.encode(
            textos, batch_size=self.batch_size, show_progress_bar=len(textos) > self.batch_size,
            convert_to_numpy=True, normalize_embeddings=True,
        )
        return np.asarray(vetores, dtype=np.float32)

    def similaridade(self, textos: Sequence[str], referencias: Sequence[str]) -> np.ndarray:
        """Matriz de cosseno (comentários × referências); embeddings são normalizados."""
        if not textos or not referencias:
            return np.empty((len(textos), len(referencias)), dtype=np.float32)
        a, b = self.gerar(textos), self.gerar(referencias)
        return np.asarray(a @ b.T, dtype=np.float32)

    def salvar(self, caminho, ids: Sequence[str], vetores: np.ndarray) -> None:
        """Armazena vetores em NPZ separado do CSV para preservar tipos e reduzir ruído."""
        np.savez_compressed(
            caminho, ids=np.asarray(list(ids), dtype=str), embeddings=np.asarray(vetores, dtype=np.float32),
            modelo=np.asarray(self.nome_modelo),
        )
