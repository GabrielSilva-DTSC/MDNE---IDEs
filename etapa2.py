"""Executa a Etapa 2 sobre uma execução ou sobre as coletas consolidadas.

Exemplos:
    python etapa2.py --sem-modelo-sentimento --entrada tests/fixtures/execucao_exemplo
    python etapa2.py --embeddings --transformer
"""
import argparse
import logging
from pathlib import Path

import pandas as pd

from src import comum
from src.modelagem.embeddings import GeradorEmbeddings
from src.pipeline_etapa2 import executar_etapa2

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("etapa2")


def main(entrada: Path | None = None, saida: Path | None = None, *, embeddings: bool = False,
         transformer: bool = False, usar_modelo_sentimento: bool = True,
         modelo_embedding: str = GeradorEmbeddings.__init__.__defaults__[0]):
    comum.garantir_pastas()
    df = comum.carregar_comentarios(entrada) if entrada else comum.carregar_coletas()
    meta = comum.ler_metadados() if comum.VIDEOS_CSV.exists() else None
    df = comum.associar_metadados(df, meta)
    logger.info("Processando %d comentários", len(df))
    resultado = executar_etapa2(df, usar_modelo_sentimento=usar_modelo_sentimento,
                                usar_transformer=transformer)
    destino = Path(saida) if saida else comum.PROCESSADOS / "comentarios_etapa2.csv"
    destino.parent.mkdir(parents=True, exist_ok=True)
    resultado.to_csv(destino, index=False, encoding="utf-8-sig")
    logger.info("CSV da Etapa 2 salvo em %s", destino)

    if embeddings:
        gerador = GeradorEmbeddings(modelo=modelo_embedding)
        textos = resultado["texto_leve"].fillna("").tolist()
        vetores = gerador.gerar(textos)
        ids = resultado["comentario_id"].fillna("").astype(str).tolist()
        caminho = destino.with_name(destino.stem + "_embeddings.npz")
        gerador.salvar(caminho, ids, vetores)
        logger.info("Embeddings normalizados (%s) salvos em %s", vetores.shape, caminho)
    return resultado


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--entrada", type=Path, help="Pasta de uma execução; padrão: consolida coletas")
    parser.add_argument("--saida", type=Path, help="CSV de saída (padrão: dados/processados/comentarios_etapa2.csv)")
    parser.add_argument("--embeddings", action="store_true", help="Gera embeddings Sentence Transformers em arquivo NPZ")
    parser.add_argument("--modelo-embedding", default=GeradorEmbeddings.__init__.__defaults__[0],
                        help="ID ou caminho local do modelo Sentence Transformers")
    parser.add_argument("--transformer", action="store_true", help="Inclui classificação Hugging Face Transformers")
    parser.add_argument("--sem-modelo-sentimento", action="store_true",
                        help="Usa o léxico de reserva da Etapa 1 (apenas testes; não use como resultado final)")
    args = parser.parse_args()
    main(args.entrada, args.saida, embeddings=args.embeddings, transformer=args.transformer,
         usar_modelo_sentimento=not args.sem_modelo_sentimento, modelo_embedding=args.modelo_embedding)
