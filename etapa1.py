"""Etapa 1 — PLN (RE + spaCy) sobre os comentários coletados por dados/brutos/bronze.py.

Uso (na raiz do projeto):
    python etapa1.py                                   # usa a coleta mais recente em dados/brutos/youtube/
    python etapa1.py --entrada dados/brutos/youtube/<execucao>
    python etapa1.py --entrada tests/fixtures/execucao_exemplo   # dados SIMULADOS, só para testar
"""
import argparse
import logging
from pathlib import Path

from src import comum
from src.analise import estatisticas as est, graficos
from src.modelagem.sentimentos import AnalisadorSentimento
from src.preprocessamento import emojis, idioma, limpeza, nlp_spacy

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("etapa1")


def main(entrada: Path = None, usar_modelo: bool = True):
    comum.garantir_pastas()
    pasta = entrada or comum.execucao_mais_recente()
    logger.info("Lendo comentários de %s", pasta)
    df = comum.carregar_comentarios(pasta)
    logger.info("%d comentários em %d vídeo(s)", len(df), df["video_id"].nunique())

    # 1) Limpeza com RE, emojis e idioma
    df["texto_leve"] = df["texto"].apply(limpeza.limpeza_leve)
    df["texto_limpo"] = df["texto"].apply(limpeza.limpeza_pesada)
    df["n_emojis"] = df["texto"].apply(emojis.contar_emojis)
    df["n_risadas"] = df["texto"].apply(limpeza.contar_risadas)
    df["n_timestamps"] = df["texto"].apply(limpeza.contar_timestamps)
    df["idioma"] = df["texto_leve"].apply(idioma.detectar_idioma)
    df["classificar"] = [idioma.deve_classificar(i, t) for i, t in zip(df["idioma"], df["texto_leve"])]
    df.loc[df["texto_leve"].str.strip() == "", "classificar"] = False   # só link/timestamp/menção
    logger.info("Idiomas: %s", df["idioma"].value_counts().to_dict())
    logger.info("%d comentários fora do recorte (outro idioma ou sem texto)", (~df["classificar"]).sum())

    # 2) spaCy: lemas e entidades
    df = nlp_spacy.processar(df, "texto_leve", "texto_limpo")
    df.to_csv(comum.INTERMEDIARIOS / "comentarios_limpos.csv", index=False, encoding="utf-8-sig")

    # 3) Sentimento (só no recorte)
    usados = df[df["classificar"]].reset_index(drop=True)
    usados = AnalisadorSentimento(usar_modelo).aplicar(usados, "texto_leve")
    usados.to_csv(comum.PROCESSADOS / "comentarios_sentimento.csv", index=False, encoding="utf-8-sig")

    # 4) Estatísticas e gráficos
    resumo = est.resumo_por_video(usados)
    resumo.to_csv(comum.TABELAS / "resumo_por_video.csv", index=False)
    est.resumo_por_tipo(usados).to_csv(comum.TABELAS / "resumo_por_tipo.csv", index=False)
    tab_termos = est.termos_por_sentimento(usados)
    tab_termos.to_csv(comum.TABELAS / "termos_por_sentimento.csv", index=False)
    est.top_emojis(usados).to_csv(comum.TABELAS / "top_emojis.csv", index=False)
    tab_ent = est.top_entidades(usados)
    tab_ent.to_csv(comum.TABELAS / "top_entidades.csv", index=False)

    graficos.sentimento_por_video(resumo)
    graficos.distribuicao_score(usados)
    graficos.termos(tab_termos)
    graficos.entidades(tab_ent)
    for video_id in usados["video_id"].unique():
        graficos.nuvem(usados, video_id)

    colunas = ["video_id", "n", "pct_positivo", "pct_neutro", "pct_negativo", "score_medio"]
    logger.info("Resumo por vídeo (método: %s):\n%s", usados["metodo_sentimento"].iloc[0],
                resumo[colunas].round(1).to_string(index=False))
    return usados, resumo


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("--entrada", type=Path, help="Pasta de uma execução do bronze.py")
    ap.add_argument("--sem-modelo", action="store_true", help="Não carrega o pysentimiento (só para testes)")
    args = ap.parse_args()
    main(args.entrada, usar_modelo=not args.sem_modelo)