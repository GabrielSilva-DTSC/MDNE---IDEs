"""Caminhos do projeto, leitura das coletas (JSONs do bronze.py) e dos metadados dos vídeos."""
import difflib
import json
import logging
import re
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import pandas as pd

logger = logging.getLogger("comum")

RAIZ = Path(__file__).resolve().parent.parent
BRUTOS = RAIZ / "dados" / "brutos" / "youtube"
INTERMEDIARIOS = RAIZ / "dados" / "intermediarios"
PROCESSADOS = RAIZ / "dados" / "processados"
VIDEOS_CSV = RAIZ / "dados" / "brutos" / "videos.csv"
ASSETS = RAIZ / "relatorio" / "assets"
TABELAS = RAIZ / "relatorio" / "tabelas"

# Só estas colunas do videos.csv entram na análise. foco_ide, grupo e escopo (linguagem/divisão
# Geral x Java x Outras) são ignoradas de propósito: a análise é por IDE, não por tipo de vídeo.
COLUNAS_META = ["nome_canal", "formato_video"]
SEM_CLASSIFICACAO = "Sem classificação"
RE_ID = re.compile(r"[A-Za-z0-9_-]{11}")


def garantir_pastas():
    for pasta in (INTERMEDIARIOS, PROCESSADOS, ASSETS, TABELAS):
        pasta.mkdir(parents=True, exist_ok=True)


# ---------- coletas ----------
def _ler_json(caminho: Path):
    dados = json.loads(caminho.read_text(encoding="utf-8"))
    video = dados.get("video") or {}
    video_id = video.get("id", caminho.stem)
    titulo = video.get("titulo", video_id)
    return video_id, [{**c, "titulo_video": titulo} for c in dados.get("comentarios", [])]


def _jsons_da_pasta(pasta: Path):
    return [p for p in sorted(pasta.glob("*.json")) if p.name != "manifesto.json"]


def execucao_mais_recente(base: Path = BRUTOS) -> Path:
    """Última pasta de coleta com pelo menos um comentário (ignora tentativas com erro)."""
    for pasta in sorted((p for p in base.iterdir() if p.is_dir()), reverse=True):
        if any(_ler_json(j)[1] for j in _jsons_da_pasta(pasta)):
            return pasta
    raise FileNotFoundError(f"Nenhuma coleta com comentários em {base}")


def carregar_comentarios(pasta: Path) -> pd.DataFrame:
    """Lê UMA execução do bronze.py: 1 linha por comentário."""
    linhas = []
    for caminho in _jsons_da_pasta(pasta):
        _, registros = _ler_json(caminho)
        linhas += [{**r, "execucao": pasta.name} for r in registros]
    return _como_dataframe(linhas, pasta)


def carregar_coletas(base: Path = BRUTOS) -> pd.DataFrame:
    """Junta TODAS as execuções. Para cada vídeo vale a coleta mais recente que tenha
    comentários; assim vídeos coletados em dias ou execuções diferentes entram juntos e
    uma recoleta substitui a anterior em vez de duplicar."""
    por_video = {}
    for pasta in sorted(p for p in base.iterdir() if p.is_dir()):      # ordem cronológica
        for caminho in _jsons_da_pasta(pasta):
            video_id, registros = _ler_json(caminho)
            if registros:
                por_video[video_id] = [{**r, "execucao": pasta.name} for r in registros]
    linhas = [r for registros in por_video.values() for r in registros]
    return _como_dataframe(linhas, base)


def _como_dataframe(linhas: list, origem: Path) -> pd.DataFrame:
    if not linhas:
        raise ValueError(f"Nenhum comentário encontrado em {origem}")
    df = pd.DataFrame(linhas)
    df["texto"] = df["texto"].fillna("").astype(str)
    df["curtidas"] = pd.to_numeric(df["curtidas"], errors="coerce").fillna(0).astype(int)
    return df


# ---------- metadados dos vídeos (dados/brutos/videos.csv) ----------
def extrair_id_video(url_ou_id: str) -> str:
    """Mesma regra do bronze.py: aceita ID, watch, youtu.be, shorts, embed e live."""
    entrada = str(url_ou_id).strip()
    if RE_ID.fullmatch(entrada):
        return entrada
    url = urlparse(entrada)
    partes = url.path.strip("/").split("/")
    host = url.hostname or ""
    if host in {"youtu.be", "www.youtu.be"}:
        identificador = partes[0]
    elif host in {"youtube.com", "www.youtube.com", "m.youtube.com", "music.youtube.com"}:
        if url.path == "/watch":
            identificador = parse_qs(url.query).get("v", [""])[0]
        elif len(partes) >= 2 and partes[0] in {"shorts", "embed", "live"}:
            identificador = partes[1]
        else:
            identificador = ""
    else:
        identificador = ""
    if not RE_ID.fullmatch(identificador):
        raise ValueError(f"Link de vídeo inválido: {entrada!r}")
    return identificador


def ler_metadados(caminho: Path = VIDEOS_CSV) -> pd.DataFrame:
    """Lê dados/brutos/videos.csv (precisa de nome_video e link_video; as demais colunas são opcionais)."""
    meta = pd.read_csv(caminho, encoding="utf-8-sig", dtype=str).fillna("")
    meta.columns = [c.strip() for c in meta.columns]
    faltando = {"nome_video", "link_video"} - set(meta.columns)
    if faltando:
        raise ValueError(f"{caminho.name} precisa das colunas {sorted(faltando)}")
    meta["id_video"] = meta["link_video"].apply(extrair_id_video)
    for coluna in COLUNAS_META:
        if coluna not in meta.columns:
            meta[coluna] = SEM_CLASSIFICACAO
        meta[coluna] = meta[coluna].replace("", SEM_CLASSIFICACAO)
    return meta


def _parecidos(a: str, b: str) -> float:
    return difflib.SequenceMatcher(None, a.lower(), b.lower()).ratio()


def associar_metadados(df: pd.DataFrame, meta) -> pd.DataFrame:
    """Acrescenta nome do vídeo, canal e formato a cada comentário e avisa sobre
    inconsistências (link repetido, título diferente do coletado, contagem muito diferente)."""
    df = df.copy()
    if meta is None or meta.empty:
        for coluna in COLUNAS_META:
            df[coluna] = SEM_CLASSIFICACAO
        df["nome_video"] = df["titulo_video"]
        return df

    titulos = df.groupby("video_id")["titulo_video"].first()
    escolhidas = []
    for video_id, g in meta.groupby("id_video", sort=False):
        if len(g) > 1:
            if video_id in titulos.index:       # fica a linha cujo nome mais se parece com o título coletado
                g = g.assign(_s=g["nome_video"].apply(lambda n: _parecidos(n, titulos[video_id])))
                g = g.sort_values("_s", ascending=False)
            logger.warning(
                "O link do vídeo %s aparece em %d linhas da planilha (%s). Só um desses vídeos pode "
                "ter esse ID: corrija o link da linha errada e colete de novo. Foi mantida: %s.",
                video_id, len(g), " | ".join(g["nome_video"]), g.iloc[0]["nome_video"])
        escolhidas.append(g.iloc[0])
    unico = pd.DataFrame(escolhidas).rename(columns={"id_video": "video_id"})
    df = df.merge(unico[["video_id", "nome_video", "n_comentarios_planilha", *COLUNAS_META]
                        if "n_comentarios_planilha" in unico.columns
                        else ["video_id", "nome_video", *COLUNAS_META]], on="video_id", how="left")

    sem_meta = df.loc[df["nome_video"].isna(), "video_id"].unique()
    if len(sem_meta):
        logger.warning("Vídeos coletados que não estão em %s: %s", VIDEOS_CSV.name, ", ".join(sem_meta))
    df["nome_video"] = df["nome_video"].fillna(df["titulo_video"])
    for coluna in COLUNAS_META:
        df[coluna] = df[coluna].fillna(SEM_CLASSIFICACAO)

    for video_id, titulo in titulos.items():
        linha = unico[unico["video_id"] == video_id]
        if not linha.empty and _parecidos(linha.iloc[0]["nome_video"], titulo) < 0.5:
            logger.warning("O título coletado de %s ('%s') é bem diferente do nome na planilha ('%s'): "
                           "confira o link.", video_id, titulo, linha.iloc[0]["nome_video"])
    if "n_comentarios_planilha" in df.columns:
        coletados = df.groupby("video_id").size()
        for video_id, n_plan in df.groupby("video_id")["n_comentarios_planilha"].first().items():
            n_plan = pd.to_numeric(n_plan, errors="coerce")
            if pd.notna(n_plan) and abs(coletados[video_id] - n_plan) > max(5, 0.15 * n_plan):
                logger.warning("%s: %d comentários coletados, mas a planilha diz %d.",
                               video_id, coletados[video_id], int(n_plan))
    return df.drop(columns=["n_comentarios_planilha"], errors="ignore")
