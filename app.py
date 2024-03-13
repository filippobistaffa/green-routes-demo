import plotly.graph_objects as go
import argparse as ap
import networkx as nx
import osmnx as ox
import numpy as np


def plot_path(origin_point, destination_point, X, Y, name='Path', color='blue', zoom=15):

    fig = go.Figure()

    fig.add_trace(go.Scattermapbox(
        lat = [origin_point[0]],
        lon = [origin_point[1]],
        mode = 'markers',
        marker = go.scattermapbox.Marker(
            size = 14,
            color = 'black',
        ),
        name = 'Origin'
    ))

    fig.add_trace(go.Scattermapbox(
        lat = [destination_point[0]],
        lon = [destination_point[1]],
        mode = 'markers',
        marker = go.scattermapbox.Marker(
            size = 14,
            color = 'red',
        ),
        name = 'Destination'
    ))

    fig.add_trace(go.Scattermapbox(
        lon = X,
        lat = Y,
        name = name,
        mode = 'lines',
        marker = {'size': 10},
        line = dict(width = 4.5, color = color)
    ))

    fig.update_layout(
        mapbox_style = 'carto-positron',
        mapbox_zoom = zoom,
        mapbox_center = {
            'lat': (origin_point[0] + destination_point[0]) / 2,
            'lon': (origin_point[1] + destination_point[1]) / 2
        }
    )

    fig.show()


if __name__ == "__main__":

    parser = ap.ArgumentParser()
    parser.add_argument('--origin', type=float, nargs=2, default=[41.4013741, 2.1552681])
    parser.add_argument('--destination', type=float, nargs=2, default=[41.4107595, 2.1433257])
    parser.add_argument('--place', type=str, default='Barcelona, Spain')
    args, additional = parser.parse_known_args()

    # obtain map from OpenStreetMap
    G = ox.graph_from_place(args.place, network_type='walk')

    # compute nodes of origin and destination points
    origin_node = ox.nearest_nodes(G, args.origin[1], args.origin[0]) 
    destination_node = ox.nearest_nodes(G, args.destination[1], args.destination[0])

    # compute shortest route
    shortest_length, shortest_route = nx.bidirectional_dijkstra(G, origin_node, destination_node)
    shortest_X = []
    shortest_Y = []
    for i in shortest_route:
        point = G.nodes[i]
        shortest_X.append(point['x'])
        shortest_Y.append(point['y'])

    plot_path(args.origin, args.destination, shortest_X, shortest_Y, 'Shortest', 'blue')
