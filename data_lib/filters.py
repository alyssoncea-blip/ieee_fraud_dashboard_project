from __future__ import annotations

import pandas as pd



def apply_filters(
    df: pd.DataFrame,
    start_date=None,
    end_date=None,
    amount_range=None,
    risk_levels=None,
    fraud_only: bool = False,
    high_risk_only: bool = False,
    product_codes=None,
):
    filtered = df.copy()

    if start_date is not None:
        filtered = filtered[filtered['TransactionDate'] >= pd.to_datetime(start_date)]
    if end_date is not None:
        filtered = filtered[filtered['TransactionDate'] <= pd.to_datetime(end_date) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)]
    if amount_range and len(amount_range) == 2:
        filtered = filtered[filtered['TransactionAmt'].between(amount_range[0], amount_range[1])]
    if risk_levels:
        filtered = filtered[filtered['risk_level'].isin(risk_levels)]
    if fraud_only:
        filtered = filtered[filtered['isFraud'] == 1]
    if high_risk_only:
        filtered = filtered[filtered['risk_score'] >= 50]
    if product_codes:
        filtered = filtered[filtered['ProductCD'].isin(product_codes)]

    return filtered
