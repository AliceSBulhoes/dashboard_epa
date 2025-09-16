import streamlit as st

def navbar():
    """
    Função que cria uma barra de navegação simples usando Streamlit.
    """

    st.logo("https://grupoepa.net.br/wp-content/uploads/2025/04/e50d93c1-0cce-46d4-bb75-1985e4968e18__1_-removebg-preview.png")

    pages = [
        st.Page(page="./pages/dashboard.py", icon=":material/dashboard:", title="Dashboard"),
    ]

    pg = st.navigation(pages=pages, expanded=True)
    pg.run()


def config_page():
    st.set_page_config(
        page_title="EPA | Dashboard",
        page_icon=":bar_chart:",
        layout="wide",
        initial_sidebar_state="expanded",
    )


def css():
    """Função que aplica estilos CSS personalizados."""
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Mulish:wght@200;400;700&display=swap');

        html, body, [class*="css"]  {
            font-family: 'Mulish', sans-serif !important;
        }
        </style>
    """, unsafe_allow_html=True)


def main():
    css()
    config_page()
    navbar()


if __name__ == "__main__":
    main()