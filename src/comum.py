"""Caminhos do projeto e leitura dos JSONs gerados por dados/brutos/bronze.py."""
import json
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
BRUTOS = RAIZ / "dados" / "brutos" / "youtube"
INTERMEDIARIOS = RAIZ / "dados" / "intermediarios"
PROCESSADOS = RAIZ / "dados" / "processados"
ASSETS = RAIZ / "relatorio" / "assets"
TABELAS = RAIZ / "relatorio" / "tabelas"


def garantir_pastas():
    for pasta in (INTERMEDIARIOS, PROCESSADOS, ASSETS, TABELAS):
        pasta.mkdir(parents=True, exist_ok=True)


def execucao_mais_recente(base: Path = BRUTOS) -> Path:
    """Última pasta de coleta que tem pelo menos um comentário (ignora a tentativa com status=erro)."""
    for pasta in sorted((p for p in base.iterdir() if p.is_dir()), reverse=True):
        manifesto = pasta / "manifesto.json"
        if manifesto.is_file():
            resultados = json.loads(manifesto.read_text(encoding="utf-8")).get("resultados", [])
            if any(r.get("total", 0) > 0 for r in resultados):
                return pasta
    raise FileNotFoundError(f"Nenhuma coleta com comentários em {base}")


def carregar_comentarios(pasta: Path) -> pd.DataFrame:
    """Lê os JSONs (que têm curtidas, datas e título do vídeo) e devolve 1 linha por comentário."""
    linhas = []
    for caminho in sorted(pasta.glob("*.json")):
        if caminho.name == "manifesto.json":
            continue
        dados = json.loads(caminho.read_text(encoding="utf-8"))
        video = dados["video"]
        for c in dados["comentarios"]:
            linhas.append({**c, "titulo_video": video.get("titulo", video["id"])})
    if not linhas:
        raise ValueError(f"Nenhum comentário encontrado em {pasta}")
    df = pd.DataFrame(linhas)
    df["texto"] = df["texto"].fillna("").astype(str)
    return df
