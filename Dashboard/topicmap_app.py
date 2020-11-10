# ========== (c) JP Hwang 2020-04-02  ==========

import logging

# ===== START LOGGER =====
logger = logging.getLogger(__name__)
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
sh = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
sh.setFormatter(formatter)
root_logger.addHandler(sh)

import pandas as pd
import numpy as np
import plotly.express as px
import dash
import dash_cytoscape as cyto
import dash_html_components as html
import dash_bootstrap_components as dbc
import dash_core_components as dcc
from dash.dependencies import Input, Output
from .Dash_fun import apply_layout_with_auth, load_object, save_object
#from sklearn.manifold import TSNE
#import umap  # pip install umap-learn
import json

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

from app import db
from app.base.models import Document

url_base = '/dash/app6/'


# docs 데이터 불러오기. #### 이 부분 db에서 불러오도록 수정필요 #####
tm_model_path = DATA_DIR + '/tm_model.z'
# user_docs_df = utils.load_obj(DATA_DIR + '/', 'user_docs_df.pkl')  
# user_docs_df = user_docs_df.reset_index(level=0).rename(columns={"index":"id", 'contents_prep_sum': 'text_sum'})

queryset = Document.query # SQLAlchemy가 만들어준 쿼리, 하지만 .all()이 없어 실행되지는 않음
user_docs_df = pd.read_sql(queryset.statement, queryset.session.bind)

# 모델 불러오기 또는 로드하기
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


# docs 데이터 + top2vec모델 데이터 결합하여 사용할 df 만들기
topics_idx_vector, docs_idx_vector, words_idx_vector = tm_model.get_2d_vectors()  # id, x, y 리턴

element_types = ["topic", "doc", "word"]
topic_df = pd.DataFrame(topics_idx_vector)
topic_df['topic_idx'] = topic_df['id']
docs_idx_vector_df = pd.DataFrame(docs_idx_vector)
word_df = pd.DataFrame(words_idx_vector)
word_df['topic_idx'] = -1

# topics_idx_vector_df['element_type'] ='topic'
# topics_idx_vector_df['topic_idx'] = topics_idx_vector_df['id']
# docs_idx_vector_df['element_type'] = 'doc'
# words_idx_vector_df['element_type'] = 'word'
# words_idx_vector_df['topic_idx'] = -1

#network_df = pd.concat([topics_idx_vector_df,docs_idx_vector_df, words_idx_vector_df])
#user_docs_df['element_type'] = 'doc'
doc_df = pd.merge(docs_idx_vector_df, user_docs_df, on=['id'], how = 'left')
#print(network_df.head())
# print(network_df.isnull().sum())
# print(network_df.columns)
# print(network_df['element_type'].value_counts())
# print(network_df.loc[network_df['element_type'] == 'doc', :][:2])
# print(network_df["topic_idx"].unique())


############### network_df에서 'element_type'가 doc인것에 대해  ['title', 'publish_date', 'text_sum', 'url'] 추가해주세요#########
# from_doc_db_colname = ['title', 'publish_date', 'text_sum', 'url']
# for colname in from_doc_db_colname:
#     network_df[colname] = colname+'22'

#doc_info_colnames = ['title', 'publish_date', 'contents', 'url', 'crawl_at', 'is_news', 'clip_at', 'contents_prep', 'text_sum', ]  #  'cited_by', 'n_cites', 
vector_colnames = ['x','y'] # id, topic_idx, word
#position_arr = network_df.loc[:, vector_colnames].to_numpy()

# position_arr = {"topic": 50, 
#                     "doc": 20, 
#                     "word": 10}

# Prep data / fill NAs
# for colname in doc_info_colnames:
#     network_df[colname] = network_df[colname].fillna("")
#network_df["cited_by"] = network_df["cited_by"].fillna("")   # edge하려면 이거 수정해줘야함
topic_df["topic_idx"] = topic_df["topic_idx"].astype(str)
doc_df["topic_idx"] = doc_df["topic_idx"].astype(str)
word_df["topic_idx"] = word_df["topic_idx"].astype(str)
doc_df["publish_date"] = doc_df["publish_date"].fillna("") 

# topic_idxs = [str(i) for i in range(len(network_df["topic_idx"].unique()))]
# lda_val_arr = network_df[topic_idxs].values


# with open("/home/lab13/prepo-flask-gentelella/data/lda_topics.json", "r") as f:
# with open("/mnt/d/yerachoi/plink-flask-gentelella/data/lda_topics.json", "r") as f:    
#     lda_topics = json.load(f)
# topics_txt = [lda_topics[str(i)] for i in range(len(lda_topics))]
# topics_txt = [[j.split("*")[1].replace('"', "") for j in i] for i in topics_txt]

topics_txt = tm_model.get_topics_info()['topics_words']
topics_txt = ["; ".join(i) for i in topics_txt]
print(topics_txt)
#element_type_ser = network_df.groupby("element_type")["topic_idx"].count().sort_values(ascending=False)
element_type_ser = {"topic": len(topic_df), 
                    "doc": len(doc_df),
                    "word": len(word_df),}

def tsne_to_cyto(tsne_val, scale_factor=40):
    return int(scale_factor * (float(tsne_val)))


def get_node_list(df_dict):  # Convert DF data to node list for cytoscape
    node_list = []
    # topic
    if df_dict['topic'] is not None:
        node_list += [{
                "data": {
                    "id": idx,
                    "origin_id": row["id"], #
                    "element_type": "topic",
                    "node_size": 30,
                },
                "position": {"x": tsne_to_cyto(row["x"]), "y": tsne_to_cyto(row["y"])},
                "classes": row["topic_idx"],
                "selectable": True,
                "grabbable": False,
            } for idx, row in df_dict['topic'].iterrows()] 

    # doc
    if df_dict['doc'] is not None:
        node_list += [{
                "data": {
                    "id": idx + len(topic_df) ,
                    "origin_id": row["id"], #  # 원 db의 아이디. 물론 docs만 의미있...
                    "title": row["title"],
                    "element_type": "doc",
                    "publish_date": row["publish_date"],
                    "text_sum": row["text_sum"],
                    #"cited_by": row["cited_by"],
                    #"n_cites": row["n_cites"],
                    "node_size": 10, #int(np.sqrt(1 + row["n_cites"]) * 10),
                    "url": row["url"],
                },
                "position": {"x": tsne_to_cyto(row["x"]), "y": tsne_to_cyto(row["y"])},
                "classes": row["topic_idx"],
                "selectable": True,
                "grabbable": False,
            }
            for idx, row in df_dict['doc'].iterrows()
        ]
    # word
    if df_dict['word'] is not None:
        node_list += [
            {
                "data": {
                    "id": idx + len(topic_df) + len(doc_df),
                    "origin_id": row["id"], #  # 원 db의 아이디. 물론 docs만 의미있...
                    "element_type": "word",
                    "node_size": 1,
                    "label": row['word']
                },
                "position": {"x": tsne_to_cyto(row["x"]), "y": tsne_to_cyto(row["y"])},
                "classes": row["topic_idx"],
                "selectable": True,
                "grabbable": False,
            }
            for idx, row in df_dict['word'].iterrows()
        ]

    return node_list


default_tsne = 40

def scale_node_loc(dim_red_algo, tsne_perp, df_dict):
    #(x_list, y_list) = get_node_locs(vectors_df, dim_red_algo, tsne_perp=tsne_perp)

    # scale_factor 구하기
    xy_df = pd.concat([topic_df[['x', 'y']], doc_df[['x', 'y']], word_df[['x', 'y']]])
    x_list = xy_df['x']
    y_list = xy_df['y']
    x_range = max(x_list) - min(x_list)
    y_range = max(y_list) - min(y_list)
    # print("Ranges: ", x_range, y_range)

    scale_factor = int(300 / (x_range + y_range))
    # in_df["x"] = x_list
    # in_df["y"] = y_list
    print(max(x_list), min(x_list), max(y_list), min(y_list), scale_factor)

    # Re-scaling to ensure proper canvas scaling vs node sizes 
    tmp_node_list = get_node_list(df_dict)
    for idx in range(len(tmp_node_list)):
        tmp_node_list[idx]["position"]["x"] = tsne_to_cyto(tmp_node_list[idx]["position"]["x"], scale_factor)
        tmp_node_list[idx]["position"]["y"] = tsne_to_cyto(tmp_node_list[idx]["position"]["y"], scale_factor)

    return tmp_node_list


startup_n_cites = 1  #startup_elms["n_cites"]
startup_element_types = ["topic", "doc", "word"]
startup_elm_list = []


col_swatch = cycle(px.colors.qualitative.Plotly) #px.colors.qualitative.Dark24
def_stylesheet = [ ]
for topic_idx in topic_df["topic_idx"].unique():
    color = next(col_swatch)
    def_stylesheet.append({
        "selector": "." + str(topic_idx),  # word는 -1이기 때문
        "style": {"background-color": color, "line-color": color},
    })


def_stylesheet += [
    {
        "selector": "node",
        "style": {"width": "data(node_size)", "height": "data(node_size)"},
    },
    #{"selector": "edge", "style": {"width": 1, "curve-style": "bezier"}},
]
# type
def_stylesheet += [
    {
        "selector": '[element_type = "topic"]',
        "style": {'shape': 'star'},
    },
    {
        "selector": '[element_type = "doc"]',
        "style": {'shape': 'ellipse'},
    },
    {
        "selector": '[element_type = "word"]',
        "style": {#'shape': 'ellipse',
                    'content': 'data(label)'},
    },
]


topics_html = list()
for topic_html in [
    html.Span([str(i) + ": " + topics_txt[i]], style={"color": next(col_swatch)})
    for i in range(len(topics_txt))
]:
    topics_html.append(topic_html)
    topics_html.append(html.Br())

body_layout = dbc.Container(
    [
        dbc.Row(
             dbc.Col(
                [dcc.Markdown(
                    """
                    -----
                    #### 주제 / 문서 / 키워드 맵
                    -----
                    """
                    ),
                                    
                ],

            ),
        ),
        dbc.Row([
            dbc.Col(
                [html.Div(
                        topics_html,
                        style={
                            "fontSize": 11,
                            "height": "100px",
                            "overflow": "auto",
                        },
                    ),
                ],
                sm=12,
                md=8,
            ),
            dbc.Col([
                dbc.Badge(
                    "요소 종류:", color="info", className="mr-1"
                ),
                dbc.FormGroup(
                    [
                        dcc.Checklist(
                            id="element_types_dropdown",
                            options=[
                                {
                                    "label": k+ " ("+ str(v)+ ")",
                                    "value": k,
                                }
                                for k, v in element_type_ser.items()
                            ],
                            value=startup_element_types,
                            #multi=True,
                            style={"width": "100%"},
                        ),
                    ]
                ),
            ]),
        ]),
        dbc.Row([
            dbc.Col(
                [
                    dbc.Row(
                        [
                            cyto.Cytoscape(
                                id="core_19_cytoscape",
                                layout={"name": "preset"},
                                style={"width": "100%", "height": "600px"},
                                elements=startup_elm_list,
                                stylesheet=def_stylesheet,
                                minZoom=0.16,
                            )
                        ]
                    ),
                    
                ],
                sm=12,
                md=8,
            ),
            dbc.Col(
                [
                    
                    dbc.Row(
                        [
                            dbc.Alert(
                                id="node-data",
                                children="Click on a node to see its details here",
                                color="secondary",
                            )
                        ]
                    ),
                ],
                sm=12,
                md=4,
            ),
        ]),
        dbc.Row(
            [
                dcc.Markdown(" "
            #         """
            # \* 'Commercial use subset' of the CORD-19 dataset from
            # [Semantic Scholar](https://pages.semanticscholar.org/coronavirus-research)
            # used, downloaded on 2/Apr/2020. The displayed nodes exclude papers that do not
            # cite and are not cited by others in this set.

            # \* Data analysis carried out for demonstration of data visualisation purposes only.
            # """
                )
            ],
            style={"fontSize": 11, "color": "gray"},
        ),
    ],
    style={"marginTop": 20},
)

layout = html.Div([body_layout])  # navbar, 


def Add_Dash(server):
    app = dash.Dash(server=server, 
                    url_base_pathname=url_base,
                    external_stylesheets=[dbc.themes.BOOTSTRAP])
    app.server.config
    apply_layout_with_auth(app, layout)

    @app.callback(
        Output("core_19_cytoscape", "elements"),
        [
            #Input("n_cites_dropdown", "value"),
            Input("element_types_dropdown", "value"),
            # Input("show_edges_radio", "checked"),
            # Input("dim_red_algo", "value"),
            # Input("tsne_perp", "value"),
        ],
    )
    #def filter_nodes(usr_min_cites, usr_element_types_list, show_edges, dim_red_algo, tsne_perp):
    def filter_nodes(usr_element_types_list=None):
        # print(usr_min_cites, usr_element_types_list, show_edges, dim_red_algo, tsne_perp)
        # Use pre-calculated nodes/edges if default values are used
        
        ### TEMP######
        usr_min_cites = 1
        show_edges = False
        dim_red_algo = "umap"
        tsne_perp = 40
        ### TEMP######


        if (
            usr_min_cites == startup_n_cites
            and usr_element_types_list == startup_element_types
            and show_edges == True
            and dim_red_algo == "tsne"
            and tsne_perp == 40
        ):
            logger.info("Using the default element list")
            return startup_elm_list

        else:
            # Generate node list
            #cur_df = network_df[(network_df.n_cites >= usr_min_cites)]
            # cur_df = network_df.copy()
            # if usr_element_types_list is not None and usr_element_types_list != []:
            #     cur_df = cur_df[(cur_df['element_type'].isin(usr_element_types_list))]

        # position_arr = cur_df.loc[:, vector_colnames].to_numpy()
            dfs = [topic_df, doc_df, word_df]
            user_select_dict = {}
            for idx, element_type in enumerate(element_types):    
                user_select_dict[element_type] = dfs[idx] if element_type in usr_element_types_list else None


            cur_node_list = scale_node_loc(dim_red_algo, tsne_perp, user_select_dict)

            conn_list = []
            # if show_edges:
            #     conn_list = draw_edges(cur_df)

            elm_list = cur_node_list + conn_list

        return elm_list


    @app.callback(
        Output("node-data", "children"), [Input("core_19_cytoscape", "mouseoverNodeData")]  # selectedNodeData
    )
    def display_nodedata(datalist):
        contents = "그래프 내 요소에 마우스를 올려보세요"

        # datalist = [datalist]
        # if datalist is not None:
        #     if len(datalist) > 0:
        #         data = datalist[-1]
        print("ssssssssssss")
        data = datalist
        if data is not None:
            if data['element_type'] == 'topic':
                contents = []
                topic_info = tm_model.get_topic_info(data["origin_id"])

                contents.append(html.H5("주제 번호: " + str(data["origin_id"])))
                contents.append(
                    html.P(
                        "키워드: "
                        + ' '.join(topic_info["topic_words"])
                    )
                )
            elif data['element_type'] == 'doc':
                contents = []
                contents.append(html.H5(data["title"].title()))
                contents.append(
                    html.P(
                        "출판일: "
                        + data["publish_date"]
                    )
                )
                contents.append(
                    html.P(
                        "요약문: "
                        + str(data["text_sum"])
                    )
                )
                contents.append(
                    html.A(
                        #id = 'link'+str(index),
                        # href=data["url"],
                        href='/docs/' + str(data["origin_id"]),
                        children='문서 정보 확인하기', 
                        target="_blank",
                        
                    )                
                )
            elif data['element_type'] == 'word':
                pass

        return contents

    return app.server


# if __name__ == "__main__":
#     app.run_server(debug=False)