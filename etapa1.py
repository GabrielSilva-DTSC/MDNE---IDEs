"""Etapa 1 — PLN (RE + spaCy) sobre os comentários coletados por dados/brutos/bronze.py.

Foco: quais IDEs são mais citadas e qual o sentimento dos comentários sobre cada uma.

Uso (na raiz do projeto):
    python etapa1.py                          # junta TODAS as coletas em dados/brutos/youtube/
    python etapa1.py --entrada dados/brutos/youtube/<execucao>   # só uma execução
    python etapa1.py --entrada tests/fixtures/execucao_exemplo --sem-modelo   # dados SIMULADOS

Os metadados dos vídeos (nome, canal, formato) vêm de dados/brutos/videos.csv; as colunas de
linguagem/grupo/escopo, se existirem, são ignoradas.
"""
import argparse
import logging
from pathlib import Path

import pandas as pd

from src import comum
from src.analise import estatisticas as est, graficos, ides as an_ides
from src.modelagem.sentimentos import AnalisadorSentimento
from src.preprocessamento import emojis, idioma, ides, limpeza, nlp_spacy

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("etapa1")


def main(entrada: Path = None, usar_modelo: bool = True, metadados: Path = comum.VIDEOS_CSV,
         min_mencoes: int = an_ides.MIN_MENCOES_PADRAO):
    comum.garantir_pastas()
    for antiga in comum.ASSETS.glob("nuvem_*.png"):       # evita sobras de execuções anteriores
        antiga.unlink()

    # 0) Leitura: uma execução (--entrada) ou todas as coletas
    if entrada:
        logger.info("Lendo comentários de %s", entrada)
        df = comum.carregar_comentarios(entrada)
    else:
        logger.info("Juntando as coletas de %s (vale a mais recente de cada vídeo)", comum.BRUTOS)
        df = comum.carregar_coletas()
    meta = comum.ler_metadados(metadados) if Path(metadados).exists() else None
    if meta is None:
        logger.warning("%s não encontrado: os vídeos ficarão sem grupo.", metadados)
    df = comum.associar_metadados(df, meta)
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

    # 3) Sentimento dos comentários (só no recorte) — panorama geral
    analisador = AnalisadorSentimento(usar_modelo)
    usados = df[df["classificar"]].reset_index(drop=True)
    usados = analisador.aplicar(usados, "texto_leve")
    usados.to_csv(comum.PROCESSADOS / "comentarios_sentimento.csv", index=False, encoding="utf-8-sig")

    # 4) IDEs citadas: uma menção = (comentário, IDE). O sentimento é do TRECHO que fala da IDE.
    mencoes = ides.extrair_mencoes(usados, "texto_leve")
    logger.info("%d comentários citam alguma IDE (%.0f%% dos classificados); %d menções no total",
                mencoes["comentario_id"].nunique(), 100 * mencoes["comentario_id"].nunique() / len(usados),
                len(mencoes))
    resumo_ide = pd.DataFrame()
    if mencoes.empty:
        logger.warning("Nenhuma IDE do catálogo (src/preprocessamento/ides.py) foi citada nos comentários.")
    else:
        mencoes = analisador.aplicar(mencoes, "texto_mencao")
        mencoes["texto_mencao_pesado"] = mencoes["texto_mencao"].apply(
            lambda t: limpeza.limpeza_pesada(ides.remover_nomes(t)))
        mencoes = nlp_spacy.processar(mencoes, "texto_mencao", "texto_mencao_pesado")
        mencoes.drop(columns=["texto_mencao_pesado"]).to_csv(
            comum.PROCESSADOS / "mencoes_ides.csv", index=False, encoding="utf-8-sig")
        resumo_ide = an_ides.resumo_por_ide(mencoes, min_mencoes)

    # 5) Estatísticas
    t = comum.TABELAS
    por_video = est.resumo_por_video(usados)
    por_video.to_csv(t / "resumo_por_video.csv", index=False)
    est.resumo_por_dimensao(usados.assign(todos="Todos"), "todos", incluir_total=False).to_csv(
        t / "resumo_geral.csv", index=False)
    est.resumo_por_tipo(usados).to_csv(t / "resumo_por_tipo.csv", index=False)
    tab_termos = est.termos_por_sentimento(usados)
    tab_termos.to_csv(t / "termos_por_sentimento.csv", index=False)
    est.top_emojis(usados).to_csv(t / "top_emojis.csv", index=False)
    tab_ent = est.top_entidades(usados)
    tab_ent.to_csv(t / "top_entidades.csv", index=False)
    if not resumo_ide.empty:
        resumo_ide.to_csv(t / "resumo_por_ide.csv", index=False)
        com_amostra = resumo_ide[resumo_ide["amostra_suficiente"]]
        principais = com_amostra["ide"].head(8).tolist()
        an_ides.termos_por_ide(mencoes, principais).to_csv(t / "termos_por_ide.csv", index=False)
        an_ides.exemplos_por_ide(mencoes, principais).to_csv(t / "exemplos_por_ide.csv", index=False)

    # 6) Gráficos
    for antigo in ("sentimento_por_grupo.png", "sentimento_por_formato.png", "intervalos_positivos_grupo.png"):
        (comum.ASSETS / antigo).unlink(missing_ok=True)      # sobras da análise por grupo
    if not resumo_ide.empty:
        graficos.ides_mais_citadas(resumo_ide)
        if len(com_amostra):
            por_saldo = com_amostra.sort_values("saldo", ascending=False)
            graficos.sentimento_por_dimensao(
                por_saldo, "ide", f"Sentimento por IDE (IDEs com {min_mencoes}+ comentários)",
                "sentimento_por_ide.png")
            graficos.intervalos_positivos(com_amostra, "ide", "intervalos_positivos_ide.png")
        else:
            logger.warning("Nenhuma IDE chegou a %d menções: sem gráficos de sentimento por IDE.", min_mencoes)
    graficos.sentimento_por_video(por_video)
    graficos.distribuicao_score(usados)
    graficos.termos(tab_termos)
    graficos.entidades(tab_ent)
    graficos.nuvem(usados, "todos", "Termos mais frequentes (todos os vídeos)")

    logger.info("Sentimento geral dos comentários (método: %s): %.0f%% positivo, %.0f%% neutro, %.0f%% negativo",
                usados["metodo_sentimento"].iloc[0], *(100 * (usados["sentimento"] == r).mean() for r in est.ORDEM))
    if not resumo_ide.empty:
        colunas = ["ide", "n_comentarios", "n_videos", "pct_positivo", "pct_neutro", "pct_negativo", "saldo"]
        logger.info("Sentimento por IDE (da mais citada):\n%s",
                    resumo_ide[colunas].head(12).round(1).to_string(index=False))
    return usados, por_video, mencoes


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("--entrada", type=Path, help="Pasta de UMA execução do bronze.py (padrão: todas)")
    ap.add_argument("--metadados", type=Path, default=comum.VIDEOS_CSV, help="CSV com os dados dos vídeos")
    ap.add_argument("--sem-modelo", action="store_true", help="Não carrega o pysentimiento (só para testes)")
    ap.add_argument("--min-mencoes", type=int, default=an_ides.MIN_MENCOES_PADRAO,
                    help="Mínimo de comentários por IDE para entrar nos gráficos de sentimento (padrão: %(default)s)")
    args = ap.parse_args()
    main(args.entrada, usar_modelo=not args.sem_modelo, metadados=args.metadados, min_mencoes=args.min_mencoes)
