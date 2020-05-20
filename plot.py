"""
Created on Thu Oct 31 18:05:19 2019

@author: andrebmo
"""
import plotly.graph_objects as go
from plotly.offline import plot
import networkx as nx
import data as d

def draw_routes(fuel_cost): #, Insts, time_periods, Vessels):
    G = nx.Graph()

    Insts = d.order_numbers
    Vessels = d.vessel_numbers
    time_periods = d.time_periods

    Inst_time_periods = [[[] for i in Insts] for v in Vessels]
    for v in Vessels:
        for i in Insts:
            for t in time_periods:
                count = 0
                for j in Insts:
                    for tau in time_periods:
                        if fuel_cost[v][j][tau][i][t] != 0 or fuel_cost[v][i][t][j][tau] != 0:
                            count += 1
                if count != 0:
                    Inst_time_periods[v][i].append(t)


    for i in Insts:
        for t in Inst_time_periods[0][i]:
            G.add_node(t*30 + i, pos=(t,i))

    for i in Insts:
        for t in time_periods:
            for j in Insts:
                for tau in time_periods:
                    if fuel_cost[0][i][t][j][tau]!= 0:
                        G.add_edge(t*30 + i, tau*30 + j, weight=fuel_cost[0][i][t][j][tau])
                        
    
    edge_x = []
    edge_y = []
    
    for edge in G.edges():
        x0, y0 = G.nodes[edge[0]]['pos']
        x1, y1 = G.nodes[edge[1]]['pos']
        edge_x.append(x0)
        edge_x.append(x1)
        edge_x.append(None)
        edge_y.append(y0)
        edge_y.append(y1)
        edge_y.append(None)
    
    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=0.5, color='#666'),
        hoverinfo='none',
        mode='lines')
    
    node_x = []
    node_y = []
    
    for node in G.nodes():
        x, y = G.nodes[node]['pos']
        node_x.append(x)
        node_y.append(y)
    
    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode='markers',
        hoverinfo='text',
        marker=dict(
            showscale=True,
            # colorscale options
            #'Greys' | 'YlGnBu' | 'Greens' | 'YlOrRd' | 'Bluered' | 'RdBu' |
            #'Reds' | 'Blues' | 'Picnic' | 'Rainbow' | 'Portland' | 'Jet' |
            #'Hot' | 'Blackbody' | 'Earth' | 'Electric' | 'Viridis' |
            colorscale='YlGnBu',
            reversescale=True,
            color=[],
            size=10,
            colorbar=dict(
                thickness=10,
                title='Node Connections',
                xanchor='left',
                titleside='right'
            ),
            line_width=2))      
    
    node_adjacencies = []
    node_text = []
    for node, adjacencies in enumerate(G.adjacency()):
        node_adjacencies.append(len(adjacencies[1]))
        node_text.append('# of connections: '+str(len(adjacencies[1])))
    
    node_trace.marker.color = node_adjacencies
    node_trace.text = node_text
    
    fig = go.Figure(data=[edge_trace, node_trace],
                 layout=go.Layout(
                    title='<br>Network graph made with Python',
                    titlefont_size=16,
                    showlegend=False,
                    hovermode='closest',
                    margin=dict(b=20,l=5,r=5,t=40),
                    annotations=[ dict(
                        text="The Arc-Flow Model",
                        showarrow=False,
                        xref="paper", yref="paper",
                        x=0.005, y=-0.002 ) ],
                    xaxis=dict(showgrid=True, zeroline=False, showticklabels=True),
                    yaxis=dict(showgrid=True, zeroline=False, showticklabels=True))
                    )
    plot(fig, auto_open=True)