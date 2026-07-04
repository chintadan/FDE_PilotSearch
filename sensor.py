"""
Author: Nikhil Chintada

sensor.py: Basic representation of a sensor model that can detect the downed pilot. 
"""
import random # Implementing probablistic detection

class Sensor:
    def __init__(self, radius, p_detect, p_false, rng):
        self.radius = radius
        # Adding for probabilistic detection
        self.p_detect = p_detect # Base true-positive probability at distance 0
        self.p_false = p_false # False-positive probablity scan when empty
        self.rng = rng or random.Random()

    def scan(self, pos, pilot_loc):
        # Scans, compares distance to pilot location, if within the sensor radius the pilot is found
        dx = abs(pos[0] - pilot_loc[0])
        dy = abs(pos[1] - pilot_loc[1])
        dist = max(dx, dy)
        if dist <= self.radius:
            # True detection: Probablity decreases with distance
            p = self.p_detect * (1.0 - dist / (self.radius + 1))
            if self.rng.random() < p:
                return {"pos": pilot_loc, "confidence": round(p, 3)} # Generate confidence
            return None
        else:
            # False positive @ current location
            if self.rng.random() < self.p_false:
                return {"pos": pos, "confidence": round(self.p_false, 3)}
            return None