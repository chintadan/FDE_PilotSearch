"""
Author: Nikhil Chintada

ditto.py: Mesh-network and CRDT functionality for drones. Basic simulation of Ditto SDK. 
"""

class Ditto:
    def __init__(self, link_range: int):
        self.link_range = link_range

    def sync(self, peers):
        return #Function to sync data between peers (Drones)