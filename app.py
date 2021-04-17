import plotly.express as px
import dash
import dash_html_components as html
import dash_core_components as dcc
from dash.dependencies import Input, Output
from func import get_covid19_data, get_geojson


df = get_covid19_data()
geojson = get_geojson()

app = dash.Dash(__name__)
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
        dcc.Graph(id='japanmap')
    )
])

@app.callback(
    dash.dependencies.Output('japanmap', 'figure'),
    [dash.dependencies.Input('selectdate', 'value')])
def update_output(selected_date):
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

if __name__ == '__main__':
    app.run_server(debug=True)