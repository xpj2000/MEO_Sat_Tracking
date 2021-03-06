"""Classes for lists of coordinates.

Includes differential calculations, from the TRTL method.
"""

import math
from geodesy import distance_lat_lon

class UnchangedPointError(Exception):
    """Consecutive GPS points are too similar."""
    pass

class BearingList:
    """Object that stores bearing calculated from GPS position."""

    def __init__(self, bearing):
        """Constructor."""
        self.bearings = [bearing]

    def add_bearing(self, bearing):
        """Insert a bearing at the beginning of the list."""
        self.bearings.insert(0, bearing)

        if len(self.bearings) > 10:
            self.bearings.pop()

    def get_bearing(self):
        """Return the first bearing in the list."""
        return self.bearings[0]

    # This stuff is for drift (maybe, we'll see how it goes)
    def delta_bearing(self):
        """Find the change in the most recent bearings."""
        return self.bearings[0] - self.bearings[1]

    def lock(self):
        """Add the same bearing to the list."""
        self.add_bearing(self.bearings[0])

    def adjust_bearing(self, delta):
        """Add delta to a bearing."""
        self.add_bearing((self.bearings[0] + delta) % 360)


class CoordsList:
    """Object with a list of the 10 most recent lat/lon values in degrees."""

    def __init__(self, lat, lon):
        """Constructor."""
        self.lats = [lat, lat]
        self.longs = [lon, lon]

    def add_coords(self, lat, lon):
        """Add new coords to beginning of list and.

        If there are more than 10 coords, discard the oldest set.
        """
        self.lats.insert(0, lat)
        self.longs.insert(0, lon)

        if len(self.lats) >= 10:
            self.lats.pop()
            self.longs.pop()

    def get_current_bearing(self):
        """Return most recent calculated bearing based on GPS coordinates.

        In degrees East of North.
        """
        # Find length of one degree of latitude and longitude based on average
        # of two most recent latitudes
        # lat_len, lon_len = nmea.len_lat_lon((self.lats[0] + self.lats[1]) / 2)

        # x = (self.longs[0] - self.longs[1]) * lon_len
        # y = (self.lats[0] - self.lats[1]) * lat_len

        if self.longs[0] == self.longs[1] or self.lats[0] == self.lats[1]:
            raise UnchangedPointError("There is not enough difference between points.")
        else:
            x_coord = (self.longs[0] - self.longs[1])
            y_coord = (self.lats[0] - self.lats[1])

            # Bearing in degrees East of North
            bearing = 90 - math.degrees(math.atan2(y_coord, x_coord))

            return bearing % 360

    def lock(self):
        """Add the same coords to the list."""
        self.add_coords(self.lats[0], self.longs[0])

    def get_dist_travelled(self):
        """Return distance between two most recent points."""
        return distance_lat_lon(self.lats[1], self.longs[1], self.lats[0], self.longs[0])


def drift_check(coords, calc_bearings, dof_bearings, threshold):
    """Check if the vessel is currently drifting.

    Check if the difference between the change in calculated bearing and the
    change in compass bearing are greater than an arbitrary threshold.
    """
    delta_diff = abs((coords.get_current_bearing() - calc_bearings.b[0]) -
                     dof_bearings.delta_bearing())

    return delta_diff > threshold


def rotate_check(bearings, threshold):
    """Check if the vessel is currently rotating."""
    return abs(bearings.delta_bearing()) > threshold
