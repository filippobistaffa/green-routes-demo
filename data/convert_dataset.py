import argparse as ap
import geopandas as gpd
import pandas as pd
import pyproj


if __name__ == "__main__":

    parser = ap.ArgumentParser()
    parser.add_argument('--no2', type=str, default='2022_tramer_no2_mapa_qualitat_aire_bcn.gpkg')
    parser.add_argument('--pm25', type=str, default='2022_tramer_pm2-5_mapa_qualitat_aire_bcn.gpkg')
    parser.add_argument('--pm10', type=str, default='2022_tramer_pm10_mapa_qualitat_aire_bcn.gpkg')
    parser.add_argument('--map', type=str, default='BCN_GrafVial_Trams_ETRS89_CSV.csv')
    parser.add_argument('--output', type=str, default='2022.csv')
    args, additional = parser.parse_known_args()

    # air quality data (only contains the road IDs, e.g., "T00001B")
    no2 = gpd.read_file(args.no2)
    pm25 = gpd.read_file(args.pm25)
    pm10 = gpd.read_file(args.pm10)

    # map road IDs to actual coordinates
    df = pd.read_csv(args.map, encoding="latin-1", index_col=0, sep=';')
    df = pd.merge(df[['COORD_X','COORD_Y','C_Tram']], no2[['TRAM', 'Rang']], left_on='C_Tram', right_on='TRAM').drop(columns=['C_Tram']).rename(columns={'Rang': 'NO2'})
    df = pd.merge(df, pm25[['TRAM', 'Rang']]).rename(columns={'Rang': 'PM25'})
    df = pd.merge(df, pm10[['TRAM', 'Rang']]).rename(columns={'Rang': 'PM10'})

    # define UTM zone and projection
    utm_zone = 31
    utm_band = 'T'
    utm_proj = pyproj.Proj(proj='utm', zone=utm_zone, ellps='WGS84', south=False)

    # function to convert UTM coordinates to latitude and longitude
    def utm_to_latlon(row):
        lon, lat = utm_proj(row['COORD_X'], row['COORD_Y'], inverse=True)
        return pd.Series({'LATITUDE': lat, 'LONGITUDE': lon})

    df[['LATITUDE', 'LONGITUDE']] = df.apply(utm_to_latlon, axis=1)
    df.to_csv(args.output, index=False)
