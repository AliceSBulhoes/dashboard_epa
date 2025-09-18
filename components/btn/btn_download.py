import streamlit as st
import io
import zipfile
import pandas as pd
import plotly.graph_objects as go

DICT_TYPE = {
    "html": "text/html",
    "excel": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "png": "application/zip",
}

def convert_fig_to_html(fig) -> str:
    """Converte um gráfico Plotly em string HTML."""
    return fig.to_html(full_html=False)

def fig_to_png_bytes(fig):
    """Tenta converter um gráfico Plotly em bytes PNG. Retorna None se Kaleido não estiver disponível."""
    try:
        buf = io.BytesIO()
        fig.write_image(buf, format="png")
        buf.seek(0)
        return buf
    except Exception as e:
        st.warning(f"PNG não disponível: {e}")
        return None

def btn(type: str, data, file_name: str, name_btn: str = "Baixar Gráficos"):
    """Cria um botão de download."""
    st.download_button(
        name_btn,
        data=data,
        file_name=file_name,
        mime=DICT_TYPE[type],
        use_container_width=True,
        help="Caso tenha dado zoom no gráfico, tente baixar pela própria interface do gráfico."
    )

def btn_download_multiple(figs, file_name_html="plots.html"):
    """Cria botões de download para múltiplos gráficos Plotly."""
    col1, col2 = st.columns(2, vertical_alignment="center")

    # HTML
    with col1:
        html = "".join([convert_fig_to_html(fig) for fig in figs])
        btn("html", html, file_name=file_name_html, name_btn="Baixar Gráficos (HTML)")

    # PNG - ZIP (só se puder)
    zip_buffer = io.BytesIO()
    has_png = False
    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zf:
        for i, fig in enumerate(figs):
            png_bytes = fig_to_png_bytes(fig)
            if png_bytes:
                zf.writestr(f"grafico_{i+1}.png", png_bytes.getvalue())
                has_png = True

    if has_png:
        zip_buffer.seek(0)
        with col2:
            btn("png", zip_buffer, file_name="graficos.zip", name_btn="Baixar Gráficos (PNG)")
    else:
        with col2:
            st.info("Download de PNG não disponível no Streamlit Cloud. Use HTML ou utilize a função de download presente na interface do gráfico.")

def btn_download_excel(df, file_name, label="Baixar Dados em Excel"):
    """Cria um botão de download para um DataFrame em formato Excel."""
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df.to_excel(
            writer,
            sheet_name=file_name.replace('.xlsx','').replace('dados_','').replace('_',' ').title().replace(' ','_'),
            index=False
        )
    st.download_button(
        label=label,
        data=buffer.getvalue(),
        file_name=file_name,
        mime="application/vnd.ms-excel",
        use_container_width=True
    )
