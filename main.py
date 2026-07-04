"""
Author: Nikhil Chintada

main.py: Simulation controller, calls other classes and functions, creates grid, logs data. 
"""

import random, sys

from drone import Drone
from sensor import Sensor
from ditto import Ditto
from autonomy import dataMule
from world_model import WorldModel
from viz import Visualizer

# Configuration of variables for sim
g_width : int = 300 #Configuration of Grid World 
g_height : int = 300 #Configuration of Grid World 
n_drones : int = 3 #Number of drones, 3 initially
sense_radius : int = 80
comms_range : int = 90
max_ticks : int = 3000
seed : int = 11 #Stable Position
#seed : int = 19 #Stable Position, rec. thresh for 300x300 is .7
#seed = None # Randomize 
#render_every : int = 12 #Control terminal ouput - not needed after viz 
pilot_loc: tuple[int, int] #Fill in later
# Adding to handle sensor.py changes (probablistic sensing)
p_detect: float = 0.9 # Tune if needed
p_false: float = 0.03 # Tune if needed

def drone_init(rng):
    drones, lane_width = [], g_width//n_drones #Populate drones in grid according to width/number of drones
    starts = {} #Adding to implement dataMule
    for i in range(n_drones):
        x0 = i * lane_width
        if i == n_drones - 1:
            x1 = g_width - 1 #Handle last drone
        else:
            x1 = (i + 1) * lane_width #Normal case
        starts[i] = (x0, 0) #Adding to implement dataMule
        drones.append(Drone(
            id= i, #Changed to int instead of str
            pos=(x0, 0), # Fix: replaced x1 w/ 0
            sens=Sensor(radius=sense_radius, p_detect=p_detect, p_false=p_false, rng=rng), # Updated for sensor.py
            auto=dataMule(area=(x0,x1), height=g_height),
            model=WorldModel()
        ))
    # Adding to handle dataMule
    for d in drones:
        for p_id, p in starts.items():
            d.model.peer_status[p_id] = {"pos": p, "t": 0, "has_fix": False} # Seed starting positions, no agent will know pilot @ t=0
    return drones

def render(pilot_loc, drones, t):
    # Renders grid world
    world = [["." for _ in range(g_width)] for _ in range(g_height)] # Empty world
    # Add pilot location
    world[pilot_loc[1]][pilot_loc[0]] = "P"
    for d in drones:
        for(x, y) in d.model.searched:
            world[y][x] = "*" #y is vertical -> row, x is horizontal -> col
    for d in drones:
        x, y = d.pos
        world[y][x] = str(d.id) # Convert to string for grid
    print(f"\n--- tick {t} ---")
    print("\n".join("".join(row) for row in world))

# Update success to check for sensor radius
def success(drones, sensor_radius):
    # End state
    # Success depends on every drone converging upon the downed pilot
    confirmations = {d.model.pilot_found for d in drones}
    if len(confirmations) != 1 or None in confirmations:
        return False
    pilot = next(iter(confirmations)) # Get agreed location
    for d in drones:
        if max(abs(d.pos[0] - pilot[0]), 
               abs(d.pos[1] - pilot[1])) > sensor_radius:
            return False
    return True # Only returns true if every drone is within sensor radius of pilot
    # return len(confirmations) == 1 and None not in confirmations #All drones have found pilot
    # Initial logic was incorrect because data type is set, which removes duplicates

def log_events(drones, t, seen):
    for d in drones:
        if d.model.pilot_found is not None and d.id not in seen:
            seen.add(d.id)
            print(f"[t={t}] DETECTION: drone {d.id} confirmed pilot at "
                  f"{d.model.pilot_found}")

# Adding to print at end of run
def print_sync_summary(ditto):
    print(f"\nTotal sync events: {len(ditto.events)}")
    for (t, kind, a, b) in ditto.events:
        print(f"  [t={t}] {kind} {a}<->{b}")


if __name__ == "__main__":
    rng = random.Random(seed) #Randomize seed
    pilot_loc = (rng.randrange(g_width), rng.randrange(g_height)) #Hide pilot randomly
    drones = drone_init(rng)
    ditto = Ditto(link_range = comms_range)
    seen = set() # Track if the pilot is seen and where
    # Toggle live to True for window (recommended for new configs/random seeds), False for log output only (terminal)
    viz = Visualizer(g_width, g_height, drones, comms_range, live=False, save_gif=True, fps=15) # Adding visualizer update

    print(f"Initialization: Pilot hidden at {pilot_loc}")

    for t in range(max_ticks):
        for d in drones: # Every drone must check for pilot
            d.sense(pilot_loc) #Pass in pilot location for sensor class
        ditto.sync(drones, t) # If in range, sync with other drones, updated with time var
        for d in drones: # Drones move to next point in search pattern
            d.move(t) #Updated move with time

        # if t % render_every == 0:   # Do not output every tick
        #     render(pilot_loc, drones, t)
        log_events(drones, t, seen)
        # Adding visualizer class update
        if t % 5 == 0: viz.update(g_width, g_height, pilot_loc, drones, t)

        if success(drones, sense_radius):             
            # render(pilot_loc, drones, t)
            viz.update(g_width, g_height, pilot_loc, drones, t) # Adding visualizer update
            print(f"\nSUCCESS at tick {t}: pilot found.")
            # print_sync_summary(ditto) # Can turn on if interested
            viz.finish() # Updated from viz.py, needed here too
            sys.exit(0)
    viz.update(g_width, g_height, pilot_loc, drones, t) 
    viz.finish() # Updated from viz.py
    print("\nEnded without success (max_ticks reached).")


