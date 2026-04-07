from __future__ import annotations

# ---- Premium color system ----

PAGE_BG = '#070d1a'
PAGE_BG_2 = '#0b1224'
PANEL_BG = 'rgba(15, 23, 42, 0.75)'
CARD_BG = '#111827'
GRID = '#1e293b'
GRID_LIGHT = '#334155'
TEXT = '#f0f4f8'
TEXT_SECONDARY = '#94a3b8'
TEXT_MUTED = '#64748b'
BORDER = '#1e2d42'
BORDER_LIGHT = '#2a3f57'

CYAN = '#22d3ee'
BLUE = '#3b82f6'
YELLOW = '#fbbf24'
ORANGE = '#f97316'
RED = '#ef4444'

# KPI accent colors
ACCENT = '#22d3ee'
ACCENT_WARNING = '#fbbf24'
ACCENT_DANGER = '#f97316'
ACCENT_CRITICAL = '#ef4444'
ACCENT_SUCCESS = '#3b82f6'
ACCENT_PURPLE = '#a78bfa'

# Risk color scale
RISK_COLORS = {
    'Low Risk': '#38bdf8',
    'Moderate Risk': '#fbbf24',
    'High Risk': '#f97316',
    'Critical Risk': '#ef4444',
}

CLASS_COLORS = {
    'Normal': '#3b82f6',
    'Fraud': '#ef4444',
}


def money_fmt(value: float) -> str:
    if value >= 1_000_000:
        return f'${value/1_000_000:,.1f}M'
    if value >= 1_000:
        return f'${value/1_000:,.1f}K'
    return f'${value:,.2f}'


def pct_fmt(value: float) -> str:
    return f'{value:.1f}%'
