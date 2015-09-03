# Matt J Williams, 2015
# http://mattjw.net
# mattjw@mattjw.net


"""
Tools for loading and processing data in the shapefile format.

Depends on two libraries:
* shapefile: see pyshp on pypi.
* shapely: see shapely on pypi.
"""


from collections import OrderedDict

import shapefile
import shapely.geometry


def polygon_shaperecords(shape_base_fname):
        """
        A generator for (multi-)polygon shapes from a suite of shapefile data,
        associated with their shape records.

        Parameters...
        `shape_base_fname`: Path prefix for the shapefiles.

        Output...
        This returns a generator. The generator yields dictionaries. Each
        dictionary corresponds to a shape, which includes the shape's
        geometry (assumed to be a polygon or multiplygon) (stored in the .shp
        file), plus the shape's attributes from the shape record (held in the 
        .dbf file).
        A dictionary contains the following two fields for geometry...
            'geom_pyshp'    the geometry directly from pyshp
            'geom_shapely'  a shapely MultiPolygon, which has been
                            obtained by converting from the pyshp 
                            representation.
        ..plus the fields of the shaperecord.
        """
        sf = shapefile.Reader(shape_base_fname)
        fields = sf.fields[1:]

        gIter = sf.iterShapes()
        rIter = sf.iterRecords()

        while True:
            try:
                shp = gIter.next()
                rec = rIter.next()

                dct = OrderedDict()  # for combined data

                #
                # pyshp geometry
                dct['geom_pyshp'] = shp

                #
                # convert to shapely object
                if not shp.shapeType == 5:
                    # 5 => shapefile's "Polygon" type, which may have multiple 'parts':
                    #     fields = MBR, Number of parts, Number of points, Parts, Points
                    # i.e., a shapefil Polygon may actually include multiple polygons
                    # shp.parts: this is a list of indexes, indicating the start of
                    # a new shape
                    raise ValueError("Expected shape type 5 (polygon) but found %s" % shp.shapeType)

                num_parts = len(shp.parts)  
                    # shp.parts gives the indxexes into the flat list of 
                    # shp.points. these indicate the array slices which 
                    # correspond to polygons
                num_points = len(shp.points)
                polys = []
                for i in xrange(num_parts):
                    start_indx = shp.parts[i]
                    if (i+1) < num_parts:
                        end_indx = shp.parts[i+1]
                    else:
                        end_indx = num_points
                    poly_pts = shp.points[start_indx:end_indx]
                    poly = shapely.geometry.Polygon(poly_pts)
                    polys.append(poly)
                mpoly = shapely.geometry.MultiPolygon(polygons=polys)  # assume no holes in poly
                
                assert sum(len(poly.exterior.coords) for poly in polys) == num_points  # check the points for individual polys sums to total points

                dct['geom_shapely'] = mpoly

                #
                # Finally, the records...
                for indx, fieldtup in enumerate(fields):
                    field = fieldtup[0]
                    dct[field] = rec[indx]

                yield dct
            except StopIteration:
                break

