import pandas as pd
import dash
import dash_html_components as html
import dash_cytoscape as cyto
from matplotlib import colors as mcolors
from dash.dependencies import Input, State, Output
from .Dash_fun import apply_layout_with_auth, load_object, save_object
from itertools import zip_longest
from ast import literal_eval
from jupyter_dash import JupyterDash


url_base = '/dash/app4/'

colors = dict(mcolors.BASE_COLORS, **mcolors.CSS4_COLORS)
# Sort colors by hue, saturation, value and name.
by_hsv = sorted((tuple(mcolors.rgb_to_hsv(mcolors.to_rgba(color)[:3])), name)
                for name, color in colors.items())
sorted_names = [name for hsv, name in by_hsv]

# colors = ['red', 'blue', 'green', 'yellow', 'pink']

# stylesheet for the web page generated

default_stylesheet = [
    {
        "selector": 'node',
        'style': {
            "opacity": 0.9,
            'height': 15,
            'width': 15,
            'background-color': '#222222',
            'label': 'data(label)'
        }
    },
    {
        "selector": 'edge',
        'style': {
            "curve-style": "bezier",
            "opacity": 0.3,
            'width': 2
        }
    },
    *[{
        "selector": '.' + color,
        'style': {'line-color': color}
    } for color in sorted_names]
]

# data loading
data_path = "/mnt/d/yerachoi/plink-flask-gentelella/data/user_docs_df2.csv"
df = pd.read_csv(data_path)

# clip_at 컬럼 시간 분 초 삭제
df.clip_at = df.clip_at.astype(str)
df['clip_at'] = df['clip_at'].str[:10]

df['cluster_reduced'] = df['cluster_reduced'].astype(str) #더하기 사용하기위해 str로 바꿔줌
df['title'] = df['title'].str.replace('"','') # title중 ""로 인해 dict안들어가짐.""없애줌

topic_lst = df.cluster_reduced.unique() 

# Giving colors to each topic("cluster_reduced") in the dataframe
df['colors'] = df['cluster_reduced'].map(dict(zip_longest(list(set(topic_lst)), sorted_names)))
# Creating the nodes within the dataframe
df['y_node_target'] = "{\"data\": {\"id\": \"" + df['title'] + "\", \"label\":\""+df['title']+"\"}, \"classes\": \"" + df['colors'] + "\"}"
df['y_node'] = "{\"data\": {\"id\": \"" + df['cluster_reduced'] + "\", \"label\":\""+df['cluster_reduced']+"\"}, \"classes\": \"" + df['colors'] + "\"}"
nodes = list(set(pd.concat([df['y_node'], df['y_node_target']]).to_list()))
df['Edges'] = "{\'data\': {\'source\':\"" + df['cluster_reduced'] + "\", \'target\': \"" + df[
    'title'] + "\"},\'classes\': \"" + df['colors'] + "\"}"

# Converting the strings to dictionaries and assigning them to variables
edges = list(set(df['Edges'].astype(str).to_list()))
edges = list(map(literal_eval, edges))
nodes = list(map(literal_eval, nodes))

# styles = {
#     'pre': {
#         'border': 'thin lightgrey solid',
#         'overflowX': 'scroll'
#     }
# }
layout = html.Div([
    cyto.Cytoscape(
        id='cytoscape',
        elements=edges + nodes,
        stylesheet=default_stylesheet,
        layout={
            'name': 'breadthfirst'
        },
        style={'height': '95vh', 'width': '100%'}
    ),
    html.P(id='cytoscape-tapNodeData-output'),
    html.P(id='cytoscape-mouseoverNodeData-output')])

def Add_Dash(server):
    app = Dash(server=server, url_base_pathname=url_base)
    apply_layout_with_auth(app, layout)

    @app.callback(Output('cytoscape-mouseoverNodeData-output', 'children'),
                    [Input('cytoscape', 'mouseoverNodeData')])
    
    def displayTapNodeData(data):
        if data:
            return "The title of documnet you hovered over is: " + data['label']


    @app.callback(Output('cytoscape-tapNodeData-output', 'children'),
                [Input('cytoscape', 'tapNodeData')])
    
    def displayTapNodeData(data):
        if data:
            doc_info_lst = ['title','url','contents_prep']
            df2 = df[df['title']== data['label']]
            return html.Div([dash_table.DataTable(
            #   style_data={
            #     'whiteSpace': 'normal',
            #     'height': 'auto',
            # },
            id='table',
            columns=[{"name": i, "id": i} for i in doc_info_lst],
            data=df2.to_dict('records'),
            style_cell={'textAlign': 'left'})])
    
    return app.server
    
