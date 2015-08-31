"""
Obtain groups near pre-selected locations.
"""

from pprint import pprint
import json
from collections import OrderedDict


import crawl_tools


def load_extracted_geonames_top_cities():
    """
    Load geonames cities from pre-processed file. We assume that the cities
    for each country are ordered by population.
    """
    fpath = 'dat/geonames_top_cities_filtered.json'
    with open(fpath) as f:
        countries2cities = json.load(f)
        return countries2cities


def retrieve_groups_near(alt_api, lon, lat, radius=25, category_id=34):
    """
    Retrieve meetup cities near lon, lat.

    API reference:
    http://www.meetup.com/meetup_api/docs/2/groups/
    """
    resp = alt_api.groups(category_id=category_id, lat=lat, lon=lon, radius=radius)
    return resp
    #meta = resp['meta']
    #results = resp['results']
    #return results


def main():
    #
    #
    # Prep
    #

    # Params
    cat_id = 34
    radius = 25.0

    # Load
    api = crawl_tools.get_meetup_api()
    alt_api = crawl_tools.get_alt_meetup_api()

    countries2cities = load_extracted_geonames_top_cities()

    del countries2cities['ie']
    del countries2cities['gb']

    #
    #
    # Crawl
    #
    for country, top_cities in countries2cities.iteritems():
        print "crawling:", country

        out = []

        for geonames_city in top_cities:
            lon = float(geonames_city['longitude'])
            lat = float(geonames_city['latitude'])

            results = retrieve_groups_near(alt_api, lon=lon, lat=lat)

            print "\t%-20s  %d" % (geonames_city['city'], len(results)), len(frozenset(map(str, results)))

            d = {'geonames_city' : geonames_city, 'results': results}
            out.append(d)

        # Save this city
        fpath_out = './dat/groups_crawl/%s.json' % (country)
        with open(fpath_out, 'w') as f:
            json.dump(out, f)


if __name__ == "__main__":
    main()
