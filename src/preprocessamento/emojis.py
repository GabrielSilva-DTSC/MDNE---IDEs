"""Tratamento de emojis (biblioteca `emoji`)."""
import emoji


def extrair_emojis(texto: str) -> list:
    return [item["emoji"] for item in emoji.emoji_list(texto)] if isinstance(texto, str) else []


def contar_emojis(texto: str) -> int:
    return len(extrair_emojis(texto))


def remover_emojis(texto: str) -> str:
    return emoji.replace_emoji(texto, replace=" ") if isinstance(texto, str) else ""


def emojis_para_palavras(texto: str) -> str:
    """':rosto_chorando_de_rir:' -> 'rosto chorando de rir' (útil se o modelo ignorar emojis)."""
    return emoji.demojize(texto, language="pt", delimiters=(" ", " ")).replace("_", " ")
