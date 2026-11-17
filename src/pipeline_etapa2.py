"""Pipeline reutilizável da Etapa 2: spaCy, sentimento e recursos opcionais de Transformers."""
import pandas as pd

from src.modelagem.sentimentos import AnalisadorSentimento
from src.preprocessamento import emojis, idioma, limpeza, semantica


def executar_etapa2(df: pd.DataFrame, *, usar_modelo_sentimento: bool = True,
                    usar_transformer: bool = False) -> pd.DataFrame:
    """Enriquece comentários; embeddings são gerados no CLI para poderem ser salvos em NPZ."""
    if "texto" not in df.columns:
        raise KeyError("O DataFrame precisa da coluna 'texto'.")
    resultado = df.copy()
    resultado["texto_leve"] = resultado["texto"].apply(limpeza.limpeza_leve)
    resultado["texto_limpo"] = resultado["texto"].apply(limpeza.limpeza_pesada)
    resultado["n_emojis"] = resultado["texto"].apply(emojis.contar_emojis)
    resultado["idioma"] = resultado["texto_leve"].apply(idioma.detectar_idioma)
    resultado["classificar"] = [idioma.deve_classificar(i, t) for i, t in
                                 zip(resultado["idioma"], resultado["texto_leve"])]
    resultado.loc[resultado["texto_leve"].str.strip() == "", "classificar"] = False
    resultado = semantica.processar(resultado, "texto_leve")

    selecionados = resultado[resultado["classificar"]].copy()
    if not selecionados.empty:
        selecionados = AnalisadorSentimento(usar_modelo_sentimento).aplicar(selecionados, "texto_leve")
        if usar_transformer:
            from src.modelagem.transformers import ClassificadorTransformers
            selecionados = ClassificadorTransformers().aplicar(selecionados, "texto_leve")
        resultado = resultado.merge(
            selecionados[["comentario_id", "sentimento", "p_pos", "p_neu", "p_neg", "score",
                          "metodo_sentimento"] + (["sentimento_transformer", "score_transformer",
                          "p_pos_transformer", "p_neu_transformer", "p_neg_transformer",
                          "modelo_transformer"] if usar_transformer else [])],
            on="comentario_id", how="left", validate="one_to_one",
        )
    else:
        for coluna in ("sentimento", "metodo_sentimento"):
            resultado[coluna] = pd.NA
        for coluna in ("p_pos", "p_neu", "p_neg", "score"):
            resultado[coluna] = pd.NA
    return resultado
