# -*- coding: utf-8 -*-
#
# Author:   Matt J Williams
#           http://www.mattjw.net
#           mattjw@mattjw.net
# Date:     2015
# License:  MIT License
#           http://opensource.org/licenses/MIT


import unicodecsv as csv
import json


__author__ = "Matt J Williams"
__author_email__ = "mattjw@mattjw.net"
__license__ = "MIT"
__copyright__ = "Copyright (c) 2015 Matt J Williams"


def load_geonames_cities(countries):
    """
    Return list of cities of the world. Via geonames dump.
    http://download.geonames.org/export/dump/

    Only cities in list of countries `countries` are retained.
    Returns dict of mappings from a country code in `countries` to list
    of cities. Assumes countries are lower-case alpha2 codes.
    """
    fpath = 'dat/geonames_cities/cities1000.txt'
    fields = 'geonameid,name,asciiname,alternatenames,latitude,longitude,feature_class,feature_code,country_code,cc2,admin1_code,admin2_code,admin3_code,admin4_code,population,elevation,dem,timezone,modification_date'.split(',')
    
    out = {code: [] for code in countries}

    with open(fpath) as fp:
        rdr = csv.DictReader(fp, fieldnames=fields, delimiter='\t', quoting=csv.QUOTE_NONE)
        for row in rdr:
            cc = row['country_code'].lower()
            if cc in countries:
                lat = float(row['latitude'])
                lon = float(row['longitude'])
                name = row['name']
                ad1 = row['admin1_code']
                pop = int(row['population'])
                
                out[cc].append({'city': name, 'state': ad1, 'population': pop,
                                'longitude': lon, 'latitude': lat})
    return out


def main():
    max_cities = 200

    countries2cities = load_geonames_cities(['us', 'gb', 'ie'])
    for country, cities in countries2cities.items():
        cities.sort(key=lambda city: -city['population'])
        cities = cities[:min([max_cities, len(cities)])]
        countries2cities[country] = cities

    with open('dat/geonames_top_cities.json', 'w') as f:
        json.dump(countries2cities, f)


if __name__ == "__main__":
    main()
