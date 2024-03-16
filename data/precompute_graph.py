from sklearn.neighbors import BallTree
import argparse as ap
import networkx as nx
import pandas as pd
import osmnx as ox
import numpy as np
import pickle
import os


from typing import Optional
from rich.console import Console
from rich.table import Column
from rich.text import Text
from rich.progress import (
    BarColumn,
    Progress,
    TextColumn,
    ProgressColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)

class MofNCompleteColumn(ProgressColumn):
    """Renders completed count/total, e.g. '  10/1000'.
    Best for bounded tasks with int quantities.
    Space pads the completed count so that progress length does not change as task progresses
    past powers of 10.
    Args:
        separator (str, optional): Text to separate completed and total values. Defaults to "/".
    """

    def __init__(self, separator: str = "/", table_column: Optional[Column] = None):
        self.separator = separator
        super().__init__(table_column=table_column)

    def render(self, task: "Task") -> Text:
        """Show completed/total."""
        completed = int(task.completed)
        total = int(task.total) if task.total is not None else "?"
        total_width = len(str(total))
        return Text(
            f"{completed:{total_width}d}{self.separator}{total}",
            style="progress.download",
        )

# Define custom progress bar
test_progress = Progress(
    TextColumn('[progress.percentage]{task.percentage:>3.0f}%'),
    BarColumn(),
    MofNCompleteColumn(),
    TextColumn('•'),
    TimeElapsedColumn(),
    TextColumn('•'),
    TimeRemainingColumn(),
)


if __name__ == '__main__':

    parser = ap.ArgumentParser()
    parser.add_argument('--place', type=str, default='Barcelona, Spain')
    parser.add_argument('--aqi', type=str, default=os.path.join(os.path.dirname(os.path.realpath(__file__)), '2022_locations_aqi.csv'))
    parser.add_argument('--output', type=str, default=os.path.join(os.path.dirname(os.path.realpath(__file__)), '2022_graph_aqi.pkl'))
    args, additional = parser.parse_known_args()

    # read air quality dataset
    aqi = pd.read_csv(args.aqi)

    # construct a ball tree to efficiently find closest points later
    aqi_nodes_rad = np.deg2rad(aqi[['LATITUDE', 'LONGITUDE']]) # haversine requires lat, lon coordinates in radians
    aqi_ball_tree = BallTree(aqi_nodes_rad, metric='haversine')

    # obtain map from OpenStreetMap
    ox.settings.use_cache = True
    ox.settings.log_console = True
    G = ox.graph_from_place(args.place, network_type='walk')

    with test_progress as progress:
        task = progress.add_task('Processing map...', total=len(G.edges))
        progress.console.print('Storing air quality indices on the edges of the graph')
        # for each edge in the graph...
        for u, v, k in G.edges:
            # find the closest point in air quality index dataset to the middle of the current edge
            middle_latlon = (G.nodes[u]['y'] + G.nodes[v]['y']) / 2, (G.nodes[u]['x'] + G.nodes[v]['x']) / 2
            middle_latlon_rad = np.deg2rad(middle_latlon)
            dist, idx = aqi_ball_tree.query(middle_latlon_rad.reshape(1, -1), k=1)
            closest = aqi.iloc[idx[:, 0]]
            # store air quality indices of closest point on the current edge
            for pollutant in ['NO2', 'PM25', 'PM10']:
                G[u][v][k][pollutant] = closest[[pollutant]].values[0].item()
            #progress.console.print(G.get_edge_data(u, v))
            progress.update(task, advance=1)

    # write output
    with open(args.output, 'wb') as f:
        print(f'Writing {args.output}')
        pickle.dump(G, f, pickle.HIGHEST_PROTOCOL)
