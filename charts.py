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


