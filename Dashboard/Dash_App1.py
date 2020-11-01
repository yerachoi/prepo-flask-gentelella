# -*- coding: utf-8 -*-
"""
Created on Sun Jul  8 10:39:33 2018

@author: jimmybow
"""
from dash import Dash
from dash.dependencies import Input, State, Output
from .Dash_fun import apply_layout_with_auth, load_object, save_object
import dash_core_components as dcc
import dash_html_components as html

import plotly.express as px
import pandas as pd
import datetime as dt

url_base = '/dash/app1/'

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

# data loading
data_path = "/mnt/d/yerachoi/plink-flask-gentelella/data/user_docs_df2.csv"
df = pd.read_csv(data_path)

# clip_at 컬럼 시간 분 초 삭제
# df.clip_at = df.clip_at.astype(str)
df['clip_at'] = df['clip_at'].astype(str)
df['clip_at'] = df['clip_at'].str[:10]

# datetime으로 변경
# df['clip_at'] = pd.to_datetime(df['clip_at'], format = '%Y-%m-%d')

# doc저장한 시점(clip_at) 기준으로 groupby한 dataframe
date_df = df.groupby('clip_at').count().reset_index()

date_lst = df.clip_at.unique()

# app = dash.Dash(__name__) # external_stylesheets=external_stylesheets)

# layout = html.Div([
#     html.Div('This is dash app1'), html.Br(),
#     dcc.Input(id = 'input_text'), html.Br(), html.Br(),
#     html.Div(id = 'target')
# ])
layout = html.Div([
    dcc.Graph(id='graph-with-slider'),
    dcc.Slider(
        id='year-slider',
        min=date_df['clip_at'].min(),
        max=date_df['clip_at'].max(),
        value=date_df['clip_at'].min(),
        marks={str(date): str(date) for date in date_lst},
        step=None
    )
])

def Add_Dash(server):
    app = Dash(server=server, url_base_pathname=url_base)
    apply_layout_with_auth(app, layout)

    # @app.callback(
    #         Output('target', 'children'),
    #         [Input('input_text', 'value')])
    # def callback_fun(value):
    #     return 'your input is {}'.format(value)
    
    @app.callback(
        Output('graph-with-slider', 'figure'),
        [Input('year-slider', 'value')])
    def create_timeseries_doc(selected_time):
        filtered_df = date_df[date_df.clip_at == selected_time]
        fig = px.scatter(filtered_df, x='clip_at', y= 'title') # title기준으로 총 doc카운트
        fig.update_traces(mode = 'lines+markers')
        fig.update_xaxes(showgrid = False, title_text='Date')
        fig.update_yaxes(type='linear', title_text = 'Total numb of docs')
    
        return fig

    return app.server