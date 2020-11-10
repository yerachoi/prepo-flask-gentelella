import json
import os

import dash
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html

import dash_cytoscape as cyto
import Dashboard.assets.dash_reusable_components as drc
import dash_bootstrap_components as dbc

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


from .Dash_fun import apply_layout_with_auth, load_object, save_object
from app import db
from app.base.models import Document, Url
from flask_login import current_user, login_required

url_base = '/dash/app6/'

# Load extra layouts
cyto.load_extra_layouts()


asset_path = os.path.dirname(os.path.abspath(__file__)) + '/assets'
print(asset_path)
app = dash.Dash(__name__, assets_folder=asset_path)
server = app.server


# ###################### DATA PREPROCESSING ######################

# docs 데이터 불러오기. #### 이 부분 db에서 불러오도록 수정필요 #####
tm_model_path = DATA_DIR + '/tm_model.z'
# user_docs_df = utils.load_obj(DATA_DIR + '/', 'user_docs_df.pkl')  
# user_docs_df = user_docs_df.reset_index(level=0).rename(columns={"index":"id", 'contents_prep_sum': 'text_sum'})
queryset_doc = Document.query # SQLAlchemy가 만들어준 쿼리, 하지만 .all()이 없어 실행되지는 않음
user_docs_df = pd.read_sql(queryset_doc.statement, queryset_doc.session.bind)


queryset_url = Url.query
user_urls_df = pd.read_sql(queryset_url.statement, queryset_url.session.bind)[['id', 'url']]
user_urls_df.rename(columns={'id':'url_id'}, 
                    inplace=True)
# print(user_urls_df)

user_docs_df = pd.merge(user_docs_df, user_urls_df,
                        on='url_id', how='outer')
# print(user_docs_df)

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


#docs 데이터 + top2vec모델 데이터 결합하여 사용할 df 만들기
# topics_idx_vector, docs_idx_vector, words_idx_vector = tm_model.get_2d_vectors()  # id, x, y 리턴

# element_types = ["topic", "doc", "word"]
# docs_idx_vector_df = pd.DataFrame(docs_idx_vector)
# word_df = pd.DataFrame(words_idx_vector)
# word_df['topic_idx'] = -1

temp_df = pd.DataFrame(tm_model.get_documents_topics(user_docs_df['id'].values, reduced=tm_model.is_reduced)[0], index=user_docs_df['id'].values).reset_index(level=0).rename(columns={"index":"id", 0: 'topic_idx'})
print(temp_df)
doc_df = pd.merge(user_docs_df, temp_df, on=['id'], how = 'left')
doc_df["topic_idx"] = doc_df["topic_idx"].astype(str)
# word_df["topic_idx"] = word_df["topic_idx"].astype(str)
doc_df["publish_date"] = doc_df["publish_date"].fillna("") 


# with open("/home/lab13/prepo-flask-gentelella/data/lda_topics.json", "r") as f:
#     lda_topics = json.load(f)
# topics_txt = [lda_topics[str(i)] for i in range(len(lda_topics))]
# topics_txt = [[j.split("*")[1].replace('"', "") for j in i] for i in topics_txt]

# topics_txt = ["; ".join(i) for i in topics_txt]
# print(topics_txt)


def insert_info_to_elements(elements):  # Convert DF data to element list for cytoscape
    # df_dict = {"topic": topic_df, "doc": doc_df, "word":word_df}
    element_inserted = []
    for element in elements:
        element_id = element['data']['id']
        id_parsed = element_id.split('_')
        if len(id_parsed) != 2:
            element_inserted.append(element)
            continue

        element_type, element_origin_id = id_parsed
        element_origin_id = int(element_origin_id)
        # my_df = df_dict[element_type]
        print(element_origin_id)

        # topic
        if element_type == 'topic':
            element.update({
                "data": {
                    "id": element_id,
                    "origin_id": element_origin_id, #
                    "element_type": "topic",
                    "node_size": 40,
                },
                #"classes": row["topic_idx"],
            })

        # doc
        elif element_type == 'doc':
            row = doc_df[doc_df['id'] == element_origin_id].to_dict('records')[0]
            element.update({
                "data": {
                    "id": element_id,
                    "origin_id": element_origin_id, #  # 원 db의 아이디. 물론 docs만 의미있...
                    "title": row["title"],
                    "element_type": "doc",
                    "publish_date": row["publish_date"],
                    "text_sum": row["text_sum"],
                    "node_size": 25, #int(np.sqrt(1 + row["n_cites"]) * 10),
                    "url": row["url"],
                    "topic_idx": row["topic_idx"],
                    #"parent": row["topic_idx"],
                },
               # "classes": row["topic_idx"],
            })
    
        # word
        elif element_type == 'word':
            element.update({
                "data": {
                    "id": element_id,
                    "origin_id": element_origin_id, #  # 원 db의 아이디. 물론 docs만 의미있...
                    "element_type": "word",
                    "node_size": 15,
                    "label": tm_model.vocab[element_origin_id],
                },
              #  "classes": row["topic_idx"],
            })
        
        element_inserted.append(element)

    return element_inserted










nodes = set()

# following_node_di = {}  # user id -> list of users they are following
# following_edges_di = {}  # user id -> list of cy edges starting from user id

followers_node_di = {}  # user id -> list of followers (cy_node format)
followers_edges_di = {}  # user id -> list of cy edges ending at user id

cy_edges = []
cy_nodes = []

edges = tm_model.get_links_info()
# print(len(edges))
# print(edges[:2])

for s, t in edges:
    if s == 'doc_0':
        print('s is doc', s, t)
    if t == 'doc_0':
        print('t is doc', s, t)


for edge in edges:
    
    for i in range(2):
        if i == 0:
            source, target = edge[0], edge[1]
        else:
            source, target = edge[1], edge[0]
        #print(source, target)

        cy_edge = {'data': {'id': source+"_"+target, 'source': source, 'target': target}}
        cy_source = {"data": {"id": source, "label": source}}
        cy_target = {"data": {"id": target, "label": target}}

        if source not in nodes:
            nodes.add(source)
            cy_nodes.append(cy_source)
        if target not in nodes:
            nodes.add(target)
            cy_nodes.append(cy_target)

        # # Process dictionary of following
        # if not following_node_di.get(source):
        #     following_node_di[source] = []
        # if not following_edges_di.get(source):
        #     following_edges_di[source] = []

        # following_node_di[source].append(cy_target)
        # following_edges_di[source].append(cy_edge)

        # Process dictionary of followers
        if not followers_node_di.get(target):
            followers_node_di[target] = []
        if not followers_edges_di.get(target):
            followers_edges_di[target] = []

        followers_node_di[target].append(cy_source)
        followers_edges_di[target].append(cy_edge)

genesis_node = cy_nodes[0]
genesis_node['classes'] = "genesis"
default_elements = insert_info_to_elements([genesis_node])

default_stylesheet = [
    {
        "selector": 'node',
        'style': {
            "opacity": 0.65,
            'z-index': 9999
        }
    },
    {
        "selector": 'edge',
        'style': {
            #"curve-style": "bezier",
            "opacity": 0.45,
            'z-index': 5000
        }
    },
    {
        'selector': '.followerNode',
        'style': {
            'background-color': '#0074D9'
        }
    },
    {
        'selector': '.followerEdge',
        "style": {
            "mid-target-arrow-color": "blue",
            "mid-target-arrow-shape": "vee",
            "line-color": "#0074D9"
        }
    },
    # {
    #     'selector': '.followingNode',
    #     'style': {
    #         'background-color': '#FF4136'
    #     }
    # },
    # {
    #     'selector': '.followingEdge',
    #     "style": {
    #         "mid-target-arrow-color": "red",
    #         "mid-target-arrow-shape": "vee",
    #         "line-color": "#FF4136",
    #     }
    # },
    {
        "selector": '.genesis',
        "style": {
            'background-color': '#B10DC9',
            "border-width": 2,
            "border-color": "purple",
            "border-opacity": 1,
            "opacity": 1,

            "label": "data(label)",
            "color": "#B10DC9",
            "text-opacity": 1,
            "font-size": 12,
            'z-index': 9999
        }
    },
    {
        'selector': ':selected',
        "style": {
            "border-width": 2,
            "border-color": "black",
            "border-opacity": 1,
            "opacity": 1,
            "label": "data(label)",
            "color": "black",
            "font-size": 12,
            'z-index': 9999
        }
    },
    # type에 따라 색 다르게 처리
    {
        "selector": '[element_type = "topic"]',
        "style": {'shape': 'star', "width": "data(node_size)", "height": "data(node_size)"},
    },
    {
        "selector": '[element_type = "doc"]',
        "style": {'shape': 'ellipse', "width": "data(node_size)", "height": "data(node_size)"},
    },
    {
        "selector": '[element_type = "word"]',
        "style": {'label': 'data(label)',
                "width": "data(node_size)", "height": "data(node_size)", 
                "text-halign": "center", "text-valign": "center",
                },
    },
]

# ################################# APP LAYOUT ################################
styles = {
    'json-output': {
        'overflow-y': 'scroll',
        'height': 'calc(50% - 25px)',
        'border': 'thin lightgrey solid'
    },
    'tab': {'height': 'calc(98vh - 80px)'}
}

layout = html.Div([
    html.Div(className='eight columns', children=[
        cyto.Cytoscape(
            id='cytoscape',
            elements=default_elements,
            stylesheet=default_stylesheet,
            style={
                'height': '95vh',
                'width': '100%'
            }
        )
    ]),

    html.Div(className='four columns', children=[
        dcc.Tabs(id='tabs', children=[
            dcc.Tab(label='Control Panel', children=[
                drc.NamedDropdown(
                    name='Layout',
                    id='dropdown-layout',
                    options=drc.DropdownOptionsList(
                        'cola',
                        'cose',
                        'cose-bilkent',
                        'grid',
                        'circle',
                        'concentric',
                        'breadthfirst',
                        'dagre',
                        'klay',
                        'spread',
                        'euler'
                        'random',
                    ),
                    value='cola',
                    clearable=False
                ),
                # drc.NamedRadioItems(
                #     name='Expand',
                #     id='radio-expand',
                #     options=drc.DropdownOptionsList(
                #         'followers',
                #         'following'
                #     ),
                #     value='followers'
                # ),
                dbc.Alert(
                    id="node-data",
                    children="Click on a node to see its details here",
                    color="secondary",
                )
            ]),

            dcc.Tab(label='JSON', children=[
                html.Div(style=styles['tab'], children=[
                    html.P('Node Object JSON:'),
                    html.Pre(
                        id='tap-node-json-output',
                        style=styles['json-output']
                    ),
                    html.P('Edge Object JSON:'),
                    html.Pre(
                        id='tap-edge-json-output',
                        style=styles['json-output']
                    )
                ])
            ])
        ]),

    ])
])


# ############################## CALLBACKS ####################################
def Add_Dash(server):
    app = dash.Dash(server=server, 
                    url_base_pathname=url_base,
                    external_stylesheets=[dbc.themes.BOOTSTRAP])
    app.server.config
    apply_layout_with_auth(app, layout)

    @app.callback(Output('tap-node-json-output', 'children'),
                [Input('cytoscape', 'tapNode')])
    def display_tap_node(data):
        return json.dumps(data, indent=2)


    @app.callback(Output('tap-edge-json-output', 'children'),
                [Input('cytoscape', 'tapEdge')])
    def display_tap_edge(data):
        return json.dumps(data, indent=2)


    @app.callback(Output('cytoscape', 'layout'),
                [Input('dropdown-layout', 'value')])
    def update_cytoscape_layout(layout):
        return {'name': layout}


    @app.callback(Output('cytoscape', 'elements'),
                [Input('cytoscape', 'tapNodeData')],
                [State('cytoscape', 'elements'),])
                #State('radio-expand', 'value')])
    def generate_elements(nodeData, elements):
        if not nodeData:
            return default_elements

        expansion_mode = 'followers'
        print(nodeData)

        # If the node has already been expanded, we don't expand it again
        if nodeData.get('expanded'):
            return elements

        # This retrieves the currently selected element, and tag it as expanded
        for element in elements:
            if nodeData['id'] == element.get('data').get('id'):
                element['data']['expanded'] = True
                break

        # if expansion_mode == 'followers':

        followers_nodes = followers_node_di.get(nodeData['id'])
        followers_edges = followers_edges_di.get(nodeData['id'])

        if followers_nodes:
            for node in followers_nodes:
                node['classes'] = 'followerNode'
            elements.extend(followers_nodes)

        if followers_edges:
            for follower_edge in followers_edges:
                follower_edge['classes'] = 'followerEdge'
            elements.extend(followers_edges)

        # elif expansion_mode == 'following':

        #     following_nodes = following_node_di.get(nodeData['id'])
        #     following_edges = following_edges_di.get(nodeData['id'])

        #     if following_nodes:
        #         for node in following_nodes:
        #             if node['data']['id'] != genesis_node['data']['id']:
        #                 node['classes'] = 'followingNode'
        #                 elements.append(node)

        #     if following_edges:
        #         for follower_edge in following_edges:
        #             follower_edge['classes'] = 'followingEdge'
        #         elements.extend(following_edges)


        return insert_info_to_elements(elements)





    @app.callback(
        Output("node-data", "children"), [Input("cytoscape", "mouseoverNodeData")]  # selectedNodeData
    )
    def display_nodedata(datalist):
        contents = "그래프 내 요소에 마우스를 올려보세요"

        # datalist = [datalist]
        # if datalist is not None:
        #     if len(datalist) > 0:
        #         data = datalist[-1]
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
                contents.append(html.A(
                        #id = 'link'+str(index),
                        # href=data["url"],
                        href='/docs/' + str(data["origin_id"]),
                        children=html.H5(data["title"].title()),
                        target="_blank",
                        
                    ))
                contents.append(html.P("주제 번호: " + str(data["topic_idx"])),   )
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

            elif data['element_type'] == 'word':
                pass

        return contents
    return app.server




# if __name__ == '__main__':
#     app.run_server(debug=True)
