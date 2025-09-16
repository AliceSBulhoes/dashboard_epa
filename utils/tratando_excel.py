import pandas as pd

def tratando_df(df):
    """Função para tratar DataFrame."""
    df.drop(columns=[col for col in df.columns if "Unnamed" in col], inplace=True)
    df = df[df['Data'].notna()]
    df.reset_index(drop=True, inplace=True)
    return df

def fillna_columns(df, columns, value=0):
    """Preenche NaN nas colunas especificadas com o valor dado."""
    for col in columns:
        if col in df.columns:
            df[col] = df[col].fillna(value)
    return df

def add_accumulated_column(df, cols_to_sum, new_col):
    """Adiciona uma coluna acumulada baseada na soma das colunas fornecidas."""
    df[new_col] = df[cols_to_sum].sum(axis=1).cumsum()
    return df

def filter_by_date(df, date_col, start, end):
    """Filtra o DataFrame pelo intervalo de datas."""
    mask = (pd.to_datetime(df[date_col]) >= pd.to_datetime(start)) & (pd.to_datetime(df[date_col]) <= pd.to_datetime(end))
    return df[mask]