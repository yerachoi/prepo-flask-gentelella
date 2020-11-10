import dash
import dash_core_components as dcc
from jupyter_dash import JupyterDash
import dash_html_components as html
from .Dash_fun import apply_layout_with_auth, load_object, save_object
from dash.dependencies import Input, State, Output
import plotly.express as px
import pandas as pd
import datetime as dt
from datetime import date, timedelta
import calendar
import dash_daq as daq
from .Dash_fun import apply_layout_with_auth, load_object, save_object

url_base = '/dash/app3/'

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

# data loading
data_path = "/mnt/d/yerachoi/plink-flask-gentelella/data/user_docs_df2.csv"
df = pd.read_csv(data_path)

# clip_at 컬럼 시간 분 초 삭제
df.clip_at = df.clip_at.astype(str)
df['clip_at'] = df['clip_at'].str[:10]

# 요일 생성하기 위해 datetime으로 변환
df['clip_at'] = pd.to_datetime(df['clip_at'], format = '%Y-%m-%d')


# 최근 한 주만 선택한 dataframe
def select_OneWeek(data):
  today = date.today()
  today = pd.to_datetime(today)

  week_prior =  today - timedelta(weeks=1)

  last_week_df = data[week_prior <= data['clip_at']]
  return last_week_df

# dataframe을 요일별화 시킴
def weekday_df(data):

  # 요일 칼럼 생성
  weekday = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
  data['day_of_week'] = data['clip_at'].apply(lambda x: x.weekday()) # get the weekday index, between 0 and 6
  data['day_of_week'] = data['day_of_week'].apply(lambda x: calendar.day_name[x]) # Monday, Tuesday...

  # Weekday로 groupby한 datarame
  week_df = data.groupby('day_of_week').count().reset_index() 
  week_df['day_of_week'] = pd.Categorical(week_df['day_of_week'],categories=weekday, ordered=True)  # Weekday 순서맞추기, not by alphabet order
  week_df = week_df.sort_values('day_of_week')
  week_df['day_of_week'] = week_df['day_of_week'].replace(['Monday'],'월요일')
  week_df['day_of_week'] = week_df['day_of_week'].replace(['Tuesday'],'화요일') 
  week_df['day_of_week'] = week_df['day_of_week'].replace(['Wednesday'],'수요일') 
  week_df['day_of_week'] = week_df['day_of_week'].replace(['Thursday'],'목요일') 
  week_df['day_of_week'] = week_df['day_of_week'].replace(['Friday'],'금요일') 
  week_df['day_of_week'] = week_df['day_of_week'].replace(['Saturday'],'토요일') 
  week_df['day_of_week'] = week_df['day_of_week'].replace(['Sunday'],'일요일') 
  return week_df


# 전체 요일별 총 doc 수 그래프
fig_total = px.bar(weekday_df(df), x='day_of_week', y= 'title', barmode='group')
fig_total.update_xaxes(title_text='요일')
fig_total.update_yaxes(title_text='전체 문서 개수')

# 최근 한 주 요일별 총 doc 수 그래프
fig_oneweek = px.bar(weekday_df(select_OneWeek(df)), x='day_of_week', y= 'title', barmode='group')
fig_oneweek.update_xaxes( title_text='요일')
fig_oneweek.update_yaxes(title_text='전체 문서 개수')

layout = html.Div([
  html.Div([
      html.Div([
          html.H3('전체 문서 개수'),
          dcc.Graph(id='g1', figure = fig_total)
      ], className="six columns"),

      html.Div([
          html.H3('최근 7일 간 문서 개수'),
          dcc.Graph(id='g2', figure= fig_oneweek)
      ], className="six columns"),
  ], className="row")
])

def Add_Dash(server):
    app = dash.Dash(server=server, url_base_pathname=url_base)
    apply_layout_with_auth(app, layout)

    return app.server