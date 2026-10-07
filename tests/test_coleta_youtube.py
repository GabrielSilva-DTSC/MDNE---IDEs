"""Verifica paginação, limite total e erros sem fazer chamadas à API real."""

import csv
import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError

from dados.brutos.bronze import (
    ClienteYouTube, ErroColeta, carregar_chave, coletar_video,
    extrair_id_video, salvar_coleta, main,
)


VIDEO_ID = "qD3zyh7-hpw"
VIDEO = {"items": [{
    "id": VIDEO_ID,
    "snippet": {"title": "Vídeo de teste", "channelTitle": "Canal de teste",
                "publishedAt": "2026-01-01T00:00:00Z"},
    "statistics": {"commentCount": "1000"},
}]}


def comentario(identificador):
    return {"id": identificador, "snippet": {
        "textDisplay": "Texto com acento, emoji 😀\ne segunda linha",
        "publishedAt": "2026-01-01T00:00:00Z", "likeCount": 2,
        "authorDisplayName": "Este campo não deve ser armazenado",
    }}


def topico(identificador, respostas=0):
    return {"snippet": {"topLevelComment": comentario(identificador),
                        "totalReplyCount": respostas}}


class ClienteSimulado:
    def __init__(self, respostas):
        self.respostas = list(respostas)
        self.requisicoes = 0
        self.chamadas = []

    def consultar(self, recurso, **parametros):
        self.requisicoes += 1
        self.chamadas.append((recurso, parametros))
        esperado, resposta = self.respostas.pop(0)
        if recurso != esperado:
            raise AssertionError(f"Esperado {esperado}, recebido {recurso}")
        if isinstance(resposta, Exception):
            raise resposta
        return resposta


class TestColetaYouTube(unittest.TestCase):
    def test_urls_e_ids_validos_e_dominio_indevido(self):
        for entrada in [VIDEO_ID, f"https://youtu.be/{VIDEO_ID}?t=30",
                        f"https://www.youtube.com/watch?v={VIDEO_ID}&list=exemplo",
                        f"https://www.youtube.com/shorts/{VIDEO_ID}"]:
            self.assertEqual(extrair_id_video(entrada), VIDEO_ID)
        with self.assertRaises(ValueError):
            extrair_id_video(f"https://outrosite.example/watch?v={VIDEO_ID}")

    def test_principais_paginados_sem_duplicar_ids(self):
        cliente = ClienteSimulado([
            ("videos", VIDEO),
            ("commentThreads", {"items": [topico("p1")], "nextPageToken": "pagina2"}),
            ("commentThreads", {"items": [topico("p1"), topico("p2")]}),
        ])
        resultado = coletar_video(cliente, VIDEO_ID, limite=5, incluir_respostas=False)
        self.assertEqual([c["comentario_id"] for c in resultado["comentarios"]], ["p1", "p2"])
        self.assertEqual(cliente.chamadas[2][1]["pageToken"], "pagina2")
        self.assertEqual(resultado["coleta"]["encerramento"], "api_esgotada")

    def test_limite_conta_principal_e_respostas_paginadas_juntos(self):
        cliente = ClienteSimulado([
            ("videos", VIDEO),
            ("commentThreads", {"items": [topico("p1", 5), topico("p2")]}),
            ("comments", {"items": [comentario("r1"), comentario("r2")],
                          "nextPageToken": "respostas2"}),
            ("comments", {"items": [comentario("r3"), comentario("r4")]}),
        ])
        resultado = coletar_video(cliente, VIDEO_ID, limite=4)
        self.assertEqual(resultado["coleta"]["total"], 4)
        self.assertEqual(resultado["coleta"]["principais"], 1)
        self.assertEqual(resultado["coleta"]["respostas"], 3)
        self.assertEqual(resultado["coleta"]["encerramento"], "limite_atingido")
        self.assertEqual(cliente.chamadas[3][1]["pageToken"], "respostas2")
        self.assertEqual(cliente.chamadas[3][1]["maxResults"], 1)
        for registro in resultado["comentarios"][1:]:
            self.assertEqual(registro["comentario_pai_id"], "p1")

    def test_comentarios_desativados_sao_erro_e_nao_coleta_vazia(self):
        cliente = ClienteSimulado([
            ("videos", VIDEO),
            ("commentThreads", ErroColeta("commentsDisabled", "Comentários desativados.")),
        ])
        resultado = coletar_video(cliente, VIDEO_ID)
        self.assertEqual(resultado["coleta"]["status"], "erro")
        self.assertEqual(resultado["coleta"]["erro"]["motivo"], "commentsDisabled")

    def test_video_indisponivel_nao_busca_comentarios(self):
        cliente = ClienteSimulado([("videos", {"items": []})])
        resultado = coletar_video(cliente, VIDEO_ID)
        self.assertEqual(resultado["coleta"]["erro"]["motivo"], "videoIndisponivel")
        self.assertEqual(cliente.requisicoes, 1)

    def test_erro_de_rede_preserva_resultado_parcial(self):
        cliente = ClienteSimulado([
            ("videos", VIDEO),
            ("commentThreads", {"items": [topico("p1")], "nextPageToken": "pagina2"}),
            ("commentThreads", ErroColeta("falhaConexao", "Falha de rede.")),
        ])
        resultado = coletar_video(cliente, VIDEO_ID)
        self.assertEqual(resultado["coleta"]["status"], "parcial")
        self.assertEqual(resultado["coleta"]["total"], 1)

    def test_json_e_csv_preservam_acentos_emojis_e_nao_guardam_autores(self):
        cliente = ClienteSimulado([
            ("videos", VIDEO), ("commentThreads", {"items": [topico("p1")]}),
        ])
        resultado = coletar_video(cliente, VIDEO_ID)
        with tempfile.TemporaryDirectory() as pasta:
            caminho_json, caminho_csv = salvar_coleta(resultado, Path(pasta))
            dados = json.loads(caminho_json.read_text(encoding="utf-8"))
            with caminho_csv.open(encoding="utf-8-sig", newline="") as arquivo:
                linhas = list(csv.DictReader(arquivo))
            self.assertEqual(linhas[0]["texto"], dados["comentarios"][0]["texto"])
            self.assertIn("😀", linhas[0]["texto"])
            self.assertNotIn("authorDisplayName", caminho_json.read_text(encoding="utf-8"))

    def test_chave_no_cabecalho_e_nunca_na_url(self):
        cliente = ClienteYouTube("segredo-de-teste")
        with patch("dados.brutos.bronze.urlopen", return_value=io.BytesIO(b'{"items": []}')) as abrir:
            cliente.consultar("videos", part="snippet", id=VIDEO_ID)
        pedido = abrir.call_args.args[0]
        self.assertNotIn("segredo-de-teste", pedido.full_url)
        self.assertEqual(pedido.get_header("X-goog-api-key"), "segredo-de-teste")

    def test_erro_http_nao_expoe_a_mensagem_remota_com_segredo(self):
        corpo = json.dumps({"error": {"message": "segredo-de-teste",
                                     "errors": [{"reason": "keyInvalid"}]}}).encode()
        erro = HTTPError("https://www.googleapis.com/", 400, "Bad Request", {}, io.BytesIO(corpo))
        with patch("dados.brutos.bronze.urlopen", side_effect=erro):
            with self.assertRaises(ErroColeta) as contexto:
                ClienteYouTube("segredo-de-teste").consultar("videos", id=VIDEO_ID)
        self.assertNotIn("segredo-de-teste", str(contexto.exception))
        self.assertEqual(contexto.exception.motivo, "keyInvalid")

    def test_leitura_da_chave_nao_executa_as_outras_linhas_do_env(self):
        with tempfile.TemporaryDirectory() as pasta, patch.dict(os.environ, {}, clear=True):
            caminho = Path(pasta) / ".env"
            caminho.write_text('OUTRA_VARIAVEL=$(comando)\nYOUTUBE_API_KEY="chave-teste"\n', encoding="utf-8")
            self.assertEqual(carregar_chave(caminho), "chave-teste")
            self.assertNotIn("OUTRA_VARIAVEL", os.environ)

    def test_orcamento_impede_requisicoes_extras_inclusive_repeticoes(self):
        cliente = ClienteYouTube("segredo-de-teste", limite_requisicoes=1)
        erro = HTTPError("https://www.googleapis.com/", 503, "Unavailable", {}, io.BytesIO())
        with patch("dados.brutos.bronze.urlopen", side_effect=erro) as abrir, \
                patch("dados.brutos.bronze.time.sleep"):
            with self.assertRaises(ErroColeta) as contexto:
                cliente.consultar("videos", id=VIDEO_ID)
        self.assertEqual(contexto.exception.motivo, "orcamentoAtingido")
        self.assertEqual(abrir.call_count, 1)
        self.assertEqual(cliente.requisicoes, 1)

    def test_orcamento_exaurido_preserva_dados_sem_marcar_falha_de_rede(self):
        cliente = ClienteSimulado([
            ("videos", VIDEO),
            ("commentThreads", {"items": [topico("p1")], "nextPageToken": "pagina2"}),
            ("commentThreads", ErroColeta("orcamentoAtingido", "Teto atingido.")),
        ])
        resultado = coletar_video(cliente, VIDEO_ID)
        self.assertEqual(resultado["coleta"]["status"], "concluido")
        self.assertEqual(resultado["coleta"]["encerramento"], "orcamento_atingido")
        self.assertEqual(resultado["coleta"]["total"], 1)

    def test_cli_divide_orcamento_entre_videos_e_conta_as_duas_coletas(self):
        def executar(cliente, video_id, **kwargs):
            # Simula uma consulta ao vídeo e uma página de comentários.
            cliente.requisicoes = 2
            return {"video": {"id": video_id}, "comentarios": [], "coleta": {
                "status": "concluido", "encerramento": "api_esgotada", "total": 0,
                "principais": 0, "respostas": 0, "requisicoes": 2,
            }}

        with tempfile.TemporaryDirectory() as pasta, \
                patch("dados.brutos.bronze.carregar_chave", return_value="segredo-de-teste"), \
                patch("dados.brutos.bronze.coletar_video", side_effect=executar), \
                patch("builtins.print"):
            codigo = main(["--saida", pasta, "--orcamento", "5"])
            arquivo = next(Path(pasta).rglob("manifesto.json"))
            manifesto = json.loads(arquivo.read_text())
        self.assertEqual(codigo, 0)
        self.assertEqual(manifesto["requisicoes"], 4)
        self.assertEqual(list(manifesto["orcamentos_por_video"].values()), [3, 2])
        self.assertEqual(sum(manifesto["orcamentos_por_video"].values()), 5)


if __name__ == "__main__":
    unittest.main()
