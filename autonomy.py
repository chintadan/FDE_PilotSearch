"""
Author: Nikhil Chintada

autonomy.py: Holds the logic for an agent's search execution. 
"""

# Update to lawnMower to dataMule, lawnMower pattern by default, but will let other drones know if pilot confirmed.
# Class for lawnmower search pattern (divide grid into areas of resposibility, move up and then down columns until area completely searched)
class dataMule:
    INVESTIGATE_LOW = 0.65 # Threshold for investigation state

    def __init__(self, area: tuple[int, int], height: int):
        self.x0, self.x1 = area # [x0, x1) columns for this drone
        self.height = height #height of grid
        self.waypoints = self.traversal()
        self.i = 0 # Iterator to keep track of where in path we are

    def traversal(self):
        # Serpentine coverage of the area: up one column, down the next.
        path = []
        going_up = True
        for x in range(self.x0, self.x1):
            ys = range(self.height) if going_up else range(self.height - 1, -1, -1) # Ascend or descend
            for y in ys:
                path.append((x, y))
            going_up = not going_up # Reset boolean
        return path

    def lawnMower_step(self, pos):
        # Updated name, this implements lawnMower pattern
        if self.sweep_complete():
            return pos
        target = self.waypoints[self.i]
        if pos == target:
            self.i += 1
            target = self.waypoints[min(self.i, len(self.waypoints) - 1)]

        return self.step(pos, target)

    # Adding method for dataMule class - AI assisted
    def next_move(self, pos, model, d_id):
        # Data Mule behavior
        # Still looking for pilot
        if model.pilot_found is not None:
            # Found the target, act as data mule
            target = self.nearest_uninformed(pos, model, d_id)
            if target is not None:
                #print(f"drone {id} MULING toward uninformed peer at {target}")
                return self.step(pos, target)
            # All known peers are informed, converge on location
            return self.step(pos, model.pilot_found)
        # Investigate state
        cell, score = model.best_candidate()
        confirm = getattr(model, "CONFIRM_THRESHOLD", 0.9)
        if cell is not None and self.INVESTIGATE_LOW <= score < confirm:
            return self.step(pos, cell) # Move toward candidate to corroborate readings
        # Default behavior
        return self.lawnMower_step(pos)


    def step(self, pos, target):
        # Move one cell toward target (4-connected: x first, then y).
        x, y = pos
        tx, ty = target
        if x != tx:
            x += 1 if tx > x else -1
        elif y != ty:
            y += 1 if ty > y else -1
        return (x, y)
    
    def sweep_complete(self):
        # Check if sweep of area is complete, useful for checking in with other drones
        return self.i >= len(self.waypoints)

    def nearest_uninformed(self, pos, model, d_id):
        #AI-generated, adding to create dataMule functionality
        #debug block for AI assist
        # print("d_id:", repr(d_id), "type:", type(d_id))
        # for k in model.peer_status:
        #     print("  key:", repr(k), "type:", type(k),
        #         "match:", k == d_id,
        #         "has_fix:", model.peer_status[k]["has_fix"])
        best, best_d = None, None
        for p_id, info in model.peer_status.items():
            if p_id == d_id or info["has_fix"]:
                continue
            d = max(abs(pos[0] - info["pos"][0]), abs(pos[1] - info["pos"][1]))
            if best_d is None or d < best_d:
                best, best_d = info["pos"], d
        return best