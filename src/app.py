import datetime
import pandas as pd
import plotly.express as px
from plotly.subplots import make_subplots
import dash
import dash_daq as daq
from dash import html
from dash import dcc
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output
from func import get_covid19_npatients, get_geojson, get_covid19_ndeaths


df = get_covid19_npatients()
geojson = get_geojson()
df_ndeaths = get_covid19_ndeaths()

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
# title
app.title = 'COVID-19 Dashboard'
server = app.server

background_color = '#EEFFFF'

ndeaths_transition_graph = px.bar(df_ndeaths, x="date", y="value", color="variable", barmode="overlay", log_y=True)
ndeaths_transition_graph.update_layout(
    paper_bgcolor=background_color
)

app.layout = html.Div(
    children=[
        html.Div(
            html.H1('COVID-19 Dashboard', style={'textAlign': 'center'})
        ),
        dbc.Row([
            dbc.Col(
                html.Div([
                    daq.ToggleSwitch(
                        id='toggle-switch',
                        value=False,
                        label=f'{df["date"].unique()[-1]}時点の累計陽性者数を表示',
                        labelPosition='left'
                    ),
                    dcc.DatePickerSingle(
                        id='selectdate',
                        min_date_allowed=datetime.datetime.strptime(df['date'].unique()[0], '%Y-%m-%d'),
                        max_date_allowed=datetime.datetime.strptime(df['date'].unique()[-1], '%Y-%m-%d'),
                        initial_visible_month=datetime.datetime.strptime(df['date'].unique()[-1], '%Y-%m-%d'),
                        date=df['date'].unique()[-1],
                        display_format='Y/M/D',
                        disabled=True
                    ),
                    dcc.Loading(
                        dcc.Graph(id='japanmap',
                                clickData={'points': [{'curveNumber': 0, 'pointNumber': 12, 'pointIndex': 12, 'location': '東京都', 'z': 729}]}
                        ),
                        type="graph"
                    )
                ]), md=5
            ),
            dbc.Col(
                html.Div([
                    dcc.Loading(
                        dcc.Graph(id='prefecture_npatients_transition'),
                        type="graph"
                    ), 
                    dcc.Loading(
                        dcc.Graph(id='prefecture_npatients_ranking'),
                        type="graph"
                    ),
                ]), md=7
            ),
        ]),
        dcc.Graph(id='ndeaths_transition',
            figure=ndeaths_transition_graph
        ),
        html.Div(['データソースは', html.A('こちら', href='https://corona.go.jp/dashboard/', target="_blank")],
            style={'padding':'20px 0px 0px 0px', 'font-size':'11pt', 'textAlign': 'center'}
        ),
        html.Div(['© 2021 ', html.A('kinosi', href='https://github.com/catdance124', target="_blank")],
            style={'padding':'20px 0px 0px 0px', 'font-size':'9pt', 'textAlign': 'center'}
        )
    ],
    style={'height':'100%', 'margin':'0', 'padding':'0', 'text-align': 'center', 'background-color':background_color}
)


@app.callback(
    Output("selectdate", "disabled"),
    [Input("toggle-switch", "value")])
def update_selectdate_disabled(toggle_cumulative):
    return toggle_cumulative


@app.callback(
    Output('japanmap', 'figure'),
    [Input('selectdate', 'date'),
    Input('toggle-switch', 'value')])
def update_japanmap(selected_date, toggle_cumulative):
    selectdf = df[df['date'] == selected_date]
    fig = px.choropleth_mapbox(selectdf,
                               geojson=geojson,
                               locations=selectdf['name_jp'],
                               color=selectdf['npatients'] if toggle_cumulative else selectdf['npatients_today'],
                               featureidkey='properties.nam_ja',
                               color_continuous_scale="Inferno",
                               mapbox_style="carto-positron",
                               zoom=4,
                               center={"lat": 36, "lon": 138},
                               opacity=0.5,
                               labels={"value": "人数"}
                               )
    fig.update_layout(
            margin={"r": 0, "t": 0, "l": 0, "b": 0}, height=600, paper_bgcolor=background_color)
    return fig


@app.callback(
    Output('prefecture_npatients_transition', 'figure'),
    [Input('japanmap', 'clickData'),
    Input('prefecture_npatients_ranking', 'clickData')])
def draw_prefecture_npatients_transition_graph(clickData_map, clickData_bar):
    # prepare data
    ctx = dash.callback_context
    if not ctx.triggered:
        prefecture = clickData_map['points'][0]['location']
    else:
        trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
        if trigger_id == 'japanmap':
            prefecture = ctx.triggered[0]['value']['points'][0]['location']
        elif trigger_id == 'prefecture_npatients_ranking':
            prefecture = ctx.triggered[0]['value']['points'][0]['label']
    selectdf = df[df['name_jp'] == prefecture].copy()
    # generate a regression line
    selectdf['date_int'] = pd.to_datetime(selectdf['date']).astype('int64') // 10**9
    help_fig = px.scatter(selectdf, x='date_int', y='npatients', trendline="lowess")
    selectdf['trend'] = help_fig["data"][1]['y']

    # figure components
    fig_components = []
    fig_components.append(
        px.bar(selectdf, x='date', y='npatients')
    )
    fig_components.append(
        px.line(selectdf, x='date', y='trend')
    )

    # trace whole figure
    fig = make_subplots()
    for fig_component in fig_components:
        for trace in range(len(fig_component["data"])):
            fig.append_trace(fig_component["data"][trace], row=1, col=1)
    fig.update_layout(
            title_text=f'{prefecture}の累計陽性数推移', title_x=0.5, 
            margin={"r": 0, "t": 40, "l": 0, "b": 0}, height=300, 
            paper_bgcolor=background_color)
    return fig


@app.callback(
    Output('prefecture_npatients_ranking', 'figure'),
    [Input('selectdate', 'date'),
    Input('toggle-switch', 'value')])
def draw_prefecture_npatients_ranking_graph(selected_date, toggle_cumulative):
    column_name = 'npatients' if toggle_cumulative else 'npatients_today'
    selectdf = df[df['date'] == selected_date].sort_values(column_name)
    
    # figure components
    fig_components = []
    fig_components.append(
        px.bar(selectdf[-10:], x=column_name, y="name_jp", barmode="overlay", 
                text=column_name, color=column_name, orientation='h')
    )
    fig_components.append(
        px.bar(selectdf[-20:-10], x=column_name, y="name_jp", barmode="overlay", 
                text=column_name, color=column_name, orientation='h')
    )

    # trace whole figure
    fig = make_subplots(rows=1, cols=2)
    for i, fig_component in enumerate(fig_components):
        for trace in range(len(fig_component["data"])):
            fig.append_trace(fig_component["data"][trace], row=1, col=i+1)
    fig.update_xaxes(range=[0, selectdf[column_name].max()])
    fig.update_layout(
            title_text=f'{df["date"].unique()[-1]}時点の累計陽性患者数' if toggle_cumulative else f'{selected_date}の陽性患者数', 
            title_x=0.5,
            margin={"r": 0, "t": 100, "l": 0, "b": 0}, height=400,
            uniformtext_minsize=12,
            paper_bgcolor=background_color)
    return fig


if __name__ == '__main__':
    app.run_server(host='0.0.0.0', debug=False)