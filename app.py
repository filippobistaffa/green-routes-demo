import plotly.graph_objects as go
import argparse as ap
import networkx as nx
import osmnx as ox
import numpy as np


def auto_zoom(X, Y):

    import planar
    b_box = planar.BoundingBox(list(zip(X, Y)))
    area = b_box.height * b_box.width

    # * 1D-linear interpolation with numpy:
    # - Pass the area as the only x-value and not as a list, in order to return a scalar as well
    # - The x-points "xp" should be in parts in comparable order of magnitude of the given area
    # - The zoom-levels are adapted to the areas, i.e. start with the smallest area possible of 0
    # which leads to the highest possible zoom value 20, and so forth decreasing with increasing areas
    # as these variables are antiproportional
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

    # show the routes
    fig = go.Figure()
    plot_markers(fig, origin_point, destination_point)
    plot_route(fig, shortest_X, shortest_Y, f'Shortest ({shortest_distace:.0f} m)', 'blue')
    zoom, center = auto_zoom(shortest_X, shortest_Y)
    fig.update_layout(
        mapbox_style = args.style,
        mapbox_zoom = zoom,
        mapbox_center = {
            'lon': center[0],
            'lat': center[1]
        },
        margin = {
            'r': 10,
            't': 10,
            'l': 10,
            'b': 10
        }
    )
    fig.show()
