from __future__ import annotations

from dash import html

from config import palette as pl
from config.settings import MAX_TABLE_ROWS


def top_risk_table(df):
    view = df.sort_values(['risk_score', 'TransactionAmt'], ascending=[False, False]).head(MAX_TABLE_ROWS).copy()
    columns = ['TransactionID', 'TransactionDate', 'ProductCD', 'TransactionAmt', 'risk_score', 'risk_level', 'isFraud']
    view = view[columns]
    view['TransactionDate'] = view['TransactionDate'].dt.strftime('%Y-%m-%d %H:%M')

    header = [html.Th(c) for c in view.columns]
    body = []
    for _, row in view.iterrows():
        cls = row['risk_level'].lower().replace(' ', '')
        status_dot = f"<span class='status-dot {cls}'></span>"
        amount = f"${row['TransactionAmt']:,.2f}"
        body.append(html.Tr([
            html.Td(str(row['TransactionID']), style={'color': pl.ACCENT, 'fontWeight': 600}),
            html.Td(row['TransactionDate']),
            html.Td(row['ProductCD']),
            html.Td(amount, style={'fontVariantNumeric': 'tabular-nums'}),
            html.Td(row['risk_score'], style={'fontWeight': '700', 'color': _risk_color(row['risk_level'])}),
            html.Td(html.Div([
                html.Span(className=f'status-dot {cls}'),
                html.Span(row['risk_level'], className=f'risk-badge {cls}'),
            ])),
            html.Td('Yes' if row['isFraud'] else '', style={'color': pl.RED if row['isFraud'] else pl.TEXT_MUTED}),
        ]))

    return html.Div(
        html.Table(
            [html.Thead(html.Tr(header)), html.Tbody(body)],
            className='table-premium',
        ),
        className='table-scroll',
    )


def _risk_color(level: str) -> str:
    _map = {
        'Low Risk': '#3b82f6',
        'Moderate Risk': '#fbbf24',
        'High Risk': '#f97316',
        'Critical Risk': '#ef4444',
    }
    return _map.get(level, pl.TEXT)
