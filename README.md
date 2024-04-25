# Compute green routes that minimize the exposure to air pollutants (NO<sub>2</sub>, PM<sub>2.5</sub>, PM<sub>10</sub>)


    usage: green-route.py [-h] [--origin ORIGIN] [--destination DESTINATION]
                          [--historical HISTORICAL] [--real-time REAL_TIME]
                          [--sensor-radius SENSOR_RADIUS] [--mamp-epochs MAMP_EPOCHS]
                          [--pollutant {no2,pm25,pm10}]
                          [--map-style {open-street-map,carto-positron,carto-darkmatter}]
    
    options:
      -h, --help                     show this help message and exit
      --origin ORIGIN                address of origin point
      --destination DESTINATION      address of destination point
      --historical HISTORICAL        *.pkl file containing historical air quality data
      --real-time REAL_TIME          *.json file containing real-time air quality data
      --sensor-radius SENSOR_RADIUS  extend air quality value of each sensor to its
                                     neighbors (up to specified number of hops)
      --mamp-epochs MAMP_EPOCHS      number of epochs of the MAMP interpolation algorithm
      --pollutant {no2,pm25,pm10}    pollutant to consider for air quality data
      --map-style {open-street-map,carto-positron,carto-darkmatter}
