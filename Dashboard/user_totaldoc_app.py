import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import plotly.express as px
import pandas as pd
import datetime as dt
import dash_daq as daq
from jupyter_dash import JupyterDash
import datetime as dt
from datetime import date, timedelta

url_base = '/dash/app2/'

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


layout = html.Div([
          
    daq.LEDDisplay(
        label="Numb of Total documents saved (Total)",
        labelPosition='bottom',
        value= df.title.count()
        ),
    daq.LEDDisplay(
        label="Numb of Total documents saved (Last one week)",
        labelPosition='bottom',
        value=select_OneWeek(df).title.count()
    )
])

def Add_Dash(server):
    app = Dash(server=server, url_base_pathname=url_base)
    apply_layout_with_auth(app,layout)
    return app.server
    
# @app.callback(
#     dash.dependencies.Output('doc-LED-display', 'value')]
# )
# def update_output(value):
#     return str(value)
