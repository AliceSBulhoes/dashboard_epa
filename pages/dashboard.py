import streamlit as st
import pandas as pd
import io
import os
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import plotly.express as px
from utils import tratando_df

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

        # Visualizar DataFrame
        # st.write(df_fl)
        # st.write(df_volume_produto)
        # st.write(df_volume)


    # Visualizar Dev
    with st.expander("Visualizar DataFrame"):
        st.write("### DataFrame FL Informações")
        st.write(df_fl.columns)
        st.write(df_fl)
        st.write("### DataFrame Volume Produto Informações")
        st.write(df_volume_produto.columns)
        st.write(df_volume_produto)
        st.write("### DataFrame Volume Bombeado Informações")
        st.write(df_volume.columns)
        st.write(df_volume)


if df_fl is not None and df_volume_produto is not None and df_volume is not None:
    # Processar os dados conforme necessário
    tipo_grafico = st.selectbox(
        "Selecione o Tipo de Gráfico",
        options=["FL", "Volume Produto", "Volume Bombeado"],
    )
    # ---------------------- Filtros Sidebar -----------------------
    st.sidebar.header("Filtros")
    # ----- Data Filter -----
    data_min = pd.to_datetime(df_volume['Data'].min())
    data_max = pd.to_datetime(df_volume['Data'].max())
    data_inicio = st.sidebar.date_input("Data Inicial", value=data_min, min_value=data_min, max_value=data_max)
    data_fim = st.sidebar.date_input("Data Final", value=data_max, min_value=data_min, max_value=data_max)

    # Filtrar DataFrame pelo intervalo de datas selecionado
    df_volume = df_volume[(pd.to_datetime(df_volume['Data']) >= pd.to_datetime(data_inicio)) & (pd.to_datetime(df_volume['Data']) <= pd.to_datetime(data_fim))]
    df_fl = df_fl[(pd.to_datetime(df_fl['Data']) >= pd.to_datetime(data_inicio)) & (pd.to_datetime(df_fl['Data']) <= pd.to_datetime(data_fim))]
    df_volume_produto = df_volume_produto[(pd.to_datetime(df_volume_produto['Data']) >= pd.to_datetime(data_inicio)) & (pd.to_datetime(df_volume_produto['Data']) <= pd.to_datetime(data_fim))]


    if tipo_grafico == "FL":
        st.info("Em construção...")

    elif tipo_grafico == "Volume Produto":
        st.write("## Gráficos de Volume Produto")

        # ---------------------- Cards -----------------------
        volume_bombeado_atual = df_volume.sort_values(by='Data', ascending=False).iloc[0]['Volume Bombeado (L)']
        volume_acumulado_atual = df_volume.sort_values(by='Data', ascending=False).iloc[0]['Volume Acumulado (L)']
        dias_sem_registro = (pd.to_datetime("today") - pd.to_datetime(df_volume['Data'].max())).days

        # KPIs
        k1, k2, k3, k4 = st.columns(4)
        with k1: card("Volume Produto Atual", 0 if pd.isna(volume_bombeado_atual) else f"{volume_bombeado_atual:.2f}", "💧", color="#0571ED")
        with k2: card("Nº de Poços em Operação ", 5, "✅", color="#2EE43D")
        with k3: card("Volume Acumulado Atual", 0 if pd.isna(volume_acumulado_atual) else f"{volume_acumulado_atual:.2f}", "📦", color="#DD7D23")
        with k4: card("Dias Sem Registro", dias_sem_registro, "🛑", color="#D7263D")

        # ---------------------- Gráficos -----------------------
        colunas_escolher = st.multiselect("Selecione as colunas para o gráfico", options=['Volume Acumulado (L)', 'Volume Bombeado (L)'])
        if colunas_escolher:
            if 'Volume Acumulado (L)' in colunas_escolher:
                fig_vol_ac = px.line(df_volume, x='Data', y='Volume Acumulado (L)' ,title='Volume Acumulado ao Longo do Tempo', color_discrete_sequence=['#c44d15'] # personalize as cores aqui
                )

            if 'Volume Bombeado (L)' in colunas_escolher:
                fig_vol_bom = px.bar(
                    df_volume,
                    x='Data',
                    y='Volume Bombeado (L)',
                    title='Volume Bombeado ao Longo do Tempo',
                    color_discrete_sequence=['#156082'] # personalize as cores aqui
                )
            
            if len(colunas_escolher) == 2:
                col1, col2 = st.columns(2)
                col1.plotly_chart(fig_vol_ac, use_container_width=True)
                col2.plotly_chart(fig_vol_bom, use_container_width=True)
            else:
                st.plotly_chart(fig_vol_ac if 'Volume Acumulado (L)' in colunas_escolher else fig_vol_bom, use_container_width=True)

        else:
            st.warning("Por favor, selecione pelo menos uma coluna para o gráfico.")


    elif tipo_grafico == "Volume Bombeado":
        st.write("## Gráficos de Volume Bombeado")

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
        colunas_escolher = st.multiselect("Selecione as colunas para o gráfico", options=['Volume Acumulado (L)', 'Volume Bombeado (L)'])
        if colunas_escolher:
            if 'Volume Acumulado (L)' in colunas_escolher:
                fig_vol_ac = px.line(df_volume, x='Data', y='Volume Acumulado (L)' ,title='Volume Acumulado ao Longo do Tempo', color_discrete_sequence=['#c44d15'] # personalize as cores aqui
                )

            if 'Volume Bombeado (L)' in colunas_escolher:
                fig_vol_bom = px.bar(
                    df_volume,
                    x='Data',
                    y='Volume Bombeado (L)',
                    title='Volume Bombeado ao Longo do Tempo',
                    color_discrete_sequence=['#156082'] # personalize as cores aqui
                )
            
            if len(colunas_escolher) == 2:
                col1, col2 = st.columns(2)
                col1.plotly_chart(fig_vol_ac, use_container_width=True)
                col2.plotly_chart(fig_vol_bom, use_container_width=True)
            else:
                st.plotly_chart(fig_vol_ac if 'Volume Acumulado (L)' in colunas_escolher else fig_vol_bom, use_container_width=True)

        else:
            st.warning("Por favor, selecione pelo menos uma coluna para o gráfico.")
   
