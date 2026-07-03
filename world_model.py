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
    peer_status: dict = field(default_factory=dict)

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

        # Fix: Was missing code in merge that handles the peer_status addition
        for p_id, info in peer.peer_status.items():
            cur = self.peer_status.get(p_id)
            if cur is None or info["t"] > cur["t"]:
                self.peer_status[p_id] = info
    
    def update(self, drone_id, pos, t):
        # AI-generated, going to implement Gossip Protocol
        """A drone records its OWN latest status each tick (LWW by t)."""
        self.peer_status[drone_id] = {
            "pos": pos, "t": t,
            "has_fix": self.pilot_found is not None,
        }