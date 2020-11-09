import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
<<<<<<< HEAD
=======
from .Dash_fun import apply_layout_with_auth, load_object, save_object
>>>>>>> fde1fa00c092367e283bc001679414ecf72a0091
import plotly.express as px
import pandas as pd
import datetime as dt
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from jupyter_dash import JupyterDash

url_base = '/dash/app5/'


<<<<<<< HEAD
data_path = "/content/hot_keyword.xlsx"
=======
data_path = "/mnt/d/yerachoi/plink-flask-gentelella/data/hot_keyword.xlsx"
>>>>>>> fde1fa00c092367e283bc001679414ecf72a0091
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
<<<<<<< HEAD
  app = Dash(server=server, url_base_pathname=url_base)
  apply_layout_with_auth(app,layout)

  return app.server
=======
    app = dash.Dash(server=server, url_base_pathname=url_base)
    apply_layout_with_auth(app, layout)

    return app.server
>>>>>>> fde1fa00c092367e283bc001679414ecf72a0091
