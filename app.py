import os
import plotly.express as px
import dash
import dash_html_components as html
import dash_core_components as dcc
from dash.dependencies import Input, Output
from func import get_covid19_npatients, get_geojson, get_covid19_ndeaths


df = get_covid19_npatients()
geojson = get_geojson()
df_ndeaths = get_covid19_ndeaths()

app = dash.Dash(__name__)
server = app.server
app.layout = html.Div([
    html.Div(
        html.H1('COVID-19 Dashboard',
                style={'textAlign': 'center'})
    ),
    dcc.Dropdown(
        id='selectdate',
        options=[{'label': i, 'value': i}
                 for i in df['date'].unique()],
        placeholder="日付を選択",
        value="2021-04-15"
    ),
    dcc.Loading(
        dcc.Graph(id='japanmap',
                clickData={'points': [{'curveNumber': 0, 'pointNumber': 12, 'pointIndex': 12, 'location': '東京都', 'z': 729}]}
        )
    ),
    dcc.Loading(
        dcc.Graph(id='prefecture_npatients_transition')
    ),
    dcc.Graph(id='ndeaths_transition',
        figure=px.bar(df_ndeaths, x="date", y="value", color="variable", barmode="overlay", log_y=True)
    )
])


@app.callback(
    dash.dependencies.Output('japanmap', 'figure'),
    [dash.dependencies.Input('selectdate', 'value')])
def update_japanmap(selected_date):
    selectdf = df[df['date'] == selected_date]
    fig = px.choropleth_mapbox(selectdf,
                               geojson=geojson,
                               locations=selectdf['name_jp'],
                               color=selectdf['npatients_today'],
                               featureidkey='properties.nam_ja',
                               color_continuous_scale="Viridis",
                               mapbox_style="carto-positron",
                               zoom=5,
                               center={"lat": 36, "lon": 138},
                               opacity=0.5,
                               labels={"value": "人数"}
                               )
    fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
    return fig


@app.callback(
    Output('prefecture_npatients_transition', 'figure'),
    Input('japanmap', 'clickData'))
def draw_prefecture_npatients_transition_graph(clickData):
    if clickData is None:
        return dash.no_update
    prefecture = clickData['points'][0]['location']
    selectdf = df[df['name_jp'] == prefecture]
    fig = px.bar(selectdf, x="date", y="npatients")
    fig.update_layout(title_text=f'{prefecture}の累計陽性数推移', title_x=0.5)
    return fig


if __name__ == '__main__':
    app.run_server(debug=True)