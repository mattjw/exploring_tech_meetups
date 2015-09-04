

## Data Colleciton

Data collection scripts are located in `crawl`.

### Pipeline

The configuration file, `config.json`, should be structured as follows:

```
{
  "meetup_api_key": "<32-bit meetup API key>",
  "mongo_port": <mongodb-port>,
  "mongo_host": "<mongodb-hostname>"
}
```

The data collection pipeline is as follows:

1. `extract_geonames_top_cities.py`: Extracts top cities (by population) from the Geonames gazetteer. The gazetteer is held in `dat/geonames_cities/`. `cities1000.txt` is obtained from the [Geonames export](http://download.geonames.org/export/dump/). The script outputs `geonames_top_cities.json` to `dat/`.
2. You may wish to edit `dat/geonames_top_cities.json` to remove some redundant cities in the Geonames data, depending on the chosen countries.
3. `crawl_groups.py`: Carries out a proximity crawl using the cities obtained from the gazetteer. Using the processed gazeteer (from previous step), retrieves meetup groups within proximity to each POI (i.e., cities). Outputs to `dat/groups_crawl/`. This is an initial, very broad, crawl of groups, that is to be filtered in subsequent steps.
4. `collect_city_groups.py`: Collects the groups from the proximity crawl, removing duplicates as necessary. Outputs to `dat/city_meetup_groups`.
5. `crawl_group_activity.py`: Using the sanitised and de-duplicated groups obtained from the previous steps, this script crawls a range of additional group attributes and stores the results (including the meetup groups) in a MongoDB datastore. The additional attributes include: group events, group membership, attendance at events, and any users encountered along the way. This crawl can take a while (10+ hours for the UK). If the script is prematurely halted, it will re-start from where it left off.

The resulting MongoDB database, `meetupdotcom`, consists of the following collections:

* `users`: Each document is a Meetup member. Crawled from the `members` endpoint.
* `groups`: Each document is a Meetup group. Crawled from the `groups` endpoint, supplemented with list of the group's events crawled from the `events` endpoint.
* `event_attendance`: Each document describes member attendance at a particular meetup event. The document specifies an event id `event_id` and list of member ids (`attendee_ids`).


### Extracting geonames

Select cities according to region population. 

Some boroughs, or subsequent filtering.

No global consistent definition of city.

Alternative approaches are to hand-select city designations. E.g., US maintains list of 'principal cities', each with its own FIPS code. 


### Caveats


## Analysis



## Dependencies and Acknowledgements

* meetup.com Python API Client. At: `https://github.com/meetup/python-api-client`.
* 
