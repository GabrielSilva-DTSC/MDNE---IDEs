"""Ingestão de comentários públicos do YouTube usando apenas o Python padrão.

Execute na raiz: python dados/brutos/bronze.py
O limite padrão é de 500 registros por vídeo, incluindo as respostas.
"""

import argparse
import csv
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlencode, urlparse
from urllib.request import Request, urlopen


# Calculamos os caminhos a partir deste arquivo, sem depender do diretório atual.
RAIZ_PROJETO = Path(__file__).resolve().parents[2]
# Estes três endpoints de leitura custam 1 unidade por requisição.
COTA_PADRAO = 10_000
VIDEOS_PADRAO = [
    "https://www.youtube.com/watch?v=qD3zyh7-hpw",
    "https://www.youtube.com/watch?v=40QyA5f3Qo0",
    "https://www.youtube.com/watch?v=Sd_PpMlPmWY",
]
COLUNAS_CSV = [
    "video_id", "comentario_id", "comentario_pai_id", "tipo", "texto",
    "curtidas", "publicado_em", "atualizado_em",
]


class ErroColeta(Exception):
    """Erro com mensagem segura para exibir e salvar, sem a chave de API."""

    def __init__(self, motivo, mensagem):
        super().__init__(mensagem)
        self.motivo = motivo


def agora_utc():
    """Registra o momento da coleta com fuso horário explícito."""
    return datetime.now(timezone.utc).isoformat()


def carregar_chave(caminho_env=RAIZ_PROJETO / ".env"):
    """Lê YOUTUBE_API_KEY do ambiente ou do .env; não executa o arquivo."""
    chave = os.environ.get("YOUTUBE_API_KEY", "").strip()
    if not chave and caminho_env.is_file():
        for linha in caminho_env.read_text(encoding="utf-8").splitlines():
            nome, separador, valor = linha.strip().partition("=")
            if separador and nome.strip() == "YOUTUBE_API_KEY":
                # Esta leitura simples aceita uma chave com ou sem aspas.
                chave = valor.strip().strip("\"'")
                break
    if not chave or chave == "sua_chave_aqui":
        raise ErroColeta(
            "chaveAusente", "Preencha YOUTUBE_API_KEY no .env da raiz do projeto."
        )
    return chave


def extrair_id_video(url_ou_id):
    """Aceita um ID, uma URL watch, youtu.be ou uma URL de Shorts/live."""
    entrada = url_ou_id.strip()
    if re.fullmatch(r"[A-Za-z0-9_-]{11}", entrada):
        return entrada

    url = urlparse(entrada)
    partes = url.path.strip("/").split("/")
    if url.scheme not in {"http", "https"}:
        raise ValueError("Use uma URL completa do YouTube ou um ID de 11 caracteres.")
    if url.hostname in {"youtu.be", "www.youtu.be"}:
        identificador = partes[0]
    elif url.hostname in {
        "youtube.com", "www.youtube.com", "m.youtube.com", "music.youtube.com"
    }:
        if url.path == "/watch":
            identificador = parse_qs(url.query).get("v", [""])[0]
        elif len(partes) >= 2 and partes[0] in {"shorts", "embed", "live"}:
            identificador = partes[1]
        else:
            identificador = ""
    else:
        identificador = ""
    if not re.fullmatch(r"[A-Za-z0-9_-]{11}", identificador):
        raise ValueError("URL de vídeo inválida: confira o domínio e o ID do vídeo.")
    return identificador


class ClienteYouTube:
    """Faz requisições GET à API oficial e conta as tentativas realizadas."""

    def __init__(self, chave, limite_requisicoes=COTA_PADRAO):
        self.chave = chave
        self.requisicoes = 0
        self.limite_requisicoes = limite_requisicoes

    def consultar(self, recurso, **parametros):
        if recurso not in {"videos", "commentThreads", "comments"}:
            raise ValueError("O coletor usa apenas os três endpoints de leitura de 1 unidade.")
        # A chave vai em um cabeçalho HTTPS, em vez de aparecer na URL.
        url = "https://www.googleapis.com/youtube/v3/" + recurso
        url += "?" + urlencode(parametros)
        pedido = Request(url, headers={
            "X-Goog-Api-Key": self.chave,
            "Accept": "application/json",
        })
        for tentativa in range(3):
            # A verificação vale também para as novas tentativas de uma requisição.
            if self.requisicoes >= self.limite_requisicoes:
                raise ErroColeta(
                    "orcamentoAtingido", "O orçamento de requisições deste vídeo foi atingido."
                )
            self.requisicoes += 1
            try:
                with urlopen(pedido, timeout=30) as resposta:
                    return json.load(resposta)
            except HTTPError as erro:
                # Só repetimos erros temporários; erros de chave/cota não se repetem.
                if erro.code in {429, 500, 502, 503, 504} and tentativa < 2:
                    erro.close()
                    time.sleep(2 ** tentativa)
                    continue
                motivo = "erroHTTP"
                try:
                    detalhes = json.load(erro).get("error", {})
                    motivos = detalhes.get("errors", [])
                    candidato = (
                        motivos[0].get("reason", "erroHTTP") if motivos
                        else detalhes.get("status", "erroHTTP")
                    )
                    if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{0,79}", candidato):
                        motivo = candidato
                except (ValueError, AttributeError, TypeError):
                    pass
                finally:
                    erro.close()
                mensagens = {
                    "commentsDisabled": "Os comentários estão desativados neste vídeo.",
                    "videoNotFound": "O vídeo não foi encontrado ou não está acessível.",
                    "keyInvalid": "A chave de API é inválida. Confira o .env.",
                    "quotaExceeded": "A cota da API foi esgotada. Interrompa a coleta.",
                    "dailyLimitExceeded": "O limite diário da API foi esgotado.",
                    "accessNotConfigured": "Ative a YouTube Data API v3 no Google Cloud.",
                    "ipRefererBlocked": "As restrições da chave não permitem esta execução.",
                }
                mensagem = mensagens.get(
                    motivo,
                    "Confira a ativação da API, a chave e suas restrições no Google Cloud.",
                )
                # Não usamos str(erro), pois mensagens remotas podem conter segredos.
                raise ErroColeta(
                    motivo, f"HTTP {erro.code} ({motivo}). {mensagem}"
                ) from None
            except (URLError, OSError):
                raise ErroColeta(
                    "falhaConexao", "Não foi possível conectar à API. Confira a rede."
                ) from None
            except ValueError:
                raise ErroColeta(
                    "respostaInvalida", "A API retornou uma resposta JSON inválida."
                ) from None


def montar_registro(comentario, video_id, comentario_pai_id=None):
    """Seleciona os campos úteis sem limpar nem classificar o texto."""
    dados = comentario["snippet"]
    return {
        "video_id": video_id,
        "comentario_id": comentario["id"],
        "comentario_pai_id": comentario_pai_id,
        "tipo": "resposta" if comentario_pai_id else "principal",
        "texto": dados.get("textDisplay", ""),
        "curtidas": dados.get("likeCount", 0),
        "publicado_em": dados.get("publishedAt"),
        "atualizado_em": dados.get("updatedAt"),
    }


def coletar_video(cliente, video_id, limite=500, incluir_respostas=True, ordem="time"):
    """Coleta até 'limite' registros totais; zero significa sem limite local.

    Percorre comentários principais por ordem da API e depois as respostas de
    cada um. Ao atingir o limite, encerra, mesmo no meio de uma conversa.
    """
    if limite < 0 or ordem not in {"time", "relevance"}:
        raise ValueError("O limite deve ser não negativo e a ordem time ou relevance.")
    inicio_requisicoes = cliente.requisicoes
    resultado = {
        "video": {
            "id": video_id, "url": f"https://www.youtube.com/watch?v={video_id}",
        },
        "coleta": {
            "iniciada_em": agora_utc(), "limite": limite,
            "incluir_respostas": incluir_respostas, "ordem": ordem,
            "orcamento_requisicoes": getattr(cliente, "limite_requisicoes", None),
            "status": "concluido", "encerramento": "api_esgotada",
        },
        "comentarios": [],
    }
    registros = resultado["comentarios"]
    ids_coletados = set()

    def limite_atingido():
        return limite > 0 and len(registros) >= limite

    def adicionar(comentario, pai=None):
        # IDs impedem duplicatas quando as páginas mudam durante a coleta.
        if comentario["id"] not in ids_coletados:
            registros.append(montar_registro(comentario, video_id, pai))
            ids_coletados.add(comentario["id"])
            return True
        return False

    try:
        videos = cliente.consultar(
            "videos", part="snippet,statistics", id=video_id,
            fields="items(id,snippet(title,channelTitle,publishedAt),statistics(commentCount))",
        ).get("items", [])
        if not videos:
            raise ErroColeta(
                "videoIndisponivel", "O vídeo não foi encontrado ou não está acessível."
            )
        video = videos[0]
        contador = video.get("statistics", {}).get("commentCount")
        resultado["video"].update({
            "titulo": video["snippet"]["title"],
            "canal": video["snippet"]["channelTitle"],
            "publicado_em": video["snippet"]["publishedAt"],
            "comentarios_informados_pela_api": int(contador) if contador else None,
        })

        pagina = None
        while not limite_atingido():
            parametros = {
                "part": "snippet", "videoId": video_id,
                "maxResults": min(100, limite - len(registros)) if limite else 100,
                "order": ordem, "textFormat": "plainText",
                "fields": (
                    "nextPageToken,items(snippet(totalReplyCount,"
                    "topLevelComment(id,snippet(textDisplay,likeCount,publishedAt,updatedAt))))"
                ),
            }
            if pagina:
                parametros["pageToken"] = pagina
            resposta = cliente.consultar("commentThreads", **parametros)
            for topico in resposta.get("items", []):
                if limite_atingido():
                    break
                principal = topico["snippet"]["topLevelComment"]
                novo = adicionar(principal)
                tem_respostas = topico["snippet"].get("totalReplyCount", 0) > 0
                if novo and incluir_respostas and tem_respostas:
                    pagina_respostas = None
                    while not limite_atingido():
                        parametros_respostas = {
                            "part": "snippet", "parentId": principal["id"],
                            "maxResults": min(100, limite - len(registros)) if limite else 100,
                            "textFormat": "plainText",
                            "fields": (
                                "nextPageToken,items(id,snippet(parentId,textDisplay,"
                                "likeCount,publishedAt,updatedAt))"
                            ),
                        }
                        if pagina_respostas:
                            parametros_respostas["pageToken"] = pagina_respostas
                        respostas = cliente.consultar("comments", **parametros_respostas)
                        for comentario in respostas.get("items", []):
                            if limite_atingido():
                                break
                            adicionar(comentario, principal["id"])
                        pagina_respostas = respostas.get("nextPageToken")
                        if not pagina_respostas:
                            break
            pagina = resposta.get("nextPageToken")
            if not pagina:
                break
        if limite_atingido():
            resultado["coleta"]["encerramento"] = "limite_atingido"
    except ErroColeta as erro:
        if erro.motivo == "orcamentoAtingido":
            resultado["coleta"]["encerramento"] = "orcamento_atingido"
        else:
            # Se a rede falhar no meio, salvamos o obtido como coleta parcial.
            resultado["coleta"].update({
                "status": "parcial" if registros else "erro", "encerramento": "erro",
                "erro": {"motivo": erro.motivo, "mensagem": str(erro)},
            })
    resultado["coleta"].update({
        "finalizada_em": agora_utc(), "total": len(registros),
        "principais": sum(r["tipo"] == "principal" for r in registros),
        "respostas": sum(r["tipo"] == "resposta" for r in registros),
        "requisicoes": cliente.requisicoes - inicio_requisicoes,
    })
    return resultado


def salvar_coleta(resultado, pasta):
    """Salva JSON com metadados e CSV com uma linha por comentário."""
    pasta.mkdir(parents=True, exist_ok=True)
    video_id = resultado["video"]["id"]
    caminho_json = pasta / f"{video_id}.json"
    caminho_csv = pasta / f"{video_id}.csv"
    with caminho_json.open("w", encoding="utf-8") as arquivo:
        json.dump(resultado, arquivo, ensure_ascii=False, indent=2)
    # utf-8-sig permite abrir o CSV no Excel preservando acentos e emojis.
    with caminho_csv.open("w", encoding="utf-8-sig", newline="") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=COLUNAS_CSV)
        escritor.writeheader()
        escritor.writerows(resultado["comentarios"])
    return caminho_json, caminho_csv


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--videos", nargs="+", default=VIDEOS_PADRAO,
                        help="URLs ou IDs dos vídeos. Por padrão, usa os três vídeos do projeto.")
    parser.add_argument("--limite", type=int, default=500,
                        help="Total por vídeo, incluindo respostas. 0 = todos disponíveis.")
    parser.add_argument("--sem-respostas", action="store_true",
                        help="Coleta somente comentários principais.")
    parser.add_argument("--ordem", choices=["time", "relevance"], default="time",
                        help="Ordem dos comentários principais: recentes ou relevantes.")
    parser.add_argument("--orcamento", type=int, default=COTA_PADRAO,
                        help="Teto de unidades desta execução, dividido entre os vídeos (até 10000).")
    parser.add_argument("--saida", type=Path, default=RAIZ_PROJETO / "dados/brutos/youtube",
                        help="Pasta na qual será criada uma subpasta para esta execução.")
    args = parser.parse_args(argv)
    if args.limite < 0:
        parser.error("--limite deve ser zero ou um número positivo.")
    if not 1 <= args.orcamento <= COTA_PADRAO:
        parser.error("--orcamento deve estar entre 1 e 10000 unidades.")
    try:
        # Valida antes de gastar cota e elimina URLs repetidas do mesmo vídeo.
        video_ids = list(dict.fromkeys(extrair_id_video(v) for v in args.videos))
        if args.orcamento < len(video_ids):
            raise ValueError("O orçamento deve permitir ao menos uma requisição por vídeo.")
        chave = carregar_chave()
    except (ValueError, ErroColeta, OSError) as erro:
        print(f"Configuração inválida: {erro}", file=sys.stderr)
        return 2

    nome_execucao = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S_%fZ")
    pasta = args.saida / nome_execucao
    pasta.mkdir(parents=True, exist_ok=False)
    parcela, resto = divmod(args.orcamento, len(video_ids))
    orcamentos = {
        video_id: parcela + (indice < resto) for indice, video_id in enumerate(video_ids)
    }
    manifesto = {
        "iniciada_em": agora_utc(), "resultados": [], "requisicoes": 0,
        "orcamento_total": args.orcamento, "orcamentos_por_video": orcamentos,
    }
    houve_erro = False
    for video_id in video_ids:
        cliente = ClienteYouTube(chave, limite_requisicoes=orcamentos[video_id])
        print(f"Coletando {video_id} (teto: {orcamentos[video_id]} requisições)...", flush=True)
        resultado = coletar_video(
            cliente, video_id, limite=args.limite,
            incluir_respostas=not args.sem_respostas, ordem=args.ordem,
        )
        caminho_json, caminho_csv = salvar_coleta(resultado, pasta)
        coleta = resultado["coleta"]
        manifesto["requisicoes"] += cliente.requisicoes
        manifesto["resultados"].append({
            "video_id": video_id, "status": coleta["status"], "total": coleta["total"],
            "json": caminho_json.name, "csv": caminho_csv.name,
            "requisicoes": coleta["requisicoes"],
        })
        print(
            f"  {coleta['total']} registros: {coleta['principais']} principais, "
            f"{coleta['respostas']} respostas. {coleta['requisicoes']} requisições. "
            f"Encerramento: {coleta['encerramento']}.",
            flush=True,
        )
        if coleta["status"] != "concluido":
            houve_erro = True
            print(f"  {coleta['erro']['mensagem']}", file=sys.stderr, flush=True)
            if coleta["erro"]["motivo"] in {
                "keyInvalid", "quotaExceeded", "dailyLimitExceeded", "accessNotConfigured",
                "ipRefererBlocked", "falhaConexao", "API_KEY_INVALID", "PERMISSION_DENIED",
            }:
                manifesto["videos_nao_tentados"] = video_ids[len(manifesto["resultados"]):]
                break
    manifesto["finalizada_em"] = agora_utc()
    with (pasta / "manifesto.json").open("w", encoding="utf-8") as arquivo:
        json.dump(manifesto, arquivo, ensure_ascii=False, indent=2)
    print(f"Arquivos salvos em: {pasta}", flush=True)
    return 1 if houve_erro else 0


if __name__ == "__main__":
    raise SystemExit(main())
