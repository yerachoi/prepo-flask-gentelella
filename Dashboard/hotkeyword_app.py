import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import plotly.express as px
import pandas as pd
import datetime as dt
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from jupyter_dash import JupyterDash

url_base = '/dash/app5/'


data_path = "/content/hot_keyword.xlsx"
word_score = pd.read_excel(data_path)
word_score = word_score.sort_values(by='score',ascending=False)

fig = go.Figure(data = [go.Bar(x=word_score.score, y=word_score.word, orientation='h',
                               marker=dict(color='LightSkyBlue'))],
                layout={'title':'Hot keywords (Top 10)'})

# change layout by descending order
fig['layout']['yaxis']['autorange'] = 'reversed'


layout = html.Div([
    dcc.Graph(id='bar-graph',figure= fig)])

def Add_Dash(server):
  app = Dash(server=server, url_base_pathname=url_base)
  apply_layout_with_auth(app,layout)

  return app.server
