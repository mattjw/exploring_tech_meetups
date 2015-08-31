"""
Crawl activity for a previously obtained dataset of groups.
Persistent storage via mongodb.

users document:
Full member information on each user identified when constructing group
documents.

groups document:
Same as group crawled via group endpoint, but with additional history of events,
event members (IDs), and attendees.
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
# Misc
def datetime_to_epoch_ms(dt):
    epoch = datetime.utcfromtimestamp(0)
    delta = dt - epoch
    secs = delta.total_seconds()
    ms = secs * 1000
    return ms

def is_int(v):
    return isinstance(v, (int, long))

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


def add_group(mdb, group):
    gid = group['id']
    assert is_int(gid)
    if not has_group(mdb, gid):
        out = OrderedDict(group)
        out['_id'] = gid
        _id = mdb[COLL_GROUPS].insert_one(out)

        #print "inserted new group:", gid #~


def add_user(mdb, user):
    """
    Add user to mongodb, if not already crawled.
    `user`: The JSON response for a given user, from
        http://www.meetup.com/meetup_api/docs/2/members/
    """
    uid = user['id']
    assert is_int(uid)
    if not has_user(mdb, uid):
        out = OrderedDict(user)
        out['_id'] = uid
        _id = mdb[COLL_USERS].insert_one(out)

        #print "inserted new user:", uid #~


def crawl_add_user(alt_api, mdb, user_id):
    """
    If user_id is not in mdb, obtain their data (from Meetup API) and add
    it.

    If user has deleted their account, insert dummy user with same ID.
    """
    if has_user(mdb, user_id):
        # no need to crawl
        return

    results = alt_api.members(member_id=user_id)  # ideally, a list of one

    if len(results) == 0:
        # user not found
        user = {'id': user_id, 'info': 'user no longer exists'}
        print "[warning | user %s not found]" % [user_id]
    elif len(results) == 1:
        user = results[0]
    else:
        raise StandardError("Too many users returned")

    add_user(mdb, user)

    print "crawled and inserted user:", user_id


#
# From disk

def load_countries():
    """
    Load meetup data for each country.
    """
    fdir = './dat/city_meetup_groups'
    country2citygroups = {}
    for fname in os.listdir(fdir):
        if not fname.endswith('json'):
            continue
        fpath = os.path.join(fdir, fname)
        country = fname.split('.')[0]
        with open(fpath) as f:
            country2citygroups[country] = json.load(f)
    return country2citygroups


#
# Crawling

def get_group_members(alt_api, group_id):
    """
    Get list of all members for groupid.
    
    Attributes for each member as returned by /members/:
        http://www.meetup.com/meetup_api/docs/2/members/
    """
    members = alt_api.members(group_id=group_id)
    return members


def get_events(alt_api, group_id, dt_frm, dt_to, status='past'):
    """
    Retrieve all events for group `group_id` between dates `from` and `to`.

    `dt_frm`, `dt_to`: Datetime objects.
    `status`: past, upcoming, proposed, cancelled, draft

    Atrributes for each event as returned by:
        http://www.meetup.com/meetup_api/docs/2/events/
    """
    time = "%d,%d" % (datetime_to_epoch_ms(dt_frm), datetime_to_epoch_ms(dt_to))
    events = alt_api.events(group_id=group_id, status=status, time=time)
    return events


def expand_event(alt_api, mdb, event):
    """
    Expand the event with additional information

    Add list of attendees to the event. These will be stored in:
        event['attendee_ids'].

    Any members encountered in this process will be added to the mongo database.

    `event`: Event JSON.
    """
    eid = event['id']

    # obtain member IDs
    attendees = alt_api.rsvps(event_id=eid, rsvp='yes')

    ids = []
    for attendee in attendees:
        if attendee['rsvp_id'] == -1:
            # host who has not RSVP'd
            continue
        ids.append(attendee['member']['member_id'])

    # crawl if necessary
    for uid in ids:
        crawl_add_user(alt_api, mdb, uid)

    # insert IDs in to event object
    event['attendee_ids'] = ids


def expand_meetup_group(alt_api, mdb, group, events_from, events_to):
    """
    Expand the group JSON with list of members, events, and RSVPs.
    Any users encountered in this process will be added to the mongo database.

    Members:
    IDs of members stored in:
        group['member_ids'].

    Events:
    JSON for each event (in period events_from to events_to) stored in:
        group['events_in_window']
    Each event is also expanded with an 'attendee_ids' field, giving list of
    user IDs..

    `group`: Group JSON.
    """
    #
    # group members
    gid = group['id']
    assert is_int(gid)

    members = get_group_members(alt_api, gid)
    
    for user in members:
        add_user(mdb, user)

    if len(members) != group['members']:
        print "[warning | missed some members", len(members), group['members'], group['name'], "]"
    group['member_ids'] = [user['id'] for user in members]

    #
    # events
    events = get_events(alt_api, gid, events_from, events_to)
    for event in events:
        expand_event(alt_api, mdb, event)

    group['events_in_window'] = events



def main():
    #
    #
    # Prep
    #

    # Params
    events_from = datetime(2013, 1, 1)
    events_to = datetime(2015, 1, 1)

    # Load
    api = crawl_tools.get_meetup_api()
    alt_api = crawl_tools.get_alt_meetup_api()

    countries2citygroups = load_countries()

    mdb = mongo_connect()

    #
    #
    # Crawl
    #
    for country, city2groups in countries2citygroups.iteritems():
        print country
        for city_ident, groups in city2groups.iteritems():
            print country, "\t", city_ident

            #if 'Cardiff' not in city_ident:
            #    continue #~

            # full supplementary crawl of each group
            for group in groups:
                gid = group['id']
                if has_group(mdb, gid):
                    # do not re-crawl
                    print "\t", group['name'], "<SKIPPING>" #~
                    continue
                print "\t", group['name'], "<CRAWLING>" #~

                expand_meetup_group(alt_api, mdb, group, events_from, events_to)
                add_group(mdb, group)


if __name__ == "__main__":
    main()




