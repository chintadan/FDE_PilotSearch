"""
Author: Nikhil Chintada

world_model.py: Data class that holds each agent's model of the world, representing the cells searched and if the pilot is found.
"""

from dataclasses import dataclass, field

@dataclass
class WorldModel:
    searched: set = field(default_factory=set)      # Cells the drone has swept
    detections: dict = field(default_factory=dict)  # Cells where the drone had a detection
    pilot_found: tuple | None = None # Convergence pilot location

    def observe(self, cell, detection):
        self.searched.add(cell) #Update WorldModel
        if detection is not None:
            self.record(cell, detection) #Record the confidence value of detection at the specified cell
    
    def record(self, cell, detection):
        #Will keep the highest confidence detection per cell.
        prevDet = self.detections.get(cell) #Get previous value
        if prevDet is None or detection["confidence"] >= prevDet["confidence"]:
            self.detections[cell] = detection #update if detection is higher confidence
        if self.pilot_found is None:
            self.pilot_found = detection["pos"]

    def merge(self, peer: "WorldModel"):
        # searched cells: grow-only set union (monotonic, conflict-free)
        self.searched |= peer.searched

        # detections: keep highest confidence per cell
        for cell, det in peer.detections.items():
            self.record(cell, det)

        # confirmed pilot: first non-None wins
        if self.pilot_found is None and peer.pilot_found is not None:
            self.pilot_found = peer.pilot_found