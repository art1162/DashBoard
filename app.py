from datetime import date
from pathlib import Path

from dash import Dash, Input, Output, State, callback, dash_table, dcc, html, no_update
from dash.exceptions import PreventUpdate
from dash.dash_table.Format import Format, Scheme
from flask import send_from_directory

from charts import cash_chart, correlation_chart, donation_chart, empty_figure, expense_chart
from data import CHANNELS, aggregate, parse_upload, select_records


app = Dash(__name__, title="Вместе в школу | Дашборд помощи")
app.server.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024
DATA_DIR = Path(__file__).resolve().parent / "data"

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
        dcc.Graph(id=graph_id, figure=empty_figure(), responsive=True,
                  config={"displaylogo": False, "modeBarButtonsToRemove": ["select2d", "lasso2d"]}),
    ], className=f"panel chart-panel {graph_id}")


def summary_panel():
    money = Format(precision=2, scheme=Scheme.fixed, group=True)
    return html.Section([
        html.H2("Сводка по категориям"),
        dash_table.DataTable(
            id="category-summary", data=[], sort_action="native", page_size=8,
            locale_format={"decimal": ",", "group": " ", "grouping": [3]},
            style_table={"overflowX": "auto"},
            style_cell={"padding": "0.7rem", "minWidth": "7rem", "fontFamily": "inherit",
                        "fontSize": ".9rem", "borderColor": "#e8e0f1", "color": "#271d3e"},
            style_cell_conditional=[{"if": {"column_id": "category"}, "textAlign": "left"}],
            style_header={"backgroundColor": "#f5f1fc", "fontWeight": "600"},
            columns=[
                {"name": "Категория", "id": "category"},
                {"name": "Взносы, ₽", "id": "donation", "type": "numeric", "format": money},
                {"name": "Закупки, ₽", "id": "purchase", "type": "numeric", "format": money},
                {"name": "Выдано, шт.", "id": "delivered", "type": "numeric"},
                {"name": "Отчёты", "id": "reported", "type": "numeric"},
            ],
        ),
    ], className="panel summary-panel")


app.layout = html.Main([
    html.Header([
        html.H1("Вместе в школу"),
        html.P("Аналитика взносов, закупок и выдачи школьных вещей семьям"),
    ], className="page-header"),
    html.Section([
        html.H2("Загрузка и фильтры"),
        html.Div([
            html.Div([
                dcc.Upload(html.Button("Загрузить CSV", type="button", className="upload-button"),
                           id="csv-upload", accept=".csv"),
                html.A("Скачать пример CSV", href="/example.csv", className="sample-link"),
            ], className="file-buttons"),
            html.Div("Ожидается CSV-файл.", id="upload-status", role="status"),
        ], className="file-actions"),
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


@app.server.get("/example.csv")
def download_example():
    return send_from_directory(DATA_DIR, "example.csv", as_attachment=True)


def display_date(value):
    return date.fromisoformat(value).strftime("%d.%m.%Y")


def display_amount(cents):
    rubles, kopecks = divmod(cents, 100)
    integer = f"{rubles:,}".replace(",", " ")
    return f"{integer},{kopecks:02d} ₽" if kopecks else f"{integer} ₽"


@callback(
    Output("dataset", "data"), Output("upload-status", "children"),
    Output("upload-status", "className"), Output("categories", "options"),
    Output("categories", "value"), Output("channels", "options"),
    Output("channels", "value"), Output("period", "value"),
    Input("csv-upload", "contents"), State("csv-upload", "filename"),
    prevent_initial_call=True,
)
def load_data(contents, filename):
    if contents is None:
        raise PreventUpdate
    try:
        records = parse_upload(contents, filename)
    except ValueError as error:
        return (no_update, str(error), "upload-error", no_update, no_update,
                no_update, no_update, no_update)

    dates = [record["date"] for record in records]
    categories = sorted({record["category"] for record in records}, key=str.casefold)
    channels = {record["channel"] for record in records}
    options = [{"label": label, "value": key} for key, label in CHANNELS.items()
               if key in channels]
    status = (f"{filename} · операций: {len(records)} · "
              f"{display_date(min(dates))} — {display_date(max(dates))}")
    return records, status, "upload-success", categories, [], options, [], "all"


@callback(
    *(Output(metric_id, "children") for metric_id, _ in METRICS),
    *(Output(graph_id, "figure") for graph_id, _ in CHARTS),
    Output("category-summary", "data"), Output("selection-status", "children"),
    Input("dataset", "data"), Input("period", "value"),
    Input("categories", "value"), Input("channels", "value"),
)
def update_dashboard(dataset, period, categories, channels):
    selected = select_records(dataset, period, set(categories or []), set(channels or []))
    if not selected:
        message = "Нет операций по выбранным фильтрам" if dataset else "Загрузите CSV, чтобы увидеть данные"
        figure = empty_figure(message)
        return "—", "—", "—", "—", figure, figure, figure, figure, [], message if dataset else ""

    totals, grouped, weeks, donations = aggregate(selected)
    summary = [
        {**values, "category": category, "donation": values["donation"] / 100,
         "purchase": values["purchase"] / 100}
        for category, values in sorted(grouped.items(), key=lambda pair: pair[0].casefold())
    ]
    return (display_amount(totals["donation"]), display_amount(totals["purchase"]),
            str(totals["delivered"]), str(totals["reported"]), cash_chart(weeks),
            expense_chart(grouped), donation_chart(donations), correlation_chart(weeks), summary,
            f"Показано операций: {len(selected)} из {len(dataset)}")


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8050, debug=False)
