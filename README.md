Author: Nikhil Chintada

Initial Commit focused on creating basics of simulation: 2D grid, 3 agents, search pattern and finding of downed pilot. Some set up of CRDT handling.

System Architecture:
- Main.py: Runs everything, calls other classes and functions. Contains the main loop that calls all other functions (and runs the    
simulator)
- Drone.py: Drone class, contains sensor, world model, comms.
- Autonomy.py: Code for search behavior (lawnmower to start). 
- Sensor.py: Handles the detection model for how a pilot is detected.
- Ditto.py: Handles the communication/CRDT behavior. “Ditto Simulator”
- World_Model.py: Handles each drone’s understanding of the world, updated through Ditto.py for network meshing and Drone.py for detections (from sensor.py). 

Approach:
1. Make a basic simulation with a 2D grid and 3 agents that explore the space, a hidden pilot, tick loop and terminal view of grid. 
2. Add CRDT + comms representative handling 
	1. Offline first storage, CRDT merge (Grow-Only Set), range-gated replication
	2. Partition/reconnection and data mule hand-off, explicit convergence success state and event logs. 
3. Document 
4. Extend original work 

