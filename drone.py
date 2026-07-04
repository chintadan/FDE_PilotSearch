"""
Author: Nikhil Chintada

drone.py: Basic drone class- contains a sensor to detect the pilot, a world_model to store and update its understanding of the world (pilot detections across grid)
"""

class Drone:
    def __init__(self, id: int, pos: tuple[int, int], sens: "Sensor", auto: "dataMule", model: "WorldModel"):
        self.id = id
        self.pos = pos
        self.sens = sens
        self.auto = auto
        self.model = model
        # Can expand by having an alive attribute in case the drone is downed, and a trail attribute for ant colony search

    def sense(self, pilot_loc):
        detection = self.sens.scan(self.pos, pilot_loc) # Call sensor scan() function
        self.model.observe(self.pos, detection, self.id) # Updating w/ self.id to handle sensor.py changes

    def move(self, t):
        self.model.update(self.id, self.pos, t) #Updated w/ t var to publish latest status before deciding next move
        self.pos = self.auto.next_move(self.pos, self.model, self.id) # Call autonomy next_move() function, added id for dataMule

    def drones_in_range(self, peer: "Drone", link_range: int): 
        # Take in another drone, see if within link_range, return boolean
        dx = abs(self.pos[0] - peer.pos[0])
        dy = abs(self.pos[1] - peer.pos[1])
        return max(dx, dy) <= link_range

    def receive(self, new_model):
        self.model.merge(new_model) # Call world_model merge function





    