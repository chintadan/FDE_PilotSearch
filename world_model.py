"""
Author: Nikhil Chintada

world_model.py: Data class that holds each agent's model of the world, representing the cells searched and if the pilot is found.
"""

from dataclasses import dataclass, field

@dataclass
# Overhaul whole class, all primary methods to handle probablistic sensor changes
class WorldModel:
    searched: set = field(default_factory=set)      # Cells the drone has swept
    detections: dict = field(default_factory=dict)  # Cells where the drone had a detection
    pilot_found: tuple | None = None # Convergence pilot location
    peer_status: dict = field(default_factory=dict)

    CONFIRM_THRESHOLD = 0.85 # Combined confidence to confirm, adding to handle probablistic sensor

    def observe(self, cell, detection, obs_id):
        self.searched.add(cell) #Update WorldModel
        if detection is not None:
            self.record(detection["pos"], obs_id, detection["confidence"]) #Record the confidence value of detection at the specified cell
        self.reevaluate()
    
    def record(self, cell, obs_id, conf):
        #Will keep the highest confidence detection per cell (idempotent)
        obs = self.detections.setdefault(cell, {})
        if conf > obs.get(obs_id, 0.0):
            obs[obs_id] = conf

    # Adding to handle probablistic sensing
    def aggregate(self, obs):
        # Compares different observers confidences - AI-generated
        prod = 1.0
        for conf in obs.values():
            prod *= (1.0 - conf)
        return 1.0 - prod

    # Adding to handle probablistic sensing
    def reevaluate(self):
        best_cell, best_score = None, 0.0
        for cell, obs in self.detections.items():
            s = self.aggregate(obs)
            if s > best_score:
                best_cell, best_score = cell, s
        if best_score >= self.CONFIRM_THRESHOLD:
            self.pilot_found = best_cell

    def merge(self, peer: "WorldModel"):
        # searched cells: grow-only set union (monotonic, conflict-free)
        self.searched |= peer.searched

        # detections: keep highest confidence per cell
        for cell, dets in peer.detections.items():
            mine = self.detections.setdefault(cell, {})
            for o_id, conf in dets.items():
                if conf > mine.get(o_id, 0.0): # Get the max per cell, observer
                    mine[o_id] = conf

        # Fix: Was missing code in merge that handles the peer_status addition
        for p_id, info in peer.peer_status.items():
            cur = self.peer_status.get(p_id)
            if cur is None or info["t"] > cur["t"]:
                self.peer_status[p_id] = info

        self.reevaluate() # Added to handle probablistic sensing
    
    def update(self, drone_id, pos, t):
        # AI-generated, going to implement Gossip Protocol
        """A drone records its OWN latest status each tick (LWW by t)."""
        self.peer_status[drone_id] = {
            "pos": pos, "t": t,
            "has_fix": self.pilot_found is not None,
        }