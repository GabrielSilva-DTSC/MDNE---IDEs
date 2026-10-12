"""Detecção de IDEs/editores citados nos comentários e extração do trecho que fala de cada uma.

Para a análise de sentimento *sobre* cada IDE, a unidade é a MENÇÃO: um par (comentário, IDE).
- Se o comentário cita uma só IDE, vale o comentário inteiro (escopo "comentario").
- Se cita várias, vale só a(s) frase(s) em que aquela IDE aparece (escopo "frase"); se a própria
  frase compara várias IDEs, vale o trecho entre vírgulas/"mas" (escopo "trecho").

Para incluir uma IDE nova, basta acrescentar uma linha em CATALOGO.
Os padrões ignoram maiúsculas; use (?-i:...) para exigir a grafia exata (ex.: IDLE, Zed).
"""
import re

import pandas as pd

CATALOGO = {
    # editores/IDEs gerais
    "VS Code": [r"\bvs\s?code\b", r"\bvscode\b", r"\bvsc\b", r"\bvisual\s+studio\s+code\b"],
    "Visual Studio": [r"\bvisual\s+studio\b(?!\s+code)"],
    "Sublime Text": [r"\bsublime(?:\s?text)?\b"],
    "Notepad++": [r"\bnotepad\s?(?:\+\+|plus)"],
    "Vim/Neovim": [r"\bvim\b", r"\bneovim\b", r"\bnvim\b"],
    "Emacs": [r"\bemacs\b"],
    "Atom": [r"\batom\b"],
    "Cursor": [r"\bcursor\b"],
    "Windsurf": [r"\bwindsurf\b"],
    "Zed": [r"(?-i:\bZed\b)"],
    # JetBrains
    "IntelliJ IDEA": [r"\bintelli\s?j\b", r"\bidea\s+(?:community|ultimate)\b"],
    "PyCharm": [r"\bpy\s?charm\b"],
    "WebStorm": [r"\bweb\s?storm\b"],
    "PhpStorm": [r"\bphp\s?storm\b"],
    "CLion": [r"\bclion\b"],
    "Rider": [r"\bjetbrains\s+rider\b", r"(?-i:\bRider\b)"],
    # Java / outras linguagens
    "Eclipse": [r"\beclipse\b"],
    "NetBeans": [r"\bnet\s?beans\b"],
    "Android Studio": [r"\bandroid\s+studio\b"],
    "Xcode": [r"\bx\s?code\b"],
    "Code::Blocks": [r"\bcode\s?::?\s?blocks\b", r"\bcodeblocks\b"],
    "Dev-C++": [r"\bdev[\s-]?c\+\+"],
    "BlueJ": [r"\bbluej\b"],
    "Delphi": [r"\bdelphi\b"],
    "Arduino IDE": [r"\barduino\s+ide\b"],
    # Python / dados
    "Jupyter": [r"\bjupyter(?:\s?(?:lab|notebook))?\b"],
    "Google Colab": [r"\bcolab\b"],
    "Spyder": [r"\bspyder\b"],
    "Thonny": [r"\bthonny\b"],
    "IDLE": [r"(?-i:\bIDLE\b)"],
    "RStudio": [r"\br\s?studio\b"],
    # online
    "Replit": [r"\brepl\.?it\b"],
    "CodeSandbox": [r"\bcode\s?sandbox\b"],
    "CodePen": [r"\bcode\s?pen\b"],
    "StackBlitz": [r"\bstack\s?blitz\b"],
    "Gitpod": [r"\bgitpod\b"],
}

_PADROES = {nome: re.compile("|".join(f"(?:{p})" for p in padroes), re.I)
            for nome, padroes in CATALOGO.items()}

RE_FRASE = re.compile(r"(?<=[.!?…])\s+|\s*[;\n]\s*")
RE_TRECHO = re.compile(r",|;|\bmas\b|\bpor[ée]m\b|\benquanto\b|\bj[áa]\b", re.I)

# palavras que aparecem junto do nome da IDE e não dizem nada sobre ela (usado nos termos por IDE)
TERMOS_GENERICOS = {"ide", "editor", "visual", "studio", "code", "vs", "plus", "text", "online"}


def encontrar_ides(texto: str) -> list:
    """IDEs citadas em `texto`, na ordem do catálogo, sem repetição."""
    if not isinstance(texto, str) or not texto:
        return []
    return [nome for nome, padrao in _PADROES.items() if padrao.search(texto)]


def remover_nomes(texto: str) -> str:
    """Troca o nome de toda IDE do catálogo por espaço. Usado antes de lematizar, para que
    'VS Code' não vire o termo 'coder' (lema do spaCy) nas palavras associadas a cada IDE."""
    for padrao in _PADROES.values():
        texto = padrao.sub(" ", texto)
    return texto


def eh_nome_de_ide(palavra: str) -> bool:
    """True se a palavra sozinha é o nome (ou apelido) de uma IDE do catálogo, p.ex. 'vscode'."""
    return bool(encontrar_ides(palavra))


def _trecho_da_ide(frase: str, ide: str) -> str:
    """Parte da frase (entre vírgulas, 'mas', 'porém'...) que cita a IDE."""
    partes = RE_TRECHO.split(frase)
    # o split mantém a ordem; ficamos com as partes que citam a IDE
    com_ide = [p.strip() for p in partes if p and _PADROES[ide].search(p)]
    return " ".join(com_ide) if com_ide else frase


def extrair_mencoes(df: pd.DataFrame, col_texto: str = "texto_leve") -> pd.DataFrame:
    """Uma linha por (comentário, IDE). Colunas novas: ide, escopo_texto, texto_mencao, isolada.

    `isolada` = True quando o texto da menção cita só essa IDE (sentimento sem ambiguidade);
    False quando o trecho ainda cita outra IDE (comparações, listas: o sentimento é do trecho todo).
    """
    linhas = []
    for registro in df.to_dict("records"):
        texto = registro.get(col_texto) or ""
        ides = encontrar_ides(texto)
        for ide in ides:
            if len(ides) == 1:
                escopo, trecho = "comentario", texto
            else:
                frases = [f for f in RE_FRASE.split(texto) if f and _PADROES[ide].search(f)]
                if any(len(encontrar_ides(f)) > 1 for f in frases):
                    escopo = "trecho"
                    trecho = " ".join(_trecho_da_ide(f, ide) for f in frases)
                else:
                    escopo, trecho = "frase", " ".join(frases)
            linhas.append({**registro, "ide": ide, "escopo_texto": escopo,
                           "texto_mencao": trecho.strip(),
                           "isolada": len(encontrar_ides(trecho)) == 1})
    colunas = list(df.columns) + ["ide", "escopo_texto", "texto_mencao", "isolada"]
    return pd.DataFrame(linhas, columns=colunas)
