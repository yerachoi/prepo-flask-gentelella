import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
from .Dash_fun import apply_layout_with_auth, load_object, save_object
import plotly.express as px
import pandas as pd
from datetime import datetime

from jupyter_dash import JupyterDash
from .Dash_fun import apply_layout_with_auth, load_object, save_object

from flask import session
from flask_login import current_user, login_required
from app import db
from app.base.models import Document, Url, User


url_base = '/dash/app1/'

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

# data loading
# user_id = current_user.get_id()
# queryset = Document.query.join(Url).filter(Url.user_id==user_id) # SQLAlchemy가 만들어준 쿼리, 하지만 .all()이 없어 실행되지는 않음
# df = pd.read_sql(queryset.statement, queryset.session.bind)
# data_path = "/mnt/d/yerachoi/plink-flask-gentelella/data/user_docs_df2.csv"
# df = pd.read_csv(data_path)


# clip_at 컬럼 시간 분 초 삭제
# df.clip_at = df.clip_at.astype(str)
# df['clip_at'] = df['clip_at'].str[:10]

# datetime으로 변경
# df['clip_at'] = pd.to_datetime(df['clip_at'], format = '%Y-%m-%d')

# df['clip_date_day'] = df['clip_date'].date()
# date_lst = df.clip_date_day.unique()

# app = dash.Dash(__name__) # external_stylesheets=external_stylesheets)

layout = html.Div([
  dcc.Graph(id='graph-with-slider',
  style={'float': 'left','margin': 'auto'}),
  dcc.DatePickerRange(
      id = 'my-date-picker-range',
      display_format = 'Y-M-D', 
      month_format='Y-M-D',
      end_date_placeholder_text='Y-M-D',
      start_date='2011-11-05',
      end_date='2020-11-11',
      # start_date=pd.to_datetime('2011-11-05', format="%Y-%m-%d"),
      # end_date=pd.to_datetime('2020-11-11', format="%Y-%m-%d"),
      # start_date=df['clip_date_day'].min().strftime("%Y-%m-%d"),
      # end_date=datetime.now().strftime("%Y-%m-%d"),
      style={'float': 'left','margin': 'auto'}
)  

])

def Add_Dash(server):
  app = dash.Dash(server=server, url_base_pathname=url_base)
  apply_layout_with_auth(app,layout)

  @app.callback(
      Output('graph-with-slider', 'figure'),
      [Input('my-date-picker-range', 'start_date'),
      Input('my-date-picker-range', 'end_date')])
  # def update_intervalCurrentTime():
  #   user_id = session.get('username', None)
  #   return session.get('username', None)

  # user_id = update_intervalCurrentTime()
  # queryset = Document.query.join(Url).filter(Url.user_id==user_id) # SQLAlchemy가 만들어준 쿼리, 하지만 .all()이 없어 실행되지는 않음
  # df = pd.read_sql(queryset.statement, queryset.session.bind)

  # df['clip_date_day'] = df['clip_date'].date()
  # date_lst = df.clip_date_day.unique()

  def create_timeseries_doc(start_date, end_date):
    # print('create_timeseries_doc')
    print(start_date, end_date)
    print(type(start_date), type(end_date))

    start_date_dt = str(pd.to_datetime(start_date, format="%Y-%m-%d"))
    end_date_dt = str(pd.to_datetime(end_date, format="%Y-%m-%d"))
    print(start_date_dt, end_date_dt)
    print(type(start_date_dt), type(end_date_dt))

    user_id = current_user.get_id()
    # print(user_id)
    queryset = Document.query.join(Url).filter(Url.user_id==user_id) # SQLAlchemy가 만들어준 쿼리, 하지만 .all()이 없어 실행되지는 않음
    df = pd.read_sql(queryset.statement, queryset.session.bind)
    # print(df.head())

    df['clip_date_day'] = pd.to_datetime(df['clip_date'], format="%Y-%m-%d").dt.date
    # date_lst = df.clip_date_day.unique()

    # doc저장한 시점(clip_at) 기준으로 groupby한 dataframe
    date_df = df.groupby('clip_date_day').count().reset_index()
    # print(date_df.head())

    filtered_df = date_df[(date_df['clip_date_day'] > pd.to_datetime(start_date_dt)) & (date_df['clip_date_day'] <= pd.to_datetime(end_date_dt))]
    # print(len(date_df['clip_date_day'] > start_date))
    fig = px.scatter(filtered_df, x='clip_date_day', y='title') # title기준으로 총 doc카운트
    fig.update_traces(mode = 'lines+markers')
    fig.update_xaxes(showgrid = False, title_text='날짜')
    fig.update_yaxes(type='linear', title_text = '전체 문서 개수')
    
    return fig
  return app.server

