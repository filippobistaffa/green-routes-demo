#!/bin/bash

pois="pois.txt"
jsons="jsons"
mkdir -p $jsons
i=1

while IFS= read -r origin; do
    j=1
    while IFS= read -r destination; do
        # Check if the two strings are different
        if [ "$i" -lt "$j" ]; then
            python3 green-route.py --origin "$origin" --destination "$destination" --export-json "$jsons/$i-$j.json" --map-style hide
        fi
        j=$(( j + 1 ))
    done < "$pois"
    i=$(( i + 1 ))
done < "$pois"
