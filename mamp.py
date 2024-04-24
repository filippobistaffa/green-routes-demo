import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import random

def export_graph_png(G, png, sensor, mask=None):
    x_pos = nx.get_node_attributes(G, 'x')
    y_pos = nx.get_node_attributes(G, 'y')
    node_colors = {
        node: 'cyan' if node == sensor else ('green' if node in mask else 'orange') for node in G.nodes()
    }
    plt.figure(figsize=(20, 15))
    nx.draw(
        G,
        pos={node: (x_pos[node], y_pos[node]) for node in G.nodes()},
        node_color=[node_colors[node] for node in G.nodes()],
        with_labels=False,
        node_size=800,
        arrows=False,
    )
    node_weights = {node: f'{weight:.0f}' for node, weight in nx.get_node_attributes(G, 'aqi').items()}
    nx.draw_networkx_labels(
        G,
        pos={node: (x_pos[node], y_pos[node]) for node in G.nodes()},
        labels=node_weights,
        font_size=20
    )
    padding = 0.001
    plt.xlim(x_pos[sensor] - padding, x_pos[sensor] + padding)
    plt.ylim(y_pos[sensor] - padding, y_pos[sensor] + padding)
    plt.savefig(png, format='PNG')
    print(f'Exported {png}')

# Compute the nodes' weights as the average of the incoming edges
def set_node_weights_avg(G, weight):
    nodes_avg_weight = {}
    for node in G.nodes:
        incoming_edges = G.in_edges(node, data=True)
        total_weight = sum(edge_data[weight] for (_, _, edge_data) in incoming_edges)
        avg_weight = total_weight / len(incoming_edges)
        nodes_avg_weight[node] = avg_weight
    nx.set_node_attributes(G, nodes_avg_weight, weight)

# Compute the edges' weights as the average of the extreme points
def set_edge_weights_avg(G, weight):
    edges_avg_weight = {}
    for u, v, k in G.edges:
        edges_avg_weight[(u, v, k)] = (G.nodes[u][weight] + G.nodes[v][weight]) / 2
    nx.set_edge_attributes(G, edges_avg_weight, weight)

def aggregate(nodes, weight):
    return sum(node[weight] for node in nodes) / len(nodes)

def combine(h, m):
    return (h + m) / 2

def MAMP(G, mask, sensors, weight='aqi', max_epochs=2, max_mse=5e-3):
    # initialise nodes' weights
    set_node_weights_avg(G, weight)
    # set the mask (true values)
    nx.set_node_attributes(G, mask, weight)
    example_sensor = random.choice(list(sensors.keys()))
    export_graph_png(G, 'epoch_00.png', example_sensor, mask)
    for epoch in range(max_epochs):
        # compute the current weights
        #G_weights = np.array(list(nx.get_node_attributes(G, weight).values()))
        # compute the graph in the next iteration
        G_next = G.copy()
        for node in G.nodes:
            neighbors = [G.nodes[neighbor] for neighbor in G.neighbors(node)]
            m = aggregate(neighbors, weight)
            h = combine(G.nodes[node][weight], m)
            G_next.nodes[node][weight] = h
        # compute the weights of the next iteration
        #G_next_weights = np.array(list(nx.get_node_attributes(G_next, weight).values()))
        # compute the MSE loss
        #mse = np.mean((G_weights - G_next_weights) ** 2)
        # advance graph to the next iteration
        G = G_next
        # re-establish sensor nodes' values
        nx.set_node_attributes(G, mask, weight)
        # check for early-stopping criterion
        #if mse < max_mse:
        #    break
        export_graph_png(G, f'epoch_{epoch+1:02d}.png', example_sensor, mask)
    # set edges' weights according to the computed nodes' weights
    set_edge_weights_avg(G, weight)
    return G

def expand_mask(G, sensors, hops=1):
    mask = {}
    if hops > 0:
        for sensor in sensors:
            neighbors = [node for node, distance in nx.single_source_shortest_path_length(G, sensor).items() if distance <= hops]
            mask.update({node: sensors[sensor] for node in neighbors})
    return mask
