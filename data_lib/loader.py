from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Tuple

import pandas as pd

from config.settings import (
    IDENTITY_NULL_THRESHOLD,
    MAX_IDENTITY_CATEGORICAL_UNIQUES,
    MAX_ROWS_DEFAULT,
    REFERENCE_START_DATE,
    TRAIN_IDENTITY,
    TRAIN_TRANSACTION,
)


NUMERIC_BASE = ['TransactionAmt', 'dist1', 'dist2']
CATEGORICAL_BASE = [
    'ProductCD', 'card4', 'card6', 'P_emaildomain', 'R_emaildomain', 'DeviceType', 'DeviceInfo'
]


class DataNotFoundError(FileNotFoundError):
    pass



def _validate_input_files() -> None:
    missing = [str(p) for p in [TRAIN_TRANSACTION, TRAIN_IDENTITY] if not Path(p).exists()]
    if missing:
        raise DataNotFoundError(
            'Required CSV files were not found. Expected files:\n'
            f'- {TRAIN_TRANSACTION}\n'
            f'- {TRAIN_IDENTITY}\n\n'
            'Download the IEEE-CIS Fraud Detection competition files from Kaggle and place the training CSVs in the data/ folder.'
        )



def _pick_identity_columns(identity_df: pd.DataFrame) -> List[str]:
    keep = ['TransactionID']
    for col in identity_df.columns:
        if col == 'TransactionID':
            continue
        null_ratio = identity_df[col].isna().mean()
        nunique = identity_df[col].nunique(dropna=True)
        if null_ratio <= IDENTITY_NULL_THRESHOLD:
            if identity_df[col].dtype == 'object':
                if nunique <= MAX_IDENTITY_CATEGORICAL_UNIQUES or col in ['DeviceType', 'DeviceInfo']:
                    keep.append(col)
            else:
                keep.append(col)
    return keep



def load_base_data(max_rows: int | None = MAX_ROWS_DEFAULT) -> Tuple[pd.DataFrame, Dict[str, List[str]]]:
    _validate_input_files()

    txn = pd.read_csv(TRAIN_TRANSACTION, nrows=max_rows)
    identity = pd.read_csv(TRAIN_IDENTITY, nrows=max_rows)

    keep_identity_cols = _pick_identity_columns(identity)
    identity = identity[keep_identity_cols]

    df = txn.merge(identity, on='TransactionID', how='left')
    df['TransactionDate'] = pd.to_datetime(REFERENCE_START_DATE) + pd.to_timedelta(df['TransactionDT'], unit='s')
    df['TransactionDay'] = df['TransactionDate'].dt.floor('D')
    df['isFraudLabel'] = df['isFraud'].map({0: 'Normal', 1: 'Fraud'})

    feature_cols = [c for c in df.columns if c.startswith('V')]
    identity_numeric = [c for c in df.columns if c.startswith('id_') and pd.api.types.is_numeric_dtype(df[c])]
    identity_categorical = [c for c in df.columns if c.startswith('id_') and not pd.api.types.is_numeric_dtype(df[c])]
    selected_numeric = [c for c in NUMERIC_BASE + feature_cols[:20] + identity_numeric[:10] if c in df.columns]
    selected_categorical = [c for c in CATEGORICAL_BASE + identity_categorical[:10] if c in df.columns]

    metadata = {
        'feature_cols': feature_cols,
        'model_numeric_cols': selected_numeric,
        'categorical_cols': selected_categorical,
    }
    return df, metadata
