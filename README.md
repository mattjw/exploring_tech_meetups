## Data Colleciton

### Pipeline

1. `extract_geonames_top_cities.py`
	* Extract top cities (by population) from geonames data.
2. `geonames_top_cities.json -> geonames_top_cities_filtered.json`
	* 
3. `crawl_groups.py`
	* 


### Extracting geonames

Selcet cities according to region population. 

Some boroughs, or subsequent filtering.

No global consistent definition of city.

Alternative approaches are to hand-select city designations. E.g., US maintains list of 'principal cities', each with its own FIPS code. 


### Caveats


### Data Model

#### On disk
* `dat`
	* `city_meetup_groups`: One JSON file per country. Each file contains a mapping from Meetup City Ident (`US:NY:New York`) to list of Meetup Groups in that city.

#### Mongodb





## Dependencies and Acknowledgements

* meetup.com Python API Client. At: `https://github.com/meetup/python-api-client`.
* 
