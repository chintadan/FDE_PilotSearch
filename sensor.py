"""
Author: Nikhil Chintada

sensor.py: Basic representation of a sensor model that can detect the downed pilot. 
"""

class Sensor:
    def __init__(self, radius: int):
        self.radius = radius

    def scan(self, pos, pilot_loc):
        # Scans, compares distance to pilot location, if within the sensor radius the pilot is found
        dx = abs(pos[0] - pilot_loc[0])
        dy = abs(pos[1] - pilot_loc[1])
        if max(dx, dy) <= self.radius:
            return {"pos": pilot_loc, "confidence": 1.0} # For now, return that we have found the pilot
        return None