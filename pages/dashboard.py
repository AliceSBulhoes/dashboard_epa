import streamlit as st
import pandas as pd
import io
import os
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import plotly.express as px
from utils import tratando_df, fillna_columns, add_accumulated_column, filter_by_date

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

# Função para agregar dados por período temporal com labels descritivos
def aggregate_by_period(df, date_column, value_columns, period='D'):
    """
    Agrega dados por período temporal
    
    Args:
        df: DataFrame
        date_column: Nome da coluna de data
        value_columns: Lista de colunas numéricas para agregar
        period: Período de agregação ('D'=diário, 'W'=semanal, 'M'=mensal, 'Q'=trimestral, 'Y'=anual)
    
    Returns:
        DataFrame agregado com coluna de período descritivo
    """
    df_agg = df.copy()
    df_agg[date_column] = pd.to_datetime(df_agg[date_column])
    df_agg = df_agg.set_index(date_column)
    
    # Agrupar por período e somar as colunas numéricas
    df_agg = df_agg[value_columns].resample(period).sum().reset_index()
    
    # Adicionar coluna com label descritivo do período
    if period == 'D':
        df_agg['Periodo'] = df_agg[date_column].dt.strftime('%d/%m/%Y')
        df_agg['Periodo_Ordenacao'] = df_agg[date_column]
    elif period == 'W':
        df_agg['Periodo'] = 'Sem ' + df_agg[date_column].dt.isocalendar().week.astype(str) + '/' + df_agg[date_column].dt.year.astype(str)
        df_agg['Periodo_Ordenacao'] = df_agg[date_column]
    elif period == 'M':
        df_agg['Periodo'] = df_agg[date_column].dt.strftime('%b/%Y')
        df_agg['Periodo_Ordenacao'] = df_agg[date_column]
    elif period == 'Q':
        df_agg['Periodo'] = 'T' + df_agg[date_column].dt.quarter.astype(str) + '/' + df_agg[date_column].dt.year.astype(str)
        df_agg['Periodo_Ordenacao'] = df_agg[date_column]
    elif period == 'Y':
        df_agg['Periodo'] = df_agg[date_column].dt.year.astype(str)
        df_agg['Periodo_Ordenacao'] = df_agg[date_column]
    
    return df_agg

# Função para agregar dados de FL (usando média)
def aggregate_fl_by_period(df, period='D'):
    """
    Agrega dados de FL por período temporal usando média
    
    Args:
        df: DataFrame de FL
        period: Período de agregação
    
    Returns:
        DataFrame agregado com coluna de período descritivo
    """
    df_agg = df.copy()
    df_agg['Data'] = pd.to_datetime(df_agg['Data'])
    df_agg = df_agg.set_index('Data')
    
    # Agrupar por poço e período, calculando a média
    df_agg = df_agg.groupby(['Poço']).resample(period).mean().reset_index()
    
    # Adicionar coluna com label descritivo do período
    if period == 'D':
        df_agg['Periodo'] = df_agg['Data'].dt.strftime('%d/%m/%Y')
        df_agg['Periodo_Ordenacao'] = df_agg['Data']
    elif period == 'W':
        df_agg['Periodo'] = 'Sem ' + df_agg['Data'].dt.isocalendar().week.astype(str) + '/' + df_agg['Data'].dt.year.astype(str)
        df_agg['Periodo_Ordenacao'] = df_agg['Data']
    elif period == 'M':
        df_agg['Periodo'] = df_agg['Data'].dt.strftime('%b/%Y')
        df_agg['Periodo_Ordenacao'] = df_agg['Data']
    elif period == 'Q':
        df_agg['Periodo'] = 'T' + df_agg['Data'].dt.quarter.astype(str) + '/' + df_agg['Data'].dt.year.astype(str)
        df_agg['Periodo_Ordenacao'] = df_agg['Data']
    elif period == 'Y':
        df_agg['Periodo'] = df_agg['Data'].dt.year.astype(str)
        df_agg['Periodo_Ordenacao'] = df_agg['Data']
    
    return df_agg

# Interface do Dashboard
st.write("# Dashboard")

# --------- Upload do Arquivo ---------
st.sidebar.write("## Upload do Arquivo")
# Download de um arquivo de exemplo
upload_file = st.sidebar.file_uploader("Upload do Arquivo", type=["csv", "xlsx"], accept_multiple_files=True, help="Faça upload de arquivos CSV ou Excel.")

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
    )
    
    # ---------------------- Filtros Sidebar -----------------------
    st.sidebar.header("Filtros")
    
    # ----- Filtro de Agregação Temporal -----
    periodo_agregacao = st.sidebar.selectbox(
        "Agregação Temporal",
        options=["Diário", "Semanal", "Mensal", "Trimestral", "Anual"],
        index=0,
        help="Selecione o período para agregar os dados"
    )
    
    # Mapear seleção para código de período do pandas
    periodo_map = {
        "Diário": "D",
        "Semanal": "W",
        "Mensal": "M",
        "Trimestral": "Q",
        "Anual": "Y"
    }
    periodo_selecionado = periodo_map[periodo_agregacao]
    
    # ----- Data Filter -----
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

        #  ----------- Preenchendo NaN ---------
        df_fl = fillna_columns(df_fl, ['NA (m)', 'NO (m)', 'Esp. (m)'], 0)


        # ----------- Filtros de Poços -----------
        filtroCol1, filtroCol2 = st.columns(2)

        pocos = df_fl['Poço'].unique().tolist()
        poço_selecionado = filtroCol1.multiselect("Selecione os Poços", options=pocos, default=pocos[0])


        # ----------- Filtrar DataFrame pelo Poço Selecionado -----------
        if poço_selecionado:
            df_fl = df_fl[df_fl['Poço'].isin(poço_selecionado)]
        else:
            st.warning("Por favor, selecione pelo menos um poço.")
            st.stop()


        # ------- Filtros de Situação do Poço ------
        tipo = ['NA (m)','NO (m)', 'Esp. (m)']
        tipo_selecionado = filtroCol2.multiselect("Selecione o Tipo", options=tipo, default=tipo[0])


        # ----------- Cards de KPIs -----------
        total_pocos = len(pocos)
        k1, k2 = st.columns(2)
        with k1: card("Total de Poços", total_pocos, "🛢️", color="#5A2781")
        with k2: card("Poços Selecionados", len(poço_selecionado), "✅", color="#2EE43D")


        # ----------- Filtrar DataFrame pelo Tipo Selecionado -----------
        if tipo_selecionado:
            # Agregar dados por período para FL
            if periodo_agregacao != "Diário":
                df_fl_agg = aggregate_fl_by_period(df_fl, periodo_selecionado)
                x_axis_column = 'Periodo'
            else:
                df_fl_agg = df_fl
                x_axis_column = 'Data'
            
            # Ordenar por período para garantir a ordem correta
            if periodo_agregacao != "Diário":
                df_fl_agg = df_fl_agg.sort_values('Periodo_Ordenacao')
            
            # Lista para armazenar as figuras criadas
            figuras = []

            if 'NA (m)' in tipo_selecionado:
                fig_na = px.bar(df_fl_agg, 
                                x=x_axis_column, 
                                y='NA (m)', 
                                color='Poço', 
                                title=f'Nível de Água (NA) - {periodo_agregacao}', 
                                color_discrete_sequence=px.colors.qualitative.Dark24,
                                barmode='group')
                figuras.append(fig_na)

            if 'NO (m)' in tipo_selecionado:
                fig_no = px.bar(df_fl_agg, 
                                x=x_axis_column, 
                                y='NO (m)', 
                                color='Poço', 
                                title=f'Nível de Óleo (NO) - {periodo_agregacao}', 
                                color_discrete_sequence=px.colors.qualitative.Dark24,
                                barmode='group')
                figuras.append(fig_no)

            if 'Esp. (m)' in tipo_selecionado:
                fig_esp = px.bar(df_fl_agg, 
                                x=x_axis_column, 
                                y='Esp. (m)', 
                                color='Poço', 
                                title=f'Espessura de Óleo - {periodo_agregacao}', 
                                color_discrete_sequence=px.colors.qualitative.Dark24,
                                barmode='group')
                figuras.append(fig_esp)

            # Aplicar atualizações de layout apenas para as figuras que foram criadas
            for fig in figuras:
                fig.update_layout(
                    xaxis_tickangle=-45,
                    legend_title_text='Poços',
                    bargap=0.15,
                    bargroupgap=0.1,
                    showlegend=True
                )
                if periodo_agregacao != "Diário":
                    fig.update_xaxes(title_text='Período')

            if len(tipo_selecionado) == 3:
                col1, col2= st.columns(2)
                col1.plotly_chart(fig_na, use_container_width=True)
                col2.plotly_chart(fig_no, use_container_width=True)
                st.plotly_chart(fig_esp, use_container_width=True)
            elif len(tipo_selecionado) == 2:
                col1, col2 = st.columns(2)
                if 'NA (m)' in tipo_selecionado and 'NO (m)' in tipo_selecionado:
                    col1.plotly_chart(fig_na, use_container_width=True)
                    col2.plotly_chart(fig_no, use_container_width=True)
                elif 'NA (m)' in tipo_selecionado and 'Esp. (m)' in tipo_selecionado:
                    col1.plotly_chart(fig_na, use_container_width=True)
                    col2.plotly_chart(fig_esp, use_container_width=True)
                else:
                    col1.plotly_chart(fig_no, use_container_width=True)
                    col2.plotly_chart(fig_esp, use_container_width=True)
            else:
                if 'NA (m)' in tipo_selecionado:
                    st.plotly_chart(fig_na, use_container_width=True)
                elif 'NO (m)' in tipo_selecionado:
                    st.plotly_chart(fig_no, use_container_width=True)
                else:
                    st.plotly_chart(fig_esp, use_container_width=True)


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
        colunas_escolher = st.multiselect("Selecione as colunas para o gráfico", options=['Volume Removido SAO (L)', 'Volume Removido Bailer (L)', 'Volume Acumulado (L)'])

        if colunas_escolher:
            # Agregar dados por período
            if periodo_agregacao != "Diário":
                df_volume_produto_agg = aggregate_by_period(
                    df_volume_produto, 
                    'Data', 
                    ['Volume Removido SAO (L)', 'Volume Removido Bailer (L)'],
                    periodo_selecionado
                )
                # Para volume acumulado, precisamos recalcular após a agregação
                df_volume_produto_agg = add_accumulated_column(
                    df_volume_produto_agg, 
                    ['Volume Removido SAO (L)', 'Volume Removido Bailer (L)'], 
                    'Volume Acumulado (L)'
                )
                x_axis_column = 'Periodo'
            else:
                df_volume_produto_agg = df_volume_produto
                x_axis_column = 'Data'
            
            # Ordenar por período para garantir a ordem correta
            if periodo_agregacao != "Diário":
                df_volume_produto_agg = df_volume_produto_agg.sort_values('Periodo_Ordenacao')
            
            if 'Volume Acumulado (L)' in colunas_escolher:
                fig_vol_ac = px.line(df_volume_produto_agg, x=x_axis_column, y='Volume Acumulado (L)' ,title=f'Volume Acumulado - {periodo_agregacao}', color_discrete_sequence=['#c44d15'])
            if 'Volume Removido SAO (L)' in colunas_escolher:
                fig_vol_sao = px.bar(
                    df_volume_produto_agg,
                    x=x_axis_column,
                    y='Volume Removido SAO (L)',
                    title=f'Volume Removido SAO - {periodo_agregacao}',
                    color_discrete_sequence=['#156082']
                )
            if 'Volume Removido Bailer (L)' in colunas_escolher:
                fig_vol_bailer = px.bar(
                    df_volume_produto_agg,
                    x=x_axis_column,
                    y='Volume Removido Bailer (L)',
                    title=f'Volume Removido Bailer - {periodo_agregacao}',
                    color_discrete_sequence=['#e17b7b']
                )
            
            # Atualizar labels do eixo X
            for fig in [fig_vol_ac, fig_vol_sao, fig_vol_bailer]:
                if periodo_agregacao != "Diário":
                    fig.update_xaxes(title_text='Período')
            
            if len(colunas_escolher) == 3:
                col1, col2, col3 = st.columns(3)
                col1.plotly_chart(fig_vol_ac, use_container_width=True)
                col2.plotly_chart(fig_vol_sao, use_container_width=True)
                col3.plotly_chart(fig_vol_bailer, use_container_width=True)
            elif len(colunas_escolher) == 2:
                col1, col2 = st.columns(2)
                if 'Volume Acumulado (L)' in colunas_escolher and 'Volume Removido SAO (L)' in colunas_escolher:
                    col1.plotly_chart(fig_vol_ac, use_container_width=True)
                    col2.plotly_chart(fig_vol_sao, use_container_width=True)
                elif 'Volume Acumulado (L)' in colunas_escolher and 'Volume Removido Bailer (L)' in colunas_escolher:
                    col1.plotly_chart(fig_vol_ac, use_container_width=True)
                    col2.plotly_chart(fig_vol_bailer, use_container_width=True)
                else:
                    col1.plotly_chart(fig_vol_sao, use_container_width=True)
                    col2.plotly_chart(fig_vol_bailer, use_container_width=True)
            else:
                if 'Volume Acumulado (L)' in colunas_escolher:
                    st.plotly_chart(fig_vol_ac, use_container_width=True)
                elif 'Volume Removido SAO (L)' in colunas_escolher:
                    st.plotly_chart(fig_vol_sao, use_container_width=True)
                else:
                    st.plotly_chart(fig_vol_bailer, use_container_width=True)



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
        colunas_escolher = st.multiselect("Selecione as colunas para o gráfico", options=['Volume Acumulado (L)', 'Volume Bombeado (L)'])
        
        if colunas_escolher:
            # Agregar dados por período
            if periodo_agregacao != "Diário":
                df_volume_agg = aggregate_by_period(
                    df_volume, 
                    'Data', 
                    ['Volume Bombeado (L)'],
                    periodo_selecionado
                )
                # Recalcular volume acumulado após agregação
                df_volume_agg = add_accumulated_column(
                    df_volume_agg, 
                    ['Volume Bombeado (L)'], 
                    'Volume Acumulado (L)'
                )
                x_axis_column = 'Periodo'
            else:
                df_volume_agg = df_volume
                x_axis_column = 'Data'
            
            # Ordenar por período para garantir a ordem correta
            if periodo_agregacao != "Diário":
                df_volume_agg = df_volume_agg.sort_values('Periodo_Ordenacao')
            
            if 'Volume Acumulado (L)' in colunas_escolher:
                fig_vol_ac = px.line(df_volume_agg, x=x_axis_column, y='Volume Acumulado (L)' ,title=f'Volume Acumulado - {periodo_agregacao}', color_discrete_sequence=['#c44d15'])
            if 'Volume Bombeado (L)' in colunas_escolher:
                fig_vol_bom = px.bar(
                    df_volume_agg,
                    x=x_axis_column,
                    y='Volume Bombeado (L)',
                    title=f'Volume Bombeado - {periodo_agregacao}',
                    color_discrete_sequence=['#156082']
                )
            
            # Atualizar labels do eixo X
            for fig in [fig_vol_ac, fig_vol_bom]:
                if periodo_agregacao != "Diário":
                    fig.update_xaxes(title_text='Período')
            
            if len(colunas_escolher) == 2:
                col1, col2 = st.columns(2)
                col1.plotly_chart(fig_vol_ac, use_container_width=True,)
                col2.plotly_chart(fig_vol_bom, use_container_width=True)
            else:
                if 'Volume Acumulado (L)' in colunas_escolher:
                    st.plotly_chart(fig_vol_ac, use_container_width=True)
                else:
                    st.plotly_chart(fig_vol_bom, use_container_width=True)

        else:
            st.warning("Por favor, selecione pelo menos uma coluna para o gráfico.")