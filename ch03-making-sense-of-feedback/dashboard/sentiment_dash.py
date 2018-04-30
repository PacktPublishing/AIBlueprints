import dash
from dash.dependencies import Input, Output
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go
import datetime
import plotly
import sqlite3
import math

db = sqlite3.connect('../sentiment/sentiment.db')
cursor = db.cursor()

app = dash.Dash("Sentiment")
app.css.append_css({'external_url': 'https://codepen.io/chriddyp/pen/bWLwgP.css'})
app.layout = html.Div(
    html.Div([
        html.H4('Sentiment Live Feed'),
        dcc.Graph(id='live-update-graph'),
        dcc.Interval(
            id='interval-component',
            interval=60*60*1000, # in milliseconds
            n_intervals=0
        ),
        html.Table([
            html.Thead([html.Tr([
                html.Th('Source'),
                html.Th('Date'),
                html.Th('Text'),
                html.Th('Sentiment')])]),
            html.Tbody(id='live-update-text')])
    ])
)

@app.callback(Output('live-update-graph', 'figure'),
              [Input('interval-component', 'n_intervals')])
def update_graph_live(n):
    cursor.execute("select datefound, source, sentiment_num from sentiment")
    data = {}
    while True:
        row = cursor.fetchone()
        if row == None:
            break
        source = row[1]
        if source not in data:
            data[source] = {}
        datefound = row[0]
        if datefound not in data[source]:
            data[source][datefound] = []
        data[source][datefound].append(row[2])

    figdata = {'sentiment': {}, 'count': {}}
    for source in data:
        figdata['sentiment'][source] = {'x': [], 'y': []}
        figdata['count'][source] = {'x': [], 'y': []}
        for datefound in data[source]:
            sentcnt = 0
            sentsum = 0
            for sentval in data[source][datefound]:
                sentsum += sentval
                sentcnt += 1
            figdata['sentiment'][source]['x'].append(datefound)
            figdata['sentiment'][source]['y'].append(sentsum / float(len(data[source][datefound])))
            figdata['count'][source]['x'].append(datefound)
            figdata['count'][source]['y'].append(sentcnt)

    fig = plotly.tools.make_subplots(rows=2, cols=1, vertical_spacing=0.2, shared_xaxes=True,
            subplot_titles=('Average sentiment', 'Number of positive and negative statements'))
    
    for source in sorted(figdata['sentiment'].keys()):
        fig.append_trace(
            go.Scatter(x = figdata['sentiment'][source]['x'],
                       y = figdata['sentiment'][source]['y'],
                       xaxis = 'x1',
                       yaxis = 'y1',
                       text = source,
                       name = source),
            1, 1)

    for source in sorted(figdata['count'].keys()):
        fig.append_trace(
            go.Scatter(x = figdata['count'][source]['x'],
                       y = figdata['count'][source]['y'],
                       xaxis = 'x1',
                       yaxis = 'y2',
                       text = source,
                       name = source,
                       showlegend = False),
            2, 1)

    fig['layout']['yaxis1'].update(range=[0, 4])

    return fig

@app.callback(Output('live-update-text', 'children'),
              [Input('interval-component', 'n_intervals')])
def update_text(n):
    cursor.execute("select datefound, source, msg, sentiment from sentiment order by datefound desc limit 20")
    result = []
    while True:
        row = cursor.fetchone()
        if row == None:
            break
        datefound = row[0]
        source = row[1]
        msg = row[2]
        sentiment = row[3]
        result.append(html.Tr([
            html.Td(source),
            html.Td(datefound),
            html.Td(msg),
            html.Td(sentiment)]))

    return result

if __name__ == '__main__':
    app.run_server()

