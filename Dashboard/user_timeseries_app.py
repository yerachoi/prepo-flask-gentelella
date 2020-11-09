import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import plotly.express as px
import pandas as pd
import datetime as dt
from jupyter_dash import JupyterDash
from .Dash_fun import apply_layout_with_auth, load_object, save_object

url_base = '/dash/app1/'

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

# data loading
data_path = "/mnt/d/yerachoi/plink-flask-gentelella/data/user_docs_df2.csv"
df = pd.read_csv(data_path)

# clip_at 컬럼 시간 분 초 삭제
df.clip_at = df.clip_at.astype(str)
df['clip_at'] = df['clip_at'].str[:10]

# datetime으로 변경
# df['clip_at'] = pd.to_datetime(df['clip_at'], format = '%Y-%m-%d')


date_lst = df.clip_at.unique()

# app = dash.Dash(__name__) # external_stylesheets=external_stylesheets)

layout = html.Div([
  dcc.Graph(id='graph-with-slider',
  style={'float': 'left','margin': 'auto'}),
  dcc.DatePickerRange(
      id = 'my-date-picker-range',
      display_format = 'Y-M-D', 
      month_format='Y-M-D',
      end_date_placeholder_text='Y-M-D',
      start_date=df['clip_at'].min(),
      style={'float': 'left','margin': 'auto'}
)  

])

def Add_Dash(server):
  app = Dash(server=server, url_base_pathname=url_base)
  apply_layout_with_auth(app,layout)

  @app.callback(
      Output('graph-with-slider', 'figure'),
      [Input('my-date-picker-range', 'start_date'),
      Input('my-date-picker-range', 'end_date')])


  def create_timeseries_doc (start_date,end_date):
    # doc저장한 시점(clip_at) 기준으로 groupby한 dataframe
    date_df = df.groupby('clip_at').count().reset_index()

    filtered_df = date_df[(date_df['clip_at'] > start_date) & (date_df['clip_at'] <=end_date)]
    fig = px.scatter(filtered_df, x='clip_at', y= 'title') # title기준으로 총 doc카운트
    fig.update_traces(mode = 'lines+markers')
    fig.update_xaxes(showgrid = False, title_text='Date')
    fig.update_yaxes(type='linear', title_text = 'Total numb of docs')
    
    return fig
  return app.server

