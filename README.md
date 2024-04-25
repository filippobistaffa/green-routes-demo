Compute green routes that minimize the exposure to air pollutants (NO<sub>2</sub>, PM<sub>2.5</sub>, PM<sub>10</sub>)
===================
This repository contains a prototype application recommending green routes for pedestrians that minimize the exposure to air pollutants, comparing the total distance and the total exposure with the shortest route computed in the classical way. This prototype implements some of the techniques presented by Sergio Calo, Filippo Bistaffa, Anders Jonsson, Vicenç Gómez, and Mar Viana in “[Spatial Air Quality Prediction in Urban Areas via Message Passing](https://www.sciencedirect.com/science/article/pii/S095219762400349X/pdfft?md5=7400987ed4288d5f46285fb2725d3efc&pid=1-s2.0-S095219762400349X-main.pdf)”, Engineering Applications of Artificial Intelligence (EAAI), DOI: [`10.1016/j.engappai.2024.108191`](https://doi.org/10.1016/j.engappai.2024.108191).

Data
----------
This prototype employs both real historical data from the [Open Data BCN portal](https://opendata-ajuntament.barcelona.cat/data/ca/dataset/mapes-immissio-qualitat-aire) (see [`data`](data) folder) and [real-time data from air quality sensors in Barcelona](https://ajuntament.barcelona.cat/qualitataire/es). Real-time data can be fetched with the [`fetch_real_time_data.py`](data/fetch_real_time_data.py) script.

Dependencies
----------
Although not mandatory, running the project in a Python *virtual environment* is recommended:

    python3 -m venv demo
    source demo/bin/activate

Required dependencies can then be installed via `pip` with the following command:

    pip install --upgrade -r requirements.txt


Usage
----------

    usage: green-route.py [-h] [--origin ORIGIN] [--destination DESTINATION]
                          [--pollutant {no2,pm25,pm10}] [--historical HISTORICAL]
                          [--real-time REAL_TIME] [--sensor-radius SENSOR_RADIUS]
                          [--mamp-epochs MAMP_EPOCHS]
                          [--map-style {open-street-map,carto-positron,carto-darkmatter}]
    
    options:
      -h, --help                     show this help message and exit
      --origin ORIGIN                address of origin point
      --destination DESTINATION      address of destination point
      --pollutant {no2,pm25,pm10}    pollutant to consider for air quality data
      --historical HISTORICAL        *.pkl file containing historical air quality data
      --real-time REAL_TIME          *.json file containing real-time air quality data
      --sensor-radius SENSOR_RADIUS  extend air quality value of each sensor to its
                                     neighbors (up to specified number of hops)
      --mamp-epochs MAMP_EPOCHS      number of epochs of the MAMP interpolation algorithm
      --map-style {open-street-map,carto-positron,carto-darkmatter}
