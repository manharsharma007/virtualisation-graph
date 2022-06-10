from flask import Flask, render_template, request, session, redirect, url_for
import numpy as np
import matplotlib.pyplot as plt
import networkx as nx
import os
import matplotlib
from networkx.readwrite import json_graph
import json
import pickle

from networkx.algorithms import centrality as cn
from includes.louvain.louvain import Louvain

import collections
import random

matplotlib.use("WebAgg")

app = Flask(__name__, template_folder='templates', static_folder='static')

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

        graph_ = {"labels":False, "n_dist": 0.1, "fixed_n":False, "node_size" : 50, "edges":"#aaaaaa", "font_color":"#eeeeee", "data":(nodes, edges)}
        pickle.dump(graph_, open('model.pkl','wb'))

        return redirect(url_for('update_graph'))

    else:
        return render_template('index.html')

@app.route('/update_graph', methods = ['GET', 'POST'])
def update_graph():
    graph_ = pickle.load(open('model.pkl','rb'))
    color_map = False
    n_list = False
    (nodes, edges) = graph_["data"]
    cluster = False

    if(request.method == 'POST'):

        if('rm_node' in request.form and not request.form['rm_node'] == ""):
            (nodes, edges) = remove_node(request.form['rm_node'], nodes, edges)

        if('rm_edge' in request.form and not request.form['rm_edge'] == ""):
            edge = request.form['rm_edge'].split(',')
            (nodes, edges) = remove_edge(edge[0], edge[1], (nodes, edges))

        if('v_process' in request.form and not request.form['v_process'] == ""):
            agents = request.form['v_process'].split(',')
            color_map = visualise_process(nodes, agents)

        if('w_node' in request.form and not request.form['w_node'] == ""):
            agents = request.form['w_node'].split(',')
            if('w_length' in request.form and not request.form['w_length'] == ""):
                length = int(request.form['w_length'])
            else:
                length = 10
            color_map = random_walk(nodes, agents, length)

        if('l_cluster' in request.form and request.form['l_cluster'] == "louvain"):
            cluster = True

        display_el = request.form.getlist("display_el")

        if('labels' in display_el):
            graph_["labels"] = True
        else:
            graph_["labels"] = False

        if('nodes' in display_el):
            graph_["fixed_n"] = True
        else:
            graph_["fixed_n"] = False

        if('n_dist' in request.form and not request.form['n_dist'] == ""):
            graph_["n_dist"] = float(request.form['n_dist'])
        else:
            graph_["n_dist"] = 1/np.sqrt(len(nodes))

        if('c_edges' in request.form and not request.form['c_edges'] == ""):
            graph_["edges"] = request.form['c_edges']

        if('c_labels' in request.form and not request.form['c_labels'] == ""):
            graph_["font_color"] = request.form['c_labels']

        if('node_size' in request.form and not request.form['node_size'] == ""):
            graph_["node_size"] = int(request.form['node_size'])


    if(not color_map):
        (n_list, color_map) = connected_components(nodes)

    graph_["data"] = (nodes, edges)

    pickle.dump(graph_, open('model.pkl','wb'))

    draw_graph(graph_, color_map, cluster)
    
    return render_template('graph.html', graph_plot = 'graphs/plots/graph_plot.png', form_data = request.form)



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
            edges.append((d[0], d[1], 1))

            if(d[0] not in nodes):
                nodes[d[0]] = {}
                nodes[d[0]]["nbrs"] = []
                nodes[d[0]]["indx"] = []
                
            
            if(d[1] not in nodes):
                nodes[d[1]] = {}
                nodes[d[1]]["nbrs"] = []
                nodes[d[1]]["indx"] = []

            if(d[1] not in nodes[d[0]]["nbrs"]):
                nodes[d[0]]["nbrs"].append(d[1])
            if(d[0] not in nodes[d[1]]["nbrs"]):
                nodes[d[1]]["nbrs"].append(d[0])

            inde += 1
            
    
    return (nodes, edges)

def remove_node(node, nodes, edges):
    if(node not in nodes):
        return(nodes, edges)

    n_list = list(nodes[node]['indx'])
    
    for k, v in nodes.items():
        if(node in nodes[k]["nbrs"]):
            nodes[k]["nbrs"].remove(node)
        
    for e in n_list:
        if(e < len(edges)):
            edges[e] = 0
        for k, v in nodes.items():
            if(e  in nodes[k]["indx"]):
                nodes[k]["indx"].remove(e)
        
    while 0 in edges: edges.remove(0)

    nodes.pop(node)
        
    return (nodes, edges)

def remove_edge(node1, node2, data):
    (nodes, edges) = data
    edge = (node1, node2, 1)
    
    index = -1
    if(edge in edges):
        index = edges.index(edge)
        edges.remove(edge)
    else:
        return (nodes, edges)

    if(index != -1):
        for k, v in nodes.items():
            if(index in nodes[k]["indx"]):
                nodes[k]["indx"].remove(index)
                
        nodes[node1]['nbrs'].remove(node2)
        nodes[node2]['nbrs'].remove(node1)

    return (nodes,edges)


def random_coloring(graph,n_colors):
    coloring = {}
    for node in graph.nodes():
        coloring[node] = np.random.randint(0,n_colors)
    return coloring


def draw_graph(graph, color_map = False, cluster = False):

    fig = plt.figure(figsize=(15,15))

    (nodes, edges) = graph["data"]
    
    G=nx.Graph()
    G.add_nodes_from(nodes)
    G.add_weighted_edges_from(edges)

    degree_dict = dict(G.degree(G.nodes()))
    nx.set_node_attributes(G, degree_dict, 'degree')

    pos = nx.spring_layout(G,k=graph["n_dist"])

    if(cluster):
        color_map = louvain_cluster(G)

    if(graph["fixed_n"]):
        node_size = [graph["node_size"] for v in degree_dict.values()]
    else:
        node_size = [graph["node_size"] * v for v in degree_dict.values()]
    if(color_map):
        nx.set_node_attributes(G, dict([(i, color_map[i]) for i in G.nodes()]), 'color')
        nx.draw(G, pos, edge_color=graph['edges'], width=0.6, font_size="12", font_color= graph["font_color"], node_color = [color_map[i] for i in G.nodes()], with_labels = graph['labels'], node_size = node_size)

    else:
        nx.draw(G, pos, edge_color=graph['edges'], width=0.6, font_size="12", font_color= graph["font_color"], with_labels = graph['labels'], node_size = node_size)

    plt.axis('off')
    plt.savefig("static/graphs/plots/graph_plot.png", dpi = 300)
    plt.clf()
    plt.close('all')

    data = json_graph.node_link_data(G)
    data["d_labels"] = False
    data["n_dist"] = 0.1
    data["fixed_n"] = False
    data["edges"] = graph["edges"]
    data["font_color"] = graph['font_color']
    with open(os.path.join(app.config['UPLOAD_PATH'], 'graph.json'), 'w') as f:
        json.dump(data, f)

def valid_coloring(graph,coloring):
    return not any([coloring[x]==coloring[y] for (x,y) in graph.edges()])

def convert_to_hex(rgba_color) :
    red = int(rgba_color["red"])
    green = int(rgba_color["green"])
    blue = int(rgba_color["blue"])
    alpha = int(rgba_color["alpha"])
    
    red = 255 if red > 255 else red
    green = 255 if green > 255 else green
    blue = 255 if blue > 255 else blue
    alpha = 255 if alpha > 255 else alpha
    
    red = 0 if red < 0 else red
    green = 0 if green < 0 else green
    blue = 0 if blue < 0 else blue
    alpha = 0 if alpha < 0 else alpha

    return '#{:02x}{:02x}{:02x}{:02x}'.format( red, green , blue, alpha )


# BFS Visualise function
def visualise_process(graph, nodes = []):
    li, color_map = [], {}
    
    for i in nodes:
        (li, color_map) = bfs(graph, i, color_map)
        
    for i,v in graph.items():
        if(i not in color_map):
            color_map[i] = convert_to_hex({"red" : 200, "green" : 200, "blue" : 200, "alpha" : 100})
    
    return color_map   
# BFS algorithm
def bfs(graph, root, color_map = {}):
    
    color = {'r' : random.randint(100,255), 'g' : random.randint(100,255), 'b' : random.randint(100,255), 'a' : 255}

    visited, queue = set(), collections.deque([root])
    visited.add(root)
    
    color_map[root] = convert_to_hex({"red" : color['r'], "green" : color['g'], "blue" : color['b'], "alpha" : color['a']})
    
    trav = []

    while queue:

        # Dequeue a vertex from queue
        vertex = queue.popleft()
        trav.append(vertex)

        # If not visited, mark it as visited, and
        # enqueue it
        for neighbour in graph[vertex]["nbrs"]:
            if neighbour not in visited:
                visited.add(neighbour)
                queue.append(neighbour)
                
                if(neighbour in color_map):
                    color_map[neighbour] = convert_to_hex({"red" : 0, "green" : 0, "blue" : 0, "alpha" : 200})
                else:
                    color_map[neighbour] = convert_to_hex({"red" : color['r'], "green" : color['g'], "blue" : color['b'], "alpha" : color['a']})
        if(color['a'] > 150):
            color['a'] = color['a'] - color['a'] * 0.15
        if(not color['r'] + color['r'] * 0.075 > 220):
            color['r'] = color['r'] + color['r'] * 0.075
        if(not color['g'] + color['g'] * 0.075 > 220):
            color['g'] = color['g'] + color['g'] * 0.075
        if(not color['b'] + color['b'] * 0.065 > 220):
            color['b'] = color['b'] + color['b'] * 0.065
    
    return (trav, color_map)


def connected_components(graph, root = False):
    
    visited = []
    nodes = set(graph.keys())
    seen = set()
    
    
    color_map = {}
    
    components = []
    
    for root in nodes:
        if(root not in seen):
            
            seen.add(root)
            visited, queue = set(), collections.deque([root])
            visited.add(root)

            trav = []
            
            re_ = random.randint(50, 200) 
            ge_ = random.randint(50, 200) 
            be_ = random.randint(50, 200) 
            ae_ = 255
            
            color_map[root] = convert_to_hex({"red" : re_, "green" : ge_, "blue" : be_, "alpha" : ae_})
            
            while queue:

                # Dequeue a vertex from queue
                vertex = queue.popleft()
                trav.append(vertex)
                seen.add(vertex)

                # If not visited, mark it as visited, and
                # enqueue it
                for neighbour in graph[vertex]["nbrs"]:
                    if neighbour not in visited:
                        visited.add(neighbour)
                        queue.append(neighbour)
                        color_map[neighbour] = convert_to_hex({"red" : re_, "green" : ge_, "blue" : be_, "alpha" : ae_})
                
                if(not ae_ < 150):
                    ae_ = ae_ - ae_ * 0.075
                if(not re_ + re_ * 0.075 > 250):
                    re_ = re_ + re_ * 0.075
                if(not ge_ + ge_ * 0.055 > 250):
                    ge_ = ge_ + ge_ * 0.055
                if(not be_ + be_ * 0.065 > 250):
                    be_ = be_ + be_ * 0.065
                    
                    
            components.append(trav)
    return (components, color_map)

def walk(graph, root, length = 10, visited_ = {}, color_map = {}):
    
    color = {'r' : random.randint(100,255), 'g' : random.randint(100,255), 'b' : random.randint(100,255), 'a' : 180}

    visited, queue = set(), collections.deque([root])
    visited.add(root)
    
    color_map[root] = convert_to_hex({"red" : color['r'], "green" : color['g'], "blue" : color['b'], "alpha" : color['a']})
    
    trav = {}

    for k in range(length):

        # Dequeue a vertex from queue
        vertex = queue.popleft()
        if(vertex in trav):
            trav[vertex] += 1
        else:
            trav[vertex] = 1

        # If not visited, mark it as visited, and
        # enqueue it
        
        if(graph[vertex]["nbrs"]):
            trail = random.choice(graph[vertex]["nbrs"])
            if(trail in visited_):
                color_map[trail] = convert_to_hex({"red" : 0, "green" : 0, "blue" : 0, "alpha" : 255})
                
            c_to_update = max(color, key=color.get)
            if('r' == c_to_update):
                color_map[trail] = convert_to_hex({"red" : color['r'] + (color['r'] * trav[vertex] / 30), "green" : color['g'] - (color['g'] * trav[vertex] / 30), "blue" : color['b'] - (color['b'] * trav[vertex] / 30), "alpha" : color['a'] })
            
            if('g' == c_to_update):
                color_map[trail] = convert_to_hex({"red" : color['r'] - (color['r'] * trav[vertex] / 30), "green" : color['g'] + (color['g'] * trav[vertex] / 30), "blue" : color['b'] - (color['b'] * trav[vertex] / 30), "alpha" : color['a'] })
            
            if('g' == c_to_update):
                color_map[trail] = convert_to_hex({"red" : color['r'] - (color['r'] * trav[vertex] / 30), "green" : color['g'] - (color['g'] * trav[vertex] / 30), "blue" : color['b'] + (color['b'] * trav[vertex] / 30), "alpha" : color['a'] })
            
            
            visited.add(trail)
            queue.append(trail)
    
    return (trav, color_map)

def random_walk(graph, nodes = [], length = 10):
    li, color_map = [], {}
    for i in nodes:
        (li, color_map) = walk(graph, i, length, li, color_map)

    for i,v in graph.items():
        if(i not in color_map):
            color_map[i] = convert_to_hex({"red" : 200, "green" : 200, "blue" : 200, "alpha" : 100})

    return color_map


def louvain_cluster(graph):
    louvain = Louvain()
    partition = louvain.getBestPartition(graph)
    clusters = {}

    for k, v in partition.items():
        
        if(v in clusters):
            clusters[v].append(k)
        else:
            clusters[v] = [k]

    color_map = {}
    visited = []

    for c in clusters.values():
        
        color = {'r' : random.randint(0,255), 'g' : random.randint(0,255), 'b' : random.randint(0,255), 'a' : 180}
        
        for i in c:
            if(i in visited):
                color_map[i] = convert_to_hex({"red" : 10, "green" : color['g'], "blue" : 10, "alpha" : 255})
            else:
                visited.append(i)
                color_map[i] = convert_to_hex({"red" : color['r'], "green" : color['g'], "blue" : color['b'], "alpha" : color['a']})

    return color_map

if __name__ == '__main__':
   app.run(debug = True)
