"""Testes da detecção de IDEs nos comentários e do resumo por IDE.
Sem rede e sem baixar modelos: python -m unittest discover -s tests -v"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd

from src.analise import ides as an_ides
from src.preprocessamento import ides


class TestDeteccao(unittest.TestCase):
    def test_apelidos_e_grafias(self):
        casos = {
            "Uso vscode todo dia": ["VS Code"],
            "VS Code é top": ["VS Code"],
            "Visual Studio Code é leve": ["VS Code"],          # não conta como Visual Studio
            "O Visual Studio pesa demais": ["Visual Studio"],
            "intellij e pycharm são da JetBrains": ["IntelliJ IDEA", "PyCharm"],
            "Neovim ou Vim?": ["Vim/Neovim"],
            "Notepad++ salvou minha vida": ["Notepad++"],
            "Rodo tudo no Colab e no Jupyter": ["Jupyter", "Google Colab"],
        }
        for texto, esperado in casos.items():
            self.assertEqual(sorted(ides.encontrar_ides(texto)), sorted(esperado), texto)

    def test_nao_confunde_palavras_comuns(self):
        self.assertEqual(ides.encontrar_ides("Tive uma ideia, o código ficou ótimo"), [])
        self.assertEqual(ides.encontrar_ides("o rider da banda"), [])          # 'Rider' só com R maiúsculo
        self.assertEqual(ides.encontrar_ides("fiquei idle esperando"), [])     # 'IDLE' só em maiúsculas
        self.assertEqual(ides.encontrar_ides("IDLE é simples"), ["IDLE"])
        self.assertEqual(ides.encontrar_ides(""), [])
        self.assertEqual(ides.encontrar_ides(None), [])

    def test_remover_nomes_antes_de_lematizar(self):
        self.assertEqual(ides.remover_nomes("Uso VS Code e Eclipse, são leves").split(), ["Uso", "e", ",", "são", "leves"])
        self.assertEqual(ides.remover_nomes("Notepad++ é simples").strip(), "é simples")

    def test_nome_de_ide_sozinho(self):
        self.assertTrue(ides.eh_nome_de_ide("vscode"))
        self.assertTrue(ides.eh_nome_de_ide("pycharm"))
        self.assertFalse(ides.eh_nome_de_ide("lento"))


class TestMencoes(unittest.TestCase):
    def _df(self, textos):
        return pd.DataFrame({"video_id": "V" * 11, "comentario_id": [f"c{i}" for i in range(len(textos))],
                             "tipo": "principal", "curtidas": 1, "texto_leve": textos})

    def test_comentario_com_uma_ide_usa_o_comentario_inteiro(self):
        m = ides.extrair_mencoes(self._df(["Uso PyCharm. É ótimo e muito rápido"]))
        self.assertEqual(len(m), 1)
        self.assertEqual(m.loc[0, "escopo_texto"], "comentario")
        self.assertEqual(m.loc[0, "texto_mencao"], "Uso PyCharm. É ótimo e muito rápido")
        self.assertTrue(m.loc[0, "isolada"])

    def test_varias_ides_em_frases_diferentes_separa_por_frase(self):
        m = ides.extrair_mencoes(self._df(["Eclipse é lento demais. IntelliJ é muito bom!"])).set_index("ide")
        self.assertEqual(m.loc["Eclipse", "texto_mencao"], "Eclipse é lento demais.")
        self.assertEqual(m.loc["IntelliJ IDEA", "texto_mencao"], "IntelliJ é muito bom!")
        self.assertEqual(set(m["escopo_texto"]), {"frase"})
        self.assertTrue(m["isolada"].all())

    def test_comparacao_na_mesma_frase_separa_por_trecho(self):
        m = ides.extrair_mencoes(self._df(["Eclipse é horrível, IntelliJ é ótimo"])).set_index("ide")
        self.assertEqual(m.loc["Eclipse", "escopo_texto"], "trecho")
        self.assertEqual(m.loc["Eclipse", "texto_mencao"], "Eclipse é horrível")
        self.assertEqual(m.loc["IntelliJ IDEA", "texto_mencao"], "IntelliJ é ótimo")
        self.assertTrue(m["isolada"].all())

    def test_trecho_ainda_com_duas_ides_nao_e_isolado(self):
        m = ides.extrair_mencoes(self._df(["Eclipse e NetBeans são ruins"]))
        self.assertEqual(len(m), 2)
        self.assertFalse(m["isolada"].any())

    def test_sem_ide_nao_gera_mencao_e_df_vazio_mantem_colunas(self):
        m = ides.extrair_mencoes(self._df(["Ótimo vídeo, parabéns!"]))
        self.assertTrue(m.empty)
        self.assertIn("ide", m.columns)


class TestResumoPorIde(unittest.TestCase):
    def setUp(self):
        linhas = []
        # VS Code: 30 menções em 6 vídeos (60% positivas); Eclipse: 12 em 3 vídeos (todas negativas);
        # Vim/Neovim: 4 menções (poucas)
        for ide, n, videos, pos in [("VS Code", 30, 6, 18), ("Eclipse", 12, 3, 0), ("Vim/Neovim", 4, 1, 2)]:
            for i in range(n):
                p = i < pos
                neg = (ide == "Eclipse")
                linhas.append({"video_id": f"{ide[:2]}{i % videos}", "ide": ide, "curtidas": i,
                               "sentimento": "positivo" if p else "negativo" if neg else "neutro",
                               "score": 0.9 if p else -0.9 if neg else 0.0, "isolada": i % 2 == 0,
                               "lemas": "rápido leve plugin vscode" if p else "lento pesado",
                               "texto_mencao": f"{ide} {i}", "escopo_texto": "comentario",
                               "nome_video": "v"})
        self.m = pd.DataFrame(linhas)

    def test_ranking_e_fatias(self):
        r = an_ides.resumo_por_ide(self.m, min_mencoes=10, n_boot=200)
        self.assertEqual(list(r["ide"]), ["VS Code", "Eclipse", "Vim/Neovim"])
        self.assertAlmostEqual(r["pct_das_mencoes"].sum(), 100)
        self.assertEqual(list(r["amostra_suficiente"]), [True, True, False])
        soma = r[["pct_positivo", "pct_neutro", "pct_negativo"]].sum(axis=1)
        self.assertTrue(((soma - 100).abs() < 1e-6).all())

    def test_saldo(self):
        r = an_ides.resumo_por_ide(self.m, n_boot=200).set_index("ide")
        self.assertAlmostEqual(r.loc["VS Code", "saldo"], 60.0)
        self.assertAlmostEqual(r.loc["Eclipse", "saldo"], -100.0)

    def test_termos_por_ide_ignoram_o_nome_da_ide(self):
        t = an_ides.termos_por_ide(self.m, ["VS Code", "Eclipse"])
        pos = t[(t["ide"] == "VS Code") & (t["sentimento"] == "positivo")]["termo"].tolist()
        self.assertIn("rápido", pos)
        self.assertNotIn("vscode", pos)
        neg = t[(t["ide"] == "Eclipse") & (t["sentimento"] == "negativo")]["termo"].tolist()
        self.assertEqual(set(neg), {"lento", "pesado"})

    def test_exemplos(self):
        e = an_ides.exemplos_por_ide(self.m, ["VS Code"], por_sentimento=2)
        self.assertEqual(len(e), 2 + 0)       # VS Code não tem negativos
        self.assertTrue((e["sentimento"] == "positivo").all())


if __name__ == "__main__":
    unittest.main()
