import networkx as nx
import numpy as np

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

def MAMP(G, mask, weight='aqi', max_epochs=1, max_mse=5e-3):
    # initialise nodes' weights
    set_node_weights_avg(G, weight)
    # set the mask (true values)
    nx.set_node_attributes(G, mask, weight)
    for epoch in range(max_epochs):
        # compute the current weights
        #G_weights = np.array([node[1][weight] for node in G.nodes(data=True)])
        # compute the graph in the next iteration
        G_next = G.copy()
        for node in G.nodes:
            neighbors = [G.nodes[neighbor] for neighbor in G.neighbors(node)]
            m = aggregate(neighbors, weight)
            h = combine(G.nodes[node][weight], m)
            G_next.nodes[node][weight] = h
        # compute the weights of the next iteration
        #G_next_weights = np.array([node[1][weight] for node in G_next.nodes(data=True)])
        # compute the MSE loss
        #mse = np.mean((G_weights - G_next_weights) ** 2)
        # advance graph to the next iteration
        G = G_next
        # re-establish sensor nodes' values
        nx.set_node_attributes(G, mask, weight)
        # check for early-stopping criterion
        #if mse < max_mse:
        #    break
    # set edges' weights according to the computed nodes' weights
    set_edge_weights_avg(G, weight)
    return G
