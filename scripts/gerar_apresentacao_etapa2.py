"""Gera uma apresentação PowerPoint da Etapa 2 em português, com exemplos do código real.

Uso:
    python scripts/gerar_apresentacao_etapa2.py
    python scripts/gerar_apresentacao_etapa2.py --saida saida/etapa2.pptx
"""
from __future__ import annotations

import argparse
from pathlib import Path

try:
    from pptx import Presentation
    from pptx.dml.color import RGBColor
    from pptx.enum.shapes import MSO_SHAPE
    from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
    from pptx.util import Inches, Pt
except ImportError as erro:
    raise SystemExit(
        "Dependência ausente. Instale com: python -m pip install -r requirements-apresentacao.txt"
    ) from erro

NAVY = RGBColor(27, 38, 59)
BLUE = RGBColor(65, 105, 150)
TEAL = RGBColor(42, 157, 143)
GOLD = RGBColor(233, 196, 106)
CORAL = RGBColor(231, 111, 81)
BG = RGBColor(247, 249, 252)
WHITE = RGBColor(255, 255, 255)
INK = RGBColor(38, 50, 56)
MUTED = RGBColor(95, 107, 120)
PALE_BLUE = RGBColor(230, 238, 247)
PALE_TEAL = RGBColor(226, 243, 239)
PALE_GOLD = RGBColor(250, 245, 224)
PALE_CORAL = RGBColor(250, 233, 228)
CODE_BG = RGBColor(20, 27, 39)
CODE_FG = RGBColor(220, 231, 243)
CODE_GREEN = RGBColor(135, 220, 170)
W, H = 13.333, 7.5
FONT = "Aptos"
CODE_FONT = "Consolas"


def add_box(slide, x, y, w, h, color, shape=MSO_SHAPE.ROUNDED_RECTANGLE):
    obj = slide.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
    obj.fill.solid()
    obj.fill.fore_color.rgb = color
    obj.line.fill.background()
    return obj


def add_text(slide, text, x, y, w, h, *, size=18, color=INK, bold=False,
             align=PP_ALIGN.LEFT, valign=MSO_ANCHOR.TOP, margin=0.05, font=FONT):
    shape = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = shape.text_frame
    tf.clear()
    tf.word_wrap = True
    tf.margin_left = Inches(margin)
    tf.margin_right = Inches(margin)
    tf.margin_top = Inches(margin)
    tf.margin_bottom = Inches(margin)
    tf.vertical_anchor = valign
    p = tf.paragraphs[0]
    p.alignment = align
    p.space_after = Pt(0)
    run = p.add_run()
    run.text = text
    run.font.name = font
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = color
    return shape


def add_code(slide, title, code, x, y, w, h, *, size=13):
    """Adiciona um trecho legível em estilo editor, baseado nos módulos do projeto."""
    add_box(slide, x, y, w, h, CODE_BG)
    add_text(slide, title, x + 0.18, y + 0.08, w - 0.36, 0.25,
             size=10, color=CODE_GREEN, bold=True, font=CODE_FONT)
    add_text(slide, code, x + 0.18, y + 0.39, w - 0.36, h - 0.48,
             size=size, color=CODE_FG, font=CODE_FONT, margin=0.02)


def add_header(slide, title, section="ETAPA 2"):
    add_text(slide, section.upper(), 0.62, 0.28, 3.2, 0.25, size=10, color=TEAL, bold=True)
    add_text(slide, title, 0.62, 0.65, 12.0, 0.62, size=27, color=NAVY, bold=True)
    add_box(slide, 0.64, 1.38, 0.75, 0.055, TEAL, MSO_SHAPE.RECTANGLE)


def add_footer(slide, number):
    add_text(slide, "Projeto MDNE · análise de comentários sobre IDEs", 0.62, 7.13, 10.4, 0.2,
             size=9, color=MUTED)
    add_text(slide, f"{number:02d}", 12.15, 7.1, 0.5, 0.24, size=10, color=MUTED, align=PP_ALIGN.RIGHT)


def new_slide(prs, title, number):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    slide.background.fill.solid()
    slide.background.fill.fore_color.rgb = BG
    add_header(slide, title)
    add_footer(slide, number)
    return slide


def add_card(slide, x, y, w, h, title, body, accent=TEAL, fill=WHITE, body_size=15):
    add_box(slide, x, y, w, h, fill)
    add_box(slide, x, y, 0.08, h, accent, MSO_SHAPE.RECTANGLE)
    add_text(slide, title, x + 0.2, y + 0.13, w - 0.38, 0.35, size=16, color=NAVY, bold=True)
    add_text(slide, body, x + 0.2, y + 0.56, w - 0.4, h - 0.66, size=body_size, color=INK)


def build_deck():
    prs = Presentation()
    prs.slide_width = Inches(W)
    prs.slide_height = Inches(H)
    prs.core_properties.title = "Etapa 2 — Análise semântica, embeddings e Transformers"
    prs.core_properties.subject = "Apresentação acadêmica do projeto de análise de comentários sobre IDEs"
    prs.core_properties.author = "Projeto MDNE — IDEs"
    prs.core_properties.keywords = "spaCy, embeddings, Transformers, análise semântica, sentimento"

    # 1. Capa
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    slide.background.fill.solid()
    slide.background.fill.fore_color.rgb = NAVY
    add_box(slide, 9.0, -0.5, 5.0, 8.5, BLUE, MSO_SHAPE.OVAL)
    add_box(slide, 10.0, 1.0, 2.8, 2.8, TEAL, MSO_SHAPE.OVAL)
    add_box(slide, 9.45, 4.15, 1.15, 1.15, GOLD, MSO_SHAPE.OVAL)
    add_box(slide, 11.5, 4.75, 0.8, 0.8, CORAL, MSO_SHAPE.OVAL)
    add_text(slide, "PROJETO MDNE · IDEs", 0.82, 1.1, 6.8, 0.35, size=13, color=GOLD, bold=True)
    add_text(slide, "Etapa 2", 0.82, 1.85, 7.6, 0.9, size=44, color=WHITE, bold=True)
    add_text(slide, "Análise semântica,\nembeddings e Transformers", 0.85, 2.9, 7.6, 1.45,
             size=28, color=WHITE, bold=True)
    add_text(slide, "Dos rótulos de sentimento à exploração do significado dos comentários.",
             0.88, 4.75, 7.2, 0.8, size=18, color=RGBColor(220, 229, 239))
    add_text(slide, "Apresentação acadêmica", 0.88, 6.65, 5.0, 0.3, size=12, color=RGBColor(190, 204, 220))

    # 2. Contexto
    slide = new_slide(prs, "De onde partimos?", 2)
    add_card(slide, 0.75, 1.8, 5.65, 3.55, "Etapa 1 · análise já existente",
             "• Coleta comentários públicos do YouTube\n• Limpa e identifica o idioma\n• Classifica sentimento\n• Analisa menções a IDEs e gera estatísticas/visualizações",
             accent=BLUE, body_size=17)
    add_card(slide, 6.85, 1.8, 5.65, 3.55, "A pergunta que ampliamos",
             "Além de “o comentário é positivo ou negativo?”, exploramos:\n\n• Sobre o que as pessoas comentam?\n• Quais comentários expressam ideias parecidas mesmo usando palavras diferentes?",
             accent=TEAL, fill=PALE_TEAL, body_size=17)
    add_text(slide, "A Etapa 2 complementa o fluxo: não apaga nem substitui as saídas da Etapa 1.",
             1.0, 5.85, 11.2, 0.5, size=19, color=NAVY, bold=True, align=PP_ALIGN.CENTER)

    # 3. Fluxo e comando real
    slide = new_slide(prs, "Novo fluxo de processamento", 3)
    steps = [("Comentários", "texto bruto", BLUE), ("Preparação", "limpeza + idioma", TEAL),
             ("spaCy", "sentenças, lemas,\nentidades e sintaxe", GOLD),
             ("Modelos", "sentimento +\nTransformer opcional", CORAL),
             ("Embeddings", "vetores para\nsimilaridade", BLUE), ("Exploração", "CSV + painel", TEAL)]
    x0, width, gap = 0.55, 1.85, 0.34
    for i, (title, body, color) in enumerate(steps):
        x = x0 + i * (width + gap)
        add_box(slide, x, 2.12, width, 1.62, WHITE)
        add_box(slide, x, 2.12, width, 0.12, color, MSO_SHAPE.RECTANGLE)
        add_text(slide, title, x + 0.1, 2.46, width - 0.2, 0.35, size=15, color=NAVY, bold=True, align=PP_ALIGN.CENTER)
        add_text(slide, body, x + 0.1, 2.93, width - 0.2, 0.62, size=12, color=INK, align=PP_ALIGN.CENTER)
        if i < len(steps) - 1:
            add_text(slide, "→", x + width, 2.7, gap, 0.35, size=18, color=MUTED, bold=True, align=PP_ALIGN.CENTER)
    add_code(slide, "COMANDO CLI · etapa2.py", "python etapa2.py --embeddings --transformer",
             1.0, 4.35, 11.3, 1.05, size=17)
    add_text(slide, "O pipeline salva o CSV semântico e, quando solicitado, os vetores em um arquivo NPZ separado.",
             1.0, 5.75, 11.3, 0.6, size=16, color=INK, align=PP_ALIGN.CENTER)

    # 4. spaCy com trecho do módulo semantica.py
    slide = new_slide(prs, "Novidade 1 · pipeline semântico com spaCy", 4)
    add_bullets = ["Divide o comentário em sentenças.", "Extrai termos de conteúdo e seus lemas.",
                   "Registra entidades identificadas pelo modelo.", "Produz relações sujeito/verbo/complemento aproximadas."]
    for i, item in enumerate(add_bullets):
        add_text(slide, "•  " + item, 0.85, 1.78 + i * 0.68, 5.55, 0.5, size=16, color=INK)
    add_code(slide, "src/preprocessamento/semantica.py", "docs = nlp.pipe(textos, batch_size=64)\n\nfor doc in docs:\n    sentencas = [s.text for s in doc.sents]\n    lemas = [t.lemma_.lower() for t in doc\n             if t.pos_ in POS_CONTEUDO and not t.is_stop]\n    entidades = [(e.text, e.label_) for e in doc.ents]",
             6.55, 1.72, 6.0, 3.75, size=12)
    add_text(slide, "Saídas no CSV: sentencas · termos_semanticos · entidades_semanticas · relacoes_sintaticas",
             0.9, 5.95, 11.7, 0.6, size=14, color=NAVY, bold=True, align=PP_ALIGN.CENTER)
    add_text(slide, "As relações sintáticas são pistas do modelo, não fatos garantidos.",
             0.9, 6.55, 11.7, 0.3, size=11, color=MUTED, align=PP_ALIGN.CENTER)

    # 5. Embeddings com trecho real
    slide = new_slide(prs, "Novidade 2 · embeddings e similaridade", 5)
    add_card(slide, 0.8, 1.75, 3.65, 1.55, "Texto", "“A IDE fica lenta com muitos plugins.”", accent=BLUE, fill=PALE_BLUE, body_size=15)
    add_text(slide, "→", 4.48, 2.27, 0.45, 0.4, size=24, color=MUTED, bold=True, align=PP_ALIGN.CENTER)
    add_card(slide, 5.0, 1.75, 3.65, 1.55, "Embedding", "Vetor de 384 dimensões\n(exemplo observado)", accent=TEAL, fill=PALE_TEAL, body_size=15)
    add_text(slide, "→", 8.69, 2.27, 0.45, 0.4, size=24, color=MUTED, bold=True, align=PP_ALIGN.CENTER)
    add_card(slide, 9.2, 1.75, 3.3, 1.55, "Busca", "Recupera textos com significado próximo.", accent=GOLD, fill=PALE_GOLD, body_size=14)
    add_code(slide, "src/modelagem/embeddings.py · vetores normalizados", "vetores = modelo.encode(\n    textos,\n    convert_to_numpy=True,\n    normalize_embeddings=True,\n)\n\n# vetores normalizados: produto escalar = cosseno",
             0.85, 3.72, 6.05, 2.25, size=12)
    add_code(slide, "app_etapa2.py · ranking por similaridade", "consulta = modelo.encode(\n    [frase], normalize_embeddings=True\n)[0]\nscores = embeddings @ consulta\nmais_proximos = scores.argsort()[::-1][:10]",
             7.18, 3.72, 5.3, 2.25, size=12)
    add_text(slide, "Resultado executado: 1.958 comentários × 384 dimensões · arquivo *_embeddings.npz",
             0.9, 6.35, 11.6, 0.35, size=15, color=NAVY, bold=True, align=PP_ALIGN.CENTER)

    # 6. Transformers com chamada real
    slide = new_slide(prs, "Novidade 3 · comparar classificadores", 6)
    add_card(slide, 0.85, 1.78, 5.55, 1.3, "Classificador principal", "Mantém sentimento, probabilidades e score da análise principal.", accent=BLUE, fill=PALE_BLUE, body_size=15)
    add_card(slide, 6.9, 1.78, 5.55, 1.3, "Transformer adicional", "Acrescenta rótulo e confiança em colunas `_transformer`.", accent=CORAL, fill=PALE_CORAL, body_size=15)
    add_code(slide, "src/modelagem/transformers.py · inferência em lote", "previsoes = pipe(\n    textos, truncation=True,\n    batch_size=self.batch_size\n)\n\nrotulo = normalizar_rotulo(pred['label'])\nconfianca = float(pred['score'])",
             0.9, 3.48, 6.1, 2.55, size=13)
    add_text(slide, "O painel cruza os rótulos dos dois modelos para expor concordâncias e divergências.",
             7.35, 3.72, 4.9, 1.05, size=18, color=NAVY, bold=True)
    add_text(slide, "Concordância não comprova acurácia. A avaliação exige uma amostra rotulada manualmente.",
             7.35, 5.0, 4.8, 0.85, size=14, color=MUTED)

    # 7. Visualização com código PCA real
    slide = new_slide(prs, "Nova visualização · app_etapa2.py", 7)
    add_card(slide, 0.85, 1.75, 3.7, 1.45, "Mapa semântico", "Projeção PCA 2D; cor representa sentimento.", accent=TEAL, fill=PALE_TEAL, body_size=15)
    add_card(slide, 4.82, 1.75, 3.7, 1.45, "Conteúdo", "Lemas, entidades e comentários para inspeção.", accent=BLUE, fill=PALE_BLUE, body_size=15)
    add_card(slide, 8.78, 1.75, 3.7, 1.45, "Busca", "Digite uma frase e recupere comentários semelhantes.", accent=GOLD, fill=PALE_GOLD, body_size=15)
    add_code(slide, "app_etapa2.py · redução de dimensão e gráfico interativo", "coords = projetar_pca(embeddings)\nmapa['PCA 1'] = coords[:, 0]\nmapa['PCA 2'] = coords[:, 1]\n\nfig = px.scatter(\n    mapa, x='PCA 1', y='PCA 2',\n    color='cor_mapa', hover_data=['texto']\n)\nst.plotly_chart(fig, use_container_width=True)",
             0.9, 3.55, 11.6, 2.55, size=13)
    add_text(slide, "PCA é exploratória: os eixos não são tópicos nomeados e proximidade não prova equivalência.",
             0.9, 6.4, 11.6, 0.35, size=12, color=MUTED, align=PP_ALIGN.CENTER)

    # 8. Demonstração
    slide = new_slide(prs, "Demonstração ao vivo", 8)
    etapas = ["Abra o painel Streamlit da Etapa 2.", "Mostre o mapa e filtre por sentimento.",
              "Explore os lemas, entidades e comentários.", "Digite uma consulta na busca semântica e leia os resultados."]
    for i, item in enumerate(etapas):
        y = 1.85 + i * 0.83
        add_text(slide, str(i + 1), 0.95, y, 0.5, 0.45, size=25, color=TEAL, bold=True)
        add_text(slide, item, 1.6, y + 0.04, 10.7, 0.5, size=18, color=NAVY, bold=True)
    add_code(slide, "COMANDOS PARA RODAR LOCALMENTE", "python etapa2.py --embeddings --transformer\nstreamlit run app_etapa2.py",
             1.0, 5.55, 11.3, 1.0, size=16)

    # 9. Fechamento
    slide = new_slide(prs, "Resultado, impacto e próximos passos", 9)
    add_card(slide, 0.8, 1.85, 3.75, 2.55, "Resultado", "CSV semântico + arquivo NPZ de embeddings + painel interativo.", accent=BLUE, fill=PALE_BLUE, body_size=16)
    add_card(slide, 4.8, 1.85, 3.75, 2.55, "Impacto", "Passamos de contagens e polaridade para explorar conteúdo e similaridade entre comentários.", accent=TEAL, fill=PALE_TEAL, body_size=16)
    add_card(slide, 8.8, 1.85, 3.75, 2.55, "Próximo passo", "Validar previsões com rótulos humanos e implementar agrupamento/rotulagem de tópicos.", accent=GOLD, fill=PALE_GOLD, body_size=16)
    add_text(slide, "A Etapa 2 amplia as perguntas possíveis; os resultados seguem sujeitos à validação e às limitações dos modelos.",
             1.0, 5.05, 11.2, 0.85, size=18, color=NAVY, bold=True, align=PP_ALIGN.CENTER)
    add_text(slide, "Obrigado(a)!", 1.0, 6.1, 11.2, 0.45, size=24, color=TEAL, bold=True, align=PP_ALIGN.CENTER)

    return prs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--saida", type=Path, default=Path("apresentacao_etapa2.pptx"),
                        help="Caminho do arquivo .pptx a gerar (padrão: apresentacao_etapa2.pptx na raiz)")
    args = parser.parse_args()
    args.saida.parent.mkdir(parents=True, exist_ok=True)
    build_deck().save(args.saida)
    print(f"Apresentação criada: {args.saida.resolve()}")
    print("Abra no PowerPoint/LibreOffice e exporte como PDF se necessário.")


if __name__ == "__main__":
    main()
