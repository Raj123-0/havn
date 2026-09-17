from __future__ import annotations
"""Module for mathematical computation and analysis."""



from scipy import stats
from statsmodels.tsa.stattools import ccf
import numpy as np
import pandas as pd


def fetch_daily_series(conn, source: str, name: str, is_metric: bool = True):
    """Retrieve daily series.
    
    Args:
        conn:
        source:
        name:
        is_metric (bool):
    
    Returns:
        The computed result
    
    """
    if is_metric:
        query = "SELECT date, avg_value as value FROM daily_metrics WHERE source = ? AND metric_name = ? ORDER BY date"
    else:
        query = "SELECT date, CAST(event_count AS DOUBLE) as value FROM daily_events WHERE source = ? AND type = ? ORDER BY date"
        
    df = conn.execute(query, (source, name)).fetchdf()
    if not df.empty:
        df['date'] = pd.to_datetime(df['date'])
        # Set date as index and resample to daily to ensure continuous time series
        df = df.set_index('date').resample('D').mean().fillna(0)
    return df


def analyze_correlation(df1, df2) -> dict:
    """
    Analyzes the correlation between two aligned pandas DataFrames.
    Both must have a 'value' column and a DatetimeIndex.
    """
    merged = pd.merge(df1, df2, left_index=True, right_index=True, suffixes=('_x', '_y'), how='inner')
    if len(merged) < 10:
        return {"error": "Not enough overlapping data points (minimum 10 required)."}
        
    x = merged['value_x'].values
    y = merged['value_y'].values
    
    # If one of the series is constant, correlation is undefined
    if np.std(x) == 0 or np.std(y) == 0:
        return {"error": "One of the data series has zero variance (constant value)."}
    
    # 1. Pearson Correlation
    pearson_r, p_value_p = stats.pearsonr(x, y)
    
    # 2. Spearman Correlation (rank-based, robust to outliers)
    spearman_r, p_value_s = stats.spearmanr(x, y)
    
    # 3. Lagged Correlation (Cross-correlation)
    # Does x predict y? (x leads y) -> ccf(y, x)
    # Does y predict x? (y leads x) -> ccf(x, y)
    nlags = min(14, len(merged) // 2)
    
    ccf_xy = ccf(x, y, adjusted=False)[:nlags+1] # y leads x
    ccf_yx = ccf(y, x, adjusted=False)[:nlags+1] # x leads y
    
    # Find the max absolute correlation across all valid lags
    best_lag_x_leads_y = int(np.argmax(np.abs(ccf_yx)))
    best_r_x_leads_y = float(ccf_yx[best_lag_x_leads_y])
    
    best_lag_y_leads_x = int(np.argmax(np.abs(ccf_xy)))
    best_r_y_leads_x = float(ccf_xy[best_lag_y_leads_x])
    
    if abs(best_r_x_leads_y) > abs(best_r_y_leads_x):
        lagged_result = {"direction": "x_leads_y", "lag_days": best_lag_x_leads_y, "r": best_r_x_leads_y}
    else:
        lagged_result = {"direction": "y_leads_x", "lag_days": best_lag_y_leads_x, "r": best_r_y_leads_x}

    # 4. Changepoint Detection (Simple Rolling Mean Shift)
    # Find the day where the absolute difference in 7-day rolling mean is maximized for both series simultaneously
    roll_x = merged['value_x'].rolling(7).mean()
    roll_y = merged['value_y'].rolling(7).mean()
    
    diff_x = np.abs(roll_x.diff())
    diff_y = np.abs(roll_y.diff())
    
    # Normalize differences to combine them
    if diff_x.max() > 0 and diff_y.max() > 0:
        norm_diff_x = diff_x / diff_x.max()
        norm_diff_y = diff_y / diff_y.max()
        combined_shift = norm_diff_x + norm_diff_y
        best_shift_idx = combined_shift.idxmax()
        changepoint = str(best_shift_idx.date()) if pd.notna(best_shift_idx) else None
    else:
        changepoint = None

    return {
        "pearson": {"r": float(pearson_r), "p_value": float(p_value_p)},
        "spearman": {"r": float(spearman_r), "p_value": float(p_value_s)},
        "lagged": lagged_result,
        "changepoint": changepoint,
        "data_points": len(merged),
        "caveat": "Correlation does not imply causation. A strong relationship might be due to a hidden confounder or coincidental trends."
    }
