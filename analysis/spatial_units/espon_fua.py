# Matt J Williams, 2015
# http://mattjw.net
# mattjw@mattjw.net


"""
Annotate a list of geographic locations (as latitudes and longitudes) with
additional information about the geographic regions they belong to.

Inputs:
* GEOPOINTS:
    CSV file of geopoints.
    Each row represents a geographic location. The position is represented
    by longitude and latitude. Each row may also contain other information
    about the location. Thus, we have "locations" and their "input labels".
* REGION SHAPES:
    Region spatial data.
    The boundaries of a set of geographic regions. The GEOPOINTS exists within
    one of these spatial regions.
* REGION ATTRIBUTES:
    CSV file containing additional attributes for the regions described in
    REGION SHAPES.
    Each row should match to an ID of a region in REGION SHAPES.

Outputs:
Each GEOPOINT is annotated with attributes (REGION ATTRIBUTES) of the region it
belongs to (REGION SHAPES).
"""


import collections
import csv
import math
import argparse
import os
from pprint import pprint


from shapefile_tools import polygon_shaperecords
import pysal
from pysal.cg.locators import PolygonLocator
import pyproj


#
#
# Params
#

MODULE_DIR = os.path.split(os.path.abspath(__file__))[0]

# REGION ATTRIBUTES files
FPATH_REGION_ATTRIBS = os.path.join(MODULE_DIR, "fua/populations_2006_and_names.csv")
REGION_ATTRIBS_ID_COL = 0
    # the column in the REGION ATTRIBUTES file that contains the region identifier
    # cross-referenced with the region id in REGION SHAPES

# REGION SHAPES file
FPATH_REGION_SHAPES = os.path.join(MODULE_DIR, "fua/fua_geoms_wgs84")
REGION_SHAPE_ID_FIELDNAME = 'id_fua'
    # the fieldname of the shape attribute in the REGION SHAPES file
    # that has the shape identifier
    # cross referenced with the id in REGION ATTRIBTUES

FUA_ID_PREFIX = 'UK'


#
#
# Script
#

def load_regions(fpath_region_shapes, region_shape_id_fieldname):
    """
    Load the geographic regions (REGION SHAPES) from a suite of shapefiles with 
    file path prefix `fpath_region_shapes`. This also checks to ensure a field
    with name `region_shape_id_fieldname` exists in each shape dictionary.
    """
    regions = {}
    # maps a pysal polygon to the input shapedict,
    # inc. pyshp geometry and shapely geometry

    for indx, shape_dict in enumerate(polygon_shaperecords(fpath_region_shapes)):
        # 'geom_pyshp', 'geom_shapely', ...
        geom_shapely = shape_dict['geom_shapely']
        geom_pysal = pysal.cg.asShape(geom_shapely)

        if region_shape_id_fieldname not in shape_dict:
            raise ValueError("'%s' not in shape file %s" % (region_shape_id_fieldname, shape_dict.keys()))

        if not shape_dict[region_shape_id_fieldname].startswith(FUA_ID_PREFIX):
            # only retain FUA units that start with particular prefix (e.g., UK)
            continue
        #else:
        #    pprint(shape_dict)
        #    print shape_dict['geom_shapely']
        #    exit()

        regions[geom_pysal] = shape_dict
    return regions


def load_region_attributes(fpath_region_attribs, region_attribs_id_col):
    """
    Load attributes (REGION ATTRIBUTES) about each region from a CSV file. The 
    ID of the region is held in column `region_attribs_id_col`.
    """
    region_attribs = {}
    # maps a region ID to an ordered dictionary of attributes
    # regarding that reigon
    # the ID is also included in the ordered dictionary

    with open(fpath_region_attribs, 'rU') as fin:
        rdr = csv.reader(fin)
        fnames = rdr.next()
        ident_colname = fnames[region_attribs_id_col]
        for row in rdr:
            dct = collections.OrderedDict(zip(fnames, row))

            # retrieve the ID
            ident = dct[ident_colname]
            region_attribs[ident] = dct

    return region_attribs


def extract_geopoint_location(geopoint_row):
    """
    Extract location data from a geopoint row (a row in GEOPOINTS) and
    normalise its format (e.g., from lat-long) to the same format that is used
    by the region shape data (i.e., REGION SHAPES).

    For example, the region geometries might be provided in BNG (British
    National Grid) format, and the geopoints might be described as long lat.
    This function would extract the geopoint's long-lat pair and
    transform them to BNG for comparison with the region geometries.
    """
    wgs84 = pyproj.Proj(init='epsg:4326')  # wgs - geodetic coordinate system
    bng = pyproj.Proj(init='epsg:27700')  # UK LSOA are in BNG (british nat grid)

    lon = float(geopoint_row[geopoints_lon_col])
    lat = float(geopoint_row[geopoints_lat_col])

    bng_east, bng_north = pyproj.transform(wgs84, bng, lon, lat)
    loc = (bng_east, bng_north)
    return loc


def save_dict_seq(seq, fpath):
    """
    Save a sequence of dics `seq` to file at path `fpath` in CSV format.
    Header will be inferred from the dict keys. Creates any intermediate
    directories in `fpath`.
    """
    if not seq:
        raise ValueError("Cannot save empty sequence")

    head, tail = os.path.split(fpath)
    if head:
        os.mkdirs(head)

    with open(fpath, 'w') as f:
        fnames = seq[0].keys()
        wrtr = csv.DictWriter(f, fnames)
        wrtr.writeheader()
        wrtr.writerows(seq)


def loc_to_region_attribs(loc, regions, region_shape_id_fieldname,
                          region_locator, region_attribs):
    """
    Find the region for the point `loc` and return its region attributes.
    Returns a dictionary of region attributes.

    Params...
    loc:
        Location.
    regions:
        Dictionary that allows lookup of PySAL shape objects to their
        region shape information.
    region_shape_id_fieldname:
        The attribute in a region shape information dict that gives the shape's
        identifier.
    region_locator:
        Lookup PySAL polygon to region attributes.
    region_attribs:
        Dictionary lookup that maps region ID to region attributes.

    Returns None if no region found.
    Throws error if multiple polygon match.
    """
    match = None  # the polygon successfully matched to this region

    #
    # First try containment
    polys = region_locator.contains_point(loc)
        # list of geom_pysal polygons

    if len(polys) > 1:
        raise RuntimeError("multiple polygons for %s" % loc)

    if len(polys) == 1:
        match = polys[0]

    #
    # Check if poly-finding worked
    if match is None:
        return None

    #
    # Resolve the attributes for this polygon
    region_dct = regions[match]
    region_id = region_dct[region_shape_id_fieldname]
    attribs_dct = dict(region_attribs[region_id])
    attribs_dct.update(region_dct)  # append geometries
    return attribs_dct


class FUACity(object):
    def __init__(self, name, fua_id, pop, lon, lat):
        self.name = name
        self.fua_id = fua_id
        self.lon = lon
        self.lat = lat
        if pop != 'N/A':
            self.pop = float(pop)
        else:
            self.pop = None

    def __str__(self):
        return self.fua_id[:2] + '::' + self.name

    def __eq__(self, other):
        if not isinstance(other, FUACity):
            return False
        return self.fua_id == other.fua_id

    def __hash__(self):
        return hash(self.fua_id)


class GeoLookup(object):
    """
    Look up the region that a point belongs to. `lookup` returns a FUACity
    describing the containing region, or None if no match found.
    """

    def __init__(self):
        self.regions = load_regions(FPATH_REGION_SHAPES, REGION_SHAPE_ID_FIELDNAME)
        self.region_locator = PolygonLocator(self.regions.iterkeys())
        self.region_attribs = load_region_attributes(FPATH_REGION_ATTRIBS, REGION_ATTRIBS_ID_COL)

    def lookup(self, lon, lat):
        loc = (lon, lat)
        attribs_dct = loc_to_region_attribs(loc, self.regions, REGION_SHAPE_ID_FIELDNAME, self.region_locator, self.region_attribs)
        if attribs_dct is None:
            return None
        c_lon = attribs_dct['geom_shapely'].centroid.x
        c_lat = attribs_dct['geom_shapely'].centroid.y
        city = FUACity(attribs_dct['name'], attribs_dct['unit_code'], attribs_dct['pop_t'],
            lon=c_lon, lat=c_lat)
        return city

    __singleton = None
    @staticmethod
    def get_singleton():
        if GeoLookup.__singleton is None:
            GeoLookup.__singleton = GeoLookup()
        return GeoLookup.__singleton


def main():

    #
    # Processing
    """
    print "[Load REGION SHAPES]"
    regions = load_regions(FPATH_REGION_SHAPES, REGION_SHAPE_ID_FIELDNAME)
    region_locator = PolygonLocator(regions.iterkeys())

    print "[Load REGION ATTRIBUTES]"
    region_attribs = load_region_attributes(FPATH_REGION_ATTRIBS, REGION_ATTRIBS_ID_COL)
    """

    geolookup = GeoLookup.get_singleton()
    print "loaded"

    geolookup = GeoLookup.get_singleton()
    geolookup = GeoLookup.get_singleton()


    lon = -3.142090
    lat = 51.473471
    print "find Cardiff:", lon, lat
    city_obj = geolookup.lookup(lon, lat)
    print city_obj
    print 'lon', city_obj.lon, 'lat', city_obj.lat

    lon = -1.503754
    lat = 52.403964
    print "find Brum:", lon, lat
    city_obj = geolookup.lookup(lon, lat)
    print city_obj

    lon = 0
    lat = 90
    print "find North Pole:", lon, lat
    city_obj = geolookup.lookup(lon, lat)
    print city_obj

if __name__ == "__main__":
    main()