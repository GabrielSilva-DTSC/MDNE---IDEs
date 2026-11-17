"""Análise semântica de comentários com pipeline linguístico spaCy.

As saídas são serializadas como JSON em colunas para continuarem portáveis em CSV.
"""
import json
import logging
from typing import Any

import pandas as pd
import spacy

logger = logging.getLogger("semantica")
MODELO = "pt_core_news_sm"
POS_CONTEUDO = {"NOUN", "PROPN", "ADJ", "VERB", "ADV"}


def carregar_modelo():
    """Carrega o modelo português com parser, POS, lematizador e NER habilitados."""
    try:
        return spacy.load(MODELO)
    except OSError:
        logger.info("Baixando modelo spaCy %s", MODELO)
        spacy.cli.download(MODELO)
        return spacy.load(MODELO)


def _json(valor: Any) -> str:
    return json.dumps(valor, ensure_ascii=False)


def _extrair_doc(doc) -> dict:
    sentencas = [s.text.strip() for s in doc.sents if s.text.strip()]
    termos = [
        {"texto": t.text, "lema": t.lemma_.lower(), "pos": t.pos_}
        for t in doc
        if t.pos_ in POS_CONTEUDO and not t.is_stop and not t.is_punct
        and t.lemma_.strip() and len(t.lemma_.strip()) > 1
    ]
    entidades = [
        {"texto": ent.text.strip(), "tipo": ent.label_}
        for ent in doc.ents if ent.text.strip()
    ]
    # Relações sujeito/verbo/objeto são pistas sintáticas, não uma extração infalível de fatos.
    relacoes = []
    for verbo in doc:
        if verbo.pos_ not in {"VERB", "AUX"}:
            continue
        sujeitos = [c.text for c in verbo.children if c.dep_ in {"nsubj", "nsubj:pass", "csubj"}]
        objetos = [c.text for c in verbo.children if c.dep_ in {"obj", "dobj", "iobj", "attr", "obl"}]
        if sujeitos or objetos:
            relacoes.append({"sujeito": sujeitos, "verbo": verbo.lemma_.lower(), "complemento": objetos})
    return {"sentencas": sentencas, "termos": termos, "entidades": entidades, "relacoes": relacoes}


def processar(df: pd.DataFrame, coluna_texto: str = "texto_leve", *, nlp=None,
              batch_size: int = 64) -> pd.DataFrame:
    """Acrescenta sentenças, termos/lemmas, entidades e relações sintáticas.

    ``nlp`` pode ser injetado por testes; em produção o modelo é carregado sob demanda.
    """
    if coluna_texto not in df.columns:
        raise KeyError(f"Coluna de texto ausente: {coluna_texto}")
    resultado = df.copy()
    if resultado.empty:
        for coluna in ("sentencas", "termos_semanticos", "entidades_semanticas", "relacoes_sintaticas"):
            resultado[coluna] = pd.Series(dtype="object")
        return resultado
    nlp = nlp or carregar_modelo()
    textos = resultado[coluna_texto].fillna("").astype(str).tolist()
    dados = [_extrair_doc(doc) for doc in nlp.pipe(textos, batch_size=batch_size)]
    resultado["sentencas"] = [_json(d["sentencas"]) for d in dados]
    resultado["termos_semanticos"] = [_json(d["termos"]) for d in dados]
    resultado["entidades_semanticas"] = [_json(d["entidades"]) for d in dados]
    resultado["relacoes_sintaticas"] = [_json(d["relacoes"]) for d in dados]
    return resultado
