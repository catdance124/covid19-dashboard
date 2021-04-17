import requests
import pandas as pd
import geopandas as gpd
import json


def get_covid19_data():
    url = "https://opendata.corona.go.jp/api/Covid19JapanAll"
    response = requests.get(url)
    df = pd.DataFrame(response.json()['itemList'])
    ## edit
    df['npatients'] = df['npatients'].astype(int)
    ## calc npatients per day
    for name in df['name_jp'].unique():
        df.loc[df['name_jp']==name, ['npatients_today']] = df[df['name_jp']==name]['npatients'].diff(-1)
    df.fillna(0)
    return df

def get_geojson():
    # url = "https://raw.githubusercontent.com/dataofjapan/land/master/japan.geojson"
    url = "japan.geojson"
    jsonfile = gpd.read_file(url)
    dfjson = json.loads(jsonfile.to_json())
    return dfjson