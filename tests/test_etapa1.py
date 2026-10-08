"""Testes sem rede e sem baixar modelos: python -m unittest discover -s tests -v"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd

from src import comum
from src.analise import estatisticas as est
from src.modelagem.sentimentos import AnalisadorSentimento
from src.preprocessamento import emojis, idioma, limpeza

EXEMPLO = Path(__file__).parent / "fixtures" / "execucao_exemplo"


class TestLimpeza(unittest.TestCase):
    def test_remove_url_mencao_timestamp(self):
        t = limpeza.limpeza_leve("@ana veja https://x.com/a aos 12:34 e 1:02:03 &amp; pronto")
        self.assertEqual(t, "veja aos e & pronto")

    def test_letras_repetidas_mas_numeros_intactos(self):
        self.assertEqual(limpeza.limpeza_leve("muuuuito 1000"), "muuito 1000")

    def test_pesada_sem_emoji_risada_pontuacao(self):
        self.assertEqual(limpeza.limpeza_pesada("Ótimo kkkkk 😂 vídeo, 10/10!"), "ótimo vídeo")

    def test_contagens(self):
        self.assertEqual(limpeza.contar_risadas("kkkk e hahaha"), 2)
        self.assertEqual(limpeza.contar_timestamps("no 3:45 e no 10:00"), 2)


class TestEmojisEIdioma(unittest.TestCase):
    def test_emojis(self):
        self.assertEqual(emojis.extrair_emojis("oi 😂 tchau 🚀"), ["😂", "🚀"])
        self.assertEqual(emojis.remover_emojis("a😂b").split(), ["a", "b"])

    def test_idioma(self):
        self.assertEqual(idioma.detectar_idioma("kkkk top"), "indefinido")
        self.assertEqual(idioma.detectar_idioma("Esse vídeo explica muito bem o conteúdo da aula"), "pt")
        self.assertEqual(idioma.detectar_idioma("This video explains the whole topic really well"), "en")

    def test_politica_de_exclusao(self):
        self.assertTrue(idioma.deve_classificar("en", "great video"))                     # curto: mantém
        self.assertFalse(idioma.deve_classificar("en", "great video thanks for all this"))  # longo: sai
        # langdetect achou "es" neste comentário em português; ele não pode ser descartado
        self.assertTrue(idioma.deve_classificar("es", "Aos erra o exemplo, ficou confuso demais"))


class TestEstatisticas(unittest.TestCase):
    def test_wilson(self):
        baixo, alto = est.intervalo_wilson(5, 10)
        self.assertLess(baixo, 0.5); self.assertGreater(alto, 0.5)
        self.assertEqual(est.intervalo_wilson(0, 0), (0.0, 0.0))

    def test_resumo_e_leitura_dos_dados(self):
        df = comum.carregar_comentarios(EXEMPLO)
        self.assertEqual(df["video_id"].nunique(), 2)
        df["texto_leve"] = df["texto"].apply(limpeza.limpeza_leve)
        df = AnalisadorSentimento(usar_modelo=False).aplicar(df, "texto_leve")
        resumo = est.resumo_por_video(df)
        soma = resumo[["pct_positivo", "pct_neutro", "pct_negativo"]].sum(axis=1)
        self.assertTrue(((soma - 100).abs() < 1e-6).all())
        self.assertEqual(resumo["n"].sum(), len(df))


if __name__ == "__main__":
    unittest.main()
