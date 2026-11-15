"""Testes unitários da Etapa 2 sem rede e sem baixar modelos."""
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd

from src.modelagem.transformers import normalizar_rotulo
from src.preprocessamento.semantica import processar


class Token:
    def __init__(self, text, lemma, pos, is_stop=False, is_punct=False, dep="", children=None):
        self.text, self.lemma_, self.pos_ = text, lemma, pos
        self.is_stop, self.is_punct, self.dep_ = is_stop, is_punct, dep
        self.children = children or []


class Span:
    def __init__(self, text):
        self.text = text


class Doc:
    def __init__(self, texto):
        self.tokens = [Token("VS Code", "VS Code", "PROPN"), Token("é", "ser", "AUX")]
        self.ents = [Span("VS Code")]
        self.sents = [Span(texto)] if texto else []

    def __iter__(self):
        return iter(self.tokens)


class FakeNLP:
    def pipe(self, textos, batch_size=64):
        return (Doc(t) for t in textos)


class TestEtapa2(unittest.TestCase):
    def test_pipeline_spacy_produz_json_csv_compativel(self):
        df = pd.DataFrame({"texto_leve": ["VS Code é excelente", None]})
        out = processar(df, nlp=FakeNLP())
        self.assertEqual(json.loads(out.loc[0, "sentencas"]), ["VS Code é excelente"])
        self.assertEqual(json.loads(out.loc[0, "entidades_semanticas"]), [{"texto": "VS Code", "tipo": ""}])
        self.assertEqual(json.loads(out.loc[1, "sentencas"]), [""])

    def test_data_frame_vazio_mantem_esquema(self):
        out = processar(pd.DataFrame({"texto_leve": []}), nlp=FakeNLP())
        self.assertIn("relacoes_sintaticas", out.columns)
        self.assertTrue(out.empty)

    def test_rotulos_multilingues(self):
        self.assertEqual(normalizar_rotulo("positive"), "positivo")
        self.assertEqual(normalizar_rotulo("NEUTRAL"), "neutro")
        self.assertEqual(normalizar_rotulo("LABEL_0"), "indefinido")


if __name__ == "__main__":
    unittest.main()
