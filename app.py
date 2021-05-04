import os, datetime
import plotly.express as px
import dash
import dash_daq as daq
import dash_html_components as html
import dash_core_components as dcc
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output
from func import get_covid19_npatients, get_geojson, get_covid19_ndeaths


df = get_covid19_npatients()
geojson = get_geojson()
df_ndeaths = get_covid19_ndeaths()

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server
app.layout = html.Div([
    html.Div(
        html.H1('COVID-19 Dashboard',
                style={'textAlign': 'center'})
    ),
    dbc.Row([
        dbc.Col(
            html.Div([
                daq.ToggleSwitch(
                    id='toggle-switch',
                    value=False,
                    label=f'{df["date"].unique()[0]}時点の累計陽性者数を表示',
                    labelPosition='left'
                ),
                dcc.DatePickerSingle(
                    id='selectdate',
                    min_date_allowed=datetime.datetime.strptime(df['date'].unique()[-1], '%Y-%m-%d'),
                    max_date_allowed=datetime.datetime.strptime(df['date'].unique()[0], '%Y-%m-%d'),
                    initial_visible_month=datetime.datetime.strptime(df['date'].unique()[0], '%Y-%m-%d'),
                    date=df['date'].unique()[0],
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
        figure=px.bar(df_ndeaths, x="date", y="value", color="variable", barmode="overlay", log_y=True)
    )
])


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
    fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0}, height=600)
    return fig


@app.callback(
    Output('prefecture_npatients_transition', 'figure'),
    [Input('japanmap', 'clickData')])
def draw_prefecture_npatients_transition_graph(clickData):
    if clickData is None:
        return dash.no_update
    prefecture = clickData['points'][0]['location']
    selectdf = df[df['name_jp'] == prefecture]
    fig = px.bar(selectdf, x="date", y="npatients")
    fig.update_layout(title_text=f'{prefecture}の累計陽性数推移', title_x=0.5, 
                    margin={"r": 0, "t": 40, "l": 0, "b": 0}, height=300)
    return fig

@app.callback(
    Output('prefecture_npatients_ranking', 'figure'),
    [Input('selectdate', 'date'),
    Input('toggle-switch', 'value')])
def draw_prefecture_npatients_ranking_graph(selected_date, toggle_cumulative):
    column_name = 'npatients' if toggle_cumulative else 'npatients_today'
    selectdf = df[df['date'] == selected_date].sort_values(column_name)
    fig = px.bar(selectdf[-15:], x=column_name, y="name_jp", barmode="overlay", orientation='h')
    title = f'{df["date"].unique()[0]}時点の累計陽性患者数' if toggle_cumulative else f'{selected_date}の陽性患者数'
    fig.update_layout(title_text=title, title_x=0.5,
                margin={"r": 0, "t": 100, "l": 0, "b": 0}, height=400)
    return fig


if __name__ == '__main__':
    app.run_server(debug=True)