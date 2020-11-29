#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# pip install dash-cytoscape==0.1.1
# 
import json
import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_cytoscape as cyto
from dash.dependencies import Input, Output
from textwrap import dedent as d

import plotly.graph_objects as go
# import MLTL compiler
from MLTL_Compiler import *
from MLTL_Resource import *

cyto.load_extra_layouts()

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server

app.title = "MLTL Compiler"
default_stylesheet = [
    {
        'selector': '[type = "ATOM"]',
        'style': {
            'background-color': '#ff9900',
            'label': 'data(name)'
        }
    },
    {
        'selector': '[type = "BOOL"]',
        'style': {
            'background-color': '#BFD7B5',
            'label': 'data(name)'
        }
    },
    {
        'selector': '[type = "NEG"]',
        'style': {
            'background-color': '#66ff99',
            'label': 'data(name)'
        }
    },
    {
        'selector': '[type = "GLOBAL"]',
        'style': {
            'background-color': '#6699ff',
            'label': 'data(name)'
        }
    },
    {
        'selector': '[type = "AND"]',
        'style': {
            'background-color': '#ff6666',
            'label': 'data(name)'
        }
    },
    {
        'selector': '[type = "UNTIL"]',
        'style': {
            'background-color': '#cc00cc',
            'label': 'data(name)'
        }
    },
    {
        'selector': 'edge',
        'style': {
            'curve-style': 'bezier',
            'target-arrow-color': 'black',
            'target-arrow-shape': 'vee',
            'line-color': 'black'
        }
    }
]

styles = {
    'json-output': {
        'overflow-y': 'scroll',
        'height': 'calc(50% - 25px)',
        'border': 'thin lightgrey solid'
    },
    'tab': {'height': 'calc(98vh - 115px)'},
}

app.layout = html.Div([
################title
    html.Div(
        [html.H1('R2U2 MLTL Compiler')],
        className = 'row',
        style = {'textAlign':'center'}
        ),

############### left view
    html.Div(
        className = 'row',
        children= [
            html.Div(
                className = 'three columns',
                children = [
                    dcc.Markdown(d("""
                            ### MLTL Formula Configuration
                            """)),
                    dcc.Markdown(d("""
                            ###### MLTL Formula
                            """)),
                    # dcc.Input(id='formula', value='a0 U[5] a1; a1&a3;', type='text'),
                    dcc.Textarea(
                        id='formula',
                        value='a0;\na1 & a2;\na3 U[1,4]a5;\nG[10] b0;\n(a3 U[1,4]a5)&(G[10] b0);',
                        style={'width': '100%', 'height': '150px'},
                    ),
                    dcc.Checklist(
                        id = 'optimization',
                        options=[
                            {'label': 'Common Subexpression Elimination', 'value': 'opt_cse'},
                        ],
                        value=['opt_cse',]
                    ),
                    html.Pre(id='compile_status', style = {'color': 'green'}),
                    dcc.Markdown(d("""   
                            **Prediction Horizon Hp**  
                            """)),
                    dcc.Input(id='pred_length', value='0', type='text'),

                    dcc.Markdown(d("---\n### System Configuration")),
                    dcc.Markdown(d("**Hardware Clock Frequency (MHz)**")),
                    dcc.Input(id='hardware_clk', value='100', type='text'),
                    dcc.Markdown(d("**LUT Type Select**")),
                    dcc.Dropdown(
                        id = 'LUT_type',
                        options=[
                            {'label': 'LUT-3', 'value': '3'},
                            {'label': 'LUT-4', 'value': '4'},
                            {'label': 'LUT-6', 'value': '6'},
                        ],
                        value='3',
                        clearable=False
                    ),
                    dcc.Markdown(d("**Resource to Observe Select**")),
                    dcc.Dropdown(
                        id = 'resource_type',
                        options=[
                            {'label': 'LUT', 'value': 'LUT'},
                            {'label': '18Kb BRAM', 'value': '18kbBRAM'},
                        ],
                        value='LUT',
                        clearable=False
                    ),  

                    dcc.Markdown(d("**Timestamp Length (bit)**")),
                    dcc.Slider(
                        id='timestamp_length',
                        min=0,
                        max=64,
                        step=1,
                        value=32,
                    ),
                    html.Div(id='slider-output-container-ts'),
                    # dcc.Input(id='timestamp_length', value='32', type='text'),
                    
                    dcc.Markdown(d("---\n### Results for Timing and Resource")),
                    html.Div(
                        # className = 'three columns',
                        # style=styles['json-output'],
                        children = [
                            dcc.Markdown(d("**Worst-case Execution Time**")),
                            html.Div(id="comp_speed",),
                            dcc.Markdown(d("**Total Entry of SCQ for the AST**")),
                            html.Div(id="tot_scq_size",),
                        ]
                    )
                    ],
                    
                    style={'height': '300px'},
                    
                ),

            html.Div(
                className = 'five columns',
                children = [
                    cyto.Cytoscape(
                        id='tree',
                        # layout={'name': 'circle'},
                        layout={'name': 'klay','klay': {'direction': 'DOWN'}},
                        stylesheet=default_stylesheet,
                        style={'width': '100%', 'height': '450px'},
                        elements=[]
                    ),
                    dcc.Graph(
                        id='resource_usage',
                        figure = go.Figure(),
                    )
                ]
            ),


            html.Div(
                className = 'four columns',
                children = [
                    dcc.Tabs(
                        id='tabs', 
                        children=[            
                            dcc.Tab(
                                label='Mouseover Data', 
                                children=[
                                    html.Div(
                                        style=styles['tab'], 
                                        children=[
                                            html.P(id='status',children=['Init']),
                                            # html.P('Node Data JSON:'),
                                            html.Pre(
                                                id='mouseover-node-data-json-output',
                                                style=styles['json-output']
                                            ),
                                            html.P('Edge Data JSON:'),
                                            html.Pre(
                                                id='mouseover-edge-data-json-output',
                                                style=styles['json-output']

                                            )
                                        ]
                                    )
                                ]
                            ),
                            dcc.Tab(
                                label='Assembly Output', 
                                children=[
                                    html.Div(
                                        style=styles['tab'], 
                                        children=[
                                            html.P('Assembly:'),
                                            html.Pre(
                                                id='assembly_window',
                                                style=styles['json-output'],
                                            ),
                                        ]
                                    )
                                ]
                            ),
                        ]
                    ),    
                
                ]
            )
        ],  
    ),
])

@app.callback(
    Output('slider-output-container-ts', 'children'),
    [Input('timestamp_length', 'value')])
def update_output(value):
    return 'You have selected "{}" bit'.format(value)

@app.callback(Output('mouseover-edge-data-json-output', 'children'),
              [Input('tree', 'mouseoverEdgeData')])
def displayMouseoverEdgeData(data):
    return json.dumps(data, indent=2)

@app.callback(
    Output('mouseover-node-data-json-output', 'children'),
    [Input('tree', 'mouseoverNodeData')])
def displayMouseoverNodeTitle(data):
    if (data==None or 'bpd' not in data):
        return html.P('None')
    return html.P(
        'Name:'+str(data['name'])+'\n'
        +'bpd:'+str(data['bpd'])+'\n'
        +'wpd:'+str(data['wpd'])+'\n'
        +'SCQ size:'+str(data['scq_size'])+'\n'
        )

@app.callback(Output('status', 'children'),
              [Input('tree', 'mouseoverNodeData')])
def displayMouseoverNodeData(data):
    if (data==None or 'num' not in data):
        return html.P('Node: Unselected')
    return html.P('Node: '+str(data['num']))


@app.callback( # multiple output is a new feature since dash==0.39.0
    [Output(component_id = 'tree', component_property = 'elements'),
    Output(component_id = 'assembly_window', component_property = 'children'),
    Output(component_id = 'compile_status', component_property = 'children'),
    Output(component_id = 'compile_status', component_property = 'style'),
    Output(component_id = 'comp_speed', component_property = 'children'),
    Output(component_id = 'tot_scq_size', component_property = 'children'),
    Output(component_id = 'resource_usage', component_property = 'figure'),
    ],
    [Input(component_id = 'formula', component_property = 'value'),
    Input(component_id = 'optimization', component_property = 'value'),
    Input(component_id = 'pred_length', component_property = 'value'),
    Input(component_id = 'hardware_clk', component_property = 'value'),
    Input(component_id = 'timestamp_length', component_property = 'value'),
    Input(component_id = 'LUT_type', component_property = 'value'),
    Input(component_id = 'resource_type', component_property = 'value'),
    ]
)
def update_element(formula, optimization, pred_length, hw_clk, timestamp_length, LUT_type, resource_type):
    opt_cse = True if 'opt_cse' in optimization else False
    pg = Postgraph(MLTL=formula,Hp=int(pred_length),optimize_cse=opt_cse)
    compile_status = "Compile status: "+ pg.status.upper()
    if (pg.status!='pass'):
        elements = []
        assembly_window = 'Error'
        style = {'color':'red'}
        comp_speed = 'NA'
    else:
        node = [
            {'data':{'id': str(node), 'num': num, 'type': node.type, 'name':node.name,'bpd':node.bpd, 'wpd':node.wpd, 'scq_size':node.scq_size} }
            for num , node in enumerate(pg.valid_node_set) if isinstance(node, Observer)
        ]

        edge = []
        for src in pg.valid_node_set:
            if (src.left):
                edge.append({'data':{'source':str(src), 'target':str(src.left)}})
            
            if (src.right):
                edge.append({'data':{'source':str(src), 'target':str(src.right)}})

        elements = node + edge
        assembly_window = pg.asm
        style = {'color':'blue'}
        tot_scq_size = pg.tot_size
        tmp = pg.tot_time/int(hw_clk)
        if tmp < 0:
            comp_speed = "Err: Operator unsupported in hardware!"
        elif tmp<1000:
            comp_speed = '{:.6f}μs/ {:.6f}MHz'.format(tmp, 1/tmp) 
        elif tmp<1000000:
            comp_speed = '{:.6f}ms/ {:.6f}KHz'.format(tmp/1000, 1/(tmp/1000)) 
        else:
            comp_speed = '{:.6f}s/ {:.6f}Hz'.format(tmp/1000000, 1/(tmp/1000000))

        resource_fig = data_process.RF

        resource_fig.config(LUT_type, tot_scq_size, int(timestamp_length))
        select_fig = resource_fig.get_LUT_fig() if resource_type == "LUT" else resource_fig.get_BRAM_fig()

    return elements, assembly_window, compile_status, style, comp_speed, tot_scq_size, select_fig

if __name__ == '__main__':
    app.run_server(debug=False)






