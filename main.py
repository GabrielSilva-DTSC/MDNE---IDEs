import streamlit as st


paginas = [
    st.Page(
        "app.py",
        title="Etapa 1 — Análise de sentimentos",
        icon=":material/analytics:",
        default=True,
    ),
    st.Page(
        "app_etapa2.py",
        title="Etapa 2 — Análise semântica",
        icon=":material/hub:",
        url_path="Etapa_2",
    ),
]

pagina = st.navigation(paginas, position="sidebar")
pagina.run()
