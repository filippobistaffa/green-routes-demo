import argparse as ap
import datetime
import requests
import json


def get_data(url):
    custom_user_agent = "Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) AppleWebKit/604.1.38 (KHTML, like Gecko) Version/11.0 Mobile/15A372 Safari/604.1"
    return requests.get(url=url, headers={"User-Agent": custom_user_agent}).text


if __name__ == '__main__':

    parser = ap.ArgumentParser()
    parser.add_argument('--url', type=str, default='https://dadesmesuresestacions.dtibcn.cat/qualitataire/services/getStations.php')
    parser.add_argument('--output', type=str, default=f'{datetime.datetime.now()}'.replace(" ", "-").split('.')[0] + '.json')
    args, additional = parser.parse_known_args()

    # fetch real-time data
    sensors_data = json.loads(get_data(args.url))

    # dump it as a JSON file
    with open(args.output, 'w') as f:
        json.dump(sensors_data, f, indent=2)
