"""Gera uma apresentação PowerPoint da Etapa 2 em português.

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

# Paleta visual inspirada no tema do projeto.
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

W, H = 13.333, 7.5
FONT = "Aptos"


def add_box(slide, x, y, w, h, color, shape=MSO_SHAPE.ROUNDED_RECTANGLE, line_color=None):
    obj = slide.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
    obj.fill.solid()
    obj.fill.fore_color.rgb = color
    obj.line.fill.background() if line_color is None else None
    if line_color is not None:
        obj.line.color.rgb = line_color
    return obj


def add_text(slide, text, x, y, w, h, *, size=18, color=INK, bold=False,
             align=PP_ALIGN.LEFT, valign=MSO_ANCHOR.TOP, margin=0.04):
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
    run.font.name = FONT
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = color
    return shape


def add_bullets(slide, items, x, y, w, h, *, size=19, color=INK, gap=9):
    shape = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = shape.text_frame
    tf.clear()
    tf.word_wrap = True
    tf.margin_left = Inches(0.06)
    tf.margin_right = Inches(0.06)
    tf.margin_top = Inches(0.03)
    for i, item in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.text = "•  " + item
        p.font.name = FONT
        p.font.size = Pt(size)
        p.font.color.rgb = color
        p.space_after = Pt(gap)
    return shape


def add_header(slide, title, section="ETAPA 2"):
    add_text(slide, section.upper(), 0.62, 0.32, 3.2, 0.28, size=10, color=TEAL, bold=True)
    add_text(slide, title, 0.62, 0.72, 12.0, 0.62, size=28, color=NAVY, bold=True)
    add_box(slide, 0.64, 1.43, 0.75, 0.055, TEAL, MSO_SHAPE.RECTANGLE)


def add_footer(slide, number):
    add_text(slide, "Projeto de análise de comentários sobre IDEs · Etapa 2", 0.62, 7.13, 10.4, 0.2,
             size=9, color=MUTED)
    add_text(slide, f"{number:02d}", 12.15, 7.1, 0.5, 0.24, size=10, color=MUTED, align=PP_ALIGN.RIGHT)


def new_slide(prs, title=None, number=None, section="ETAPA 2"):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    slide.background.fill.solid()
    slide.background.fill.fore_color.rgb = BG
    if title:
        add_header(slide, title, section)
    if number is not None:
        add_footer(slide, number)
    return slide


def add_card(slide, x, y, w, h, title, body, accent=TEAL, fill=WHITE, title_size=17, body_size=14):
    add_box(slide, x, y, w, h, fill)
    add_box(slide, x, y, 0.08, h, accent, MSO_SHAPE.RECTANGLE)
    add_text(slide, title, x + 0.22, y + 0.18, w - 0.4, 0.42, size=title_size, color=NAVY, bold=True)
    add_text(slide, body, x + 0.22, y + 0.68, w - 0.42, h - 0.82, size=body_size, color=INK)


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
    slide.background.fill.solid(); slide.background.fill.fore_color.rgb = NAVY
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
    add_card(slide, 0.75, 1.85, 5.65, 3.5, "Etapa 1 · análise já existente",
             "• Coleta comentários públicos do YouTube\n• Limpa e identifica o idioma\n• Classifica sentimento\n• Analisa menções a IDEs e gera estatísticas/visualizações",
             accent=BLUE, fill=WHITE, body_size=17)
    add_card(slide, 6.85, 1.85, 5.65, 3.5, "A pergunta que ampliamos",
             "Além de “o comentário é positivo ou negativo?”, queremos explorar:\n\n• Sobre o que as pessoas comentam?\n• Quais comentários expressam ideias parecidas, mesmo usando palavras diferentes?",
             accent=TEAL, fill=PALE_TEAL, body_size=17)
    add_text(slide, "A Etapa 2 complementa o fluxo: não apaga nem substitui as saídas da Etapa 1.",
             1.0, 5.85, 11.2, 0.5, size=19, color=NAVY, bold=True, align=PP_ALIGN.CENTER)

    # 3. Mapa do pipeline
    slide = new_slide(prs, "Novo fluxo de processamento", 3)
    steps = [
        ("Comentários", "texto bruto", BLUE),
        ("Preparação", "limpeza + idioma", TEAL),
        ("spaCy", "sentenças, lemas,\nentidades, sintaxe", GOLD),
        ("Modelos", "sentimento +\nTransformer opcional", CORAL),
        ("Embeddings", "vetores para\nsimilaridade", BLUE),
        ("Exploração", "CSV + painel\ninterativo", TEAL),
    ]
    x0, width, gap = 0.55, 1.85, 0.34
    for i, (title, body, color) in enumerate(steps):
        x = x0 + i * (width + gap)
        add_box(slide, x, 2.55, width, 2.05, WHITE)
        add_box(slide, x, 2.55, width, 0.13, color, MSO_SHAPE.RECTANGLE)
        add_text(slide, title, x + 0.12, 2.9, width - 0.24, 0.42, size=16, color=NAVY, bold=True, align=PP_ALIGN.CENTER)
        add_text(slide, body, x + 0.12, 3.48, width - 0.24, 0.8, size=13, color=INK, align=PP_ALIGN.CENTER)
        if i < len(steps) - 1:
            add_text(slide, "→", x + width, 3.22, gap, 0.4, size=20, color=MUTED, bold=True, align=PP_ALIGN.CENTER)
    add_text(slide, "Execução reproduzível:  python etapa2.py --embeddings --transformer",
             0.9, 5.35, 11.5, 0.55, size=18, color=NAVY, bold=True, align=PP_ALIGN.CENTER)
    add_text(slide, "Os recursos opcionais de embeddings e Transformers são carregados quando solicitados.",
             1.0, 6.0, 11.3, 0.35, size=13, color=MUTED, align=PP_ALIGN.CENTER)

    # 4. SpaCy
    slide = new_slide(prs, "Novidade 1 · pipeline semântico com spaCy", 4)
    cards = [
        (0.75, 1.9, "Sentenças", "Divide o comentário em frases para facilitar a leitura do contexto.", BLUE, PALE_BLUE),
        (6.85, 1.9, "Termos e lemas", "Extrai palavras de conteúdo e formas-base, agrupando variações morfológicas.", TEAL, PALE_TEAL),
        (0.75, 4.0, "Entidades", "Registra entidades identificadas pelo modelo de português; nomes de produtos podem exigir revisão.", GOLD, PALE_GOLD),
        (6.85, 4.0, "Relações sintáticas", "Produz pistas aproximadas de sujeito, verbo e complemento — não fatos garantidos.", CORAL, PALE_CORAL),
    ]
    for x, y, title, body, accent, fill in cards:
        add_card(slide, x, y, 5.7, 1.7, title, body, accent=accent, fill=fill, body_size=15)
    add_text(slide, "Essas colunas ficam no CSV da Etapa 2 em formato JSON.",
             1.0, 6.1, 11.3, 0.4, size=16, color=NAVY, bold=True, align=PP_ALIGN.CENTER)

    # 5. Embeddings
    slide = new_slide(prs, "Novidade 2 · embeddings e similaridade", 5)
    add_text(slide, "Texto", 0.9, 2.0, 1.5, 0.4, size=17, color=NAVY, bold=True, align=PP_ALIGN.CENTER)
    add_box(slide, 0.75, 2.5, 2.6, 1.1, PALE_BLUE)
    add_text(slide, "“A IDE fica lenta\ncom muitos plugins”", 0.9, 2.73, 2.3, 0.6, size=15, color=INK, align=PP_ALIGN.CENTER)
    add_text(slide, "→", 3.45, 2.82, 0.55, 0.4, size=24, color=MUTED, bold=True, align=PP_ALIGN.CENTER)
    add_box(slide, 4.1, 2.5, 3.5, 1.1, PALE_TEAL)
    add_text(slide, "[0.12, −0.08, …, 0.31]\nvetor semântico", 4.25, 2.72, 3.2, 0.65, size=16, color=NAVY, bold=True, align=PP_ALIGN.CENTER)
    add_text(slide, "→", 7.72, 2.82, 0.55, 0.4, size=24, color=MUTED, bold=True, align=PP_ALIGN.CENTER)
    add_box(slide, 8.35, 2.5, 4.0, 1.1, PALE_GOLD)
    add_text(slide, "buscar comentários\ncom significado próximo", 8.52, 2.72, 3.65, 0.65, size=16, color=NAVY, bold=True, align=PP_ALIGN.CENTER)
    add_text(slide, "Execução registrada", 0.9, 4.35, 2.6, 0.35, size=17, color=NAVY, bold=True)
    add_text(slide, "1.958 comentários × 384 dimensões", 0.9, 4.78, 6.0, 0.55, size=25, color=TEAL, bold=True)
    add_text(slide, "Os vetores são guardados no arquivo NPZ separado do CSV. A similaridade cosseno ordena textos por proximidade semântica aproximada.",
             0.9, 5.6, 11.5, 0.85, size=16, color=INK)
    add_text(slide, "Ilustração conceitual: os números do vetor acima não são dados reais do comentário.",
             0.9, 6.58, 11.5, 0.25, size=10, color=MUTED)

    # 6. Transformer
    slide = new_slide(prs, "Novidade 3 · comparar classificadores", 6)
    add_card(slide, 0.8, 2.0, 5.55, 2.8, "Classificador principal",
             "Saída da Etapa 1\n\nSentimento, probabilidades e score\n\nContinua preservado no resultado.", accent=BLUE, fill=PALE_BLUE, body_size=17)
    add_card(slide, 6.95, 2.0, 5.55, 2.8, "Transformer adicional",
             "Previsão independente\n\nColunas com sufixo `_transformer`\n\nPode concordar ou divergir do modelo principal.", accent=CORAL, fill=PALE_CORAL, body_size=17)
    add_text(slide, "A comparação revela concordância e divergência — não determina sozinha qual modelo está correto.",
             1.0, 5.45, 11.2, 0.8, size=19, color=NAVY, bold=True, align=PP_ALIGN.CENTER)
    add_text(slide, "Para medir acurácia, é necessária uma amostra avaliada e rotulada manualmente.",
             1.0, 6.28, 11.2, 0.35, size=14, color=MUTED, align=PP_ALIGN.CENTER)

    # 7. Painel
    slide = new_slide(prs, "Nova visualização · app_etapa2.py", 7)
    items = [
        ("Mapa semântico", "Projeção PCA 2D; cada ponto representa um comentário e a cor indica sentimento.", TEAL),
        ("Conteúdo", "Lemas frequentes, entidades reconhecidas e comentários para inspeção.", BLUE),
        ("Comparação", "Matriz de concordância entre classificador principal e Transformer.", CORAL),
        ("Busca semântica", "Consulta uma ideia e recupera comentários mais semelhantes pelo embedding.", GOLD),
    ]
    for i, (title, body, accent) in enumerate(items):
        y = 1.9 + i * 1.12
        add_box(slide, 0.9, y, 11.45, 0.88, WHITE)
        add_box(slide, 0.9, y, 0.12, 0.88, accent, MSO_SHAPE.RECTANGLE)
        add_text(slide, title, 1.2, y + 0.12, 2.55, 0.36, size=17, color=NAVY, bold=True)
        add_text(slide, body, 3.75, y + 0.12, 8.2, 0.55, size=15, color=INK)
    add_text(slide, "PCA é exploratória: os eixos não são tópicos nomeados e proximidade não prova equivalência.",
             1.0, 6.55, 11.3, 0.3, size=12, color=MUTED, align=PP_ALIGN.CENTER)

    # 8. Demo
    slide = new_slide(prs, "Demonstração ao vivo", 8)
    add_text(slide, "1", 0.95, 2.0, 0.5, 0.5, size=27, color=TEAL, bold=True)
    add_text(slide, "Abra `app_etapa2.py` no Streamlit", 1.6, 2.03, 10.2, 0.45, size=20, color=NAVY, bold=True)
    add_text(slide, "2", 0.95, 2.95, 0.5, 0.5, size=27, color=TEAL, bold=True)
    add_text(slide, "Mostre o mapa e filtre por sentimento", 1.6, 2.98, 10.2, 0.45, size=20, color=NAVY, bold=True)
    add_text(slide, "3", 0.95, 3.9, 0.5, 0.5, size=27, color=TEAL, bold=True)
    add_text(slide, "Explore lemas, entidades e exemplos de comentários", 1.6, 3.93, 10.2, 0.45, size=20, color=NAVY, bold=True)
    add_text(slide, "4", 0.95, 4.85, 0.5, 0.5, size=27, color=TEAL, bold=True)
    add_text(slide, "Digite uma consulta na busca semântica e leia os resultados", 1.6, 4.88, 10.4, 0.6, size=20, color=NAVY, bold=True)
    add_box(slide, 1.0, 6.0, 11.3, 0.65, NAVY)
    add_text(slide, "streamlit run app_etapa2.py", 1.2, 6.12, 10.9, 0.35, size=18, color=WHITE, bold=True, align=PP_ALIGN.CENTER)

    # 9. Fechamento
    slide = new_slide(prs, "Resultado, impacto e próximos passos", 9)
    add_card(slide, 0.8, 1.9, 3.75, 2.7, "Resultado", "CSV semântico + arquivo NPZ de embeddings + painel interativo.", accent=BLUE, fill=PALE_BLUE, body_size=17)
    add_card(slide, 4.8, 1.9, 3.75, 2.7, "Impacto", "Passamos de contagens e polaridade para explorar conteúdo e similaridade entre comentários.", accent=TEAL, fill=PALE_TEAL, body_size=17)
    add_card(slide, 8.8, 1.9, 3.75, 2.7, "Próximo passo", "Validar previsões com rótulos humanos e, futuramente, implementar agrupamento/rotulagem de tópicos.", accent=GOLD, fill=PALE_GOLD, body_size=17)
    add_text(slide, "A Etapa 2 amplia as perguntas possíveis; seus resultados continuam sujeitos à validação e às limitações dos modelos.",
             1.0, 5.35, 11.2, 0.85, size=19, color=NAVY, bold=True, align=PP_ALIGN.CENTER)
    add_text(slide, "Obrigado(a)!", 1.0, 6.25, 11.2, 0.45, size=24, color=TEAL, bold=True, align=PP_ALIGN.CENTER)

    return prs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--saida", type=Path, default=Path("apresentacao_etapa2.pptx"),
                        help="Caminho do arquivo .pptx a gerar (padrão: apresentacao_etapa2.pptx na raiz)")
    args = parser.parse_args()
    args.saida.parent.mkdir(parents=True, exist_ok=True)
    build_deck().save(args.saida)
    print(f"Apresentação criada: {args.saida.resolve()}")
    print("Abra o arquivo no PowerPoint ou LibreOffice Impress. Para PDF, use Arquivo > Exportar/Salvar como PDF.")


if __name__ == "__main__":
    main()
