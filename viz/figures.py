from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from config import palette as pl

FONT_SCALE = 1.0


def _s(px: float) -> int:
    return max(1, int(round(px * FONT_SCALE)))


def _style(fig, light_theme: bool = False):
    """Apply dark premium theme to any figure, compact margins for 100vh."""
    text = '#0f172a' if light_theme else pl.TEXT
    text_muted = '#475569' if light_theme else pl.TEXT_MUTED
    grid = '#cbd5e1' if light_theme else '#1e293b'
    hover_bg = '#f8fafc' if light_theme else '#111827'
    hover_border = '#cbd5e1' if light_theme else '#2a3f57'

    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family='Inter, -apple-system, sans-serif', color=text, size=_s(10)),
        margin=dict(l=32, r=8, t=12, b=46),
        hoverlabel=dict(
            bgcolor=hover_bg,
            bordercolor=hover_border,
            font_family='Inter, sans-serif',
            font=dict(color=text, size=_s(10)),
        ),
    )
    fig.update_xaxes(
        showgrid=True, gridcolor=grid, zeroline=False, gridwidth=0.5,
        tickfont=dict(family='Inter, sans-serif', size=_s(8), color=text_muted),
    )
    fig.update_yaxes(
        showgrid=True, gridcolor=grid, zeroline=False, gridwidth=0.5,
        tickfont=dict(family='Inter, sans-serif', size=_s(8), color=text_muted),
    )
    return fig


def risk_distribution(df: pd.DataFrame, light_theme: bool = False):
    hist, bins = np.histogram(df['risk_score'], bins=40)
    bin_centers = (bins[:-1] + bins[1:]) / 2
    max_bin = 100
    colors = [_score_color(min(max(c, 0), max_bin)) for c in bin_centers]
    labels = [f'{bins[i]:.0f}' for i in range(len(hist))]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=labels, y=hist,
        marker_color=colors, marker_line_width=0,
        hovertemplate='%{x}<br>Cases: %{y:,}<extra></extra>',
    ))
    fig.update_layout(
        showlegend=False, bargap=0.05,
        xaxis=dict(title='Score', title_standoff=4, tickangle=-60, tickfont=dict(size=_s(7))),
        yaxis=dict(title='Cases', title_font=dict(size=_s(9))),
    )
    return _style(fig, light_theme)


def risk_breakdown(df: pd.DataFrame, light_theme: bool = False):
    text_muted = '#475569' if light_theme else pl.TEXT_MUTED
    order = list(pl.RISK_COLORS.keys())
    counts = df['risk_level'].value_counts().reindex(order, fill_value=0).reset_index()
    counts.columns = ['risk_level', 'count']
    y_max = float(counts['count'].max()) if len(counts) else 0.0
    y_top = max(1.0, y_max * 1.10)

    fig = go.Figure()
    for _, row in counts.iterrows():
        fig.add_trace(go.Bar(
            x=[row['risk_level']], y=[row['count']],
            marker_color=pl.RISK_COLORS[row['risk_level']],
            marker_line_width=0,
            text=[f"{row['count']:,}"],
            textposition='outside',
            cliponaxis=False,
            textfont=dict(family='Inter, sans-serif', size=_s(9), color=text_muted),
            hovertemplate='%{x}<br>Count: %{y:,}<extra></extra>',
        ))

    fig.update_layout(
        barmode='group', showlegend=False, bargap=0.35,
        xaxis=dict(title=None, title_standoff=4, tickfont=dict(size=_s(8), color=text_muted)),
        yaxis=dict(title=None, range=[0, y_top], automargin=True),
    )
    fig = _style(fig, light_theme)
    fig.update_layout(margin=dict(l=32, r=8, t=12, b=46))
    return fig


def risk_over_time(df: pd.DataFrame, light_theme: bool = False):
    daily = df.groupby('TransactionDay').agg(
        mean_risk=('risk_score', 'mean'),
        high_risk_tx=('is_high_risk', 'sum'),
    ).reset_index()

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=daily['TransactionDay'], y=daily['high_risk_tx'],
        name='High Risk',
        marker_color='rgba(59,130,246,0.12)',
        yaxis='y2',
        hovertemplate='%{x}<br>High Risk Tx: %{y:,}<extra></extra>',
    ))
    fig.add_trace(go.Scatter(
        x=daily['TransactionDay'], y=daily['mean_risk'],
        mode='lines', name='Mean Risk',
        line=dict(color=pl.ACCENT, width=2),
        fill='tozeroy', fillcolor='rgba(59,130,246,0.07)',
        hovertemplate='%{x}<br>Mean Risk: %{y:.2f}<extra></extra>',
    ))

    fig.update_layout(
        yaxis=dict(title='Mean Risk', side='left'),
        yaxis2=dict(title=None, overlaying='y', side='right', showgrid=False, showticklabels=False),
        hovermode='x unified', showlegend=False,
    )
    fig = _style(fig, light_theme)
    fig.update_layout(margin=dict(l=32, r=8, t=12, b=46))
    return fig


def amount_feature_scatter(df: pd.DataFrame, light_theme: bool = False):
    text_muted = '#475569' if light_theme else pl.TEXT_MUTED
    sample = df.sample(min(12000, len(df)), random_state=42) if len(df) > 12000 else df

    fig = go.Figure()

    normal = sample[sample['isFraud'] == 0]
    if len(normal):
        fig.add_trace(go.Scatter(
            x=normal['TransactionAmt'], y=normal['risk_score'],
            mode='markers', name='Normal',
            marker=dict(color='rgba(59,130,246,0.5)', size=3.5, line=dict(width=0)),
            hovertemplate='Amt: %{x:.2f}<br>Risk: %{y:.1f}<extra></extra>',
        ))

    fraud = sample[sample['isFraud'] == 1]
    if len(fraud):
        fig.add_trace(go.Scatter(
            x=fraud['TransactionAmt'], y=fraud['risk_score'],
            mode='markers', name='Fraud',
            marker=dict(color='rgba(239,68,68,0.75)', size=4.5,
                        line=dict(color='#ef4444', width=1)),
            hovertemplate='Amt: %{x:.2f}<br>Risk: %{y:.1f}<extra></extra>',
        ))

    fig.update_layout(
        showlegend=True,
        legend=dict(
            orientation='h', yanchor='top', y=1.08, xanchor='right', x=1,
            font=dict(family='Inter, sans-serif', size=_s(8), color=text_muted),
            bgcolor='rgba(0,0,0,0)',
        ),
        xaxis=dict(title='Amount', title_standoff=4, title_font=dict(size=_s(9))),
        yaxis=dict(title='Risk', title_font=dict(size=_s(9))),
    )
    fig = _style(fig, light_theme)
    fig.update_layout(margin=dict(l=32, r=8, t=12, b=46))
    return fig


def fraud_risk_box(df: pd.DataFrame, light_theme: bool = False):
    text_muted = '#475569' if light_theme else pl.TEXT_MUTED
    fig = go.Figure()
    for cls_name, cls_color in pl.CLASS_COLORS.items():
        mask = df['isFraudLabel'] == cls_name
        sub = df.loc[mask, 'risk_score']
        if len(sub) == 0:
            continue
        fig.add_trace(go.Box(
            y=[sub.values], name=cls_name,
            marker=dict(color=cls_color, size=3),
            line=dict(color=cls_color, width=1.5),
            fillcolor='rgba(0,0,0,0)', boxpoints=False, hoverinfo='skip',
        ))
    fig.update_layout(
        showlegend=False,
        xaxis=dict(title='Class', tickfont=dict(size=_s(9), color=text_muted)),
        yaxis=dict(title='Risk Score', title_font=dict(size=_s(9))),
        boxmode='group',
    )
    fig = _style(fig, light_theme)
    fig.update_layout(margin=dict(l=32, r=8, t=12, b=46))
    return fig


def feature_heatmap(df: pd.DataFrame, light_theme: bool = False):
    text_muted = '#475569' if light_theme else pl.TEXT_MUTED
    v_cols = [c for c in df.columns if c.startswith('V')][:20]
    if not v_cols:
        return _style(go.Figure(), light_theme)

    heat = df.groupby('risk_level')[v_cols].mean().reindex(list(pl.RISK_COLORS.keys()))
    z = heat.values

    fig = go.Figure(data=go.Heatmap(
        z=z,
        x=[f'F{i+1}' for i in range(len(heat.columns))],
        y=[r.replace(' Risk', '') for r in heat.index],
        zmin=0,
        colorbar=dict(
            title='Avg', titleside='right',
            title_font=dict(size=_s(8), color=text_muted),
            tickfont=dict(size=_s(7), color=text_muted),
            thickness=8, lenmode='fraction', len=0.7,
            bgcolor='rgba(0,0,0,0)',
        ),
        colorscale=[
            [0, '#38bdf8'], [0.33, '#5ab0ff'],
            [0.5, '#F59E0B'], [0.75, '#E67E22'], [1, '#E74C3C'],
        ],
    ))

    fig.update_layout(
        xaxis=dict(title='Feature', title_standoff=4, tickfont=dict(size=_s(7), color=text_muted)),
        yaxis=dict(title='Risk Level', tickfont=dict(size=_s(8), color=text_muted)),
    )
    fig = _style(fig, light_theme)
    fig.update_layout(margin=dict(l=80, r=4, t=12, b=46))
    return fig


def _score_color(score):
    """Score 0-100 → color from cyan → yellow → orange → red."""
    t = min(max(score, 0), 100) / 100.0
    if t <= 0.25:
        s = t / 0.25
        r = int(46 + (241 - 46) * s)
        g = int(134 + (196 - 134) * s)
        b = int(222 + (15 - 222) * s)
    elif t <= 0.50:
        s = (t - 0.25) / 0.25
        r = int(241 + (230 - 241) * s)
        g = int(196 + (126 - 196) * s)
        b = int(15 + (34 - 15) * s)
    elif t <= 0.75:
        s = (t - 0.50) / 0.25
        r = int(230 + (231 - 230) * s)
        g = int(126 + (76 - 126) * s)
        b = int(34 + (60 - 34) * s)
    else:
        return '#E74C3C'
    return f'rgb({r},{g},{b})'
