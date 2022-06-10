from flask import Flask, render_template, request, session, redirect, url_for
import numpy as np
import matplotlib.pyplot as plt
import networkx as nx
import os
import matplotlib
from networkx.readwrite import json_graph
import json

from networkx.algorithms import centrality as cn

matplotlib.use("WebAgg")

app = Flask(__name__, template_folder='static')

app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024
app.config['UPLOAD_EXTENSIONS'] = ['.tgf']
app.config['UPLOAD_PATH'] = 'static/assets/uploads'
app.secret_key = 'any random string'
app.config['colors'] = ['red','blue','green','yellow','purple']


@app.route('/')
def index():
	return render_template('index.html')

@app.route('/create_graph', methods = ['GET', 'POST'])
def create_graph():
    if(request.method == 'POST'):
        f = request.files['file']
        filename = f.filename
        f.save(os.path.join(app.config['UPLOAD_PATH'],filename))

        (nodes, edges) = prepare_data(os.path.join(app.config['UPLOAD_PATH'],filename))

        session['nodes'] = nodes
        session['edges'] = edges
        return redirect(url_for('update_graph'))

    else:
        return render_template('index.html')

@app.route('/update_graph', methods = ['GET', 'POST'])
def update_graph():
    nodes = session['nodes']
    edges = session['edges']
    if(request.method == 'POST'):

        if('rm_node' in request.form and not request.form['rm_node'] == ""):
            (nodes, edges) = remove_node(request.form['rm_node'])

        if('rm_edge' in request.form and not request.form['rm_edge'] == ""):
            edges = remove_edge(request.form['rm_edge'])

        if('v_process' in request.form and not request.form['v_process'] == ""):
            (n_list, color_map) = bfs(nodes, request.form['v_process'])

        if('v_node' in request.form and not request.form['v_node'] == ""):
            (n_list, color_map) = bfs(nodes, request.form['v_node'])

    session['nodes'] = nodes
    session['edges'] = edges

    draw_graph(nodes, edges, color_map = False, n_list = False)
    
    G = nx.Graph()
    G.add_nodes_from(nodes)
    G.add_edges_from(edges)

    degree_dict = dict(G.degree(G.nodes()))
    nx.set_node_attributes(G, degree_dict, 'degree')

    coloring = random_coloring(G, len(app.config['colors']))
    data = draw_graph(G, coloring, app.config['colors'])

    # pos = nx.spring_layout(G)

    # nx.draw_networkx(G, with_labels = True)
    # plt.savefig("static/assets/images/graph_plot.png")
    # plt.clf()
    # plt.close('all')

    with open(os.path.join(app.config['UPLOAD_PATH'], 'graph.json'), 'w') as f:
        json.dump(data, f)
    return render_template('graph.html', graph_plot = 'assets/images/graph_plot.png')



@app.route('/interactive_graph')
def interactive_graph():
    return render_template('interactive_graph.html')


#prepare the data
#@files - input file to read
#@indices - tuple of indices to fetech from the file
#@labls - dictionary of labels and their coressponding category value

def prepare_data(file):
    with open(file) as f:
        data = f.read()

    #data = data.replace('class-','')
    data = data.splitlines()
    
    nodes = {}
    edges = []
    inde = 0
    
    flag = False
    
    for ind, i in enumerate(data):
        
        i = i.strip()
        
        if(i == ''):
            continue
        
        if(i == "#"):
            flag = True
            continue
            
        if(flag == False):
            d = i.split(' ');
            nodes[d[0]] = {}
            nodes[d[0]]["nbrs"] = []
            nodes[d[0]]["indx"] = []

            
        else:
            d = i.split(' ')
            edges.append((d[0], d[1]))
            nodes[d[0]]["indx"].append(inde)
            nodes[d[1]]["indx"].append(inde)

            if(d[1] not in nodes[d[0]]["nbrs"]):
                nodes[d[0]]["nbrs"].append(d[1])
            if(d[0] not in nodes[d[1]]["nbrs"]):
                nodes[d[1]]["nbrs"].append(d[0])

            inde += 1
            
    
    return (nodes, edges)

def remove_node(node):
    nodes = session['nodes']
    edges = session['edges']
    n_list = nodes[node]['indx']

    for e in n_list:
        edges[e] = 0
        
    while 0 in edges: edges.remove(0)

    nodes.pop(node)
        
    return (nodes, edges)

def remove_node(edge):
    edges = session['edges']
    
    edges.remove(edge)
        
    return edges


def random_coloring(graph,n_colors):
    coloring = {}
    for node in graph.nodes():
        coloring[node] = np.random.randint(0,n_colors)
    return coloring

def draw_graph_random_coloring(G,coloring,colors):
    fig = plt.figure()
    n_colors = len(colors)

    degree_dict = dict(G.degree(G.nodes()))
    nx.set_node_attributes(G, degree_dict, 'degree')
    
    betweenness_dict = nx.betweenness_centrality(G) # Run betweenness centrality
    eigenvector_dict = nx.eigenvector_centrality(G) # Run eigenvector centrality

    # Assign each to an attribute in your network
    nx.set_node_attributes(G, betweenness_dict, 'betweenness')
    nx.set_node_attributes(G, eigenvector_dict, 'eigenvector')

    nx.draw(G, with_labels = True)

    plt.axis('off')
    plt.savefig("static/assets/images/graph_plot.png")
    plt.clf()
    plt.close('all')

    data = json_graph.node_link_data(G)
    return data

def valid_coloring(graph,coloring):
    return not any([coloring[x]==coloring[y] for (x,y) in graph.edges()])

def convert_to_hex(rgba_color) :
    red = int(rgba_color["red"])
    green = int(rgba_color["green"])
    blue = int(rgba_color["blue"])
    alpha = int(rgba_color["alpha"])
    return '#{:02x}{:02x}{:02x}{:02x}'.format( red, green , blue, alpha )

if __name__ == '__main__':
   app.run(debug = True)
