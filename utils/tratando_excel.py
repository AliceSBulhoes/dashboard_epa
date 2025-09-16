import pandas as pd

def tratando_df(df):
    """Função para tratar DataFrame."""
    df.drop(columns=[col for col in df.columns if "Unnamed" in col], inplace=True)
    df = df[df['Data'].notna()]
    df.reset_index(drop=True, inplace=True)
    return df