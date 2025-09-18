import streamlit as st
import pandas as pd
import io
import os
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import plotly.express as px
from utils import tratando_df, fillna_columns, add_accumulated_column, filter_by_date
from components.btn import btn_download_multiple

# Helpers para limpar filtros via callbacks
def _clear_state_key(key: str):
    st.session_state[key] = []

# Inicializa os DataFrames como None para evitar NameError
df_fl = None
df_volume_produto = None
df_volume = None

# Variáveis Globais
DATA_DIR = os.path.join(os.getcwd(), 'data')

if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)


def card(kpi_titulo: str, kpi_valor: int, emoji: str = "", color: str = "#5A2781"):
    st.markdown(
        f"""
        <div style="
            background: linear-gradient(135deg, {color}22, {color}11);
            border: 1px solid {color}33;
            border-radius: 16px; padding: 18px 18px;
            ">
            <div style="font-size:14px;color:#555;margin-bottom:6px">{emoji} {kpi_titulo}</div>
            <div style="font-size:30px;font-weight:700;color:{color}">{kpi_valor}</div>
        </div>
        """,
        unsafe_allow_html=True)

# Interface do Dashboard
st.write("# Dashboard")

# --------- Upload do Arquivo ---------
st.sidebar.write("## Upload do Arquivo")
# Download de um arquivo de exemplo
upload_file = st.sidebar.file_uploader("Upload do Arquivo", type=["csv", "xlsx"], accept_multiple_files=True, key="file_uploader", help="Faça upload de arquivos CSV ou Excel.")

# st.write("*OBS: O arquivo pegará apenas a primeira página, se tiver múltiplas páginas.*")

if upload_file is not None:
    for uploaded_file in upload_file:
        # DF Vendas
        df_volume = pd.read_excel(uploaded_file, sheet_name="Volume Bombeado", engine='openpyxl')
        df_volume = tratando_df(df_volume)

        # DF Volume Produto
        df_volume_produto = pd.read_excel(uploaded_file, sheet_name="Volume Produto", engine='openpyxl')
        df_volume_produto = tratando_df(df_volume_produto)
        
        # DF FL
        df_fl = pd.read_excel(uploaded_file, sheet_name="FL", engine='openpyxl')
        df_fl = tratando_df(df_fl)

        # DF Hidrogeológicos
        df_hidrometros = pd.read_excel(uploaded_file, sheet_name="Hidrômetros", engine='openpyxl')
        df_hidrometros = tratando_df(df_hidrometros)

        # DF Coleta
        # df_coleta = pd.read_excel(uploaded_file, sheet_name="Coleta", engine='openpyxl')
        # df_coleta = tratando_df(df_coleta)
        

        # Visualizar DataFrame
        # st.write(df_fl)
        # st.write(df_volume_produto)
        # st.write(df_volume)


    # Visualizar Dev
    with st.expander("Visualizar DataFrame"):
        st.write("### DataFrame FL Informações")
        if df_fl is not None:
            st.write(df_fl.columns)
            st.write(df_fl)
        else:
            st.write("Nenhum dado carregado para FL.")

        st.write("### DataFrame Volume Produto Informações")
        if df_volume_produto is not None:
            st.write(df_volume_produto.columns)
            st.write(df_volume_produto)
        else:
            st.write("Nenhum dado carregado para Volume Produto.")

        st.write("### DataFrame Volume Bombeado Informações")
        if df_volume is not None:
            st.write(df_volume.columns)
            st.write(df_volume)
        else:
            st.write("Nenhum dado carregado para Volume Bombeado.")


if df_fl is not None and df_volume_produto is not None and df_volume is not None:
    # Processar os dados conforme necessário
    tipo_grafico = st.selectbox(
        "Selecione o Tipo de Gráfico",
        options=["FL", "Volume Produto", "Volume Bombeado"],
        index=0
    )
    # ---------------------- Filtros Sidebar -----------------------
    st.sidebar.header("Filtros")

    # -------- Categorias --------
    st.sidebar.write("### Categorias")
    categorias = ['Operacional', 'Hidrogeológicos', 'Hidrogeoquímicos', 'Parâmetros in Situ']
    
    # Initialize session state for categories
    if "filtro_categorias" not in st.session_state:
        st.session_state["filtro_categorias"] = [categorias[0]]
    
    default_categorias = [cat for cat in st.session_state["filtro_categorias"] if cat in categorias] if "filtro_categorias" in st.session_state else [categorias[0]]
    if not default_categorias:
        default_categorias = [categorias[0]]
    categoria_selecionada = st.sidebar.multiselect(
        "Selecione a Categoria",
        options=categorias,
        default=default_categorias,
        key="filtro_categorias"
    )
    if not categoria_selecionada:
        st.sidebar.warning("Por favor, selecione pelo menos uma categoria.")
        st.stop()
    st.sidebar.button("Limpar", key="btn_limpar_categorias", on_click=_clear_state_key, kwargs={"key": "filtro_categorias"},width='stretch')

    # ----- Data Filter -----
    st.sidebar.write("### Faixa de Data")
    data_min = pd.to_datetime(df_volume['Data'].min())
    data_max = pd.to_datetime(df_volume['Data'].max())
    data_inicio = st.sidebar.date_input("Data Inicial", value=data_min, min_value=data_min, max_value=data_max)
    data_fim = st.sidebar.date_input("Data Final", value=data_max, min_value=data_min, max_value=data_max)



    # Filtrar DataFrame pelo intervalo de datas selecionado
    df_volume = filter_by_date(df_volume, 'Data', data_inicio, data_fim)
    df_fl = filter_by_date(df_fl, 'Data', data_inicio, data_fim)
    df_volume_produto = filter_by_date(df_volume_produto, 'Data', data_inicio, data_fim)


    if tipo_grafico == "FL":
        st.write("## Gráficos de Fase Livre")

        # Preencher NaN
        df_fl = fillna_columns(df_fl, ['NA (m)', 'NO (m)', 'Esp. (m)'], 0)

        # Filtros de Poços
        filtroCol1, filtroCol2 = st.columns(2)
        pocos = df_fl['Poço'].unique().tolist()

        if "filtro_pocos" not in st.session_state:
            st.session_state["filtro_pocos"] = [pocos[0]]

        pocos_col1, pocos_col2 = filtroCol1.columns([3,1], vertical_alignment="center")
        poço_selecionado = pocos_col1.multiselect(
            "Selecione os Poços",
            options=pocos,
            default=st.session_state["filtro_pocos"] if st.session_state["filtro_pocos"] else [pocos[0]],
            key="filtro_pocos"
        )
        pocos_col2.button("Limpar", key="btn_limpar_pocos", on_click=_clear_state_key, kwargs={"key":"filtro_pocos"})

        if poço_selecionado:
            df_fl = df_fl[df_fl['Poço'].isin(poço_selecionado)]
        else:
            st.warning("Por favor, selecione pelo menos um poço.")
            st.stop()

        # Filtros de Tipo
        tipo = ['NA (m)','NO (m)','Esp. (m)']
        if "filtro_tipos" not in st.session_state:
            st.session_state["filtro_tipos"] = [tipo[0]]

        tipos_col1, tipos_col2 = filtroCol2.columns([3,1], vertical_alignment="center")
        tipo_selecionado = tipos_col1.multiselect(
            "Selecione o Tipo",
            options=tipo,
            default=st.session_state["filtro_tipos"] if st.session_state["filtro_tipos"] else [tipo[0]],
            key="filtro_tipos"
        )
        if not tipo_selecionado:
            st.warning("Por favor, selecione pelo menos um tipo.")
            st.stop()
        tipos_col2.button("Limpar", key="btn_limpar_tipos", on_click=_clear_state_key, kwargs={"key":"filtro_tipos"})

        # Criar figuras
        figuras = []

        if 'NA (m)' in tipo_selecionado:
            fig_na = px.bar(
                df_fl,
                x='Data',
                y='NA (m)',
                color='Poço',
                title='Nível de Água (NA)',
                color_discrete_sequence=px.colors.qualitative.Dark24,
                barmode='group'
            )
            fig_na.update_layout(dragmode='zoom', xaxis_tickangle=-45, legend_title_text='Poços')
            figuras.append(fig_na)

        if 'NO (m)' in tipo_selecionado:
            fig_no = px.bar(
                df_fl,
                x='Data',
                y='NO (m)',
                color='Poço',
                title='Nível de Óleo (NO)',
                color_discrete_sequence=px.colors.qualitative.Dark24,
                barmode='group'
            )
            fig_no.update_layout(dragmode='zoom', xaxis_tickangle=-45, legend_title_text='Poços')
            figuras.append(fig_no)

        if 'Esp. (m)' in tipo_selecionado:
            fig_esp = px.bar(
                df_fl,
                x='Data',
                y='Esp. (m)',
                color='Poço',
                title='Espessura de Óleo',
                color_discrete_sequence=px.colors.qualitative.Dark24,
                barmode='group'
            )
            fig_esp.update_layout(dragmode='zoom', xaxis_tickangle=-45, legend_title_text='Poços')
            figuras.append(fig_esp)

        # Exibir gráficos
        n_figs = len(figuras)
        if n_figs == 3:
            col1, col2 = st.columns(2)
            col1.plotly_chart(fig_na, use_container_width=True, key="fl_na_col1")
            col2.plotly_chart(fig_no, use_container_width=True, key="fl_no_col2")
            st.plotly_chart(fig_esp, use_container_width=True, key="fl_esp_col3")
        elif n_figs == 2:
            col1, col2 = st.columns(2)
            col1.plotly_chart(figuras[0], use_container_width=True, key="fl_fig1")
            col2.plotly_chart(figuras[1], use_container_width=True, key="fl_fig2")
        elif n_figs == 1:
            st.plotly_chart(figuras[0], use_container_width=True, key="fl_single")

        # Botão de download (dados completos)
        if figuras:
            btn_download_multiple(figuras)



    elif tipo_grafico == "Volume Produto":
        st.write("## Gráficos de Volume Produto")

        # -------- Valor Acumulado --------
        df_volume_produto = fillna_columns(df_volume_produto, ['Volume Removido SAO (L)', 'Volume Removido Bailer (L)'], 0)
        df_volume_produto = add_accumulated_column(df_volume_produto, ['Volume Removido SAO (L)', 'Volume Removido Bailer (L)'], 'Volume Acumulado (L)')

        # ---------------------- Cards -----------------------
        volume_acumulado_atual = df_volume_produto.sort_values(by='Data', ascending=False).iloc[0]['Volume Acumulado (L)']
        volume_produto_atual_removido_sao = df_volume_produto.sort_values(by='Data', ascending=False).iloc[0]['Volume Removido SAO (L)']
        volume_acumulado_atual_removido_bailer = df_volume_produto.sort_values(by='Data', ascending=False).iloc[0]['Volume Removido Bailer (L)']
        dias_sem_registro = (pd.to_datetime("today") - pd.to_datetime(df_volume_produto['Data'].max())).days
        # KPIs
        k1, k2, k3, k4 = st.columns(4)
        with k1: card("Volume Removido SAO Atual", 0 if pd.isna(volume_produto_atual_removido_sao) else f"{volume_produto_atual_removido_sao:.2f}", "💧", color="#0571ED")
        with k2: card("Volume Removido Bailer Atual", 0 if pd.isna(volume_acumulado_atual_removido_bailer) else f"{volume_acumulado_atual_removido_bailer:.2f}", "📦", color="#DD7D23")
        with k3: card("Volume Acumulado Atual ", 0 if pd.isna(volume_acumulado_atual) else f"{volume_acumulado_atual:.2f}", "✅", color="#2EE43D")
        with k4: card("Dias Sem Registro", dias_sem_registro, "🛑", color="#D7263D")

        # ---------------------- Gráficos -----------------------
        # Initialize session state for produto columns
        if "filtro_colunas_produto" not in st.session_state:
            st.session_state["filtro_colunas_produto"] = []
        
        col1, col2 = st.columns([3, 1],vertical_alignment="center")
        colunas_escolher = col1.multiselect("Selecione as colunas para o gráfico", options=['Volume Removido SAO (L)', 'Volume Removido Bailer (L)', 'Volume Acumulado (L)'], default=st.session_state["filtro_colunas_produto"] if st.session_state["filtro_colunas_produto"] else ['Volume Removido SAO (L)'], key="filtro_colunas_produto")
        if not colunas_escolher:
            st.warning("Por favor, selecione pelo menos uma coluna.")
            st.stop()
        col2.button("Limpar", key="btn_limpar_colunas_prod", on_click=_clear_state_key, kwargs={"key": "filtro_colunas_produto"})

        figuras = []

        if colunas_escolher:
            if 'Volume Acumulado (L)' in colunas_escolher:
                fig_vol_ac = px.line(df_volume_produto, x='Data', y='Volume Acumulado (L)' ,title='Volume Acumulado ao Longo do Tempo', color_discrete_sequence=['#c44d15'])
                figuras.append(fig_vol_ac)

            if 'Volume Removido SAO (L)' in colunas_escolher:
                fig_vol_sao = px.bar(
                    df_volume_produto,
                    x='Data',
                    y='Volume Removido SAO (L)',
                    title='Volume Removido SAO ao Longo do Tempo',
                    color_discrete_sequence=['#156082']
                )
                figuras.append(fig_vol_sao)

            if 'Volume Removido Bailer (L)' in colunas_escolher:
                fig_vol_bailer = px.bar(
                    df_volume_produto,
                    x='Data',
                    y='Volume Removido Bailer (L)',
                    title='Volume Removido Bailer ao Longo do Tempo',
                    color_discrete_sequence=['#e17b7b']
                )
                figuras.append(fig_vol_bailer)
            
            # Exibir gráficos
            n_figs = len(figuras)
            if n_figs == 3:
                col1, col2, col3 = st.columns(3)
                col1.plotly_chart(fig_vol_ac, use_container_width=True, key="vol_acumulado")
                col2.plotly_chart(fig_vol_sao, use_container_width=True, key="vol_sao")
                col3.plotly_chart(fig_vol_bailer, use_container_width=True, key="vol_bailer")
                
            elif len(colunas_escolher) == 2:
                col1, col2 = st.columns(2)
                if 'Volume Acumulado (L)' in colunas_escolher and 'Volume Removido SAO (L)' in colunas_escolher:
                    col1.plotly_chart(fig_vol_ac, use_container_width=True, key="vol_acumulado")
                    col2.plotly_chart(fig_vol_sao, use_container_width=True, key="vol_sao")
                elif 'Volume Acumulado (L)' in colunas_escolher and 'Volume Removido Bailer (L)' in colunas_escolher:
                    col1.plotly_chart(fig_vol_ac, use_container_width=True, key="vol_acumulado")
                    col2.plotly_chart(fig_vol_bailer, use_container_width=True, key="vol_bailer")
                else:
                    col1.plotly_chart(fig_vol_sao, use_container_width=True, key="vol_sao")
                    col2.plotly_chart(fig_vol_bailer, use_container_width=True, key="vol_bailer")
            else:
                if 'Volume Acumulado (L)' in colunas_escolher:
                    st.plotly_chart(fig_vol_ac, use_container_width=True, key="vol_acumulado")
                elif 'Volume Removido SAO (L)' in colunas_escolher:
                    st.plotly_chart(fig_vol_sao, use_container_width=True, key="vol_sao")
                else:
                    st.plotly_chart(fig_vol_bailer, use_container_width=True, key="vol_bailer")

            if figuras:
                btn_download_multiple(figuras)
                


    elif tipo_grafico == "Volume Bombeado":
        st.write("## Gráficos de Volume Bombeado")

        # -------- Valor Acumulado --------
        df_volume = fillna_columns(df_volume, ['Volume Bombeado (L)'], 0)
        df_volume = add_accumulated_column(df_volume, ['Volume Bombeado (L)'], 'Volume Acumulado (L)')
        
        # ---------------------- Cards -----------------------
        volume_bombeado_atual = df_volume.sort_values(by='Data', ascending=False).iloc[0]['Volume Bombeado (L)']
        volume_acumulado_atual = df_volume.sort_values(by='Data', ascending=False).iloc[0]['Volume Acumulado (L)']
        dias_sem_registro = (pd.to_datetime("today") - pd.to_datetime(df_volume['Data'].max())).days

        # KPIs
        k1, k2, k3, k4 = st.columns(4)
        with k1: card("Volume Bombeado Atual", 0 if pd.isna(volume_bombeado_atual) else f"{volume_bombeado_atual:.2f}", "💧", color="#0571ED")
        with k2: card("Nº de Poços em Operação ", 5, "✅", color="#2EE43D")
        with k3: card("Volume Acumulado Atual", 0 if pd.isna(volume_acumulado_atual) else f"{volume_acumulado_atual:.2f}", "📦", color="#DD7D23")
        with k4: card("Dias Sem Registro", dias_sem_registro, "🛑", color="#D7263D")

        # ---------------------- Gráficos -----------------------
        # Initialize session state for bombeado columns
        if "filtro_colunas_bombeado" not in st.session_state:
            st.session_state["filtro_colunas_bombeado"] = []
        
        col1, col2 = st.columns([3, 1],vertical_alignment="center")
        colunas_escolher = col1.multiselect("Selecione as colunas para o gráfico", options=['Volume Acumulado (L)', 'Volume Bombeado (L)'], default=st.session_state["filtro_colunas_bombeado"] if st.session_state["filtro_colunas_bombeado"] else ['Volume Acumulado (L)'], key="filtro_colunas_bombeado")
        if not colunas_escolher:
            st.warning("Por favor, selecione pelo menos uma coluna.")
            st.stop()
        col2.button("Limpar", key="btn_limpar_colunas_bomb", on_click=_clear_state_key, kwargs={"key": "filtro_colunas_bombeado"})
        
        figuras = []

        if colunas_escolher:
            if 'Volume Acumulado (L)' in colunas_escolher:
                fig_vol_ac = px.line(df_volume, x='Data', y='Volume Acumulado (L)' ,title='Volume Acumulado ao Longo do Tempo', color_discrete_sequence=['#c44d15'])
                figuras.append(fig_vol_ac)

            if 'Volume Bombeado (L)' in colunas_escolher:
                fig_vol_bom = px.bar(
                    df_volume,
                    x='Data',
                    y='Volume Bombeado (L)',
                    title='Volume Bombeado ao Longo do Tempo',
                    color_discrete_sequence=['#156082']
                )
                figuras.append(fig_vol_bom)

            n_figs = len(figuras)
            if n_figs == 2:
                col1, col2 = st.columns(2)
                col1.plotly_chart(fig_vol_ac, use_container_width=True, key="vol_acumulado_bomb")
                col2.plotly_chart(fig_vol_bom, use_container_width=True, key="vol_bombeado")
            else:
                if 'Volume Acumulado (L)' in colunas_escolher:
                    st.plotly_chart(fig_vol_ac, use_container_width=True, key="vol_acumulado_bomb")
                else:
                    st.plotly_chart(fig_vol_bom, use_container_width=True, key="vol_bombeado")

            if figuras:
                btn_download_multiple(figuras)

        else:
            st.warning("Por favor, selecione pelo menos uma coluna para o gráfico.")
   