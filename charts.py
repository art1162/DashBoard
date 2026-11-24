import plotly.graph_objects as go

COLORS = ("#6d45be", "#c96129", "#35868b", "#5278cb", "#95578b", "#648548")


def chart_base():
    figure = go.Figure()
    figure.update_layout(template="plotly_white", height=300, margin=dict(l=60, r=20, t=18, b=50),
                         separators=", ", colorway=COLORS, hoverlabel=dict(namelength=-1))
    figure.update_xaxes(automargin=True)
    figure.update_yaxes(automargin=True)
    return figure


def empty_figure(message="Загрузите CSV, чтобы увидеть данные"):
    figure = chart_base()
    figure.update_xaxes(visible=False)
    figure.update_yaxes(visible=False)
    figure.add_annotation(x=0.5, y=0.5, xref="paper", yref="paper", text=message, showarrow=False)
    return figure


def cash_chart(weeks):
    if not weeks:
        return empty_figure("За период нет денежных операций")
    figure = chart_base()
    for event, label in (("donation", "Взносы по СБП"), ("purchase", "Закупки фонда")):
        figure.add_scatter(x=list(weeks), y=[row[event] / 100 for row in weeks.values()],
                           mode="lines+markers", name=label,
                           hovertemplate="Неделя с %{x|%d.%m.%Y}<br>%{y:,.2f} ₽")
    figure.update_xaxes(tickformat="%d.%m.%y")
    figure.update_yaxes(ticksuffix=" ₽", rangemode="tozero")
    figure.update_layout(legend=dict(orientation="h", x=0, y=1.14), margin=dict(t=44))
    return figure


def expense_chart(categories):
    expenses = sorted(((name, values["purchase"] / 100) for name, values in categories.items()
                       if values["purchase"] > 0), key=lambda pair: -pair[1])
    if not expenses:
        return empty_figure("За период нет закупок фонда")
    figure = chart_base()
    figure.add_pie(labels=[name for name, _ in expenses], values=[amount for _, amount in expenses],
                   hole=0.58, textinfo="percent",
                   hovertemplate="%{label}<br>%{value:,.2f} ₽ · %{percent}<extra></extra>")
    figure.update_layout(legend=dict(orientation="h", x=0, y=-0.02), margin=dict(l=18, r=18, b=60))
    return figure


def donation_chart(donations):
    if not donations:
        return empty_figure("За период нет денежных взносов")
    figure = chart_base()
    figure.add_histogram(x=[value / 100 for value in donations], nbinsx=14,
                         marker=dict(line=dict(width=1, color="#fff")),
                         hovertemplate="Размер взноса: %{x} ₽<br>Операций: %{y}<extra></extra>")
    figure.update_xaxes(title="Размер взноса, ₽")
    figure.update_yaxes(title="Количество взносов", rangemode="tozero", dtick=1)
    return figure


def correlation_chart(weeks):
    if not weeks:
        return empty_figure("За период нет денежных операций")
    figure = chart_base()
    figure.add_scatter(x=[row["donation"] / 100 for row in weeks.values()],
                       y=[row["purchase"] / 100 for row in weeks.values()],
                       customdata=[week.strftime("%d.%m.%Y") for week in weeks],
                       mode="markers", marker=dict(size=10, opacity=0.8, line=dict(color="#fff", width=1)),
                       hovertemplate="Неделя с %{customdata}<br>Взносы: %{x:,.2f} ₽"
                                     "<br>Закупки: %{y:,.2f} ₽<extra></extra>")
    figure.update_xaxes(title="Взносы, ₽", rangemode="tozero")
    figure.update_yaxes(title="Закупки, ₽", rangemode="tozero")
    return figure
