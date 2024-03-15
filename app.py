import plotly.graph_objects as go
import argparse as ap
import networkx as nx
import osmnx as ox
import numpy as np


def auto_zoom(X, Y):
    import planar
    b_box = planar.BoundingBox(list(zip(X, Y)))
    area = b_box.height * b_box.width
    zoom = np.interp(
        x = area,
        xp = [0, 5**-10, 4**-10, 3**-10, 2**-10, 1**-10, 1**-5],
        fp = [20, 17, 16, 15, 14, 7, 5]
    )
    return zoom, b_box.center


def distance_lat_lon(x, y):
    from sklearn.metrics.pairwise import haversine_distances
    from math import radians
    x_radians = [radians(_) for _ in x]
    y_radians = [radians(_) for _ in y]
    result = haversine_distances([x_radians, y_radians])
    return result[0, 1] * 6371000 # Earth's radius


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


if __name__ == "__main__":

    parser = ap.ArgumentParser()
    parser.add_argument('--origin', type=str)
    parser.add_argument('--destination', type=str)
    parser.add_argument('--style', type=str, choices=['open-street-map', 'carto-positron', 'carto-darkmatter'], default='carto-positron')
    args, additional = parser.parse_known_args()

    # compute coordinates of origin and destination points
    origin_point = np.array(ox.geocode(args.origin))
    destination_point = np.array(ox.geocode(args.destination))

    # compute centroid for the map
    centroid_point = (origin_point + destination_point) / 2

    # obtain map from OpenStreetMap
    ox.settings.use_cache = True
    ox.settings.log_console = True
    G = ox.graph_from_point(centroid_point, dist=distance_lat_lon(centroid_point, origin_point), network_type='walk')

    # compute nodes on the graph corresponding to origin and destination points
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

    # add elements to the map
    fig = go.Figure()
    plot_point(fig, origin_point, args.origin, 'black')
    plot_point(fig, destination_point, args.destination, 'red')
    plot_route(fig, shortest_X, shortest_Y, f'Shortest route ({shortest_distace:.0f} m)', 'blue')

    # show the map
    zoom, center = auto_zoom(shortest_X, shortest_Y)
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
