import pandas as pd
from typing import Dict, List, Optional


def ensure_datetime(df: pd.DataFrame, date_col: str) -> pd.DataFrame:
    """Ensure the date column is in pandas datetime64[ns] without timezone."""
    if not pd.api.types.is_datetime64_any_dtype(df[date_col]):
        df = df.copy()
        df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
    return df


def clamp_date_range(
    df: pd.DataFrame, date_col: str, start, end
) -> pd.DataFrame:
    """
    Filter by inclusive [start, end] date range safely.
    Accepts datetime/date/str for start/end.
    """
    df = ensure_datetime(df, date_col)
    if start is not None:
        start = pd.to_datetime(start)
    if end is not None:
        # Make end inclusive up to the end of the day
        end = pd.to_datetime(end)
    mask = True
    if start is not None:
        mask = mask & (df[date_col] >= start)
    if end is not None:
        mask = mask & (df[date_col] <= end)
    return df.loc[mask]


def granularity_to_freq(granularity: str) -> str:
    """Map PT labels to pandas frequency strings."""
    g = granularity.strip().lower()
    if g.startswith("di"):  # Diário
        return "D"
    if g.startswith("se"):  # Semanal (ISO week starting Monday)
        return "W-MON"
    if g.startswith("me"):  # Mensal
        return "MS"  # Month start; keeps labels aligned to first day
    if g.startswith("an") or g.startswith("anu"):  # Anual
        return "YS"  # Year start
    # default to daily
    return "D"


def aggregate_by_period(
    df: pd.DataFrame,
    date_col: str,
    freq: str,
    agg_map: Dict[str, str],
    group_keys: Optional[List[str]] = None,
) -> pd.DataFrame:
    """
    Aggregate a dataframe by time period using pd.Grouper.

    - df: input dataframe (unmodified)
    - date_col: name of the datetime column
    - freq: pandas frequency string (e.g., 'D', 'W-MON', 'MS', 'YS')
    - agg_map: mapping of column -> aggregation function ('sum', 'mean', etc.)
    - group_keys: additional keys to group by (e.g., ['Poço'])
    """
    if group_keys is None:
        group_keys = []
    df = ensure_datetime(df, date_col)
    # Build grouping keys
    grouper = [pd.Grouper(key=date_col, freq=freq)]
    group_cols = group_keys + grouper
    grouped = df.groupby(group_cols, dropna=False).agg(agg_map).reset_index()
    # Optional: sort for better plotting/cumsum
    grouped = grouped.sort_values(group_keys + [date_col])
    return grouped


def add_cumulative(
    df: pd.DataFrame, date_col: str, value_cols: List[str], new_col: str
) -> pd.DataFrame:
    """
    Add a cumulative sum column from a list of columns summed row-wise, ordered by date.
    """
    df = df.copy()
    df[value_cols] = df[value_cols].fillna(0)
    df[new_col] = df[value_cols].sum(axis=1)
    df = df.sort_values(date_col)
    df[new_col] = df[new_col].cumsum()
    return df


def full_period_index(start, end, freq: str) -> pd.DatetimeIndex:
    """
    Build a continuous DatetimeIndex between start and end inclusive with the given frequency.
    Ensures we cover the entire selected range for plotting/aggregation continuity.
    """
    s = pd.to_datetime(start)
    e = pd.to_datetime(end)
    # Ensure end is inclusive; for freq-based ranges, date_range includes end if aligned
    idx = pd.date_range(s, e, freq=freq)
    # If range produces no points due to misalignment (rare), include end
    if len(idx) == 0:
        idx = pd.DatetimeIndex([s, e])
    return idx
