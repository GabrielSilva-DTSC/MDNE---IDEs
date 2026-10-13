"""Testes da leitura de várias coletas, dos metadados dos vídeos e das estatísticas por grupo.
Sem rede e sem baixar modelos: python -m unittest discover -s tests -v"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd

from src import comum
from src.analise import estatisticas as est


def _json(pasta: Path, video_id: str, titulo: str, textos: list, status="concluido"):
    pasta.mkdir(parents=True, exist_ok=True)
    comentarios = [{"video_id": video_id, "comentario_id": f"{video_id}_{i}", "comentario_pai_id": None,
                    "tipo": "principal", "texto": t, "curtidas": i, "publicado_em": "2026-10-01T00:00:00Z",
                    "atualizado_em": "2026-10-01T00:00:00Z"} for i, t in enumerate(textos)]
    (pasta / f"{video_id}.json").write_text(json.dumps(
        {"video": {"id": video_id, "titulo": titulo}, "coleta": {"status": status},
         "comentarios": comentarios}, ensure_ascii=False), encoding="utf-8")


class TestColetas(unittest.TestCase):
    def test_mais_recente_vence_e_erro_nao_substitui(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            _json(base / "20261001T000000_0Z", "AAAAAAAAAAA", "A", ["velho1", "velho2"])
            _json(base / "20261001T000000_0Z", "BBBBBBBBBBB", "B", ["b1"])
            _json(base / "20261002T000000_0Z", "AAAAAAAAAAA", "A", ["novo"])                     # recoleta
            _json(base / "20261002T000000_0Z", "BBBBBBBBBBB", "B", [], status="erro")           # falhou
            df = comum.carregar_coletas(base)
            self.assertEqual(sorted(df.loc[df.video_id == "AAAAAAAAAAA", "texto"]), ["novo"])
            self.assertEqual(len(df[df.video_id == "BBBBBBBBBBB"]), 1)       # manteve a coleta boa
            self.assertEqual(len(df), 2)

    def test_pasta_so_com_erro_levanta(self):
        with tempfile.TemporaryDirectory() as tmp:
            _json(Path(tmp) / "x", "AAAAAAAAAAA", "A", [], status="erro")
            with self.assertRaises(ValueError):
                comum.carregar_coletas(Path(tmp))


class TestMetadados(unittest.TestCase):
    def test_extrair_id_formatos(self):
        esperado = "-pmU-NLUYCk"
        for url in ["https://youtu.be/-pmU-NLUYCk?si=x", "https://www.youtube.com/watch?v=-pmU-NLUYCk",
                    "https://youtube.com/shorts/-pmU-NLUYCk", esperado]:
            self.assertEqual(comum.extrair_id_video(url), esperado)
        with self.assertRaises(ValueError):
            comum.extrair_id_video("https://exemplo.com/abc")

    def test_videos_csv_do_projeto(self):
        meta = comum.ler_metadados()
        self.assertEqual(len(meta), 21)
        self.assertEqual(meta["id_video"].nunique(), 21)           # nenhum link repetido
        self.assertEqual(set(meta["formato_video"]), {"Normal", "Shorts"})

    def test_link_repetido_escolhe_o_titulo_parecido(self):
        meta = pd.DataFrame({
            "nome_video": ["IDE favorita dos programadores", "Rankeando as melhores IDEs para PROGRAMAR"],
            "link_video": ["https://youtu.be/AAAAAAAAAAA"] * 2, "id_video": ["AAAAAAAAAAA"] * 2,
            "grupo": ["Geral", "Geral"], "escopo": ["Geral", "Geral"], "foco_ide": ["Geral"] * 2,
            "nome_canal": ["SpaceCoding", "Pedroca"], "formato_video": ["Shorts", "Normal"]})
        df = pd.DataFrame({"video_id": ["AAAAAAAAAAA"] * 2, "comentario_id": ["1", "2"],
                           "titulo_video": ["Rankeando as melhores IDEs para PROGRAMAR (minha experiência)"] * 2})
        with self.assertLogs("comum", level="WARNING"):
            out = comum.associar_metadados(df, meta)
        self.assertEqual(set(out["nome_canal"]), {"Pedroca"})
        self.assertEqual(set(out["formato_video"]), {"Normal"})

    def test_sem_metadados(self):
        df = pd.DataFrame({"video_id": ["AAAAAAAAAAA"], "titulo_video": ["x"]})
        out = comum.associar_metadados(df, None)
        self.assertEqual(out["nome_canal"].iloc[0], comum.SEM_CLASSIFICACAO)
        self.assertNotIn("grupo", out.columns)            # a análise não usa mais a divisão por linguagem


class TestEstatisticasPorGrupo(unittest.TestCase):
    def setUp(self):
        linhas = []
        for g, videos in {"Geral": 6, "Java": 5}.items():
            for v in range(videos):
                for i in range(20):
                    pos = (i % 2 == 0) if g == "Geral" else (i % 5 == 0)
                    linhas.append({"video_id": f"{g}{v}", "titulo_video": f"{g}{v}", "grupo": g,
                                   "sentimento": "positivo" if pos else "neutro",
                                   "score": 0.9 if pos else 0.0, "curtidas": 1})
        self.df = pd.DataFrame(linhas)

    def test_resumo_por_dimensao(self):
        r = est.resumo_por_dimensao(self.df, "grupo", n_boot=300)
        self.assertEqual(list(r["grupo"]), ["Todos", "Geral", "Java"])
        self.assertEqual(r.loc[0, "n_comentarios"], 220)
        soma = r[["pct_positivo", "pct_neutro", "pct_negativo"]].sum(axis=1)
        self.assertTrue(((soma - 100).abs() < 1e-6).all())
        self.assertTrue(r["ic_video_positivo_inf"].notna().all())          # ≥5 vídeos em todos

    def test_bootstrap_e_reprodutivel(self):
        a = est.ic_bootstrap_por_video(self.df, "positivo", 300, semente=0)
        b = est.ic_bootstrap_por_video(self.df, "positivo", 300, semente=0)
        self.assertEqual(a, b)
        self.assertLess(a[0], a[1])

    def test_comparacao_detecta_diferenca(self):
        c = est.comparar_grupos(self.df, "grupo", "Geral", "Java")
        pos = c[c["sentimento"] == "positivo"].iloc[0]
        self.assertFalse(pos["sobrepoe_ic_comentarios"])                   # 50% x 20%: bem diferentes

    def test_sobrepoe(self):
        self.assertTrue(est.sobrepoe(10, 20, 15, 30))
        self.assertFalse(est.sobrepoe(10, 20, 21, 30))
        self.assertIsNone(est.sobrepoe(float("nan"), 1, 0, 1))


if __name__ == "__main__":
    unittest.main()
