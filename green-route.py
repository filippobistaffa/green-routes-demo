import plotly.graph_objects as go
import argparse as ap
import networkx as nx
import osmnx as ox
import numpy as np
import webcolors
import pickle
import json
import os
import re

from mamp import MAMP, expand_mask

def point_trace(point, name='Point', color='black', label=None, group=None, group_title=None):
    if color is not None:
        if not color.startswith('#'):
            color = webcolors.name_to_hex(color)
        rgb = webcolors.hex_to_rgb(color)
        # https://github.com/bgrins/TinyColor/blob/b49018c9f2dbca313d80d7a4dad25e26143cfe01/mod.js#L43 +
        # https://github.com/bgrins/TinyColor/blob/b49018c9f2dbca313d80d7a4dad25e26143cfe01/mod.js#L63
        color_is_dark = (rgb.red * 0.299 + rgb.green * 0.587 + rgb.blue * 0.114) < 128
    return go.Scattermapbox(
        lat = [point[0]],
        lon = [point[1]],
        mode = 'markers+text',
        marker = dict(
            size = 14 if label is None else 30,
            color = color
        ),
        name = name,
        text = label,
        hovertemplate = f'{name}',
        textfont = dict(color='white') if color_is_dark else None,
        legendgroup=group,
        legendgrouptitle_text=group_title,
    )

def decompose_coordinates(G, coordinate_list):
    X = []
    Y = []
    for i in coordinate_list:
        point = G.nodes[i]
        X.append(point['x'])
        Y.append(point['y'])
    return X, Y

def route_trace(G, route, name='Route', color='blue', group=None, group_title=None):
    X, Y = decompose_coordinates(G, route)
    return go.Scattermapbox(
        lon = X,
        lat = Y,
        name = name,
        mode = 'lines',
        line = dict(
            width = 4.5,
            color = color
        ),
        hovertemplate = f'{name}',
        legendgroup=group,
        legendgrouptitle_text=group_title,
    )

if __name__ == "__main__":

    parser = ap.ArgumentParser(
        #description = "Compute green routes minimizing the exposure to air pollutants",
        formatter_class=lambda prog: ap.HelpFormatter(prog,max_help_position=33))
    parser.add_argument('--origin', type=str, help='address of origin point')
    parser.add_argument('--destination', type=str, help='address of destination point')
    parser.add_argument('--pollutant', type=str, choices=['no2', 'pm25', 'pm10'], default='no2',
        help='pollutant to consider for air quality data')
    parser.add_argument('--historical', type=str,
        default=os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data', '2022_graph_aqi.pkl'),
        help='*.pkl file containing historical air quality data')
    parser.add_argument('--real-time', type=str,
        help='*.json file containing real-time air quality data')
    parser.add_argument('--sensor-radius', type=int, default=1,
        help='extend air quality value of each sensor to its neighbors (up to specified number of hops)')
    parser.add_argument('--mamp-epochs', type=int, default=2,
        help='number of epochs of the MAMP interpolation algorithm')
    parser.add_argument('--map-style', type=str, choices=['open-street-map', 'carto-positron', 'carto-darkmatter'],
        default='carto-positron')
    args, additional = parser.parse_known_args()

    # load precomputed graph
    with open(args.historical, 'rb') as f:
        G = pickle.load(f)

    # generate map
    fig = go.Figure()

    # compute coordinates of origin and destination points
    origin_point = np.array(ox.geocode(args.origin))
    destination_point = np.array(ox.geocode(args.destination))

    # compute nodes on the graph corresponding to origin and destination points
    origin_node = ox.nearest_nodes(G, origin_point[1], origin_point[0])
    destination_node = ox.nearest_nodes(G, destination_point[1], destination_point[0])

    # show origin and destination points
    fig.add_trace(point_trace(origin_point, args.origin, 'black', group='origin', group_title='Origin'))
    fig.add_trace(point_trace(destination_point, args.destination, 'red', group='destination', group_title='Destination'))

    # air quality index function
    def aqi(edge_data):
        aqi_data = edge_data[args.pollutant.upper()].split(' ')[0]
        if aqi_data.startswith('>'):
            aqi_value = 1.5 * float(aqi_data[1:])
        else:
            aqi_range = [float(n) for n in aqi_data.split('-')]
            aqi_value = (aqi_range[0] + aqi_range[0]) / 2
        return aqi_value

    # exposure function
    def exposure(edge_data):
        return edge_data['length'] * edge_data['aqi']

    # store air quality index and exposure on each edge
    for u, v, k in G.edges:
        G[u][v][k]['aqi'] = aqi(G[u][v][k])
        G[u][v][k]['exposure'] = exposure(G[u][v][k])

    # compute shortest route
    shortest_distance, shortest_route = nx.bidirectional_dijkstra(G, origin_node, destination_node, weight='length')
    shortest_exposure = nx.path_weight(G, shortest_route, 'exposure')

    # compute green route based on historical data
    historical_exposure, historical_route = nx.bidirectional_dijkstra(G, origin_node, destination_node, weight='exposure')
    historical_distance = nx.path_weight(G, historical_route, 'length')

    # html names for pullutants
    pollutants = {
        'no2': 'NO<sub>2</sub>',
        'pm25': 'PM<sub>2.5</sub>',
        'pm10': 'PM<sub>10</sub>',
    }

    # incorporate sensor data if available
    if args.real_time is not None:
        sensor_traces = []
        sensor_nodes_aqi = {}
        with open(args.real_time) as f:
            sensors = json.load(f)
            datetime = sensors[0]['measures'][0]['datetime']
            legend_first = True
            for sensor in sensors:
                sensor_node = ox.nearest_nodes(G, float(sensor['longitude']), float(sensor['latitude']))
                for measure in sensor['measures']:
                    if args.pollutant.upper() == re.sub(r'<[^>]+>', '', measure['acronym']):
                        sensor_nodes_aqi[sensor_node] = int(measure['value'])
                        # create sensors' traces to plot them later
                        sensor_traces.append(point_trace(
                            (sensor['latitude'], sensor['longitude']),
                            name = f"{sensor['name']}: {measure['value']} {measure['unit']} {pollutants[args.pollutant]}",
                            color = measure['color'],
                            label = measure['value'],
                            group='sensors',
                            group_title=f'Sensors ({datetime})' if legend_first else None))
                legend_first = False
        # extend the sensors' values for the desired number of hops
        mask = expand_mask(G, sensor_nodes_aqi, args.sensor_radius)
        # run MAMP algorithm
        G = MAMP(G, {**mask, **sensor_nodes_aqi}, sensor_nodes_aqi, max_epochs=args.mamp_epochs)
        # recompute exposure with updated air quality values
        for u, v, k in G.edges:
            G[u][v][k]['exposure'] = exposure(G[u][v][k])
        shortest_exposure = nx.path_weight(G, shortest_route, 'exposure')
        historical_exposure = nx.path_weight(G, historical_route, 'exposure')
        # compute green route based on real-time data
        realtime_exposure, realtime_route = nx.bidirectional_dijkstra(G, origin_node, destination_node, weight='exposure')
        realtime_distance = nx.path_weight(G, realtime_route, 'length')

    # compute and show KPIs (%)
    def compute_kpis(shortest_distance, shortest_exposure, green_distance, green_exposure):
        exposure_diff_percentage = 100 * (green_exposure - shortest_exposure) / shortest_exposure
        distance_diff_percentage = 100 * (green_distance - shortest_distance) / shortest_distance
        print(f'{args.pollutant.upper()} exposure difference: {exposure_diff_percentage:+.2f}%')
        print(f'Distance difference: {distance_diff_percentage:+.2f}%')
        return exposure_diff_percentage, distance_diff_percentage

    print(f'Shortest route total distance: {shortest_distance:.2f} m')
    print(f'Shortest route total exposure: {shortest_exposure:.2f}')
    print(f'Green route (historical data) total distance: {historical_distance:.2f} m')
    print(f'Green route (historical data) total exposure: {historical_exposure:.2f}')
    historical_exposure_diff, historical_distance_diff = compute_kpis(
        shortest_distance, shortest_exposure, historical_distance, historical_exposure)

    if args.real_time is not None:
        print(f'Green route (historical + real-time data) total distance: {realtime_distance:.2f} m')
        print(f'Green route (historical + real-time data) total exposure: {realtime_exposure:.2f}')
        realtime_exposure_diff, realtime_distance_diff = compute_kpis(
            shortest_distance, shortest_exposure, realtime_distance, realtime_exposure)

    # create routes' traces to plot them later
    route_traces = []
    route_traces.append(route_trace(G, shortest_route, f'Shortest ({shortest_distance:.0f} m)', 'blue',
        group='routes', group_title='Routes'))
    route_traces.append(route_trace(G, historical_route, '{0} ({1:.0f} m, {2:+.0f}% {3})'.format(
        'Green' if args.real_time is None else 'Historical', historical_distance,
        historical_exposure_diff, pollutants[args.pollutant]), 'green', group='routes'))
    if args.real_time is not None:
        route_traces.append(route_trace(G, realtime_route,
            f'Historical + Real-Time ({realtime_distance:.0f} m, {realtime_exposure_diff:+.0f}% {pollutants[args.pollutant]})',
            '#90EE90', group='routes'))

    # add traces to the figure
    for trace in route_traces:
        fig.add_trace(trace)
    if args.real_time is not None:
        for trace in sensor_traces:
            fig.add_trace(trace)

    # show the map
    def auto_zoom(G, coordinate_list):
        X, Y = decompose_coordinates(G, coordinate_list)
        from shapely.geometry import MultiPoint
        multi_point = MultiPoint(list(zip(X, Y)))
        bounding_box = multi_point.bounds
        center_x = (bounding_box[0] + bounding_box[2]) / 2
        center_y = (bounding_box[1] + bounding_box[3]) / 2
        area = (bounding_box[2] - bounding_box[0]) * (bounding_box[3] - bounding_box[1])
        zoom = np.interp(
            x = area,
            xp = [0, 5**-10, 4**-10, 3**-10, 2**-10, 1**-10, 1**-5],
            fp = [20, 17, 16, 15, 14, 7, 5])
        return 0.95 * zoom, (center_x, center_y)
    zoom, center = auto_zoom(G, shortest_route + historical_route)
    fig.update_layout(
        mapbox_style = args.map_style,
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
        },
        #hovermode = False
    )
    fig.show()
