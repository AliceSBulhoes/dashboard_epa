import streamlit as st
import pandas as pd
import io
import os
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from utils import tratando_df, fillna_columns, add_accumulated_column, filter_by_date, create_dual_y_axis_chart, group_data_by_period, create_poco_dual_y_axis_chart
from components.btn import btn_download_multiple, btn_download_excel

# Helpers para limpar filtros via callbacks
def _clear_state_key(key: str):
    st.session_state[key] = []

# Inicializa os DataFrames como None para evitar NameError
df_fl = None
df_volume_produto = None
df_volume = None
df_volume_infiltrado = None

# Variáveis Globais
DATA_DIR = os.path.join(os.getcwd(), 'data')

if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)


def card(kpi_titulo: str, kpi_valor, emoji: str = "", color: str = "#5A2781"):
    # Adjust font size based on content length
    font_size = "18px" if isinstance(kpi_valor, str) and len(str(kpi_valor)) > 50 else "30px"
    
    st.markdown(
        f"""
        <div style="
            background: linear-gradient(135deg, {color}22, {color}11);
            border: 1px solid {color}33;
            border-radius: 16px; padding: 18px 18px;
            margin-bottom: 12px;
            height: 100%;
            min-height: 120px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            ">
            <div style="font-size:14px;color:#555;margin-bottom:6px">{emoji} {kpi_titulo}</div>
            <div style="font-size:{font_size};font-weight:700;color:{color}">{kpi_valor}</div>
        </div>
        """,
        unsafe_allow_html=True)

# Interface do Dashboard
st.write("# Dashboard")

# --------- Upload do Arquivo ---------
st.sidebar.write("## Upload do Arquivo")
# Download de um arquivo de exemplo
upload_file = st.sidebar.file_uploader("", type=["csv", "xlsx"], accept_multiple_files=True, key="file_uploader", help="Faça upload de arquivos CSV ou Excel.")

# st.write("*OBS: O arquivo pegará apenas a primeira página, se tiver múltiplas páginas.*")

if upload_file is not None and len(upload_file) > 0:
    for uploaded_file in upload_file:
        # DF Vendas
        df_volume = pd.read_excel(uploaded_file, sheet_name="Volume Bombeado", engine='openpyxl')
        df_volume = tratando_df(df_volume)

        # DF Volume Produto
        df_volume_infiltrado = pd.read_excel(uploaded_file, sheet_name="Volume Infiltrado", engine='openpyxl')
        df_volume_infiltrado = tratando_df(df_volume_infiltrado)

        # DF FL
        #df_fl = pd.read_excel(uploaded_file, sheet_name="FL", engine='openpyxl')
        #df_fl = tratando_df(df_fl)

        # DF Hidrogeológicos
        #df_hidrometros = pd.read_excel(uploaded_file, sheet_name="Hidrômetros", engine='openpyxl')
        #df_hidrometros = tratando_df(df_hidrometros)

        # DF Coleta
        # df_coleta = pd.read_excel(uploaded_file, sheet_name="Coleta", engine='openpyxl')
        # df_coleta = tratando_df(df_coleta)
        

        # Visualizar DataFrame
        # st.write(df_fl)
        # st.write(df_volume_produto)
        # st.write(df_volume)


    # Visualizar Dev
    with st.expander("Visualizar DataFrame"):
        #st.write("### DataFrame FL Informações")
        #if df_fl is not None:
            #st.write(df_fl.columns)
            #st.write(df_fl)
        #else:
            #st.write("Nenhum dado carregado para FL.")

        st.write("### DataFrame Volume Infiltrado Informações")
        if df_volume_infiltrado is not None:
            st.write(df_volume_infiltrado.columns)
            st.write(df_volume_infiltrado)
        else:
            st.write("Nenhum dado carregado para Volume Infiltrado.")

        st.write("### DataFrame Volume Bombeado Informações")
        if df_volume is not None:
            st.write(df_volume.columns)
            st.write(df_volume)
        else:
            st.write("Nenhum dado carregado para Volume Bombeado.")


    if df_volume_infiltrado is not None and df_volume is not None:
        # ARMAZENAR OS VALORES ORIGINAIS ANTES DE QUALQUER FILTRAGEM
        # Usar dados tanto de volume_infiltrado quanto de volume para determinar o range de datas
        dates_volume = pd.to_datetime(df_volume['Data']) if df_volume is not None else pd.Series(dtype='datetime64[ns]')
        dates_infiltrado = pd.to_datetime(df_volume_infiltrado['Data']) if df_volume_infiltrado is not None else pd.Series(dtype='datetime64[ns]')
        
        all_dates = pd.concat([dates_volume, dates_infiltrado], ignore_index=True).dropna()
        data_min_original = pd.to_datetime(all_dates.min()) if len(all_dates) > 0 else pd.to_datetime('today')
        data_max_original = pd.to_datetime(all_dates.max()) if len(all_dates) > 0 else pd.to_datetime('today')
        
        # Processar os dados conforme necessário
        tipo_grafico = st.selectbox(
            "Selecione o Tipo de Gráfico",
            options=["Volume Infiltrado", "Volume Bombeado"],
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
        # USAR OS VALORES ORIGINAIS PARA OS DATE_INPUTS
        data_inicio = st.sidebar.date_input(
            "Data Inicial", 
            value=data_min_original, 
            min_value=data_min_original, 
            max_value=data_max_original, 
            format="DD/MM/YYYY"
        )
        data_fim = st.sidebar.date_input(
            "Data Final", 
            value=data_max_original, 
            min_value=data_min_original, 
            max_value=data_max_original, 
            format="DD/MM/YYYY"
        )

        # Filtrar DataFrame pelo intervalo de datas selecionado
        df_volume = filter_by_date(df_volume, 'Data', data_inicio, data_fim)
        #df_fl = filter_by_date(df_fl, 'Data', data_inicio, data_fim)
        df_volume_infiltrado = filter_by_date(df_volume_infiltrado, 'Data', data_inicio, data_fim)

        # ----- Agrupamento Temporal -----
        st.sidebar.write("### Agrupamento Temporal")
        agrupamento_temporal = st.sidebar.selectbox(
            "Agrupar dados por:",
            options=["day", "week", "month"],
            format_func=lambda x: {"day": "Dia", "week": "Semana", "month": "Mês"}[x],
            index=0,
            help="Agrupa e soma os valores por período selecionado"
        )


        if tipo_grafico == "Volume Infiltrado":
            st.write("## Gráficos de Volume Infiltrado")

            # -------- Aplicar Agrupamento Temporal --------
            if agrupamento_temporal != "day":
                df_volume_infiltrado = group_data_by_period(
                    df_volume_infiltrado,
                    'Data',
                    ['Volume Infiltrado'], 
                    agrupamento_temporal,
                    group_by_col='Ponto'
                )

            # ---------------------- Gráficos -----------------------
            # Initialize session state for infiltrado columns
            if "filtro_colunas_infiltrado" not in st.session_state:
                st.session_state["filtro_colunas_infiltrado"] = []
            if "filtro_pontos_infiltrado" not in st.session_state:
                st.session_state["filtro_pontos_infiltrado"] = []
        
            # Get unique pontos (excluding 'Acumulado' and 'Geral')
            pontos_disponiveis = sorted([p for p in df_volume_infiltrado['Ponto'].unique() if p not in ['Acumulado', 'Geral']])
        
            col1, col2, col3 = st.columns([2, 2, 1], vertical_alignment="center")
            colunas_escolher = col1.multiselect(
                "Selecione o tipo de gráfico",
                options=['Volume por Ponto com Estatísticas', 'Volume Pontos vs Acumulado (Linhas)', 'Volume Pontos vs Acumulado (Barras)', 'Volume Ponto Temporal', 'Boxplot Volume por Data'],
                default=st.session_state["filtro_colunas_infiltrado"] if st.session_state["filtro_colunas_infiltrado"] else ['Volume Pontos vs Acumulado (Linhas)'],
                key="filtro_colunas_infiltrado"
            )
        
            # Default to all pontos if not already set
            default_pontos = st.session_state["filtro_pontos_infiltrado"] if st.session_state["filtro_pontos_infiltrado"] else pontos_disponiveis
        
            pontos_escolhidos = col2.multiselect(
                "Selecione os pontos",
                options=pontos_disponiveis,
                default=default_pontos,
                key="filtro_pontos_infiltrado"
            )
        
            if not colunas_escolher:
                st.warning("Por favor, selecione pelo menos um tipo de gráfico.")
                st.stop()
            if not pontos_escolhidos:
                st.warning("Por favor, selecione pelo menos um ponto.")
                st.stop()
            col3.button("Limpar", key="btn_limpar_colunas_inf", on_click=lambda: [_clear_state_key("filtro_colunas_infiltrado"), _clear_state_key("filtro_pontos_infiltrado")])
        
            figuras = []

            if colunas_escolher:
                if 'Volume por Ponto com Estatísticas' in colunas_escolher:
                    # Gráfico de linhas com estatísticas
                    df_plot = df_volume_infiltrado[df_volume_infiltrado['Ponto'].isin(pontos_escolhidos)].copy()
                
                    if not df_plot.empty:
                        # Calcula estatísticas por data
                        stats = (
                            df_plot.groupby('Data', as_index=False)
                            .agg(
                                media=('Volume Infiltrado', 'mean'),
                                maximo=('Volume Infiltrado', 'max'),
                                minimo=('Volume Infiltrado', 'min')
                            )
                        )
                        stats['media'] = stats['media'].round(2)
                    
                        # Gráfico principal com pontos e linhas por ponto
                        fig_stats = px.line(
                            df_plot,
                            x='Data',
                            y='Volume Infiltrado',
                            color='Ponto',
                            markers=True,
                            title='Volume Infiltrado por Ponto com Estatísticas'
                        )
                    
                        # Add transparency to all ponto lines
                        for trace in fig_stats.data:
                            trace.line.width = 2
                            trace.opacity = 0.7
                    
                        # Adiciona linhas de estatísticas
                        fig_stats.add_trace(go.Scatter(
                            x=stats['Data'], y=stats['media'],
                            mode='lines+markers',
                            name='Média',
                            line=dict(color='black', dash='dash', width=2),
                            opacity=0.7
                        ))
                        fig_stats.add_trace(go.Scatter(
                            x=stats['Data'], y=stats['maximo'],
                            mode='lines',
                            name='Máximo',
                            line=dict(color='green', dash='dot', width=2),
                            opacity=0.7
                        ))
                        fig_stats.add_trace(go.Scatter(
                            x=stats['Data'], y=stats['minimo'],
                            mode='lines',
                            name='Mínimo',
                            line=dict(color='red', dash='dot', width=2),
                            opacity=0.7
                        ))
                    
                        # Layout
                        fig_stats.update_layout(
                            yaxis_title='Volume Infiltrado (m³)',
                            xaxis_title='Data',
                            hovermode='x unified',
                            template='plotly_white',
                            legend=dict(
                                orientation='h',
                                yanchor='top',
                                y=-0.2,
                                xanchor='center',
                                x=0.5
                            )
                        )
                        figuras.append(fig_stats)
            
                if 'Volume Pontos vs Acumulado (Linhas)' in colunas_escolher:
                    # Gráfico com duplo eixo Y
                    df_work = df_volume_infiltrado.copy()
                
                    # Separa acumulado e pontos (filtrando pelos pontos selecionados)
                    df_pontos = df_work[df_work['Ponto'].isin(pontos_escolhidos)].copy()
                    df_acum = df_work[df_work['Ponto'] == 'Acumulado'].copy()
                
                    if not df_pontos.empty or not df_acum.empty:
                        # Cria figura com eixo Y secundário
                        fig_dual = make_subplots(specs=[[{"secondary_y": True}]])
                    
                        # Adiciona as linhas dos pontos (eixo primário)
                        for ponto, d in df_pontos.groupby('Ponto'):
                            fig_dual.add_trace(
                                go.Scatter(
                                    x=d['Data'],
                                    y=d['Volume Infiltrado'],
                                    mode='lines+markers',
                                    name=ponto,
                                    line=dict(width=2),
                                    opacity=0.7
                                ),
                                secondary_y=False
                            )
                    
                        # Adiciona a linha do acumulado (eixo secundário)
                        if not df_acum.empty:
                            fig_dual.add_trace(
                                go.Scatter(
                                    x=df_acum['Data'],
                                    y=df_acum['Volume Infiltrado'],
                                    mode='lines+markers',
                                    name='Acumulado',
                                    line=dict(color='black', width=3),
                                    opacity=0.8
                                ),
                                secondary_y=True
                            )
                    
                        # Atualiza layout e eixos
                        fig_dual.update_layout(
                            title='Volume Infiltrado por Ponto e Volume Acumulado (Linhas)',
                            hovermode='x unified',
                            template='plotly_white',
                            legend=dict(
                                orientation='h',
                                yanchor='top',
                                y=-0.2,
                                xanchor='center',
                                x=0.5
                            )
                        )
                    
                        fig_dual.update_xaxes(title_text='Data')
                    
                        fig_dual.update_yaxes(
                            title_text='Volume Infiltrado (m³)',
                            secondary_y=False,
                            rangemode='tozero',
                            showgrid=True,
                            zeroline=True
                        )
                        fig_dual.update_yaxes(
                            title_text='Volume Acumulado (m³)',
                            secondary_y=True,
                            rangemode='tozero',
                            showgrid=False,
                            zeroline=False,
                            showline=False,
                            ticks=''
                        )
                        figuras.append(fig_dual)
            
                if 'Volume Pontos vs Acumulado (Barras)' in colunas_escolher:
                    # Gráfico com duplo eixo Y - versão com barras
                    df_work = df_volume_infiltrado.copy()
                
                    # Separa acumulado e pontos (filtrando pelos pontos selecionados)
                    df_pontos = df_work[df_work['Ponto'].isin(pontos_escolhidos)].copy()
                    df_acum = df_work[df_work['Ponto'] == 'Acumulado'].copy()
                
                    if not df_pontos.empty or not df_acum.empty:
                        # Cria figura com eixo Y secundário
                        fig_dual_bars = make_subplots(specs=[[{"secondary_y": True}]])
                    
                        # Adiciona as barras dos pontos (eixo primário)
                        for ponto, d in df_pontos.groupby('Ponto'):
                            fig_dual_bars.add_trace(
                                go.Bar(
                                    x=d['Data'],
                                    y=d['Volume Infiltrado'],
                                    name=ponto,
                                    opacity=0.7
                                ),
                                secondary_y=False
                            )
                    
                        # Adiciona a linha do acumulado (eixo secundário)
                        if not df_acum.empty:
                            fig_dual_bars.add_trace(
                                go.Scatter(
                                    x=df_acum['Data'],
                                    y=df_acum['Volume Infiltrado'],
                                    mode='lines+markers',
                                    name='Acumulado',
                                    line=dict(color='black', width=4),
                                    marker=dict(
                                        size=12,
                                        color='white',
                                        line=dict(color='black', width=2)
                                    ),
                                    opacity=1.0
                                ),
                                secondary_y=True
                            )
                    
                        # Configure x-axis tick format based on temporal grouping
                        xaxis_config = {'title_text': 'Data'}
                    
                        # Prepare custom tick labels in Portuguese
                        if agrupamento_temporal == 'month':
                            # Show last day of each month
                            if not df_acum.empty:
                                xaxis_config['tickmode'] = 'array'
                                xaxis_config['tickvals'] = df_acum['Data'].tolist()
                                month_map = {1: 'Jan', 2: 'Fev', 3: 'Mar', 4: 'Abr', 5: 'Mai', 6: 'Jun',
                                           7: 'Jul', 8: 'Ago', 9: 'Set', 10: 'Out', 11: 'Nov', 12: 'Dez'}
                                xaxis_config['ticktext'] = [f"{month_map[d.month]} {d.day}" for d in df_acum['Data']]
                        elif agrupamento_temporal == 'week':
                            # Show last day of each week
                            if not df_acum.empty:
                                xaxis_config['tickmode'] = 'array'
                                xaxis_config['tickvals'] = df_acum['Data'].tolist()
                                month_map = {1: 'Jan', 2: 'Fev', 3: 'Mar', 4: 'Abr', 5: 'Mai', 6: 'Jun',
                                           7: 'Jul', 8: 'Ago', 9: 'Set', 10: 'Out', 11: 'Nov', 12: 'Dez'}
                                xaxis_config['ticktext'] = [f"{month_map[d.month]} {d.day}" for d in df_acum['Data']]
                        else:  # day
                            # Show every week (every 7 days)
                            xaxis_config['dtick'] = 7 * 24 * 60 * 60 * 1000  # 7 days in milliseconds
                            # For daily view, we need to use tickformatstops for Portuguese months
                            month_map = {1: 'Jan', 2: 'Fev', 3: 'Mar', 4: 'Abr', 5: 'Mai', 6: 'Jun',
                                       7: 'Jul', 8: 'Ago', 9: 'Set', 10: 'Out', 11: 'Nov', 12: 'Dez'}
                            # Get all dates that will be shown and create custom labels
                            if not df_pontos.empty:
                                all_dates = pd.date_range(start=df_pontos['Data'].min(), end=df_pontos['Data'].max(), freq='7D')
                                xaxis_config['tickmode'] = 'array'
                                xaxis_config['tickvals'] = all_dates.tolist()
                                xaxis_config['ticktext'] = [f"{month_map[d.month]} {d.day}" for d in all_dates]
                    
                        # Find peak value for annotation (excluding 'Acumulado')
                        if not df_pontos.empty:
                            # Ensure we're only working with non-Acumulado data
                            df_pontos_only = df_pontos[df_pontos['Ponto'] != 'Acumulado'].copy()
                            if not df_pontos_only.empty:
                                # Calculate total volume per date (sum across all pontos)
                                volume_por_data = df_pontos_only.groupby('Data')['Volume Infiltrado'].sum().reset_index()
                                max_idx = volume_por_data['Volume Infiltrado'].idxmax()
                                peak_date = volume_por_data.loc[max_idx, 'Data']
                                peak_value = volume_por_data.loc[max_idx, 'Volume Infiltrado']
                        
                            # Format peak date label in Portuguese
                            month_map = {1: 'Jan', 2: 'Fev', 3: 'Mar', 4: 'Abr', 5: 'Mai', 6: 'Jun',
                                       7: 'Jul', 8: 'Ago', 9: 'Set', 10: 'Out', 11: 'Nov', 12: 'Dez'}
                            peak_label = f"{month_map[peak_date.month]} {peak_date.day}"
                    
                        # Atualiza layout e eixos
                        fig_dual_bars.update_layout(
                            title='Volume Infiltrado por Ponto e Volume Acumulado (Barras)',
                            hovermode='x unified',
                            template='plotly_white',
                            barmode='group',  # Dodged bars, not stacked
                            legend=dict(
                                orientation='h',
                                yanchor='top',
                                y=-0.2,
                                xanchor='center',
                                x=0.5,
                                font=dict(size=14)
                            ),
                            font=dict(size=14),
                            title_font=dict(size=16)
                        )
                    
                        xaxis_config['title_font'] = dict(size=16)
                        xaxis_config['tickfont'] = dict(size=14)
                        fig_dual_bars.update_xaxes(**xaxis_config)
                    
                        fig_dual_bars.update_yaxes(
                            title_text='Volume Infiltrado (m³)',
                            secondary_y=False,
                            rangemode='tozero',
                            showgrid=True,
                            zeroline=True,
                            title_font=dict(size=16),
                            tickfont=dict(size=14)
                        )
                        fig_dual_bars.update_yaxes(
                            title_text='Volume Acumulado (m³)',
                            secondary_y=True,
                            rangemode='tozero',
                            showgrid=False,
                            zeroline=False,
                            showline=False,
                            ticks='',
                            title_font=dict(size=16),
                            tickfont=dict(size=14)
                        )
                    
                        # Add annotation for peak value
                        if not df_pontos.empty:
                            df_pontos_only = df_pontos[df_pontos['Ponto'] != 'Acumulado'].copy()
                            if not df_pontos_only.empty:
                                # Calculate annotation position
                                # Find the date with highest sum, then position at 25% above the highest individual ponto on that date
                                y_max_on_peak_date = df_pontos_only[df_pontos_only['Data'] == peak_date]['Volume Infiltrado'].max()
                                annotation_y = y_max_on_peak_date * 1.25  # 25% above the highest bar on that date
                            
                                fig_dual_bars.add_annotation(
                                    x=peak_date,
                                    y=annotation_y,
                                    text=f"Pico de infiltração<br>{peak_value:.1f} m³",
                                    ax=0,
                                    ay=0,
                                    bgcolor="rgba(255, 255, 255, 0.8)",
                                    bordercolor="#333",
                                    borderwidth=1,
                                    borderpad=4,
                                    font=dict(size=12, color="#333")
                                )
                    
                        figuras.append(fig_dual_bars)
            
                if 'Volume Ponto Temporal' in colunas_escolher:
                    # Gráfico com Ponto no eixo X e Data como cor
                    df_work = df_volume_infiltrado[df_volume_infiltrado['Ponto'].isin(pontos_escolhidos)].copy()
                
                    if not df_work.empty:
                        # Calculate statistics per ponto for hover tooltip
                        stats_per_ponto = df_work.groupby('Ponto')['Volume Infiltrado'].agg([
                            ('mean', 'mean'),
                            ('std', 'std'),
                            ('min', 'min'),
                            ('max', 'max')
                        ]).round(2)
                    
                        # Convert dates to string for discrete coloring
                        df_work['Data_str'] = df_work['Data'].dt.strftime('%Y-%m-%d')
                    
                        fig_ponto_temporal = px.bar(
                            df_work,
                            x='Ponto',
                            y='Volume Infiltrado',
                            color='Data_str',
                            title='Volume Infiltrado por Ponto (Temporal)',
                            labels={'Data_str': 'Data'},
                            barmode='group'
                        )
                    
                        # Create invisible scatter trace for unified hover on each ponto
                        for ponto in pontos_escolhidos:
                            if ponto in stats_per_ponto.index:
                                stats = stats_per_ponto.loc[ponto]
                                hover_text = (f"<b>{ponto}</b><br>" +
                                            f"Média: {stats['mean']:.2f} m³<br>" +
                                            f"Desvio Padrão: {stats['std']:.2f} m³<br>" +
                                            f"Min: {stats['min']:.2f} m³<br>" +
                                            f"Max: {stats['max']:.2f} m³")
                            
                                fig_ponto_temporal.add_trace(
                                    go.Scatter(
                                        x=[ponto],
                                        y=[stats['max']],
                                        mode='markers',
                                        marker=dict(size=0.1, opacity=0),
                                        hovertemplate=hover_text + '<extra></extra>',
                                        showlegend=False,
                                        hoverinfo='text'
                                    )
                                )
                    
                        # Remove hover from bars
                        fig_ponto_temporal.update_traces(
                            hovertemplate=None,
                            hoverinfo='skip',
                            selector=dict(type='bar')
                        )
                    
                        fig_ponto_temporal.update_layout(
                            hovermode='x',
                            template='plotly_white',
                            showlegend=False,  # Remove legend
                            font=dict(size=14),
                            title_font=dict(size=16),
                            xaxis=dict(
                                title_font=dict(size=16),
                                tickfont=dict(size=14)
                            ),
                            yaxis=dict(
                                title_font=dict(size=16),
                                tickfont=dict(size=14)
                            )
                        )
                    
                        figuras.append(fig_ponto_temporal)
            
                if 'Boxplot Volume por Data' in colunas_escolher:
                    # Boxplot com Data no eixo X e Volume por ponto
                    df_work = df_volume_infiltrado[df_volume_infiltrado['Ponto'].isin(pontos_escolhidos)].copy()
                
                    if not df_work.empty:
                        # Format dates for display
                        df_work['Data_str'] = df_work['Data'].dt.strftime('%Y-%m-%d')
                    
                        fig_boxplot = px.box(
                            df_work,
                            x='Data_str',
                            y='Volume Infiltrado',
                            title='Distribuição de Volume Infiltrado por Data',
                            labels={'Data_str': 'Data'}
                        )
                    
                        fig_boxplot.update_layout(
                            hovermode='x unified',
                            template='plotly_white',
                            font=dict(size=14),
                            title_font=dict(size=16),
                            xaxis=dict(
                                title_font=dict(size=16),
                                tickfont=dict(size=12),
                                tickangle=-45
                            ),
                            yaxis=dict(
                                title_font=dict(size=16),
                                tickfont=dict(size=14)
                            ),
                            margin=dict(b=100)
                        )
                    
                        figuras.append(fig_boxplot)

                n_figs = len(figuras)
                if n_figs == 1:
                    st.plotly_chart(figuras[0], use_container_width=True, key="single_inf_chart")
                elif n_figs == 2:
                    col1, col2 = st.columns(2)
                    col1.plotly_chart(figuras[0], use_container_width=True, key="inf_chart_1")
                    col2.plotly_chart(figuras[1], use_container_width=True, key="inf_chart_2")
                elif n_figs == 3:
                    col1, col2 = st.columns(2)
                    col1.plotly_chart(figuras[0], use_container_width=True, key="inf_chart_1")
                    col2.plotly_chart(figuras[1], use_container_width=True, key="inf_chart_2")
                    st.plotly_chart(figuras[2], use_container_width=True, key="inf_chart_3")
                else:
                    # Para mais gráficos, exibir em pares
                    for i in range(0, n_figs, 2):
                        if i + 1 < n_figs:
                            col1, col2 = st.columns(2)
                            col1.plotly_chart(figuras[i], use_container_width=True, key=f"inf_chart_{i}")
                            col2.plotly_chart(figuras[i+1], use_container_width=True, key=f"inf_chart_{i+1}")
                        else:
                            st.plotly_chart(figuras[i], use_container_width=True, key=f"inf_chart_{i}")

                if figuras:
                    btn_download_multiple(figuras)

            # --------- CARDS DE ESTATÍSTICAS DESCRITIVAS ---------
            st.write("---")
            st.write("### Estatísticas Descritivas")
        
            # Filtrar dados pelos pontos selecionados
            df_stats_filtered = df_volume_infiltrado[df_volume_infiltrado['Ponto'].isin(pontos_escolhidos)].copy()
        
            if not df_stats_filtered.empty:
                # Média de Volume Infiltrado por período
                periodo_label = {"day": "dia", "week": "semana", "month": "mês"}[agrupamento_temporal]
                media_volume = df_stats_filtered['Volume Infiltrado'].mean()
            
                # Ponto com maior leitura total
                volume_por_ponto = df_stats_filtered.groupby('Ponto')['Volume Infiltrado'].sum()
                ponto_max = volume_por_ponto.idxmax()
                volume_max = volume_por_ponto.max()
            
                # Ponto com menor leitura total
                ponto_min = volume_por_ponto.idxmin()
                volume_min = volume_por_ponto.min()
            
                # Exibir cards
                k1, k2, k3 = st.columns(3)
                with k1:
                    card("Média por " + periodo_label.capitalize(), f"{media_volume:.2f} m³", "📊", color="#4A90E2")
                with k2:
                    card("Ponto com Maior Volume (" + periodo_label.capitalize() + ")", f"{ponto_max}: {volume_max:.2f} m³", "⬆️", color="#2EE43D")
                with k3:
                    card("Ponto com Menor Volume (" + periodo_label.capitalize() + ")", f"{ponto_min}: {volume_min:.2f} m³", "⬇️", color="#FF6B6B")

            # --------- TABELA DE ESTATÍSTICAS POR PONTO ---------
            st.write("---")
            st.write("### Estatísticas por Ponto")
        
            # Filtrar dados pelos pontos selecionados (excluindo 'Acumulado' e 'Geral')
            df_table_filtered = df_volume_infiltrado[df_volume_infiltrado['Ponto'].isin(pontos_escolhidos)].copy()
        
            if not df_table_filtered.empty:
                # Calcular estatísticas gerais (todos os pontos selecionados juntos)
                stats_geral = {
                    'Ponto': 'Geral',
                    'Média': df_table_filtered['Volume Infiltrado'].mean(),
                    'Desvio-Padrão': df_table_filtered['Volume Infiltrado'].std(),
                    'Mínimo': df_table_filtered['Volume Infiltrado'].min(),
                    'Mediana': df_table_filtered['Volume Infiltrado'].median(),
                    'Máximo': df_table_filtered['Volume Infiltrado'].max()
                }
            
                # Calcular estatísticas por ponto
                stats_per_ponto = df_table_filtered.groupby('Ponto')['Volume Infiltrado'].agg([
                    ('Média', 'mean'),
                    ('Desvio-Padrão', 'std'),
                    ('Mínimo', 'min'),
                    ('Mediana', 'median'),
                    ('Máximo', 'max')
                ]).reset_index()
            
                # Criar DataFrame combinado (Geral + individual)
                df_stats_table = pd.concat([
                    pd.DataFrame([stats_geral]),
                    stats_per_ponto
                ], ignore_index=True)
            
                # Arredondar valores para 2 casas decimais
                numeric_columns = ['Média', 'Desvio-Padrão', 'Mínimo', 'Mediana', 'Máximo']
                df_stats_table[numeric_columns] = df_stats_table[numeric_columns].round(2)
            
                # Aplicar estilo à tabela
                st.dataframe(
                    df_stats_table,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Ponto": st.column_config.TextColumn("Ponto", width="medium"),
                        "Média": st.column_config.NumberColumn("Média (m³)", format="%.2f"),
                        "Desvio-Padrão": st.column_config.NumberColumn("Desvio-Padrão (m³)", format="%.2f"),
                        "Mínimo": st.column_config.NumberColumn("Mínimo (m³)", format="%.2f"),
                        "Mediana": st.column_config.NumberColumn("Mediana (m³)", format="%.2f"),
                        "Máximo": st.column_config.NumberColumn("Máximo (m³)", format="%.2f")
                    }
                )
            
                # Botão para download em Excel
                btn_download_excel(df_stats_table, "estatisticas_volume_infiltrado.xlsx")
                


        elif tipo_grafico == "Volume Bombeado":
            st.write("## Gráficos de Volume Bombeado")

            # -------- Aplicar Agrupamento Temporal --------
            if agrupamento_temporal != "day":
                df_volume = group_data_by_period(
                    df_volume,
                    'Data',
                    ['Volume Bombeado (m³)'], 
                    agrupamento_temporal,
                    group_by_col='Poço'
                )

            # ---------------------- Cards -----------------------
            if not df_volume.empty:
                # Calcular informações para os cards
                df_volume_sorted = df_volume.sort_values(by='Data', ascending=False)
                
                # Volume Bombeado - último mês e total
                data_mais_recente = df_volume_sorted['Data'].iloc[0]
                # Filtrar dados do último mês
                data_um_mes_atras = data_mais_recente - pd.DateOffset(months=1)
                df_ultimo_mes = df_volume[(df_volume['Data'] >= data_um_mes_atras) & (df_volume['Poço'] != 'Acumulado')]
                volume_ultimo_mes = df_ultimo_mes['Volume Bombeado (m³)'].sum()
                
                # Volume total acumulado (pegar da linha 'Acumulado' na data mais recente)
                df_acumulado = df_volume[(df_volume['Poço'] == 'Acumulado') & (df_volume['Data'] == data_mais_recente)]
                volume_total = df_acumulado['Volume Bombeado (m³)'].iloc[0] if not df_acumulado.empty else 0
                
                # Número de poços ativos e seus nomes
                df_volume_sem_acum = df_volume[df_volume['Poço'] != 'Acumulado']
                pocos_ativos = sorted(df_volume_sem_acum['Poço'].unique())
                num_pocos_ativos = len(pocos_ativos)
                pocos_ativos_text = ', '.join(pocos_ativos)
                
                # Formatar mês
                month_map_pt = {1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril', 5: 'Maio', 6: 'Junho',
                               7: 'Julho', 8: 'Agosto', 9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'}
                mes_formatado = f"{month_map_pt[data_mais_recente.month]}/{data_mais_recente.year}"
                data_formatada = data_mais_recente.strftime('%d/%m/%Y')
                
                # Cards
                k1, k2 = st.columns(2)
                with k1: 
                    card_text = f"{volume_ultimo_mes:.2f} m³ ({mes_formatado})<br>{volume_total:.2f} m³ (acumulado até {data_formatada})"
                    card("Volume Bombeado", card_text, "💧", color="#0571ED")
                with k2: 
                    card_text_pocos = f"{num_pocos_ativos}<br><em style='font-size:14px;font-weight:400;'>{pocos_ativos_text}</em>"
                    card("Poços de Bombeamento Ativos", card_text_pocos, "🏭", color="#2EE43D")
                
                # Cards para Volume Infiltrado
                if df_volume_infiltrado is not None and not df_volume_infiltrado.empty:
                    df_infiltrado_sorted = df_volume_infiltrado.sort_values(by='Data', ascending=False)
                    
                    # Volume Infiltrado - último mês e total
                    data_mais_recente_inf = df_infiltrado_sorted['Data'].iloc[0]
                    data_um_mes_atras_inf = data_mais_recente_inf - pd.DateOffset(months=1)
                    df_ultimo_mes_inf = df_volume_infiltrado[(df_volume_infiltrado['Data'] >= data_um_mes_atras_inf) & (df_volume_infiltrado['Ponto'] != 'Acumulado')]
                    volume_ultimo_mes_inf = df_ultimo_mes_inf['Volume Infiltrado'].sum()
                    
                    # Volume total infiltrado (pegar da linha 'Acumulado' na data mais recente)
                    df_acumulado_inf = df_volume_infiltrado[(df_volume_infiltrado['Ponto'] == 'Acumulado') & (df_volume_infiltrado['Data'] == data_mais_recente_inf)]
                    volume_total_inf = df_acumulado_inf['Volume Infiltrado'].iloc[0] if not df_acumulado_inf.empty else 0
                
                # Número de pontos ativos para infiltrado e seus nomes
                df_infiltrado_sem_acum = df_volume_infiltrado[
                    (df_volume_infiltrado['Ponto'] != 'Acumulado') & 
                    (df_volume_infiltrado['Ponto'] != 'Geral')
                ]
                pontos_ativos = sorted(df_infiltrado_sem_acum['Ponto'].unique())
                num_pocos_ativos_inf = len(pontos_ativos)
                pontos_ativos_text = ', '.join(pontos_ativos)
                
                # Formatar mês e data
                mes_formatado_inf = f"{month_map_pt[data_mais_recente_inf.month]}/{data_mais_recente_inf.year}"
                data_formatada_inf = data_mais_recente_inf.strftime('%d/%m/%Y')
                
                k3, k4 = st.columns(2)
                with k3:
                    card_text_inf = f"{volume_ultimo_mes_inf:.2f} m³ ({mes_formatado_inf})<br>{volume_total_inf:.2f} m³ (acumulado até {data_formatada_inf})"
                    card("Volume Infiltrado", card_text_inf, "💦", color="#DD7D23")
                with k4:
                    card_text_pontos = f"{num_pocos_ativos_inf}<br><em style='font-size:14px;font-weight:400;'>{pontos_ativos_text}</em>"
                    card("Pontos de Infiltração Ativos", card_text_pontos, "🔧", color="#9C27B0")

        # ---------------------- Gráficos -----------------------
        # Initialize session state for bombeado columns
        if "filtro_colunas_bombeado" not in st.session_state:
            st.session_state["filtro_colunas_bombeado"] = []
        if "filtro_pocos_bombeado" not in st.session_state:
            st.session_state["filtro_pocos_bombeado"] = []
        
        # Get unique poços (excluding 'Acumulado')
        pocos_disponiveis = sorted([p for p in df_volume['Poço'].unique() if p != 'Acumulado'])
        
        col1, col2, col3 = st.columns([2, 2, 1], vertical_alignment="center")
        colunas_escolher = col1.multiselect(
            "Selecione o tipo de gráfico",
            options=['Volume por Poço com Estatísticas', 'Volume Poços vs Acumulado (Linhas)', 'Volume Poços vs Acumulado (Barras)', 'Volume Poço Temporal', 'Boxplot Volume por Data'],
            default=st.session_state["filtro_colunas_bombeado"] if st.session_state["filtro_colunas_bombeado"] else ['Volume Poços vs Acumulado (Linhas)'],
            key="filtro_colunas_bombeado"
        )
        
        # Default to all poços if not already set
        default_pocos = st.session_state["filtro_pocos_bombeado"] if st.session_state["filtro_pocos_bombeado"] else pocos_disponiveis
        
        pocos_escolhidos = col2.multiselect(
            "Selecione os poços",
            options=pocos_disponiveis,
            default=default_pocos,
            key="filtro_pocos_bombeado"
        )
        
        if not colunas_escolher:
            st.warning("Por favor, selecione pelo menos um tipo de gráfico.")
            st.stop()
        if not pocos_escolhidos:
            st.warning("Por favor, selecione pelo menos um poço.")
            st.stop()
        col3.button("Limpar", key="btn_limpar_colunas_bomb", on_click=lambda: [_clear_state_key("filtro_colunas_bombeado"), _clear_state_key("filtro_pocos_bombeado")])
        
        figuras = []

        if colunas_escolher:
            if 'Volume por Poço com Estatísticas' in colunas_escolher:
                # Gráfico de linhas com estatísticas (baseado na primeira abordagem do notebook)
                # Substitui 0 por NaN e filtra pelos poços selecionados
                df_plot = df_volume[df_volume['Poço'].isin(pocos_escolhidos)].copy()
                #df_plot['Volume Bombeado (m³)'] = df_plot['Volume Bombeado (m³)'].replace(0, np.nan)
                
                if not df_plot.empty:
                    # Calcula estatísticas por data
                    stats = (
                        df_plot.groupby('Data', as_index=False)
                        .agg(
                            media=('Volume Bombeado (m³)', 'mean'),
                            maximo=('Volume Bombeado (m³)', 'max'),
                            minimo=('Volume Bombeado (m³)', 'min')
                        )
                    )
                    stats['media'] = stats['media'].round(2)
                    
                    # Gráfico principal com pontos e linhas por poço
                    fig_stats = px.line(
                        df_plot,
                        x='Data',
                        y='Volume Bombeado (m³)',
                        color='Poço',
                        markers=True,
                        title='Volume Bombeado por Poço com Estatísticas'
                    )
                    
                    # Add transparency to all poço lines
                    for trace in fig_stats.data:
                        trace.line.width = 2
                        trace.opacity = 0.7
                    
                    # Adiciona linhas de estatísticas
                    fig_stats.add_trace(go.Scatter(
                        x=stats['Data'], y=stats['media'],
                        mode='lines+markers',
                        name='Média',
                        line=dict(color='black', dash='dash', width=2),
                        opacity=0.7
                    ))
                    fig_stats.add_trace(go.Scatter(
                        x=stats['Data'], y=stats['maximo'],
                        mode='lines',
                        name='Máximo',
                        line=dict(color='green', dash='dot', width=2),
                        opacity=0.7
                    ))
                    fig_stats.add_trace(go.Scatter(
                        x=stats['Data'], y=stats['minimo'],
                        mode='lines',
                        name='Mínimo',
                        line=dict(color='red', dash='dot', width=2),
                        opacity=0.7
                    ))
                    
                    # Layout
                    fig_stats.update_layout(
                        yaxis_title='Volume Bombeado (m³)',
                        xaxis_title='Data',
                        hovermode='x unified',
                        template='plotly_white',
                        legend=dict(
                            orientation='h',
                            yanchor='top',
                            y=-0.2,
                            xanchor='center',
                            x=0.5
                        )
                    )
                    figuras.append(fig_stats)
            
            if 'Volume Poços vs Acumulado (Linhas)' in colunas_escolher:
                # Gráfico com duplo eixo Y (baseado na segunda abordagem do notebook)
                # Substitui 0 por NaN
                df_work = df_volume.copy()
                #df_work['Volume Bombeado (m³)'] = df_work['Volume Bombeado (m³)'].replace(0, np.nan)
                
                # Separa acumulado e poços (filtrando pelos poços selecionados)
                df_pocos = df_work[df_work['Poço'].isin(pocos_escolhidos)].copy()
                df_acum = df_work[df_work['Poço'] == 'Acumulado'].copy()
                
                if not df_pocos.empty or not df_acum.empty:
                    # Cria figura com eixo Y secundário
                    fig_dual = make_subplots(specs=[[{"secondary_y": True}]])
                    
                    # Adiciona as linhas dos poços (eixo primário)
                    for poco, d in df_pocos.groupby('Poço'):
                        fig_dual.add_trace(
                            go.Scatter(
                                x=d['Data'],
                                y=d['Volume Bombeado (m³)'],
                                mode='lines+markers',
                                name=poco,
                                line=dict(width=2),
                                opacity=0.7
                            ),
                            secondary_y=False
                        )
                    
                    # Adiciona a linha do acumulado (eixo secundário)
                    if not df_acum.empty:
                        fig_dual.add_trace(
                            go.Scatter(
                                x=df_acum['Data'],
                                y=df_acum['Volume Bombeado (m³)'],
                                mode='lines+markers',
                                name='Acumulado',
                                line=dict(color='black', width=3),
                                opacity=0.8
                            ),
                            secondary_y=True
                        )
                    
                    # Atualiza layout e eixos
                    fig_dual.update_layout(
                        title='Volume Bombeado por Poço e Volume Acumulado (Linhas)',
                        hovermode='x unified',
                        template='plotly_white',
                        legend=dict(
                            orientation='h',
                            yanchor='top',
                            y=-0.2,
                            xanchor='center',
                            x=0.5
                        )
                    )
                    
                    fig_dual.update_xaxes(title_text='Data')
                    
                    fig_dual.update_yaxes(
                        title_text='Volume Bombeado (m³)',
                        secondary_y=False,
                        rangemode='tozero',
                        showgrid=True,
                        zeroline=True
                    )
                    fig_dual.update_yaxes(
                        title_text='Volume Acumulado (m³)',
                        secondary_y=True,
                        rangemode='tozero',
                        showgrid=False,
                        zeroline=False,
                        showline=False,
                        ticks=''
                    )
                    figuras.append(fig_dual)
            
            if 'Volume Poços vs Acumulado (Barras)' in colunas_escolher:
                # Gráfico com duplo eixo Y - versão com barras
                df_work = df_volume.copy()
                
                # Separa acumulado e poços (filtrando pelos poços selecionados)
                df_pocos = df_work[df_work['Poço'].isin(pocos_escolhidos)].copy()
                df_acum = df_work[df_work['Poço'] == 'Acumulado'].copy()
                
                if not df_pocos.empty or not df_acum.empty:
                    # Cria figura com eixo Y secundário
                    fig_dual_bars = make_subplots(specs=[[{"secondary_y": True}]])
                    
                    # Adiciona as barras dos poços (eixo primário)
                    for poco, d in df_pocos.groupby('Poço'):
                        fig_dual_bars.add_trace(
                            go.Bar(
                                x=d['Data'],
                                y=d['Volume Bombeado (m³)'],
                                name=poco,
                                opacity=0.7
                            ),
                            secondary_y=False
                        )
                    
                    # Adiciona a linha do acumulado (eixo secundário)
                    if not df_acum.empty:
                        fig_dual_bars.add_trace(
                            go.Scatter(
                                x=df_acum['Data'],
                                y=df_acum['Volume Bombeado (m³)'],
                                mode='lines+markers',
                                name='Acumulado',
                                line=dict(color='black', width=4),
                                marker=dict(
                                    size=12,
                                    color='white',
                                    line=dict(color='black', width=2)
                                ),
                                opacity=1.0
                            ),
                            secondary_y=True
                        )
                    
                    # Configure x-axis tick format based on temporal grouping
                    xaxis_config = {'title_text': 'Data'}
                    
                    # Prepare custom tick labels in Portuguese
                    if agrupamento_temporal == 'month':
                        # Show last day of each month
                        if not df_acum.empty:
                            xaxis_config['tickmode'] = 'array'
                            xaxis_config['tickvals'] = df_acum['Data'].tolist()
                            month_map = {1: 'Jan', 2: 'Fev', 3: 'Mar', 4: 'Abr', 5: 'Mai', 6: 'Jun',
                                       7: 'Jul', 8: 'Ago', 9: 'Set', 10: 'Out', 11: 'Nov', 12: 'Dez'}
                            xaxis_config['ticktext'] = [f"{month_map[d.month]} {d.day}" for d in df_acum['Data']]
                    elif agrupamento_temporal == 'week':
                        # Show last day of each week
                        if not df_acum.empty:
                            xaxis_config['tickmode'] = 'array'
                            xaxis_config['tickvals'] = df_acum['Data'].tolist()
                            month_map = {1: 'Jan', 2: 'Fev', 3: 'Mar', 4: 'Abr', 5: 'Mai', 6: 'Jun',
                                       7: 'Jul', 8: 'Ago', 9: 'Set', 10: 'Out', 11: 'Nov', 12: 'Dez'}
                            xaxis_config['ticktext'] = [f"{month_map[d.month]} {d.day}" for d in df_acum['Data']]
                    else:  # day
                        # Show every week (every 7 days)
                        xaxis_config['dtick'] = 7 * 24 * 60 * 60 * 1000  # 7 days in milliseconds
                        # For daily view, we need to use tickformatstops for Portuguese months
                        month_map = {1: 'Jan', 2: 'Fev', 3: 'Mar', 4: 'Abr', 5: 'Mai', 6: 'Jun',
                                   7: 'Jul', 8: 'Ago', 9: 'Set', 10: 'Out', 11: 'Nov', 12: 'Dez'}
                        # Get all dates that will be shown and create custom labels
                        if not df_pocos.empty:
                            all_dates = pd.date_range(start=df_pocos['Data'].min(), end=df_pocos['Data'].max(), freq='7D')
                            xaxis_config['tickmode'] = 'array'
                            xaxis_config['tickvals'] = all_dates.tolist()
                            xaxis_config['ticktext'] = [f"{month_map[d.month]} {d.day}" for d in all_dates]
                    
                    # Find peak value for annotation (excluding 'Acumulado')
                    if not df_pocos.empty:
                        # Ensure we're only working with non-Acumulado data
                        df_pocos_only = df_pocos[df_pocos['Poço'] != 'Acumulado'].copy()
                        if not df_pocos_only.empty:
                            # Calculate total volume per date (sum across all poços)
                            volume_por_data = df_pocos_only.groupby('Data')['Volume Bombeado (m³)'].sum().reset_index()
                            max_idx = volume_por_data['Volume Bombeado (m³)'].idxmax()
                            peak_date = volume_por_data.loc[max_idx, 'Data']
                            peak_value = volume_por_data.loc[max_idx, 'Volume Bombeado (m³)']
                        
                        # Format peak date label in Portuguese
                        month_map = {1: 'Jan', 2: 'Fev', 3: 'Mar', 4: 'Abr', 5: 'Mai', 6: 'Jun',
                                   7: 'Jul', 8: 'Ago', 9: 'Set', 10: 'Out', 11: 'Nov', 12: 'Dez'}
                        peak_label = f"{month_map[peak_date.month]} {peak_date.day}"
                    
                    # Atualiza layout e eixos
                    fig_dual_bars.update_layout(
                        title='Volume Bombeado por Poço e Volume Acumulado (Barras)',
                        hovermode='x unified',
                        template='plotly_white',
                        barmode='group',  # Dodged bars, not stacked
                        legend=dict(
                            orientation='h',
                            yanchor='top',
                            y=-0.2,
                            xanchor='center',
                            x=0.5,
                            font=dict(size=14)
                        ),
                        font=dict(size=14),
                        title_font=dict(size=16)
                    )
                    
                    xaxis_config['title_font'] = dict(size=16)
                    xaxis_config['tickfont'] = dict(size=14)
                    fig_dual_bars.update_xaxes(**xaxis_config)
                    
                    fig_dual_bars.update_yaxes(
                        title_text='Volume Bombeado (m³)',
                        secondary_y=False,
                        rangemode='tozero',
                        showgrid=True,
                        zeroline=True,
                        title_font=dict(size=16),
                        tickfont=dict(size=14)
                    )
                    fig_dual_bars.update_yaxes(
                        title_text='Volume Acumulado (m³)',
                        secondary_y=True,
                        rangemode='tozero',
                        showgrid=False,
                        zeroline=False,
                        showline=False,
                        ticks='',
                        title_font=dict(size=16),
                        tickfont=dict(size=14)
                    )
                    
                    # Add annotation for peak value
                    if not df_pocos.empty:
                        df_pocos_only = df_pocos[df_pocos['Poço'] != 'Acumulado'].copy()
                        if not df_pocos_only.empty:
                            # Calculate annotation position
                            # Find the date with highest sum, then position at 10% above the highest individual poço on that date
                            y_max_on_peak_date = df_pocos_only[df_pocos_only['Data'] == peak_date]['Volume Bombeado (m³)'].max()
                            annotation_y = y_max_on_peak_date * 1.25  # 10% above the highest bar on that date
                            
                            fig_dual_bars.add_annotation(
                                x=peak_date,
                                y=annotation_y,
                                text=f"Pico de bombeamento<br>{peak_value:.1f} m³",
                                #showarrow=True,
                                #arrowhead=2,
                                #arrowsize=1,
                                #arrowwidth=2,
                                #arrowcolor="#333",
                                ax=0,
                                ay=0,
                                bgcolor="rgba(255, 255, 255, 0.8)",
                                bordercolor="#333",
                                borderwidth=1,
                                borderpad=4,
                                font=dict(size=12, color="#333")
                            )
                    
                    figuras.append(fig_dual_bars)
            
            if 'Volume Poço Temporal' in colunas_escolher:
                # Gráfico com Poço no eixo X e Data como cor
                df_work = df_volume[df_volume['Poço'].isin(pocos_escolhidos)].copy()
                
                if not df_work.empty:
                    # Calculate statistics per poço for hover tooltip
                    stats_per_poco = df_work.groupby('Poço')['Volume Bombeado (m³)'].agg([
                        ('mean', 'mean'),
                        ('std', 'std'),
                        ('min', 'min'),
                        ('max', 'max')
                    ]).round(2)
                    
                    # Convert dates to string for discrete coloring
                    df_work['Data_str'] = df_work['Data'].dt.strftime('%Y-%m-%d')
                    
                    fig_poco_temporal = px.bar(
                        df_work,
                        x='Poço',
                        y='Volume Bombeado (m³)',
                        color='Data_str',
                        title='Volume Bombeado por Poço (Temporal)',
                        labels={'Data_str': 'Data'},
                        barmode='group'
                    )
                    
                    # Create invisible scatter trace for unified hover on each poço
                    for poco in pocos_escolhidos:
                        if poco in stats_per_poco.index:
                            stats = stats_per_poco.loc[poco]
                            hover_text = (f"<b>{poco}</b><br>" +
                                        f"Média: {stats['mean']:.2f} m³<br>" +
                                        f"Desvio Padrão: {stats['std']:.2f} m³<br>" +
                                        f"Min: {stats['min']:.2f} m³<br>" +
                                        f"Max: {stats['max']:.2f} m³")
                            
                            fig_poco_temporal.add_trace(
                                go.Scatter(
                                    x=[poco],
                                    y=[stats['max']],
                                    mode='markers',
                                    marker=dict(size=0.1, opacity=0),
                                    hovertemplate=hover_text + '<extra></extra>',
                                    showlegend=False,
                                    hoverinfo='text'
                                )
                            )
                    
                    # Remove hover from bars
                    fig_poco_temporal.update_traces(
                        hovertemplate=None,
                        hoverinfo='skip',
                        selector=dict(type='bar')
                    )
                    
                    fig_poco_temporal.update_layout(
                        hovermode='x',
                        template='plotly_white',
                        showlegend=False,  # Remove legend
                        font=dict(size=14),
                        title_font=dict(size=16),
                        xaxis=dict(
                            title_font=dict(size=16),
                            tickfont=dict(size=14)
                        ),
                        yaxis=dict(
                            title_font=dict(size=16),
                            tickfont=dict(size=14)
                        )
                    )
                    
                    figuras.append(fig_poco_temporal)
            
            if 'Boxplot Volume por Data' in colunas_escolher:
                # Boxplot com Data no eixo X e Volume por poço
                df_work = df_volume[df_volume['Poço'].isin(pocos_escolhidos)].copy()
                
                if not df_work.empty:
                    # Format dates for display
                    df_work['Data_str'] = df_work['Data'].dt.strftime('%Y-%m-%d')
                    
                    fig_boxplot = px.box(
                        df_work,
                        x='Data_str',
                        y='Volume Bombeado (m³)',
                        title='Distribuição de Volume Bombeado por Data',
                        labels={'Data_str': 'Data'}
                    )
                    
                    fig_boxplot.update_layout(
                        hovermode='x unified',
                        template='plotly_white',
                        font=dict(size=14),
                        title_font=dict(size=16),
                        xaxis=dict(
                            title_font=dict(size=16),
                            tickfont=dict(size=12),
                            tickangle=-45
                        ),
                        yaxis=dict(
                            title_font=dict(size=16),
                            tickfont=dict(size=14)
                        ),
                        margin=dict(b=100)
                    )
                    
                    figuras.append(fig_boxplot)

            n_figs = len(figuras)
            if n_figs == 1:
                st.plotly_chart(figuras[0], use_container_width=True, key="single_bomb_chart")
            elif n_figs == 2:
                col1, col2 = st.columns(2)
                col1.plotly_chart(figuras[0], use_container_width=True, key="bomb_chart_1")
                col2.plotly_chart(figuras[1], use_container_width=True, key="bomb_chart_2")
            elif n_figs == 3:
                col1, col2 = st.columns(2)
                col1.plotly_chart(figuras[0], use_container_width=True, key="bomb_chart_1")
                col2.plotly_chart(figuras[1], use_container_width=True, key="bomb_chart_2")
                st.plotly_chart(figuras[2], use_container_width=True, key="bomb_chart_3")
            else:
                # Para mais gráficos, exibir em pares
                for i in range(0, n_figs, 2):
                    if i + 1 < n_figs:
                        col1, col2 = st.columns(2)
                        col1.plotly_chart(figuras[i], use_container_width=True, key=f"bomb_chart_{i}")
                        col2.plotly_chart(figuras[i+1], use_container_width=True, key=f"bomb_chart_{i+1}")
                    else:
                        st.plotly_chart(figuras[i], use_container_width=True, key=f"bomb_chart_{i}")

            if figuras:
                btn_download_multiple(figuras)

        # --------- CARDS DE ESTATÍSTICAS DESCRITIVAS ---------
        st.write("---")
        st.write("### Estatísticas Descritivas")
        
        # Filtrar dados pelos poços selecionados
        df_stats_filtered = df_volume[df_volume['Poço'].isin(pocos_escolhidos)].copy()
        
        if not df_stats_filtered.empty:
            # Média de Volume Bombeado por período
            periodo_label = {"day": "dia", "week": "semana", "month": "mês"}[agrupamento_temporal]
            media_volume = df_stats_filtered['Volume Bombeado (m³)'].mean()
            
            # Poço com maior leitura total
            volume_por_poco = df_stats_filtered.groupby('Poço')['Volume Bombeado (m³)'].sum()
            poco_max = volume_por_poco.idxmax()
            volume_max = volume_por_poco.max()
            
            # Poço com menor leitura total
            poco_min = volume_por_poco.idxmin()
            volume_min = volume_por_poco.min()
            
            # Exibir cards
            k1, k2, k3 = st.columns(3)
            with k1:
                card("Média por " + periodo_label.capitalize(), f"{media_volume:.2f} m³", "📊", color="#4A90E2")
            with k2:
                card("Poço com Maior Volume", f"{poco_max}: {volume_max:.2f} m³", "⬆️", color="#2EE43D")
            with k3:
                card("Poço com Menor Volume", f"{poco_min}: {volume_min:.2f} m³", "⬇️", color="#FF6B6B")

        # --------- TABELA DE ESTATÍSTICAS POR POÇO ---------
        st.write("---")
        st.write("### Estatísticas por Poço")
        
        # Filtrar dados pelos poços selecionados (excluindo 'Acumulado')
        df_table_filtered = df_volume[df_volume['Poço'].isin(pocos_escolhidos)].copy()
        
        if not df_table_filtered.empty:
            # Calcular estatísticas gerais (todos os poços selecionados juntos)
            stats_geral = {
                'Poço': 'Geral',
                'Média': df_table_filtered['Volume Bombeado (m³)'].mean(),
                'Desvio-Padrão': df_table_filtered['Volume Bombeado (m³)'].std(),
                'Mínimo': df_table_filtered['Volume Bombeado (m³)'].min(),
                'Mediana': df_table_filtered['Volume Bombeado (m³)'].median(),
                'Máximo': df_table_filtered['Volume Bombeado (m³)'].max()
            }
            
            # Calcular estatísticas por poço
            stats_per_poco = df_table_filtered.groupby('Poço')['Volume Bombeado (m³)'].agg([
                ('Média', 'mean'),
                ('Desvio-Padrão', 'std'),
                ('Mínimo', 'min'),
                ('Mediana', 'median'),
                ('Máximo', 'max')
            ]).reset_index()
            
            # Criar DataFrame combinado (Geral + individual)
            df_stats_table = pd.concat([
                pd.DataFrame([stats_geral]),
                stats_per_poco
            ], ignore_index=True)
            
            # Arredondar valores para 2 casas decimais
            numeric_columns = ['Média', 'Desvio-Padrão', 'Mínimo', 'Mediana', 'Máximo']
            df_stats_table[numeric_columns] = df_stats_table[numeric_columns].round(2)
            
            # Aplicar estilo à tabela
            st.dataframe(
                df_stats_table,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Poço": st.column_config.TextColumn("Poço", width="medium"),
                    "Média": st.column_config.NumberColumn("Média (m³)", format="%.2f"),
                    "Desvio-Padrão": st.column_config.NumberColumn("Desvio-Padrão (m³)", format="%.2f"),
                    "Mínimo": st.column_config.NumberColumn("Mínimo (m³)", format="%.2f"),
                    "Mediana": st.column_config.NumberColumn("Mediana (m³)", format="%.2f"),
                    "Máximo": st.column_config.NumberColumn("Máximo (m³)", format="%.2f")
                }
            )
            
            # Botão para download em Excel
            btn_download_excel(df_stats_table, "estatisticas_volume_bombeado.xlsx")

else:
    # Mensagem de barreira quando não há dados carregados
    st.info("📁 Faça o upload dos dados para começar!")
    st.markdown("""
        <div style="
            text-align: center;
            padding: 60px 20px;
            color: #666;
        ">
            <p style="font-size: 18px; margin-bottom: 10px;">
                Por favor, utilize o menu lateral para fazer upload do arquivo Excel com os dados.
            </p>
            <p style="font-size: 14px; color: #999;">
                O arquivo deve conter as planilhas: "Volume Bombeado" e "Volume Infiltrado"
            </p>
        </div>
    """, unsafe_allow_html=True)