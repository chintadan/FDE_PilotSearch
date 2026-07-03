"""
Author: Nikhil Chintada

ditto.py: Mesh-network and CRDT functionality for drones. Basic simulation of Ditto SDK. 
"""

from itertools import combinations
from copy import deepcopy

class Ditto:
    def __init__(self, link_range: int):
        self.link_range = link_range
        self.events = [] #Adding for observability

    def sync(self, peers, t):
        # Updated, based upon Grow-Only Union, adding t to track timing of sim
        for a, b in combinations(peers, 2):
            if a.drones_in_range(b, self.link_range):
                # snapshot both BEFORE mutating either -> symmetric merge
                a_snap = deepcopy(a.model)
                b_snap = deepcopy(b.model)
                a.receive(b_snap)
                b.receive(a_snap)
                self.events.append((t, "SYNC", a.id, b.id))