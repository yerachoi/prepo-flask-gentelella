import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
from .Dash_fun import apply_layout_with_auth, load_object, save_object
import plotly.express as px
import pandas as pd
import datetime as dt
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from jupyter_dash import JupyterDash

from app import db
from app.base.models import Document, Url
from flask_login import current_user, login_required

import sys
import os
from pathlib import Path
import pandas as pd
from itertools import cycle

PARENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = PARENT_DIR + '/data'
PREPO_DIR = PARENT_DIR + '/prepo'

sys.path.insert(0, PARENT_DIR)
sys.path.insert(0, PREPO_DIR)
from prepo.prepo.topic_model import TopicModel 
from prepo.prepo import utils


url_base = '/dash/app5/'


data_path = "/mnt/d/yerachoi/plink-flask-gentelella/data/hot_keyword.xlsx"
word_score = pd.read_excel(data_path)
word_score = word_score.sort_values(by='score',ascending=False)

tm_model_path = DATA_DIR + '/tm_model.z'

queryset_doc = Document.query # SQLAlchemy가 만들어준 쿼리, 하지만 .all()이 없어 실행되지는 않음
user_docs_df = pd.read_sql(queryset_doc.statement, queryset_doc.session.bind)

# 모델 생성하기 또는 로드하기
BUILD_TM_MODEL = False
if BUILD_TM_MODEL or not Path(tm_model_path).exists():
    tm_model = TopicModel(user_docs_df['text_sum'], 
                    doc_ids=user_docs_df['id'],
                    )
    tm_model.save(tm_model_path)
    print("tm_model is saved")
else:
    tm_model = TopicModel.load(tm_model_path)
    print("tm_model is loaded")


queryset_doc = Document.query # SQLAlchemy가 만들어준 쿼리, 하지만 .all()이 없어 실행되지는 않음
user_docs_df = pd.read_sql(queryset_doc.statement, queryset_doc.session.bind)
doc_ids = list(user_docs_df['id'])

hot_words, hot_words_scores = tm_model.get_keywords_by_doc(doc_ids, doc_ids)
print(hot_words[:10])
print(hot_words_scores[:10])

fig = go.Figure(data = [go.Bar(x=hot_words_scores, y=hot_words, orientation='h',
                               marker=dict(color='LightSkyBlue'))],
                layout={'title':'Hot keywords'})

# fig = go.Figure(data = [go.Bar(x=word_score.score, y=word_score.word, orientation='h',
#                                marker=dict(color='LightSkyBlue'))],
#                 layout={'title':'Hot keywords (Top 10)'})

# change layout by descending order
fig['layout']['yaxis']['autorange'] = 'reversed'


layout = html.Div([
    dcc.Graph(id='bar-graph',figure= fig)])

def Add_Dash(server):
    app = dash.Dash(server=server, url_base_pathname=url_base)
    apply_layout_with_auth(app, layout)

    return app.server
