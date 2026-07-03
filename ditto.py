"""
Author: Nikhil Chintada

ditto.py: Mesh-network and CRDT functionality for drones. Basic simulation of Ditto SDK. 
"""

class Ditto:
    def __init__(self, link_range: int):
        self.link_range = link_range
        self.events = [] #Adding for observability

    def sync(self, peers, t):
        #AI Generated, based upon Grow-Only Union, adding t to track timing of sim
        for a, b in combinations(drones, 2):
            if a.in_range_of(b, self.comms_range):
                # snapshot both BEFORE mutating either -> symmetric merge
                a_snap = deepcopy(a.belief)
                b_snap = deepcopy(b.belief)
                a.receive(b_snap)
                b.receive(a_snap)
                self.events.append((t, "SYNC", a.id, b.id))