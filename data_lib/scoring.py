from __future__ import annotations

from typing import Iterable, List

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

from config.settings import RANDOM_STATE



def _minmax(series: pd.Series) -> pd.Series:
    s = series.astype(float)
    min_v, max_v = float(s.min()), float(s.max())
    if max_v - min_v == 0:
        return pd.Series(np.zeros(len(s)), index=s.index)
    return (s - min_v) / (max_v - min_v)



def _robust_z(series: pd.Series) -> pd.Series:
    s = series.astype(float).fillna(series.median())
    median = s.median()
    mad = np.median(np.abs(s - median))
    if mad == 0:
        mad = max(float(s.std()), 1.0)
    return pd.Series(np.abs((s - median) / mad), index=s.index)



def score_transactions(df: pd.DataFrame, numeric_cols: Iterable[str]) -> pd.DataFrame:
    scored = df.copy()
    numeric_cols = [c for c in numeric_cols if c in scored.columns]

    X = scored[numeric_cols].copy()
    X = X.replace([np.inf, -np.inf], np.nan)
    X = X.fillna(X.median(numeric_only=True))

    iso = IsolationForest(
        n_estimators=200,
        contamination='auto',
        random_state=RANDOM_STATE,
        n_jobs=-1,
    )
    iso.fit(X)
    raw_model_score = -iso.score_samples(X)

    amount_component = _minmax(_robust_z(scored['TransactionAmt']))
    model_component = _minmax(pd.Series(raw_model_score, index=scored.index))

    v_cols = [c for c in scored.columns if c.startswith('V')]
    if v_cols:
        feature_extreme = scored[v_cols].abs().mean(axis=1)
    else:
        feature_extreme = pd.Series(np.zeros(len(scored)), index=scored.index)
    feature_component = _minmax(feature_extreme.fillna(feature_extreme.median()))

    card1_freq = scored['card1'].fillna(-1).map(scored['card1'].fillna(-1).value_counts(normalize=True)) if 'card1' in scored.columns else 0
    email_mismatch = (
        (scored['P_emaildomain'].fillna('missing') != scored['R_emaildomain'].fillna('missing')).astype(int)
        if {'P_emaildomain', 'R_emaildomain'}.issubset(scored.columns)
        else pd.Series(np.zeros(len(scored)), index=scored.index)
    )
    rarity_component = _minmax((1 - pd.Series(card1_freq, index=scored.index).fillna(0)) + email_mismatch)

    scored['model_component'] = model_component
    scored['amount_component'] = amount_component
    scored['feature_component'] = feature_component
    scored['rarity_component'] = rarity_component

    scored['risk_score'] = (
        0.45 * scored['model_component']
        + 0.25 * scored['amount_component']
        + 0.20 * scored['feature_component']
        + 0.10 * scored['rarity_component']
    ) * 100
    scored['risk_score'] = scored['risk_score'].clip(0, 100).round(2)

    bins = [-0.01, 25, 50, 75, 100]
    labels = ['Low Risk', 'Moderate Risk', 'High Risk', 'Critical Risk']
    scored['risk_level'] = pd.cut(scored['risk_score'], bins=bins, labels=labels)
    scored['risk_level'] = scored['risk_level'].astype(str)
    scored['is_high_risk'] = scored['risk_score'] >= 50
    scored['is_critical_risk'] = scored['risk_score'] >= 75
    return scored
