"""
Verify consistency of data exported to mongo by the `crawl_group_activity.py`
script.
"""


from pprint import pprint
import json
from collections import OrderedDict
import os
from datetime import datetime

import pymongo

import crawl_tools


MONGO_DBNAME = "meetupdotcom"
COLL_USERS = "users"
COLL_GROUPS = "groups"


#
# From mongo

def has_user(mdb, user_id):
    ret = mdb[COLL_USERS].find_one({'_id': user_id})
    return ret is not None


def has_group(mdb, group_id):
    ret = mdb[COLL_GROUPS].find_one({'_id': group_id})
    return ret is not None


def mongo_connect():
    config = crawl_tools.get_config()

    mclient = pymongo.mongo_client.MongoClient(config['mongo_host'], config['mongo_port'])
    #mclient[MONGO_DBNAME].authenticate(MONGO_USER, MONGO_PW)
    mdb = mclient[MONGO_DBNAME]
    return mdb


#
# Main script
def main():

    mdb = mongo_connect()

    for group in mdb[COLL_GROUPS].find():
        events = group['events_in_window']
        member_ids = group['member_ids']

        attendee_ids = frozenset(sum([event['attendee_ids'] for event in events], []))

        num_events = len(events)

        # ensure all attendees crawled
        for event in events:
            for uid in event['attendee_ids']:
                assert has_user(mdb, uid)

        # ensure all members crawled
        for uid in member_ids:
            assert has_user(mdb, uid)

        print "%-40s  |  %5d members  |  %5d events  |  %5d members attended" % (
            group['name'], len(member_ids), len(events), len(attendee_ids))

        users = [mdb[COLL_USERS].find_one({'_id': uid})for uid in attendee_ids]
        print "\t", ', '.join([user['name'] for user in users])
        

if __name__ == "__main__":
    main()




