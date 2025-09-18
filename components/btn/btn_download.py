import streamlit as st
import io
import zipfile
import pandas as pd

DICT_TYPE = {
    "html": "text/html",
    "excel": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "png": "application/zip",
}

def convert_fig_to_html(fig) -> str:
    """Converte um gráfico Plotly em string HTML."""
    return fig.to_html(full_html=False)

def fig_to_png_bytes(fig):
    """Converte um gráfico Plotly em bytes PNG."""
    buf = io.BytesIO()
    fig.write_image(buf, format="png")
    buf.seek(0)
    return buf

# def figs_to_excel_bytes(figs):
#     """Converte gráficos Plotly em um arquivo Excel contendo os dados de cada trace."""
#     output = io.BytesIO()
#     with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
#         for i, fig in enumerate(figs):
#             df_total = pd.DataFrame()
#             for j, trace in enumerate(fig.data):
#                 # Pega x e y
#                 df_trace = pd.DataFrame()
#                 if hasattr(trace, 'x') and hasattr(trace, 'y'):
#                     df_trace[f"X_Trace{j+1}"] = trace.x
#                     df_trace[f"Y_Trace{j+1}"] = trace.y
#                 # Concatena os dados ao dataframe do gráfico
#                 df_total = pd.concat([df_total, df_trace], axis=1)
#             # Salva uma aba por gráfico
#             df_total.to_excel(writer, sheet_name=f"Grafico_{i+1}", index=False)
#     output.seek(0)
#     return output

def btn(type: str, data, file_name: str, name_btn: str = "Baixar Gráficos"):
    """Cria um botão de download."""
    st.download_button(name_btn, data=data, file_name=file_name, mime=DICT_TYPE[type], use_container_width=True, help="Caso tenha dado zoom no gráfico, tente baixar pela própria interface do gráfico.")

def btn_download_multiple(figs, file_name_html="plots.html"):
    """Cria botões de download para múltiplos gráficos Plotly."""

    col1, col2 = st.columns(2, vertical_alignment="center")

    # HTML
    with col1:
        html = "".join([convert_fig_to_html(fig) for fig in figs])
        btn("html", html, file_name=file_name_html, name_btn="Baixar Gráficos (HTML)")

    # Excel - agora com os dados dos gráficos
    # excel_bytes = figs_to_excel_bytes(figs)
    # btn("excel", excel_bytes, file_name="dados.xlsx", name_btn="Baixar Dados (Excel)")

    # PNG - ZIP
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zf:
        for i, fig in enumerate(figs):
            png_bytes = fig_to_png_bytes(fig)
            zf.writestr(f"grafico_{i+1}.png", png_bytes.getvalue())
    zip_buffer.seek(0)
    with col2:
        btn("png", zip_buffer, file_name="graficos.zip", name_btn="Baixar Gráficos (PNG)")
