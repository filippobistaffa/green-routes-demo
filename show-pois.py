import plotly.graph_objects as go
import argparse as ap
import osmnx as ox
import numpy as np
import webcolors

def point_trace(point, name='Point', color='black', label=None):
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
        showlegend = False
    )

if __name__ == "__main__":

    parser = ap.ArgumentParser()
    parser.add_argument('--pois', type=str, default='pois.txt')
    parser.add_argument('--map-style', type=str, choices=['open-street-map', 'carto-positron', 'carto-darkmatter'],
        default='open-street-map')
    args, additional = parser.parse_known_args()
    
    with open(args.pois, 'r') as f:
        pois = [line.strip() for line in f.readlines()]

    points = [ox.geocode(poi) for poi in pois]
    fig = go.Figure()
    for i, (point, poi) in enumerate(zip(points, pois)):
        fig.add_trace(point_trace(point, poi, label=str(i+1), color='#265793'))
    def auto_zoom(points):
        from shapely.geometry import MultiPoint
        multi_point = MultiPoint([[lon, lat] for lat, lon in points])
        bounding_box = multi_point.bounds
        center_x = (bounding_box[0] + bounding_box[2]) / 2
        center_y = (bounding_box[1] + bounding_box[3]) / 2
        area = (bounding_box[2] - bounding_box[0]) * (bounding_box[3] - bounding_box[1])
        zoom = np.interp(
            x = area,
            xp = [0, 5**-10, 4**-10, 3**-10, 2**-10, 1**-10, 1**-5],
            fp = [20, 17, 16, 15, 14, 7, 5])
        return 0.9 * zoom, (center_x, center_y)
    zoom, center = auto_zoom(points)
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
    )
    fig.show()
