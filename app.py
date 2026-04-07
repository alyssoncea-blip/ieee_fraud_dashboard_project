from __future__ import annotations

import json
import re
import math

import dash
from dash import dcc, html, Input, Output, no_update
from dash.dependencies import ALL, MATCH, ALLSMALLER
import dash_bootstrap_components as dbc
import plotly.graph_objects as go

from config import palette as pl
from data_lib.filters import apply_filters
from data_lib.loader import DataNotFoundError, load_base_data
from data_lib.scoring import score_transactions
from viz.figures import (
    amount_feature_scatter,
    feature_heatmap,
    risk_breakdown,
    risk_distribution,
    risk_over_time,
)
from viz.layouts import base_layout, kpi_card
from viz.tables import top_risk_table


external_stylesheets = [dbc.themes.BOOTSTRAP]
app = dash.Dash(
    __name__,
    external_stylesheets=external_stylesheets,
    suppress_callback_exceptions=True,
)
app.title = 'Transaction Risk Intelligence Dashboard'
server = app.server

CHART_GRAPHS = [
    'risk-distribution',
    'risk-breakdown',
    'risk-over-time',
    'amount-feature-scatter',
    'feature-heatmap',
]
MENU_ACTIONS = [
    'fullscreen',
    'maximize-widget',
    'reset-layout',
    'density-compact',
    'density-comfortable',
    'theme-toggle',
    'zoom-in',
    'zoom-out',
    'pan',
    'brush',
    'reset-zoom',
    'refresh',
    'reset-filters',
    'export-png',
    'export-pdf',
    'export-csv',
    'export-excel',
    'copy-image',
]
CLOSE_ACTIONS = ['close-fullscreen']


# ---- Load data & build layout --------------------------------------

try:
    DF, METADATA = load_base_data()
    DF = score_transactions(DF, METADATA['model_numeric_cols'])
    layout_body = base_layout(DF, METADATA)
    HAS_DATA = True
    AMOUNT_MIN = 0
    AMOUNT_MAX = int(max(int(DF['TransactionAmt'].quantile(0.99)), 1000))
except DataNotFoundError as exc:
    layout_body = dbc.Alert(str(exc), color='danger', className='mt-5')
    DF = None
    METADATA = None
    HAS_DATA = False
    AMOUNT_MIN = 0
    AMOUNT_MAX = 1000


# ---- Build list of all menu n_clicks IDs for ONE combined callback --
_menu_inputs = []
for gid in CHART_GRAPHS:
    for act in MENU_ACTIONS:
        _menu_inputs.append({'type': 'menu-item', 'action': act, 'chart': gid})

_close_inputs = []
for gid in CHART_GRAPHS:
    for act in CLOSE_ACTIONS:
        _close_inputs.append({'type': 'panel-close', 'action': act, 'chart': gid})


# Wrap layout with hidden store
app.layout = html.Div([
    dcc.Store(id='_menu-trigger'),
    dcc.Store(id='_resize-trigger'),
    dcc.Store(id='_heatmap-init-trigger'),
    dcc.Store(id='_theme-trigger'),
    dcc.Interval(id='_heatmap-init-refresh', interval=850, n_intervals=0, max_intervals=1),
    layout_body,
])


# ---- Single clientside callback: detect click → execute action ----

js_do_action = '''
function() {
    try {
        var ctx = window.dash_clientside.callback_context;
        if (!ctx.triggered) return window.dash_clientside.no_update;

        var propId = ctx.triggered[0].prop_id;
        var idStr = propId.split('.')[0];
        if (!idStr.startsWith('{')) return window.dash_clientside.no_update;

        var spec = JSON.parse(idStr);
        var chartId = spec.chart;
        var action  = spec.action;
        var host = document.getElementById(chartId);
        if (!host) return window.dash_clientside.no_update;
        var gd = host.querySelector('.js-plotly-plot') || host;
        var panel = host.closest('.panel-card');

    function getRange(ax) {
        if (!ax) return null;
        return Array.isArray(ax.range) ? ax.range : null;
    }
    function scaleRange(range, factor) {
        if (!range || range.length !== 2) return null;
        var a = range[0], b = range[1];
        var isDate = (typeof a === 'string' || typeof b === 'string');
        if (isDate) {
            var d0 = new Date(a).getTime();
            var d1 = new Date(b).getTime();
            if (!isFinite(d0) || !isFinite(d1)) return null;
            var c = (d0 + d1) / 2;
            var h = (d1 - d0) * factor / 2;
            return [new Date(c - h), new Date(c + h)];
        }
        var c2 = (a + b) / 2;
        var h2 = (b - a) * factor / 2;
        return [c2 - h2, c2 + h2];
    }
    function exportCsv(filename, mimeType) {
        var traces = gd.data || [];
        if (!traces.length) return;
        var rows = ['trace_index,x,y,text,name'];
        for (var t = 0; t < traces.length; t++) {
            var tr = traces[t];
            var x = Array.isArray(tr.x) ? tr.x : [];
            var y = Array.isArray(tr.y) ? tr.y : [];
            var text = Array.isArray(tr.text) ? tr.text : [];
            var m = Math.max(x.length, y.length, text.length, 1);
            for (var i = 0; i < m; i++) {
                var xv = (x[i] !== undefined ? x[i] : '');
                var yv = (y[i] !== undefined ? y[i] : '');
                var tv = (text[i] !== undefined ? text[i] : '');
                var name = tr.name || '';
                rows.push([t, xv, yv, tv, name].map(function(v){
                    var s = String(v).replaceAll('"', '""');
                    return '"' + s + '"';
                }).join(','));
            }
        }
        var blob = new Blob([rows.join('\\n')], {type: mimeType || 'text/csv'});
        var url  = URL.createObjectURL(blob);
        var a    = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }

        if (action === 'fullscreen' || action === 'maximize-widget') {
            if (panel) panel.classList.toggle('is-maximized');
        } else if (action === 'close-fullscreen') {
            if (panel) panel.classList.remove('is-maximized');
        } else if (action === 'reset-layout') {
        document.querySelectorAll('.panel-card.is-maximized').forEach(function(el){ el.classList.remove('is-maximized'); });
    } else if (action === 'density-compact') {
        document.body.classList.add('density-compact');
        document.body.classList.remove('density-comfortable');
        window.dispatchEvent(new Event('resize'));
    } else if (action === 'density-comfortable') {
        document.body.classList.add('density-comfortable');
        document.body.classList.remove('density-compact');
        window.dispatchEvent(new Event('resize'));
    } else if (action === 'theme-toggle') {
        document.body.classList.toggle('theme-light');
    } else if (action === 'zoom-in' || action === 'zoom-out') {
        var xr = getRange((gd.layout || {}).xaxis);
        var yr = getRange((gd.layout || {}).yaxis);
        var factor = action === 'zoom-in' ? 0.8 : 1.25;
        var upd = {};
        var nx = scaleRange(xr, factor);
        var ny = scaleRange(yr, factor);
        if (nx) upd['xaxis.range'] = nx;
        if (ny) upd['yaxis.range'] = ny;
        if (Object.keys(upd).length) Plotly.relayout(gd, upd);
    } else if (action === 'pan') {
        Plotly.relayout(gd, {'dragmode': 'pan'});
    } else if (action === 'brush') {
        Plotly.relayout(gd, {'dragmode': 'select'});
    } else if (action === 'reset-zoom') {
        Plotly.relayout(gd, {'xaxis.autorange': true, 'yaxis.autorange': true, 'dragmode': 'zoom'});
    } else if (action === 'refresh') {
        window.dispatchEvent(new Event('resize'));
    } else if (action === 'reset-filters') {
        window.location.reload();
    } else if (action === 'export-png') {
        Plotly.downloadImage(gd, {format: 'png', width: 1400, height: 900, filename: chartId});
    } else if (action === 'export-pdf') {
        Plotly.toImage(gd, {format: 'png', width: 1400, height: 900}).then(function(url){
            var w = window.open('', '_blank');
            if (!w) return;
            w.document.write('<html><head><title>' + chartId + '</title></head><body style="margin:0"><img style="width:100%" src="' + url + '"/></body></html>');
            w.document.close();
            w.focus();
            w.print();
        });
    } else if (action === 'export-csv') {
        exportCsv(chartId + '_data.csv', 'text/csv');
    } else if (action === 'export-excel') {
        exportCsv(chartId + '_data.xls', 'application/vnd.ms-excel');
        } else if (action === 'copy-image') {
        Plotly.toImage(gd, {format: 'png', width: 1200, height: 800}).then(function(url){
            if (!navigator.clipboard || !window.ClipboardItem) return;
            fetch(url).then(function(r){ return r.blob(); }).then(function(blob){
                return navigator.clipboard.write([new ClipboardItem({'image/png': blob})]);
            }).catch(function(){});
        });
        }
        return {action: action, chart: chartId, ts: Date.now()};
    } catch (e) {
        console.error('menu action error', e);
        return window.dash_clientside.no_update;
    }
}
'''

app.clientside_callback(
    js_do_action,
    Output('_menu-trigger', 'data'),
    [Input(mid, 'n_clicks') for mid in (_menu_inputs + _close_inputs)],
    prevent_initial_call=True,
)

js_force_resize = '''
function(_figure) {
    if (typeof window !== 'undefined') {
        var host = document.getElementById('feature-heatmap');
        var gd = host ? (host.querySelector('.js-plotly-plot') || host) : null;
        var doResize = function() {
            try {
                if (gd && window.Plotly && window.Plotly.Plots && window.Plotly.Plots.resize) {
                    window.Plotly.Plots.resize(gd);
                }
                window.dispatchEvent(new Event('resize'));
            } catch (e) {}
        };
        window.requestAnimationFrame(doResize);
        setTimeout(doResize, 120);
        setTimeout(doResize, 360);
    }
    return Date.now();
}
'''

app.clientside_callback(
    js_force_resize,
    Output('_resize-trigger', 'data'),
    Input('feature-heatmap', 'figure'),
)

js_heatmap_init_refresh = '''
function(_n) {
    if (typeof window === 'undefined') return window.dash_clientside.no_update;

    var host = document.getElementById('feature-heatmap');
    var gd = host ? (host.querySelector('.js-plotly-plot') || host) : null;
    if (!gd || !window.Plotly) return Date.now();

    var force = function() {
        try {
            if (window.Plotly.Plots && window.Plotly.Plots.resize) {
                window.Plotly.Plots.resize(gd);
            }
            if (window.Plotly.relayout) {
                window.Plotly.relayout(gd, {'xaxis.autorange': true, 'yaxis.autorange': true});
            }
        } catch (e) {}
    };

    setTimeout(force, 60);
    setTimeout(force, 220);
    setTimeout(force, 520);
    return Date.now();
}
'''

app.clientside_callback(
    js_heatmap_init_refresh,
    Output('_heatmap-init-trigger', 'data'),
    Input('_heatmap-init-refresh', 'n_intervals'),
)

js_toggle_theme = '''
function(lightThemeValue) {
    var on = Array.isArray(lightThemeValue) && lightThemeValue.length > 0;
    if (typeof document !== 'undefined' && document.body) {
        document.body.classList.toggle('theme-light', on);
    }
    return {light: on, ts: Date.now()};
}
'''

app.clientside_callback(
    js_toggle_theme,
    Output('_theme-trigger', 'data'),
    Input('toggle-light-theme', 'value'),
)


@app.callback(
    Output('amount-range', 'value'),
    Output('amount-min-input', 'value'),
    Output('amount-max-input', 'value'),
    Input('amount-range', 'value'),
    Input('amount-min-input', 'value'),
    Input('amount-max-input', 'value'),
)
def sync_amount_range(slider_value, min_input, max_input):
    trigger_id = None
    try:
        trigger_id = dash.ctx.triggered_id
    except Exception:
        trigger_id = None

    if isinstance(slider_value, (list, tuple)) and len(slider_value) == 2:
        low, high = slider_value
    else:
        low, high = AMOUNT_MIN, AMOUNT_MAX

    if trigger_id == 'amount-min-input':
        low = min_input
    elif trigger_id == 'amount-max-input':
        high = max_input
    elif trigger_id is None:
        low = min_input if min_input is not None else low
        high = max_input if max_input is not None else high

    low = _coerce_amount(low, AMOUNT_MIN)
    high = _coerce_amount(high, AMOUNT_MAX)

    low = max(AMOUNT_MIN, min(AMOUNT_MAX, low))
    high = max(AMOUNT_MIN, min(AMOUNT_MAX, high))

    if low > high:
        if trigger_id == 'amount-min-input':
            high = low
        elif trigger_id == 'amount-max-input':
            low = high
        else:
            low, high = high, low

    return [low, high], f'{low}', f'{high}'


# ================================================================
# MAIN DASHBOARD CALLBACK
# ================================================================

@app.callback(
    Output('avg-risk-filter-gauge', 'children'),
    Output('kpi-row-container', 'children'),
    Output('risk-distribution', 'figure'),
    Output('risk-breakdown', 'figure'),
    Output('risk-over-time', 'figure'),
    Output('amount-feature-scatter', 'figure'),
    Output('feature-heatmap', 'figure'),
    Output('top-risk-table', 'children'),
    Input('date-range', 'start_date'),
    Input('date-range', 'end_date'),
    Input('amount-range', 'value'),
    Input('risk-levels', 'value'),
    Input('toggle-high-risk', 'value'),
    Input('toggle-fraud', 'value'),
    Input('toggle-light-theme', 'value'),
)
def update_dashboard(start_date, end_date, amount_range, risk_levels,
                     high_risk_val, fraud_val, light_theme_val):
        toggles = []
        if high_risk_val and len(high_risk_val) > 0:
            toggles.append('high_risk')
        if fraud_val and len(fraud_val) > 0:
            toggles.append('fraud')
        light_theme = bool(light_theme_val and len(light_theme_val) > 0)

        filtered = apply_filters(
            DF,
            start_date=start_date,
            end_date=end_date,
            amount_range=amount_range,
            risk_levels=risk_levels,
            fraud_only='fraud' in toggles,
            high_risk_only='high_risk' in toggles,
            product_codes=[],
        )

        total_tx = len(filtered)
        avg_risk = filtered['risk_score'].mean() if total_tx else 0
        high_risk_count = int(filtered['is_high_risk'].sum()) if total_tx else 0
        critical_risk = int(filtered['is_critical_risk'].sum()) if total_tx else 0
        high_risk_amt = float(filtered.loc[filtered['is_high_risk'], 'TransactionAmt'].sum()) if total_tx else 0
        fraud_total = int(filtered['isFraud'].sum()) if total_tx else 0
        fraud_capture = 0
        if fraud_total:
            fraud_capture = 100 * float(filtered.loc[filtered['isFraud'] == 1, 'is_high_risk'].mean())

        mean_score = float(avg_risk) if total_tx else 0
        gauge_color = _gauge_color(mean_score)
        score_clamped = max(0.0, min(100.0, mean_score))
        gauge_text = '#0f172a' if light_theme else pl.TEXT
        gauge_muted = '#64748b' if light_theme else pl.TEXT_MUTED
        gauge_value_shadow = 'rgba(15,23,42,0.18)' if light_theme else 'rgba(0,0,0,0.55)'
        gauge_outline = 'rgba(241,245,249,0.85)' if light_theme else 'rgba(7,13,26,0.95)'
        low_high_main = '#64748b' if light_theme else '#ffffff'
        low_high_shadow = 'rgba(15,23,42,0.18)' if light_theme else 'rgba(0,0,0,0.65)'

        # Needle geometry for a speedometer-like gauge.
        cx, cy = 0.5, 0.20
        needle_len = 0.32
        angle_deg = 180.0 - (score_clamped / 100.0) * 180.0
        angle_rad = math.radians(angle_deg)
        nx = cx + needle_len * math.cos(angle_rad)
        ny = cy + needle_len * math.sin(angle_rad)
        dx = nx - cx
        dy = ny - cy
        length = math.hypot(dx, dy) or 1.0
        px = -dy / length
        py = dx / length
        base_half = 0.014
        tip_half = 0.0028
        bx1, by1 = cx + px * base_half, cy + py * base_half
        bx2, by2 = cx - px * base_half, cy - py * base_half
        tx1, ty1 = nx + px * tip_half, ny + py * tip_half
        tx2, ty2 = nx - px * tip_half, ny - py * tip_half
        needle_path = (
            f'M {bx1:.4f},{by1:.4f} '
            f'L {tx1:.4f},{ty1:.4f} '
            f'L {tx2:.4f},{ty2:.4f} '
            f'L {bx2:.4f},{by2:.4f} Z'
        )

        fig_gauge = go.Figure(go.Indicator(
            mode='gauge',
            value=mean_score,
            domain=dict(x=[0, 1], y=[0, 1]),
            gauge=dict(
                axis=dict(
                    range=[0, 100],
                    showticklabels=False,
                    ticks="",
                ),
                bar=dict(color=gauge_color, thickness=0.8),
                steps=[
                    dict(range=[0, 6], color='rgba(120,170,220,0.24)'),
                    dict(range=[6, 25], color='rgba(46,134,222,0.22)'),
                    dict(range=[25, 50], color='rgba(241,196,15,0.20)'),
                    dict(range=[50, 75], color='rgba(230,126,34,0.20)'),
                    dict(range=[75, 100], color='rgba(231,76,60,0.22)'),
                ],
                threshold=dict(
                    line=dict(color=gauge_color, width=4),
                    thickness=0.82,
                    value=score_clamped,
                ),
                bgcolor='rgba(0,0,0,0)',
                borderwidth=0,
                shape='angular',
            ),
        ))
        value_text = f'<b>{score_clamped:.1f}</b>'
        fig_gauge.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            font_color=gauge_text,
            margin=dict(l=10, r=10, t=0, b=8),
            height=120,
            transition=dict(duration=520, easing='cubic-in-out'),
            shapes=[
                dict(
                    type='path',
                    xref='paper', yref='paper',
                    path=needle_path,
                    line=dict(color='#7a8fa8' if light_theme else '#8ea1b5', width=1),
                    fillcolor='#8ea4bf' if light_theme else '#b8c4d3',
                    layer='above',
                ),
                dict(
                    type='circle',
                    xref='paper', yref='paper',
                    x0=cx - 0.014, x1=cx + 0.014,
                    y0=cy - 0.014, y1=cy + 0.014,
                    line=dict(color='#64748b', width=1),
                    fillcolor='#dbe6f4' if light_theme else '#cbd5e1',
                    layer='above',
                ),
            ],
            annotations=[
                dict(
                    x=0.505, y=0.105, xref='paper', yref='paper',
                    text=value_text, showarrow=False,
                    font=dict(size=24, color=gauge_value_shadow),
                ),
                dict(
                    x=0.498, y=0.11, xref='paper', yref='paper',
                    text=value_text, showarrow=False,
                    font=dict(size=24, color=gauge_outline),
                ),
                dict(
                    x=0.502, y=0.11, xref='paper', yref='paper',
                    text=value_text, showarrow=False,
                    font=dict(size=24, color=gauge_outline),
                ),
                dict(
                    x=0.5, y=0.106, xref='paper', yref='paper',
                    text=value_text, showarrow=False,
                    font=dict(size=24, color=gauge_outline),
                ),
                dict(
                    x=0.5, y=0.114, xref='paper', yref='paper',
                    text=value_text, showarrow=False,
                    font=dict(size=24, color=gauge_outline),
                ),
                dict(
                    x=0.5, y=0.11, xref='paper', yref='paper',
                    text=value_text, showarrow=False,
                    font=dict(size=24, color=gauge_text),
                ),
                dict(
                    x=0.142, y=0.036, xref='paper', yref='paper',
                    text='<b>Low</b>', showarrow=False,
                    font=dict(size=14, color=low_high_shadow),
                ),
                dict(
                    x=0.862, y=0.036, xref='paper', yref='paper',
                    text='<b>High</b>', showarrow=False,
                    font=dict(size=14, color=low_high_shadow),
                ),
                dict(
                    x=0.14, y=0.04, xref='paper', yref='paper',
                    text='<b>Low</b>', showarrow=False,
                    font=dict(size=14, color=low_high_main),
                ),
                dict(
                    x=0.86, y=0.04, xref='paper', yref='paper',
                    text='<b>High</b>', showarrow=False,
                    font=dict(size=14, color=low_high_main),
                ),
            ],
        )

        gauge_kpi = html.Div(
            [
                html.Div('Average Risk Level', className='kpi-title'),
                dcc.Graph(figure=fig_gauge, config={'displayModeBar': False}, className='kpi-gauge-inline'),
            ],
            className='filter-gauge-card',
        )

        cards = [
            kpi_card('Total Transactions', f'{total_tx:,}', pl.ACCENT),
            kpi_card('Average Risk Score', f'{avg_risk:.1f}', pl.YELLOW),
            kpi_card('High Risk Transactions', f'{high_risk_count:,}', pl.ORANGE),
            kpi_card('Critical Risk', f'{critical_risk:,}', pl.RED),
            kpi_card('Total High-Risk Amount', pl.money_fmt(high_risk_amt), pl.ACCENT_WARNING),
            kpi_card('Fraud Capture Rate', pl.pct_fmt(fraud_capture), pl.ACCENT_PURPLE),
        ]
        kpis = html.Div(cards, className='kpi-row-inner')

        if total_tx == 0:
            fg = go.Figure()
            kpis_empty = html.Div([
                *cards,
                html.Div('No data for the selected filters.', className='empty-state'),
            ], className='kpi-row-inner')
            return gauge_kpi, kpis_empty, fg, fg, fg, fg, fg, html.Div('', className='empty-state')

        return (
            gauge_kpi,
            kpis,
            risk_distribution(filtered, light_theme=light_theme),
            risk_breakdown(filtered, light_theme=light_theme),
            risk_over_time(filtered, light_theme=light_theme),
            amount_feature_scatter(filtered, light_theme=light_theme),
            feature_heatmap(filtered, light_theme=light_theme),
            top_risk_table(filtered),
        )


def _gauge_color(score: float) -> str:
    if score >= 75:
        return pl.RISK_COLORS['Critical Risk']
    elif score >= 50:
        return pl.RISK_COLORS['High Risk']
    elif score >= 25:
        return pl.RISK_COLORS['Moderate Risk']
    return pl.RISK_COLORS['Low Risk']


def _coerce_amount(value, fallback: int) -> int:
    if value is None or value == '':
        return fallback
    try:
        if isinstance(value, str):
            cleaned = re.sub(r'[^0-9,.-]', '', value).strip()
            if not cleaned:
                return fallback

            if ',' in cleaned and '.' in cleaned:
                if cleaned.rfind(',') > cleaned.rfind('.'):
                    cleaned = cleaned.replace('.', '').replace(',', '.')
                else:
                    cleaned = cleaned.replace(',', '')
            elif ',' in cleaned:
                parts = cleaned.split(',')
                if len(parts) == 2 and len(parts[1]) <= 2:
                    cleaned = cleaned.replace(',', '.')
                else:
                    cleaned = cleaned.replace(',', '')
            elif '.' in cleaned:
                parts = cleaned.split('.')
                if len(parts) > 2:
                    cleaned = cleaned.replace('.', '')
                elif len(parts) == 2 and len(parts[1]) > 2:
                    cleaned = cleaned.replace('.', '')

            return int(round(float(cleaned)))
        return int(round(float(value)))
    except (TypeError, ValueError):
        return fallback


if __name__ == '__main__':
    app.run(debug=True, port=8051)
