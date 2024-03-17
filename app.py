import plotly.graph_objects as go
import argparse as ap
import networkx as nx
import osmnx as ox
import numpy as np
import pickle
import sys
import os


if __name__ == "__main__":

    parser = ap.ArgumentParser()
    parser.add_argument('--origin', type=str)
    parser.add_argument('--destination', type=str)
    parser.add_argument('--graph', type=str, default=os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data', '2022_graph_aqi.pkl'))
    parser.add_argument('--style', type=str, choices=['open-street-map', 'carto-positron', 'carto-darkmatter'], default='carto-positron')
    parser.add_argument('--aqi', type=str, choices=['no2', 'pm25', 'pm10'], default='no2')
    args, additional = parser.parse_known_args()

    # load precomputed graph
    with open(args.graph, 'rb') as f:
        G = pickle.load(f)

    # compute coordinates of origin and destination points
    origin_point = np.array(ox.geocode(args.origin))
    destination_point = np.array(ox.geocode(args.destination))

    # compute nodes on the graph corresponding to origin and destination points
    origin_node = ox.nearest_nodes(G, origin_point[1], origin_point[0])
    destination_node = ox.nearest_nodes(G, destination_point[1], destination_point[0])

    # air quality index function
    def aqi(edge_data):
        length = edge_data['length']
        aqi_data = edge_data[args.aqi.upper()].split(' ')[0]
        if aqi_data.startswith('>'):
            aqi_value = 1.5 * float(aqi_data[1:])
        else:
            aqi_range = [float(n) for n in aqi_data.split('-')]
            aqi_value = (aqi_range[0] + aqi_range[0]) / 2
        return length * aqi_value

    # store air quality index on each edge
    for u, v in G.edges():
        G[u][v][0]['aqi'] = aqi(G.get_edge_data(u, v)[0])

    # compute shortest route
    shortest_distance, shortest_route = nx.bidirectional_dijkstra(G, origin_node, destination_node, weight='length')
    try:
        shortest_exposure = nx.path_weight(G, shortest_route, 'aqi')
    except KeyError:
        print('ERROR: Missing air quality data for selected locations', file=sys.stderr)
        quit()
    print(f'Shortest route total distance: {shortest_distance:.2f}')
    print(f'Shortest route total exposure: {shortest_exposure:.2f}')
    shortest_X = []
    shortest_Y = []
    for i in shortest_route:
        point = G.nodes[i]
        shortest_X.append(point['x'])
        shortest_Y.append(point['y'])

    # compute green route
    green_exposure, green_route = nx.bidirectional_dijkstra(G, origin_node, destination_node, weight='aqi')
    green_distance = nx.path_weight(G, green_route, 'length')
    print(f'Green route total distance: {green_distance:.2f}')
    print(f'Green route total exposure: {green_exposure:.2f}')
    green_X = []
    green_Y = []
    for i in green_route:
        point = G.nodes[i]
        green_X.append(point['x'])
        green_Y.append(point['y'])

    # compute KPIs (%)
    exposure_reduction_percentage = 100 * (shortest_exposure - green_exposure) / shortest_exposure
    distance_increase_percentage = 100 * (green_distance - shortest_distance) / shortest_distance
    print(f'{args.aqi.upper()} exposure reduction: -{exposure_reduction_percentage:.2f}%')
    print(f'Distance increase: +{distance_increase_percentage:.2f}%')

    # generate map
    fig = go.Figure()

    def plot_point(fig, point, name='Point', color='black'):
        fig.add_trace(go.Scattermapbox(
            lat = [point[0]],
            lon = [point[1]],
            mode = 'markers',
            marker = go.scattermapbox.Marker(
                size = 14,
                color = color,
            ),
            name = name
        ))

    def plot_route(fig, X, Y, name='Route', color='blue'):
        fig.add_trace(go.Scattermapbox(
            lon = X,
            lat = Y,
            name = name,
            mode = 'lines',
            marker = {'size': 10},
            line = dict(width = 4.5, color = color)
        ))

    # add elements to the map
    plot_point(fig, origin_point, args.origin, 'black')
    plot_point(fig, destination_point, args.destination, 'red')
    plot_route(fig, shortest_X, shortest_Y, f'Shortest route ({shortest_distance:.0f} m)', 'blue')
    plot_route(fig, green_X, green_Y, f'Green route ({green_distance:.0f} m, -{exposure_reduction_percentage:.0f}% {args.aqi.upper()})', 'green')

    # show the map
    def auto_zoom(X, Y):
        import planar
        b_box = planar.BoundingBox(list(zip(X, Y)))
        area = b_box.height * b_box.width
        zoom = np.interp(
            x = area,
            xp = [0, 5**-10, 4**-10, 3**-10, 2**-10, 1**-10, 1**-5],
            fp = [20, 17, 16, 15, 14, 7, 5]
        )
        return 0.95 * zoom, b_box.center
    zoom, center = auto_zoom(shortest_X + green_X, shortest_Y + green_Y)
    fig.update_layout(
        mapbox_style = args.style,
        mapbox_zoom = zoom,
        mapbox_center = {
            'lon': center[0],
            'lat': center[1]
        },
        margin = {
            'r': 30,
            't': 30,
            'l': 30,
            'b': 30
        }
    )
    fig.show()
