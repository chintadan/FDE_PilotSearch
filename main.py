"""
Author: Nikhil Chintada

main.py: Simulation controller, calls other classes and functions, creates grid, logs data. 
"""

import random, sys

from drone import Drone
from sensor import Sensor
from ditto import Ditto
from autonomy import lawnMower
from world_model import WorldModel

# Configuration of variables for sim
g_width : int = 24 #Configuration of Grid World 
g_height : int = 24 #Configuration of Grid World 
n_drones : int = 3 #Number of drones, 3 initially
sense_radius : int = 2
comms_range : int = 6
max_ticks : int = 3000
seed : int = 42 #Eventually randomize
render_every : int = 12 #Control terminal ouput 
pilot_loc: tuple[int, int] #Fill in later

def drone_init():
    drones, lane_width = [], g_width//n_drones #Populate drones in grid according to width/number of drones
    for i in range(n_drones):
        x0 = i * lane_width
        if i == n_drones - 1:
            x1 = g_width - 1 #Handle last drone
        else:
            x1 = (i + 1) * lane_width #Normal case
        drones.append(Drone(
            id= str(i),
            pos=(x0, x1), 
            sens=Sensor(radius=sense_radius), 
            auto=lawnMower(area=(x0,x1), height=g_height),
            model=WorldModel()
        ))
    return drones

def render(pilot_loc, drones, t):
    # Renders grid world
    world = [["." for _ in range(g_width)] for _ in range(g_height)] # Empty world
    # Add pilot location
    world[pilot_loc[1]][pilot_loc[0]] = "P"
    for d in drones:
        for(x, y) in d.model.searched:
            # if not (0 <= x < g_width and 0 <= y < g_height):
            #     print(f"OUT OF BOUNDS cell from drone {d.id}: (x={x}, y={y}) "
            #           f"grid is width={g_width} height={g_height}")
            #     continue
            world[y][x] = "*" #y is vertical -> row, x is horizontal -> col
    for d in drones:
        x, y = d.pos
        world[y][x] = d.id
        # print(d.id, d.auto.waypoints[0], d.auto.waypoints[-1])
        # ys = [y for (x, y) in d.auto.waypoints]
        # print(d.id, "y range:", min(ys), "to", max(ys), "count:", len(d.auto.waypoints))
    print(f"\n--- tick {t} ---")
    print("\n".join("".join(row) for row in world))

def success(drones):
    # End state
    # Initially, check if any drone has spotted the pilot in their world_model, return bool
    for d in drones:
        if d.model.pilot_found is not None:
            return True
    return False

def log_events(drones, t, seen):
    for d in drones:
        if d.model.pilot_found is not None and d.id not in seen:
            seen.add(d.id)
            print(f"[t={t}] DETECTION: drone {d.id} confirmed pilot at "
                  f"{d.model.pilot_found}")

if __name__ == "__main__":
    rng = random.Random(seed) #Randomize seed
    pilot_loc = (rng.randrange(g_width), rng.randrange(g_height)) #Hide pilot randomly
    drones = drone_init()
    ditto = Ditto(link_range = comms_range)
    seen = set() # Track if the pilot is seen and where

    print(f"Initialization: Pilot hidden at {pilot_loc}")

    for t in range(max_ticks):
        for d in drones: # Every drone must check for pilot
            d.sense(pilot_loc) #Pass in pilot location for sensor class
        ditto.sync(drones) # If in range, sync with other drones
        for d in drones: # Drones move to next point in search pattern
            d.move()

        if t % render_every == 0:   # Do not output every tick
            render(pilot_loc, drones, t)
        log_events(drones, t, seen)

        if success(drones):             
            render(pilot_loc, drones, t)
            print(f"\nSUCCESS at tick {t}: pilot found.")
            sys.exit(0)

    print("\nEnded without success (max_ticks reached).")


