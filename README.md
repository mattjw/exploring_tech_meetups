An exploratory analysis of technology communities across the UK using data from [Meetup.com](http://www.meetup.com/).

Data is crawled from the Meetup API. See below for a description of the data collection process.

The results of the analysis can be found in the report in the `presentation` directory. A typeset version can be viewed [here](http://mattjw.github.io/exploring_tech_meetups/presentation/output/meetup.html). Data analysis was carried out in the IPython Notebook `analysis/meetup_analysis.ipynb`.


## Data Collection

Data collection scripts are located in `crawl`.

### Pipeline

The configuration file `config.json` should be structured as follows:

```
{
  "meetup_api_key": "<32-character meetup API key>",
  "mongo_port": <mongodb-port>,
  "mongo_host": "<mongodb-hostname>"
}
```

The data collection pipeline is as follows:

1. `extract_geonames_top_cities.py`: Extracts top cities (by population) from the Geonames gazetteer. The gazetteer is held in `dat/geonames_cities/`. `cities1000.txt` is obtained from the [Geonames export](http://download.geonames.org/export/dump/). The script outputs `geonames_top_cities.json` to `dat/`.
2. You may wish to edit `dat/geonames_top_cities.json` to remove some redundant cities in the Geonames data, depending on the chosen countries.
3. `crawl_groups.py`: Carries out a proximity crawl using the cities obtained from the gazetteer. Using the processed gazeteer (from previous step), retrieves meetup groups within proximity to each POI (i.e., cities). Outputs to `dat/groups_crawl/`. This is an initial, very broad, crawl of groups, that is to be filtered in subsequent steps.
4. `collect_city_groups.py`: Collects the groups from the proximity crawl, removing duplicates as necessary. Outputs to `dat/city_meetup_groups`.
5. `crawl_group_activity.py`: Using the sanitised and de-duplicated groups obtained from the previous steps, this script crawls a range of additional group attributes and stores the results (including the meetup groups) in a MongoDB datastore. The additional attributes include: group events, group membership, attendance at events, and any users encountered along the way. This crawl can take a while (around 5 hours for three years of UK tech groups). If the script is prematurely halted, it will re-start from where it left off.

The resulting MongoDB database, `meetupdotcom`, consists of the following collections:

* `users`: Each document is a Meetup member. Crawled from the `members` endpoint.
* `groups`: Each document is a Meetup group. Crawled from the `groups` endpoint, supplemented with list of the group's events crawled from the `events` endpoint.
* `event_attendance`: Each document describes member attendance at a particular meetup event. The document specifies an event id `event_id` and list of member ids (`attendee_ids`).

### Alternative API Client

As noted on the [Meetup developer page](http://www.meetup.com/meetup_api/clients/), the Python API is now quite out of date. A very simple alternative client, with rate limiting, is implemented in `crawl_tools.py` (see class `AltMeetup`).

## Dependencies and Attribution

* Meetup Python API Client. At: `https://github.com/meetup/python-api-client`.