"""Identificação de idioma (langdetect, com semente fixa para resultados repetíveis)."""
import re

from langdetect import DetectorFactory, detect_langs
from langdetect.lang_detect_exception import LangDetectException

DetectorFactory.seed = 0
MIN_PALAVRAS_DETECCAO = 3      # abaixo disso a detecção é pouco confiável ("kkkk", "top!")
MIN_PALAVRAS_EXCLUSAO = 5      # só excluímos do português quem tem texto suficiente
CONFIANCA_MINIMA = 0.95        # langdetect confunde português com espanhol; só aceitamos "outro idioma" com certeza


# O langdetect confunde português com estas línguas parecidas, mesmo com alta confiança.
# Elas não são excluídas: o risco de perder comentário em português é maior que o de manter um estrangeiro.
LINGUAS_PROXIMAS = {"pt", "es", "gl", "ca", "it", "ro", "fr"}


def contar_palavras(texto: str) -> int:
    return len(re.findall(r"[A-Za-zÀ-ÿ]{2,}", texto))


def detectar_idioma(texto: str) -> str:
    if contar_palavras(texto) < MIN_PALAVRAS_DETECCAO:
        return "indefinido"
    try:
        melhor = detect_langs(texto)[0]
    except LangDetectException:
        return "indefinido"
    if melhor.lang != "pt" and melhor.prob < CONFIANCA_MINIMA:
        return "indefinido"
    return melhor.lang


def deve_classificar(idioma: str, texto: str) -> bool:
    """Português, línguas parecidas e comentários curtos/indefinidos entram; texto longo em idioma distante (ex.: inglês) sai."""
    return (idioma in LINGUAS_PROXIMAS or idioma == "indefinido"
            or contar_palavras(texto) < MIN_PALAVRAS_EXCLUSAO)
