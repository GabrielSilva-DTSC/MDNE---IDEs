"""Limpeza de comentários com expressões regulares (RE).

A API já entrega plainText (sem HTML), então não é preciso BeautifulSoup aqui;
html.unescape cobre entidades como &amp; que ainda aparecem.
"""
import html
import re
import unicodedata

from .emojis import remover_emojis

RE_URL = re.compile(r"https?://\S+|www\.\S+", re.I)
RE_MENCAO = re.compile(r"@[\w.\-]+")
RE_HASHTAG = re.compile(r"#(\w+)")
RE_TIMESTAMP = re.compile(r"\b\d{1,2}:\d{2}(?::\d{2})?\b")        # "12:34" — comum em comentários de vídeo
RE_RISADA = re.compile(
    r"\b(?:k{3,}|(?:ha){2,}h?|(?:he){2,}h?|(?:rs){2,}|(?:hu){2,}e*|(?:ah){2,}h?)\b", re.I)
RE_LETRA_REPETIDA = re.compile(r"([^\W\d_])\1{2,}")              # "muuuito" -> "muuito"
RE_NAO_LETRA = re.compile(r"[^A-Za-zÀ-ÿ\s]")
RE_ESPACOS = re.compile(r"\s+")


def normalizar(texto: str) -> str:
    if not isinstance(texto, str):
        return ""
    texto = unicodedata.normalize("NFC", html.unescape(texto))
    return texto.replace("\u200b", "")


def limpeza_leve(texto: str) -> str:
    """Tira URL, @menção, timestamp e '#'. Mantém emojis, maiúsculas e pontuação
    (úteis para o NER do spaCy e para o modelo de sentimento)."""
    texto = normalizar(texto)
    texto = RE_URL.sub(" ", texto)
    texto = RE_MENCAO.sub(" ", texto)
    texto = RE_TIMESTAMP.sub(" ", texto)
    texto = RE_HASHTAG.sub(r"\1", texto)
    texto = RE_LETRA_REPETIDA.sub(r"\1\1", texto)
    return RE_ESPACOS.sub(" ", texto).strip()


def limpeza_pesada(texto: str) -> str:
    """Só letras minúsculas, sem emoji nem risada — entrada da lematização/nuvem de palavras."""
    texto = RE_RISADA.sub(" ", normalizar(texto))   # antes da limpeza leve, que encolhe "kkkkk" para "kk"
    texto = remover_emojis(limpeza_leve(texto))
    texto = RE_NAO_LETRA.sub(" ", texto).lower()
    return RE_ESPACOS.sub(" ", texto).strip()


def contar_risadas(texto: str) -> int:
    return len(RE_RISADA.findall(normalizar(texto)))


def contar_timestamps(texto: str) -> int:
    return len(RE_TIMESTAMP.findall(normalizar(texto)))
