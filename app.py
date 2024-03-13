import plotly.graph_objects as go
import argparse as ap
import networkx as nx
import osmnx as ox
import numpy as np


def plot_markers(fig, origin, destination):

    fig.add_trace(go.Scattermapbox(
        lat = [origin[0]],
        lon = [origin[1]],
        mode = 'markers',
        marker = go.scattermapbox.Marker(
            size = 14,
            color = 'black',
        ),
        name = 'Origin'
    ))

    fig.add_trace(go.Scattermapbox(
        lat = [destination[0]],
        lon = [destination[1]],
        mode = 'markers',
        marker = go.scattermapbox.Marker(
            size = 14,
            color = 'red',
        ),
        name = 'Destination'
    ))


def plot_route(fig, X, Y, name='Route', color='blue', zoom=15):

    fig.add_trace(go.Scattermapbox(
        lon = X,
        lat = Y,
        name = name,
        mode = 'lines',
        marker = {'size': 10},
        line = dict(width = 4.5, color = color)
    ))


if __name__ == "__main__":

    parser = ap.ArgumentParser()
    parser.add_argument('--origin', type=str)
    parser.add_argument('--destination', type=str)
    parser.add_argument('--place', type=str, default='Barcelona, Spain')
    parser.add_argument('--style', type=str, choices=['open-street-map', 'carto-positron', 'carto-darkmatter'], default='carto-positron')
    parser.add_argument('--zoom', type=int, default=15)
    args, additional = parser.parse_known_args()

    # obtain map from OpenStreetMap
    ox.settings.use_cache = True
    ox.settings.log_console = True
    G = ox.graph_from_place(args.place, network_type='walk')

    # compute nodes of origin and destination points
    origin_point = ox.geocode(args.origin)
    destination_point = ox.geocode(args.destination)
    origin_node = ox.nearest_nodes(G, origin_point[1], origin_point[0])
    destination_node = ox.nearest_nodes(G, destination_point[1], destination_point[0])

    # compute shortest route
    shortest_distace, shortest_route = nx.bidirectional_dijkstra(G, origin_node, destination_node, weight='length')
    print(f'Shortest route total distance: {shortest_distace}')
    shortest_X = []
    shortest_Y = []
    for i in shortest_route:
        point = G.nodes[i]
        shortest_X.append(point['x'])
        shortest_Y.append(point['y'])

    # show the routes
    fig = go.Figure()
    plot_markers(fig, origin_point, destination_point)
    plot_route(fig, shortest_X, shortest_Y, f'Shortest ({shortest_distace:.0f} m)', 'blue')
    fig.update_layout(
        mapbox_style = args.style,
        mapbox_zoom = args.zoom,
        mapbox_center = {
            'lat': (origin_point[0] + destination_point[0]) / 2,
            'lon': (origin_point[1] + destination_point[1]) / 2
        }
    )
    fig.show()
