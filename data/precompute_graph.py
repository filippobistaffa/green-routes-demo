import argparse as ap
import networkx as nx
import pandas as pd
import osmnx as ox
import pickle

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


if __name__ == '__main__':

    parser = ap.ArgumentParser()
    parser.add_argument('--aqi', type=str, default='2022.csv')
    parser.add_argument('--place', type=str, default='Barcelona, Spain')
    parser.add_argument('--output', type=str, default='2022_graph_aqi.pkl')
    args, additional = parser.parse_known_args()

    # obtain map from OpenStreetMap
    ox.settings.use_cache = True
    ox.settings.log_console = True
    G = ox.graph_from_place(args.place, network_type='walk')

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

    # read and process air quality data
    ox.settings.log_console = False
    aqi = pd.read_csv(args.aqi)

    with test_progress as progress:
        task = progress.add_task('Processing map...', total=len(aqi))
        for _, row in aqi.iterrows():
            point = row[['LATITUDE', 'LONGITUDE']].values
            u, v, k = ox.nearest_edges(G, point[1], point[0])
            for aqi in ['NO2', 'PM25', 'PM10']:
                G[u][v][k][aqi] = row[[aqi]].values[0]
            progress.console.print(G.get_edge_data(u, v))
            progress.update(task, advance=1)

    # write output
    with open(args.output, 'wb') as f:
        pickle.dump(G, f, pickle.HIGHEST_PROTOCOL)
