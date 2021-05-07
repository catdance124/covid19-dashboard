import requests
import pandas as pd
import geopandas as gpd
import numpy as np
import json


def get_covid19_npatients():
    url = "https://opendata.corona.go.jp/api/Covid19JapanAll"
    response = requests.get(url)
    df = pd.DataFrame(response.json()['itemList'])
    ## edit
    df['npatients'] = df['npatients'].astype(int)
    df.sort_values(['name_jp', 'date'], inplace=True)
    df.loc[df["npatients"] > df["npatients"].quantile(0.9999999), ['npatients']] = np.nan
    df["npatients"].interpolate(inplace=True)
    ## calc npatients per day
    for name in df['name_jp'].unique():
        df.loc[df['name_jp']==name, ['npatients_today']] = df[df['name_jp']==name]['npatients'].diff(1)
    df = df.dropna()
    return df


def get_covid19_ndeaths():
    df_npatients = get_covid19_npatients()
    url = "https://opendata.corona.go.jp/api/Covid19JapanNdeaths"
    response = requests.get(url)
    df_ndeaths = pd.DataFrame(response.json()['itemList'])
    merged = pd.merge(df_npatients.groupby(by=['date']).sum(), df_ndeaths, on='date')
    merged.drop('npatients_today', axis=1, inplace=True)
    return pd.melt(merged, id_vars=['date'])

def get_geojson():
    # url = "https://raw.githubusercontent.com/dataofjapan/land/master/japan.geojson"
    url = "japan.geojson"
    jsonfile = gpd.read_file(url)
    dfjson = json.loads(jsonfile.to_json())
    return dfjson