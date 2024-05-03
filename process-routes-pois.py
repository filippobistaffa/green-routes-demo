import argparse as ap
import pandas as pd
import numpy as np
import json
import os

if __name__ == "__main__":

    parser = ap.ArgumentParser()
    parser.add_argument('--jsons', type=str, default='jsons')
    parser.add_argument('--csv', type=str, default='table.csv')
    args, additional = parser.parse_known_args()

    exposures = []
    distances = []

    for file in os.listdir(args.jsons):
        if file.endswith(".json"):
            filename = os.path.join(args.jsons, file)
            with open(filename) as f:
                data = json.load(f)
                shortest_exposure = data['shortest']['exposure']
                shortest_distance = data['shortest']['distance']
                green_exposure = data['historical']['exposure']
                green_distance = data['historical']['distance']
                exposures.append(100 * (green_exposure - shortest_exposure) / shortest_exposure)
                distances.append(100 * (green_distance - shortest_distance) / shortest_distance)

    df = pd.DataFrame(data=np.array([exposures, distances]).T, columns=['exposure', 'distance'])
    df.to_csv(args.csv, index=False)
