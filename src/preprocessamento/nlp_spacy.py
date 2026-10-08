"""Lematização e reconhecimento de entidades com spaCy (pt_core_news_sm)."""
import logging

import pandas as pd
import spacy

logger = logging.getLogger("nlp_spacy")
MODELO = "pt_core_news_sm"
CLASSES_CONTEUDO = {"NOUN", "PROPN", "ADJ", "VERB"}
POS_RUIDO_NER = {"VERB", "AUX", "INTJ", "ADJ", "ADV"}   # o modelo sm marca "Gostei"/"Amei" como entidade
STOP_EXTRA = {"vídeo", "video", "canal", "comentário", "vc", "vcs", "pra", "pro", "né", "tá", "ta",
              "aí", "ai", "muito", "tudo", "assim", "aqui", "cara", "mano", "gente"}


def carregar_modelo():
    try:
        return spacy.load(MODELO, disable=["parser"])
    except OSError:
        logger.info("Baixando o modelo %s ...", MODELO)
        spacy.cli.download(MODELO)
        return spacy.load(MODELO, disable=["parser"])


def processar(df: pd.DataFrame, col_leve: str, col_pesada: str) -> pd.DataFrame:
    """Acrescenta `lemas` (palavras de conteúdo) e `entidades` ('texto|TIPO;texto|TIPO')."""
    nlp = carregar_modelo()
    df = df.copy()
    docs_pesados = nlp.pipe(df[col_pesada].tolist(), batch_size=64)
    df["lemas"] = [
        " ".join(
            t.lemma_.lower() for t in doc
            if t.pos_ in CLASSES_CONTEUDO and not t.is_stop and len(t.lemma_) > 2
            and t.lemma_.lower() not in STOP_EXTRA)
        for doc in docs_pesados]
    docs_leves = nlp.pipe(df[col_leve].tolist(), batch_size=64)     # NER precisa de maiúsculas
    df["entidades"] = [
        ";".join(f"{e.text.strip()}|{e.label_}" for e in doc.ents
                  if len(e.text.strip()) > 2 and e.root.pos_ not in POS_RUIDO_NER)
        for doc in docs_leves]
    return df
