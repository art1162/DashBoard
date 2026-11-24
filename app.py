from dash import Dash, dcc, html

from charts import empty_figure


app = Dash(__name__, title="Вместе в школу | Дашборд помощи")

CHARTS = (
    ("cash-flow", "Поступления и закупки"),
    ("expenses", "Структура закупок"),
    ("donations", "Распределение взносов"),
    ("correlation", "Взносы и закупки по неделям"),
)
METRICS = (
    ("total-donations", "Взносы по СБП"),
    ("total-expenses", "Закупки фонда"),
    ("total-items", "Выдано вещей"),
    ("total-reports", "Отправлено отчётов"),
)


def chart_panel(graph_id, title):
    return html.Section([
        html.H2(title),
        dcc.Graph(id=graph_id, figure=empty_figure(), config={"displaylogo": False}),
    ], className=f"panel chart-panel {graph_id}")


def summary_panel():
    return html.Section([
        html.H2("Сводка по категориям"),
        html.Div("Загрузите CSV, чтобы увидеть сводку.", id="category-summary"),
    ], className="panel summary-panel")


app.layout = html.Main([
    html.Header([
        html.H1("Вместе в школу"),
        html.P("Дашборд адресной помощи школьникам"),
    ], className="page-header"),
    html.Section([
        html.H2("Загрузка и фильтры"),
        dcc.Upload(html.Button("Выбрать CSV", type="button"), id="csv-upload", accept=".csv"),
        html.Div("Ожидается CSV-файл.", id="upload-status", role="status"),
        html.Div([
            html.Div([
                html.Label("Период", htmlFor="period"),
                dcc.Dropdown(id="period", options=[
                    {"label": "Весь период", "value": "all"},
                    {"label": "Последние 30 дней", "value": 30},
                    {"label": "Последние 90 дней", "value": 90},
                    {"label": "Последние 365 дней", "value": 365},
                ], value="all", clearable=False),
            ]),
            html.Div([
                html.Label("Категория вещей", htmlFor="categories"),
                dcc.Dropdown(id="categories", multi=True, placeholder="Все категории"),
            ]),
            html.Div([
                html.Label("Способ помощи", htmlFor="channels"),
                dcc.Dropdown(id="channels", multi=True, placeholder="Все способы"),
            ]),
        ], className="filters"),
        html.Div(id="selection-status", role="status"),
    ], className="panel controls"),
    html.Section([
        html.Article([html.P(label), html.Strong("—", id=metric_id)], className="metric")
        for metric_id, label in METRICS
    ], className="metrics", **{"aria-label": "Ключевые показатели"}),
    html.Div([chart_panel(graph_id, title) for graph_id, title in CHARTS], className="charts"),
    summary_panel(),
    dcc.Store(id="dataset"),
], className="dashboard")


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8050, debug=False)
