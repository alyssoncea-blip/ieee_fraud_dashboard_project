from __future__ import annotations

from dash import dcc, html
import dash_bootstrap_components as dbc

from config import palette as pl

MENU_ITEMS = [
    ('fullscreen', 'Fullscreen'),
    ('maximize-widget', 'Maximize Widget'),
    ('reset-layout', 'Reset Layout'),
    ('density-compact', 'Compact Mode'),
    ('density-comfortable', 'Comfortable Mode'),
    ('theme-toggle', 'Toggle Theme'),
    ('zoom-in', 'Zoom In'),
    ('zoom-out', 'Zoom Out'),
    ('pan', 'Pan Mode'),
    ('brush', 'Select Range'),
    ('reset-zoom', 'Reset Zoom'),
    ('refresh', 'Refresh'),
    ('reset-filters', 'Reset Filters'),
    ('export-png', 'Export PNG'),
    ('export-pdf', 'Export PDF'),
    ('export-csv', 'Export Data'),
    ('export-excel', 'Export Excel'),
    ('copy-image', 'Copy Image'),
]


def kpi_card(title: str, value: str, accent: str):
    glow_hex = accent.lstrip('#')
    r, g, b = int(glow_hex[0:2], 16), int(glow_hex[2:4], 16), int(glow_hex[4:6], 16)
    return html.Div(
        [
            html.Div(title, className='kpi-title'),
            html.Div(value, className='kpi-value'),
        ],
        className='kpi-card',
        style={
            '--kpi-accent': accent,
            '--kpi-glow-shadow': f'rgba({r},{g},{b},0.12)',
        },
    )


def toggle_switch(toggle_id: str, label: str):
    """DBC switch toggle for dark theme."""
    return dbc.Checklist(
        id=toggle_id,
        options=[{'label': label, 'value': 'on'}],
        value=[],
        switch=True,
        inline=True,
        className='premium-toggle',
    )


def _chart_menu_items(panel_id: str):
    """Build dropdown menu items for a chart panel."""
    items = []
    for action, label in MENU_ITEMS:
        items.append(
            html.Button(
                label,
                className='chart-menu-item',
                id={'type': 'menu-item', 'action': action, 'chart': panel_id},
                n_clicks=0,
                type='button',
            )
        )
    return items


def _chart_menu(panel_id: str):
    """Build the full chart menu (trigger + dropdown)."""
    return html.Div(
        [
            html.Div(
                '⋯',
                className='chart-menu-trigger',
                tabIndex=0,
                role='button',
                **{'aria-label': 'Open chart menu'},
            ),
            html.Div(_chart_menu_items(panel_id), className='chart-menu-dropdown'),
        ],
        className='chart-menu',
    )


def _panel_actions(panel_id: str):
    return html.Div(
        [
            _chart_menu(panel_id),
            html.Button(
                '×',
                id={'type': 'panel-close', 'action': 'close-fullscreen', 'chart': panel_id},
                n_clicks=0,
                className='panel-close-btn',
                title='Close fullscreen',
            ),
        ],
        className='panel-actions',
    )


def _panel(title: str, graph_id: str):
    """Reusable chart panel with embedded menu and unique graph id."""
    return html.Div(
        [
            html.Div(
                [
                    html.Span(title, className='panel-title'),
                    _panel_actions(graph_id),
                ],
                className='panel-header',
            ),
            html.Div(dcc.Graph(id=graph_id, config={'displayModeBar': False}), className='panel-body'),
        ],
        className='panel-card',
    )


def base_layout(df, metadata):
    min_date = df['TransactionDate'].min().date()
    max_date = df['TransactionDate'].max().date()

    amount_max = int(df['TransactionAmt'].quantile(0.99))
    amt_label = int(max(amount_max, 1000))
    slider_step = 1
    tick_vals = sorted(set([0, amt_label // 4, amt_label // 2, (3 * amt_label) // 4, amt_label]))
    marks = {v: f'${v:,.0f}' for v in tick_vals}

    return dbc.Container(
        [
            # ========== HEADER ==========
            html.Div(
                [
                    html.H1('Transaction Risk Intelligence Dashboard', className='page-title'),
                ],
                className='header-row',
            ),

            # ========== FILTER AREA + RIGHT GAUGE ==========
            html.Div(
                [
                    html.Div(
                        [
                            html.Div([
                                html.Label('Date Range', className='filter-label'),
                                dcc.DatePickerRange(
                                    id='date-range',
                                    min_date_allowed=min_date,
                                    max_date_allowed=max_date,
                                    start_date=min_date,
                                    end_date=max_date,
                                    display_format='YYYY-MM-DD',
                                    month_format='MMM YYYY',
                                    clearable=False,
                                    with_portal=False,
                                    number_of_months_shown=1,
                                    show_outside_days=True,
                                ),
                            ], className='filter-col'),
                            html.Div([
                                html.Label('Amount Range', className='filter-label'),
                                html.Div(
                                    [
                                        dcc.RangeSlider(
                                            id='amount-range',
                                            min=0,
                                            max=amt_label,
                                            step=slider_step,
                                            value=[0, amt_label],
                                            marks=marks,
                                            allowCross=False,
                                            updatemode='drag',
                                            className='amount-range-slider',
                                            tooltip={'placement': 'bottom', 'always_visible': False},
                                        ),
                                        html.Div(
                                            [
                                                dcc.Input(
                                                    id='amount-min-input',
                                                    type='text',
                                                    value='0',
                                                    debounce=True,
                                                    className='amount-input',
                                                    placeholder='Min',
                                                ),
                                                dcc.Input(
                                                    id='amount-max-input',
                                                    type='text',
                                                    value=f'{amt_label}',
                                                    debounce=True,
                                                    className='amount-input',
                                                    placeholder='Max',
                                                ),
                                            ],
                                            className='amount-input-row',
                                        ),
                                    ],
                                    className='amount-range-wrapper',
                                ),
                            ], className='filter-col'),
                            html.Div([
                                html.Label('Risk Level', className='filter-label'),
                                dcc.Dropdown(
                                    id='risk-levels',
                                    options=[{'label': k, 'value': k} for k in pl.RISK_COLORS],
                                    value=list(pl.RISK_COLORS.keys()),
                                    multi=True, clearable=False,
                                    placeholder='Select Risk Level',
                                ),
                            ], className='filter-col'),
                            html.Div([
                                html.Label('Filter', className='filter-label'),
                                html.Div([
                                    toggle_switch('toggle-high-risk', 'High Risk Only'),
                                    toggle_switch('toggle-fraud', 'Fraud Only'),
                                ], className='toggle-inline toggle-stack'),
                            ], className='filter-col'),
                            html.Div([
                                html.Label('Theme', className='filter-label'),
                                html.Div([
                                    toggle_switch('toggle-light-theme', 'Light Version'),
                                ], className='toggle-inline'),
                            ], className='filter-col'),
                        ],
                        className='filter-bar',
                    ),
                    html.Div(id='avg-risk-filter-gauge', className='filter-gauge-col'),
                ],
                className='filter-row',
            ),

            # ========== KPI ROW ==========
            html.Div(id='kpi-row-container'),

            # ========== CHART ROW 1 ==========
            html.Div([
                html.Div(
                    [
                        html.Div(
                            [
                                html.Span('Risk Score Distribution', className='panel-title'),
                                _panel_actions('risk-distribution'),
                            ],
                            className='panel-header',
                        ),
                        html.Div(dcc.Graph(id='risk-distribution', config={'displayModeBar': False}), className='panel-body'),
                    ],
                    className='panel-card',
                ),
                html.Div(
                    [
                        html.Div(
                            [
                                html.Span('Risk Level Breakdown', className='panel-title'),
                                _panel_actions('risk-breakdown'),
                            ],
                            className='panel-header',
                        ),
                        html.Div(dcc.Graph(id='risk-breakdown', config={'displayModeBar': False}), className='panel-body'),
                    ],
                    className='panel-card',
                ),
            ], className='chart-row'),

            # ========== CHART ROW 2 ==========
            html.Div([
                html.Div(
                    [
                        html.Div(
                            [
                                html.Span('Risk Over Time', className='panel-title'),
                                _panel_actions('risk-over-time'),
                            ],
                            className='panel-header',
                        ),
                        html.Div(dcc.Graph(id='risk-over-time', config={'displayModeBar': False}), className='panel-body'),
                    ],
                    className='panel-card',
                ),
                html.Div(
                    [
                        html.Div(
                            [
                                html.Span('Amount vs Risk Score', className='panel-title'),
                                _panel_actions('amount-feature-scatter'),
                            ],
                            className='panel-header',
                        ),
                        html.Div(dcc.Graph(id='amount-feature-scatter', config={'displayModeBar': False}), className='panel-body'),
                    ],
                    className='panel-card',
                ),
            ], className='chart-row'),

            # ========== CHART ROW 3: Heatmap + Table ==========
            html.Div([
                html.Div(
                    [
                        html.Div(
                            [
                                html.Span('Feature Risk Heatmap', className='panel-title'),
                                _panel_actions('feature-heatmap'),
                            ],
                            className='panel-header',
                        ),
                        html.Div(dcc.Graph(id='feature-heatmap', config={'displayModeBar': False}), className='panel-body'),
                    ],
                    className='panel-card',
                ),
                html.Div(
                    [
                        html.Div(
                            [
                                html.Span('Top Risky Transactions', className='panel-title'),
                            ],
                            className='panel-header',
                        ),
                        html.Div(id='top-risk-table', className='table-scroll'),
                    ],
                    className='panel-card',
                ),
            ], className='chart-row'),
        ],
        fluid=True,
        className='page-shell',
    )
