import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go


def group_data_by_period(df, x_col, y_cols, grouping="day"):
    """
    Agrupa dados por período temporal (dia, semana, mês).
    
    Args:
        df: DataFrame com os dados
        x_col: nome da coluna de data
        y_cols: lista de colunas numéricas para agrupar
        grouping: 'day', 'week' ou 'month'
    
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
    
    # Agrupar por período
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
