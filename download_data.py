"""Helper script for downloading the competition files after you have accepted the Kaggle competition rules.

Usage:
1) Install the Kaggle API and configure kaggle.json.
2) Run: python download_data.py
"""

from pathlib import Path
import subprocess
import sys

DATA_DIR = Path(__file__).resolve().parent / 'data'
DATA_DIR.mkdir(exist_ok=True)

cmd = [
    sys.executable,
    '-m',
    'kaggle',
    'competitions',
    'download',
    '-c',
    'ieee-fraud-detection',
    '-p',
    str(DATA_DIR),
]

print('Running:', ' '.join(cmd))
subprocess.run(cmd, check=True)
print('\nDownload complete. Unzip the archive into the data/ folder so train_transaction.csv and train_identity.csv are available.')
