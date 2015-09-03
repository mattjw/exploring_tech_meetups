# -*- coding: utf-8 -*-
#
# Author:   Matt J Williams
#           http://www.mattjw.net
#           mattjw@mattjw.net
# Date:     2015
# License:  MIT License
#           http://opensource.org/licenses/MIT


"""
Support for crawling Meetup.
"""


__author__ = "Matt J Williams"
__author_email__ = "mattjw@mattjw.net"
__license__ = "MIT"
__copyright__ = "Copyright (c) 2015 Matt J Williams"


import json
import collections
from pprint import pprint
from spatial_units import espon_fua

import pymongo


CONFIG_FPATH = 'config.json'
MONGO_DBNAME = "meetupdotcom"
COLL_USERS = "users"
COLL_GROUPS = "groups"
COLL_ATTENDANCE = 'event_attendance'


def get_config():
    """
    Retrieve list of configuration options.
    """
    with open(CONFIG_FPATH) as f:
        config = json.load(f)
        return config


def mongo_connect():
    config = get_config()

    mclient = pymongo.mongo_client.MongoClient(config['mongo_host'], config['mongo_port'])
    #mclient[MONGO_DBNAME].authenticate(MONGO_USER, MONGO_PW)
    mdb = mclient[MONGO_DBNAME]
    return mdb


def get_attendee_ids(mdb, event_id):
    doc = mdb[COLL_ATTENDANCE].find_one({'_id': event_id})
    assert doc is not None
    attendee_ids = doc['attendee_ids']
    return attendee_ids


def get_city2groups(country_code):
    """
    Obtain meetup gruops for country `country_code`.
    Return dictionary that maps:
        city_ident -> list of meetup groups in city

    The city_ident is construted in a country-specific way.

    The list of attendees at each event will be inserted into each event. These
    are obtained via the `event_attendance` table and add as an attribute
    `attendee_ids` of the event.
    Member IDs will not be expanded. 
    """
    if country_code == 'GB':
        geolookup = espon_fua.GeoLookup.get_singleton()
        def f(group):
            lat = group['lat']
            lon = group['lon']
            fua_city_obj = geolookup.lookup(lon, lat)
            if fua_city_obj is None:
                return '<unknown>'
            else:
                return fua_city_obj
        ident_func = f
        #ident_func = lambda group: "%s:%s:%s" % (group['country'], '', group['city'])
    elif country_code == 'US':
        ident_func = lambda group: "%s:%s:%s" % (group['country'], group['country'], group['city'])
    elif country_code == 'IE':
        ident_func = lambda group: "%s:%s:%s" % (group['country'], '', group['city'])
        #~
    else:
        raise ValueError("unknown country %s" % (country_code))

    mdb = mongo_connect()
    city2groups = collections.defaultdict(lambda: [])

    groups_iter = mdb[COLL_GROUPS].find({'country' : country_code})
    for group in groups_iter:
        # expand events with attendee_ids
        for event in group['events_in_window']:
            eid = event['id']
            attendee_ids = get_attendee_ids(mdb, eid)
            event['attendee_ids'] = attendee_ids

        # store according to city
        ident = ident_func(group)
        city2groups[ident].append(group)

    return dict(city2groups)


def main():
    city2groups = get_city2groups('GB')
    for city, groups in city2groups.iteritems():
        if 'Cardiff' in city:
            for group in groups:
                if 'unified' in group['name']:
                    pprint(group)
                    exit()



if __name__ == "__main__":
    main()







