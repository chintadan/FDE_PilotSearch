"""
Author: Nikhil Chintada

autonomy.py: Holds the logic for an agent's search execution. 
"""

# Class for lawnmower search pattern (divide grid into areas of resposibility, move up and then down columns until area completely searched)
class lawnMower:
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

    def next_move(self, pos, belief):
        if self.i >= len(self.waypoints):
            return pos # area fully covered; hold position

        target = self.waypoints[self.i]
        if pos == target:
            self.i += 1
            target = self.waypoints[min(self.i, len(self.waypoints) - 1)]

        return self.step(pos, target)

    def step(self, pos, target):
        """Move one cell toward target (4-connected: x first, then y)."""
        x, y = pos
        tx, ty = target
        if x != tx:
            x += 1 if tx > x else -1
        elif y != ty:
            y += 1 if ty > y else -1
        return (x, y)
