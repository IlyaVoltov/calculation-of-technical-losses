#!/usr/bin/env python
# coding: utf-8

"""
Визуализация тех потерь
"""


import dash
import dash_table
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import pandas as pd
import numpy  as np
from   shapely.geometry import Polygon, Point
import json
from dash.dependencies import Input, Output

app1 = dash.Dash(__name__)

loss_df = pd.read_csv('data//generallosses.csv')  .set_index('datetime')
loss_df.index = pd.to_datetime(loss_df.index)
file = 'data//TS2199.json'
openfile = open(file, encoding = 'utf-8')
jsondata = json.load(openfile)
df = pd.DataFrame(jsondata)
openfile.close()

props = []
for i in df.index:
    feat  = df.features[i]
    prop  = feat['properties']
    name  = prop['name']
    types = prop['type']
    
    features = pd.DataFrame(feat)
    f_type = features.loc['type', 'geometry']
    
    if f_type == 'Polygon':
        geocode = features.loc['coordinates', 'geometry'][0]
        
        geo_lon = []
        geo_lat = []
    
        for geo_inst in geocode:
            geo_lon.append(geo_inst[0]) 
            geo_lat.append(geo_inst[1])
            
    elif f_type == 'LineString':
        geocode = features.loc['coordinates', 'geometry']
        
        geo_lon = []
        geo_lat = []
    
        for geo_inst in geocode:
            geo_lon.append(geo_inst[0]) 
            geo_lat.append(geo_inst[1])
        
    else:
        geo_lon = features.loc['coordinates', 'geometry'][0]
        geo_lat = features.loc['coordinates', 'geometry'][1]
        
    props.append([f_type, name, types, geo_lon, geo_lat])

topology = pd.DataFrame(props, 
                        columns = ['type', 'name', 'class', 'lon', 'lat'])

t_group  = topology.groupby('type')
line_df  = t_group.get_group('LineString').reset_index().iloc[:, 1:]
point_df = t_group.get_group('Point')
poly_df  = t_group.get_group('Polygon')

access = 'pk.eyJ1Ijoia3Vrc2Vua29zcyIsImEiOiJjazE4NDlkZTQwMmtwM2NzenRmbm9rNjF2In0.j0d6QcToTviyQ0-KdzEIMA'

map_figure = go.Figure(go.Scattermapbox(
                                        lat = point_df.lat,
                                        lon = point_df.lon,
                                        mode = 'markers',
                                        marker = go.scattermapbox.Marker(color = '#00a8ff',
                                                                         size = 10),
                                        name = 'Кабельные киоски',
                                        hoverinfo = 'skip',
                                        showlegend = False))   


for i, types, name, cl, lon, lat in line_df.itertuples():
    line_custom = line_df.iloc[i, :]
    len_lat = len(lat)
    df_repeated = pd.concat([line_custom] * len_lat, axis = 1).T.reset_index().iloc[:, 1 : 4]
    map_figure.add_trace(go.Scattermapbox(
                                        lat = lat,
                                        lon = lon,
                                        mode = 'lines',
                                        name = 'Кабельные линии',
                                        marker = go.scattermapbox.Marker(color = '#3248a8'),
                                        customdata = df_repeated,
                                        hovertemplate = 'Наименование - %{customdata[1]}' + 
                                                        '<br>Тип объекта - %{customdata[2]}<br>',
                                        showlegend = False))  
        
for i, types, name, cl, lon, lat in poly_df.itertuples():
    map_figure.add_trace(go.Scattermapbox(
                                        lat = lat,
                                        lon = lon,
                                        mode = 'lines+text',
                                        fill = 'toself',
                                        name = 'Здания и сооружения',
                                        marker = go.scattermapbox.Marker(size = 1,
                                                                         color = '#3248a8'),
                                        showlegend = False,
                                        hoverinfo = 'skip',
                                        fillcolor = 'rgba(0, 168, 255, 0.6)'))
map_figure.update_layout(
                  clickmode = 'select',
                  margin = {'r' : 0,'t' : 0, 'l' : 0, 'b' : 0},
                  hovermode = 'closest',
                  hoverlabel = dict(
                                    bgcolor = 'black', 
                                    font_size = 10, 
                                    font_family = 'Helvetica',
                                    font_color = 'white'
                                    ),
                  mapbox = dict(
                                accesstoken = access,
                                bearing = 0,
                                center = go.layout.mapbox.Center(
                                         lat = 60.005654,
                                         lon = 30.419074
                                         ),
                  pitch = 0,
                  zoom = 16,   
                  style = 'light'    
    )
)                                        


app1.layout = html.Div(children = [dcc.Graph(id = 'fill_area',
                                            figure = map_figure,
                                            style = {'height' : 700})])

app1.layout = html.Div(children = [
        html.Div([
            dcc.Graph(id = 'map', 
                      figure = map_figure,
                      hoverData = {'points': [{'customdata': ['LineString',
                                                              'ТП 2199/2 - Р 630/А']}]})
        ]),

        html.Div([
            dcc.Graph(id = 'bar_chart')
        ]),
    ])

def create_graph(df, line_name):
    return {
        'data': [dict(
                    x = df.index,
                    y = df.round(2),
                    type = 'scatter',
                    marker = dict(color = '#3248a8'),
                    mode = 'lines',
                    name = 'Потери',
                    fill = 'tozeroy',
                    template = 'plotly_dark',
                    textposition = 'outside',
                    showlegend = False)],
        
        'layout': dict(
                   xaxis = dict(title = 'Дата и время показания прибора учета'),
                   yaxis = dict(title = 'Технические потери электроэнергии, кВтч'),
                   hovermode = 'x',
                   template = 'plotly_dark',
                   title = line_name,
                   font = dict(color = '#3248a8'))}
     
@app.callback(
    dash.dependencies.Output('bar_chart', 'figure'),
    [dash.dependencies.Input('map', 'hoverData')])

def create_plot(hoverData):
    type_branch = hoverData['points'][0]['customdata'][0]
    line_name = hoverData['points'][0]['customdata'][1]
    check_name = line_name in loss_df.columns
    
    if (type_branch == 'LineString') and (check_name == True):
        df = loss_df[line_name]
    else:
        df = pd.Series(0, index = loss_df.index)
    return create_graph(df, line_name)
