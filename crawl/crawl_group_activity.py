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
from collections import OrderedDict, defaultdict
import os
from datetime import datetime

import pymongo

import crawl_tools


MONGO_DBNAME = "meetupdotcom"
COLL_USERS = "users"
COLL_GROUPS = "groups"
COLL_ATTENDANCE = 'event_attendance'

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


def expand_meetup_group(alt_api, mdb, group, events_from, events_to):
    """
    Expand the group JSON with list of members, events.
    Any users encountered in this process will be added to the mongo database.

    RSVPs (attendance) will be handled later.

    Members:
    IDs of members stored in:
        group['member_ids'].

    Events:
    JSON for each event (in period events_from to events_to) stored in:
        group['events_in_window']
    This will not include attendees (see: event_attendance collection).

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
    group['events_in_window'] = events


#
# Crawling event attendance

def has_event_attendees(mdb, event_id):
    """
    Returns True if we already have a list of attendees for the event
    `event_id`.
    """
    ret = mdb[COLL_ATTENDANCE].find_one({'_id': event_id})
    return ret is not None


def add_event_attendees(mdb, event_attendees):
    """
    Add event attendance info to mongodb, if not already added.
    event_attendees:
        A dict of form {event_id:..., attendee_ids: [...]}
    """
    event_id = event_attendees['event_id']

    if not has_event_attendees(mdb, event_id):
        out = OrderedDict(event_attendees)
        out['_id'] = event_id

        assert 'attendee_ids' in event_attendees

        _id = mdb[COLL_ATTENDANCE].insert_one(out)


def crawl_event_attendance(alt_api, mdb):
    """
    Collect and store the attendance (RSVP) information for each event in 
    `events`.

    The COLL_ATTENDANCE will store documents of the form:
        event_id -> {_id, attendees:[list of user IDs]}

    If an event attendee has not been seen before, we additionally collect
    their data and store it in the user collection.

    Note: event IDs are alphanumeric.
    """
    #
    # Obtain to do list...
    all_event_ids = []
    for group in mdb[COLL_GROUPS].find():
        if group['country'] != 'GB':
            print group['name'], "    --    discarding non-GB [%s]" % group['country'] #~
            continue

        for event in group['events_in_window']:
            all_event_ids.append(event['id'])

    seen_event_ids = [attendance_doc['event_id'] for attendance_doc in mdb[COLL_ATTENDANCE].find()]

    unseen_event_ids = frozenset(all_event_ids) - frozenset(seen_event_ids)
    unseen_event_ids = list(unseen_event_ids)

    #
    # Now crawl attendance info for each event in `unseen_event_ids`
    # We'll progress in chunks of 50 events
    while len(unseen_event_ids) > 0:
        # fill buffer
        next_ids = []
        while len(next_ids) < 50 and len(unseen_event_ids) > 0:
            next_ids.append(unseen_event_ids.pop())

        print "checking %s events | %s events remaining" % (len(next_ids), len(unseen_event_ids))
        #print "querying", next_ids #~

        # retrieve attendance info
        event2attendees = defaultdict(lambda: set())
        for eid in next_ids:
            # we'll preemptively force in the (empty) list of attendees here,
            # because some times there are events with no attendees
            event2attendees[eid] = set()

        event_ids_str = ','.join(next_ids)
        results = alt_api.rsvps(event_id=event_ids_str, rsvp='yes')
        for result in results:
            if result['rsvp_id'] == -1:
                # host who has not RSVP'd
                print "no RSVP"
                continue

            event_id = result['event']['id']
            user_id = result['member']['member_id']

            if not has_user(mdb, user_id):
                crawl_add_user(alt_api, mdb, user_id)

            event2attendees[event_id].add(user_id)

        # save attendance info
        for event_id, attendee_ids in event2attendees.iteritems():
            attendee_ids = list(attendee_ids)
            out = {'event_id': event_id, 'attendee_ids': attendee_ids}

            #print "saved attendance doc", out
            add_event_attendees(mdb, out)


def main():
    #
    #
    # Prep
    #

    # Params
    events_from = datetime(2012, 6, 1)
    events_to = datetime(2015, 6, 1)

    # Load
    api = crawl_tools.get_meetup_api()
    alt_api = crawl_tools.get_alt_meetup_api()

    countries2citygroups = load_countries()

    mdb = mongo_connect()

    print "from", events_from
    print "to", events_to

    #
    #
    # Crawl -- expand groups, obtain members
    #
    print "\nSTAGE 1: Expand groups"
    for country, city2groups in countries2citygroups.iteritems():
        print country
        for city_ident, groups in city2groups.iteritems():
            #if 'Swansea' not in city_ident:
            #    continue

            print country, "\t", city_ident

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

    print "\nSTAGE 2: Crawl attendance for each event"
    crawl_event_attendance(alt_api, mdb)

if __name__ == "__main__":
    main()




