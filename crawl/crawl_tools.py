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


import re
import json
import requests
import urlparse
import urllib

import ratelim

from meetup import Meetup


CONFIG_FPATH = 'config.json'
RATELIM_DUR = 60 * 60   # window = 1 hour
RATELIM_QUERIES = 1000  # window = meetup allows roughly 1080 per hour


def get_config():
    """
    Retrieve list of configuration options.
    """
    with open(CONFIG_FPATH) as f:
        config = json.load(f)
        return config


def get_meetup_api():
    """
    Retrieve the Meetup API object.
    """
    api_key = get_config()['meetup_api_key']
    api = Meetup(api_key)
    return api


def get_alt_meetup_api():
    """
    Retrieve the alternative (custom) implementation of the Meetup API.
    Some parts of the official API are deprecated.
    """
    api_key = get_config()['meetup_api_key']
    api = AltMeetup(api_key)
    return api

DEFAULT_PAGINATION_COUNT = 200  # 200 is API default if page is missing

class AltMeetup(object):
    def __init__(self, api_key):
        self._api_key = api_key
        self._base_url = 'https://api.meetup.com/2'

    @ratelim.patient(RATELIM_QUERIES, RATELIM_DUR)
    def query_gateway(self, url):
        """
        Run query with complete url `url`. The main gateway to Meetup API.

        Returns:
        JSON. Typical Meetup response is 'meta' and 'results'.
        In addition, this function adds a 'rate' sub-dictionary.

        rate.limit:              Absolute max number requests per window.
        rate.limit_remaining:    Remaining requests in current window.
        rate.reset:              Time (secs) until window is reset.

        More info at: http://www.meetup.com/meetup_api/#limits
        """
        try:
            response = requests.get(url=url)
            if response.status_code != 200:
                raise StandardError()
        except StandardError as ex:
            print response.url
            print response.json()
            raise ex

        out = response.json()
        out['rate'] = {}
        out['rate']['limit'] = response.headers['X-RateLimit-Limit']
        out['rate']['limit_remaining'] = response.headers['X-RateLimit-Remaining']
        out['rate']['reset'] = response.headers['X-RateLimit-Reset']

        if int(out['rate']['limit_remaining']) == 0:
            print "warning: reached rate limit", out['rate']
        return out

    def query_get(self, path, params):
        """
        Issue GET query to meetup API. Automatically adds API key.

        path: URL path. Not including leading slash.
        get_parmas: dict of GET parameters.
        """
        d = dict(params)
        if 'sig' not in d:
            d['key'] = self._api_key
        if 'format' not in d:
            d['format'] = 'json'
        if 'page' not in d:
            d['page'] = DEFAULT_PAGINATION_COUNT


        url = self._base_url + '/' + path + "?" + urllib.urlencode(d)
        out = self.query_gateway(url)
        return out

    def query_get_all_results(self, path, params):
        """
        Obtain all results from an API query. Follows 'meta.next', concatenating
        multiple HTTP responses as needed.

        Returns: sequence of results.
        """
        results = []

        resp = self.query_get(path, params)
        while True:
            # Extend results
            results.extend(resp['results'])

            # Prepare for next iteration
            next_url = resp['meta']['next']

            #print "num results:", len(resp['results']), next_url, path, params#~

            if next_url == "":
                break
            resp = self.query_gateway(next_url)
        return results

    def cities(self, **kwargs):
        params = kwargs
        ret = self.query_get('cities', params)
        return ret

    def groups(self, **kwargs):
        """Returns list of results (groups)."""
        params = kwargs
        ret = self.query_get_all_results('groups', params)
        return ret

    def members(self, **kwargs):
        """Returns list of results (members)."""
        params = kwargs
        ret = self.query_get_all_results('members', params)
        return ret

    def events(self, **kwargs):
        """Return list of results (events)."""
        params = kwargs
        ret = self.query_get_all_results('events', params)
        return ret

    def rsvps(self, **kwargs):
        """Return list of results (rsvps)."""
        params = kwargs
        ret = self.query_get_all_results('rsvps', params)
        return ret


