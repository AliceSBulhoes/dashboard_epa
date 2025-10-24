import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go


def group_data_by_period(df, x_col, y_cols, grouping="day", group_by_col=None):
    """
    Agrupa dados por período temporal (dia, semana, mês).
    
    Args:
        df: DataFrame com os dados
        x_col: nome da coluna de data
        y_cols: lista de colunas numéricas para agrupar
        grouping: 'day', 'week' ou 'month'
        group_by_col: coluna adicional para agrupar (ex: 'Poço', 'Ponto')
    
    Returns:
        DataFrame agrupado
    """
    if grouping == "day" or len(df) == 0:
        return df.copy()
    
    df_copy = df.copy()
    df_copy[x_col] = pd.to_datetime(df_copy[x_col])
    
    # Definir a frequência de agrupamento
    freq_map = {
        "week": "W",
        "month": "M"
    }
    freq = freq_map.get(grouping, "D")
    
    # Se temos uma coluna de agrupamento adicional (ex: Poço)
    if group_by_col and group_by_col in df_copy.columns:
        # Separar dados de 'Acumulado' e outros
        df_acumulado = df_copy[df_copy[group_by_col] == 'Acumulado'].copy()
        df_outros = df_copy[df_copy[group_by_col] != 'Acumulado'].copy()
        
        # Para dados normais (não acumulado): somar
        agg_dict_sum = {}
        for col in y_cols:
            if col in df_outros.columns:
                agg_dict_sum[col] = 'sum'
        
        if not df_outros.empty:
            df_grouped_outros = df_outros.set_index(x_col).groupby([pd.Grouper(freq=freq), group_by_col]).agg(agg_dict_sum).reset_index()
        else:
            df_grouped_outros = pd.DataFrame()
        
        # Para dados de 'Acumulado': pegar último valor do período (já é acumulado)
        if not df_acumulado.empty:
            # Para cada período, pegar a última data (valor mais recente/máximo)
            df_acumulado_sorted = df_acumulado.sort_values(by=x_col)
            df_grouped_acum = df_acumulado_sorted.set_index(x_col).groupby([pd.Grouper(freq=freq), group_by_col]).last().reset_index()
        else:
            df_grouped_acum = pd.DataFrame()
        
        # Combinar os dois DataFrames
        if not df_grouped_outros.empty and not df_grouped_acum.empty:
            df_grouped = pd.concat([df_grouped_outros, df_grouped_acum], ignore_index=True)
        elif not df_grouped_outros.empty:
            df_grouped = df_grouped_outros
        elif not df_grouped_acum.empty:
            df_grouped = df_grouped_acum
        else:
            df_grouped = pd.DataFrame()
    else:
        # Preparar dicionário de agregação
        agg_dict = {}
        for col in y_cols:
            if col in df_copy.columns:
                agg_dict[col] = 'sum'
        
        # Copiar outras colunas não-numéricas (mantém a primeira ocorrência)
        for col in df_copy.columns:
            if col != x_col and col not in y_cols:
                if df_copy[col].dtype == 'object' or df_copy[col].dtype == 'category':
                    agg_dict[col] = 'first'
        
        # Agrupar apenas por período
        df_grouped = df_copy.set_index(x_col).groupby(pd.Grouper(freq=freq)).agg(agg_dict).reset_index()
    
    # Remover períodos sem dados (todos os valores numéricos são 0 ou NaN)
    numeric_cols = [col for col in y_cols if col in df_grouped.columns]
    if numeric_cols:
        # Manter apenas linhas onde pelo menos uma coluna numérica tem valor > 0
        mask = df_grouped[numeric_cols].sum(axis=1) > 0
        df_grouped = df_grouped[mask].copy()
    
    return df_grouped

def create_dual_y_axis_chart(df, x_col, y_col, title_prefix,
                             color_primary="#156082", color_secondary="#c44d15",
                             num_ticks=5, pad_rel=0.08, clip_markers=False,
                             grouping="day"):
    df_sorted = df.sort_values(by=x_col).copy()

    # Remove zeros iniciais até o primeiro valor não-zero
    if len(df_sorted) > 0:
        first_nonzero_idx = None
        for idx, value in enumerate(df_sorted[y_col]):
            if value != 0:
                first_nonzero_idx = idx
                break
        if first_nonzero_idx is not None and first_nonzero_idx > 0:
            df_sorted = df_sorted.iloc[first_nonzero_idx:].copy()

    # Aplicar agrupamento temporal se necessário
    if grouping != "day":
        df_sorted = group_data_by_period(df_sorted, x_col, [y_col], grouping)

    # Acumulado
    df_sorted[f'{y_col}_Acumulado'] = df_sorted[y_col].cumsum()

    # Valores originais
    y1_min = float(df_sorted[y_col].min()) if len(df_sorted) else 0.0
    y1_max = float(df_sorted[y_col].max()) if len(df_sorted) else 1.0
    y2_min = float(df_sorted[f'{y_col}_Acumulado'].min()) if len(df_sorted) else 0.0
    y2_max = float(df_sorted[f'{y_col}_Acumulado'].max()) if len(df_sorted) else 1.0

    # Evita divisão por zero criando small range se necessário
    if y1_max == y1_min:
        y1_max = y1_min + 1.0
    if y2_max == y2_min:
        y2_max = y2_min + 1.0

    # Padding relativo. Garante que pontos não fiquem tocando o limite. Eles estavam colados ao topo do plot antes.
    span1 = y1_max - y1_min
    span2 = y2_max - y2_min
    pad1 = span1 * pad_rel
    pad2 = span2 * pad_rel

    y1_low = y1_min - pad1
    y1_high = y1_max + pad1
    y2_low = y2_min - pad2
    y2_high = y2_max + pad2

    # Transformação linear usando os ranges PADed, assim ticks alinham-se visualmente
    def transform_y_to_y2(y):
        return y2_low + (y - y1_low) * (y2_high - y2_low) / (y1_high - y1_low)

    # Gera posições de ticks e formata textos
    left_tickvals = np.linspace(y1_low, y1_high, num_ticks)
    right_tickvals = [transform_y_to_y2(v) for v in left_tickvals]

    # Formatação dos textos
    # left como com 2 decimais somente se necessário
    def fmt_left(v):
        if abs(v) >= 1000:
            return f"{int(round(v)):,}"
        if abs(v - round(v)) < 1e-6:
            return str(int(round(v)))
        return f"{round(v, 2)}"
    left_ticktext = [fmt_left(v) for v in left_tickvals]
    right_ticktext = [f"{int(round(v)):,}" for v in right_tickvals]

    # Criar figura
    fig = px.bar(
        df_sorted,
        x=x_col,
        y=y_col,
        title=f'{title_prefix} - Valores Individuais vs Acumulados',
        color_discrete_sequence=[color_primary]
    )

    # Adiciona a trace acumulada
    scatter_kwargs = dict(mode='lines+markers', name=f'{title_prefix} Acumulado',
                          yaxis="y2", line=dict(color=color_secondary, width=3), marker=dict(size=6))
    if clip_markers:
        scatter_kwargs['cliponaxis'] = False

    fig.add_trace(go.Scatter(
        x=df_sorted[x_col],
        y=df_sorted[f'{y_col}_Acumulado'],
        **scatter_kwargs
    ))

    # Forçar ranges e ticks
    fig.update_yaxes(range=[y1_low, y1_high], title=f"{title_prefix} (Individual)", secondary_y=False,
                     tickmode="array", tickvals=left_tickvals, ticktext=left_ticktext)

    fig.update_layout(
        yaxis2=dict(
            title=f"{title_prefix} (Acumulado)",
            overlaying="y",
            side="right",
            showgrid=False,
            tickmode="array",
            tickvals=right_tickvals,
            ticktext=right_ticktext,
            range=[y2_low, y2_high]
        ),
        dragmode='zoom',
        xaxis_tickangle=-45,
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.3,
            xanchor="center",
            x=0.5,
            title_text='Séries'
        ),
        hovermode='x unified',
        margin=dict(b=100)
    )

    # renomear primeira trace
    fig.data[0].name = f'{title_prefix} Individual'

    return fig


def create_poco_dual_y_axis_chart(df, title_prefix="Volume Bombeado por Poço",
                                  color_palette=None, num_ticks=5, pad_rel=0.08, 
                                  clip_markers=False, grouping="day"):
    """
    Cria gráfico com duplo eixo Y para dados de poços.
    
    Args:
        df: DataFrame com colunas 'Data', 'Poço', 'Volume Bombeado (m³)'
        title_prefix: Prefixo do título do gráfico
        color_palette: Lista de cores para diferentes poços
        num_ticks: Número de ticks nos eixos Y
        pad_rel: Padding relativo para os eixos Y
        clip_markers: Se True, permite marcadores fora da área do plot
        grouping: Agrupamento temporal ('day', 'week', 'month')
    
    Returns:
        Figura plotly com duplo eixo Y
    """
    if df.empty:
        return go.Figure()
    
    df_work = df.copy()
    df_work['Data'] = pd.to_datetime(df_work['Data'])
    
    # Converter 0 para NaN para não plotar barras vazias
    df_work.loc[df_work['Volume Bombeado (m³)'] == 0, 'Volume Bombeado (m³)'] = np.nan
    
    # Separar dados de poços individuais e acumulado
    df_pocos = df_work[df_work['Poço'] != 'Acumulado'].copy()
    df_acumulado = df_work[df_work['Poço'] == 'Acumulado'].copy()
    
    # Aplicar agrupamento temporal se necessário
    if grouping != "day":
        if not df_pocos.empty:
            df_pocos = group_data_by_period(df_pocos, 'Data', ['Volume Bombeado (m³)'], grouping)
        if not df_acumulado.empty:
            df_acumulado = group_data_by_period(df_acumulado, 'Data', ['Volume Bombeado (m³)'], grouping)
    
    # Ordenar por data
    df_pocos = df_pocos.sort_values(by='Data')
    df_acumulado = df_acumulado.sort_values(by='Data')
    
    # Definir paleta de cores para poços
    if color_palette is None:
        color_palette = px.colors.qualitative.Set3
    
    # Criar figura
    fig = go.Figure()
    
    # Adicionar barras para cada poço (lado esquerdo)
    if not df_pocos.empty:
        pocos_unicos = df_pocos['Poço'].unique()
        
        for i, poco in enumerate(pocos_unicos):
            df_poco = df_pocos[df_pocos['Poço'] == poco]
            color = color_palette[i % len(color_palette)]
            
            fig.add_trace(go.Bar(
                x=df_poco['Data'],
                y=df_poco['Volume Bombeado (m³)'],
                name=poco,
                marker_color=color,
                yaxis="y",
                offsetgroup=i,  # Para barras lado a lado
                legendgroup="pocos",
                legendgrouptitle_text="Poços Individuais"
            ))
    
    # Adicionar linha para acumulado (lado direito)
    if not df_acumulado.empty:
        fig.add_trace(go.Scatter(
            x=df_acumulado['Data'],
            y=df_acumulado['Volume Bombeado (m³)'],
            mode='lines+markers',
            name='Acumulado',
            line=dict(color='#c44d15', width=3),
            marker=dict(size=6, color='#c44d15'),
            yaxis="y2",
            legendgroup="acumulado",
            legendgrouptitle_text="Volume Acumulado"
        ))
    
    # Calcular ranges para os eixos Y
    y1_values = df_pocos['Volume Bombeado (m³)'].dropna() if not df_pocos.empty else pd.Series([0])
    y2_values = df_acumulado['Volume Bombeado (m³)'].dropna() if not df_acumulado.empty else pd.Series([0])
    
    if len(y1_values) == 0:
        y1_values = pd.Series([0])
    if len(y2_values) == 0:
        y2_values = pd.Series([0])
    
    y1_min, y1_max = float(y1_values.min()), float(y1_values.max())
    y2_min, y2_max = float(y2_values.min()), float(y2_values.max())
    
    # Evitar divisão por zero
    if y1_max == y1_min:
        y1_max = y1_min + 1.0
    if y2_max == y2_min:
        y2_max = y2_min + 1.0
    
    # Aplicar padding
    span1 = y1_max - y1_min
    span2 = y2_max - y2_min
    pad1 = span1 * pad_rel
    pad2 = span2 * pad_rel
    
    y1_low = y1_min - pad1
    y1_high = y1_max + pad1
    y2_low = y2_min - pad2
    y2_high = y2_max + pad2
    
    # Configurar ticks alinhados
    def transform_y_to_y2(y):
        return y2_low + (y - y1_low) * (y2_high - y2_low) / (y1_high - y1_low)
    
    left_tickvals = np.linspace(y1_low, y1_high, num_ticks)
    right_tickvals = [transform_y_to_y2(v) for v in left_tickvals]
    
    # Formatação dos textos dos ticks
    def fmt_tick(v):
        if abs(v) >= 1000:
            return f"{int(round(v)):,}"
        if abs(v - round(v)) < 1e-6:
            return str(int(round(v)))
        return f"{round(v, 2)}"
    
    left_ticktext = [fmt_tick(v) for v in left_tickvals]
    right_ticktext = [fmt_tick(v) for v in right_tickvals]
    
    # Configurar layout
    fig.update_layout(
        title=f'{title_prefix} - Individual vs Acumulado',
        xaxis=dict(title='Data', tickangle=-45),
        yaxis=dict(
            title='Volume Bombeado Individual (m³)',
            range=[y1_low, y1_high],
            tickmode="array",
            tickvals=left_tickvals,
            ticktext=left_ticktext
        ),
        yaxis2=dict(
            title='Volume Bombeado Acumulado (m³)',
            overlaying="y",
            side="right",
            showgrid=False,
            tickmode="array",
            tickvals=right_tickvals,
            ticktext=right_ticktext,
            range=[y2_low, y2_high]
        ),
        barmode='group',  # Barras lado a lado
        dragmode='zoom',
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.3,
            xanchor="center",
            x=0.5,
            title_text='Séries'
        ),
        hovermode='x unified',
        margin=dict(b=100)
    )
    
    return fig
