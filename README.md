# FDE_PilotSearch
Author: Nikhil Chintada

**FDE_PilotSearch** is a prototype implementation to demonstrate autonomous system operation in a contested environment (network partitions) that utilizes **Grow-Only CRDT** (state-based) via a **Gossip Protocol** in emulation of the Ditto SDK. Agents traverse the search area, acting as **Data Mules** and converging once a downed pilot has been spotted to coordinate rescue. 
### Demo
[Demo GIF](https://github.com/chintadan/FDE_PilotSearch/blob/master/run_final.gif)
## Table of Contents
1. [[#Usage]]
2. [[#Features]]
	1. [[#Autonomous Agents]]
	2. [[#Sync Strategy and Conflict Resolution]]
	3. [[#Visualization & Logging]]
	4. [[#Assumptions & Trade-Offs]]
	5. [[#Scaling & Limitations]]
3. [[#Development Notes]]
	1. [[#AI Usage]]
	2. [[#Roadmap & Production]]
## Usage
```
# Bash
# Clone
git clone https://github.com/chintadan/FDE_PilotSearch.git
cd FDE_PilotSearch
# Install for live view window and gif generation
pip install matplotlib 
pip install PyQt5
pip install imageio
# Run
python main.py
```
The simulation is configurable via main.py. Change the grid size, number of drones, sensor radius, pilot location seed, probabilistic sensing, confidence thresholds (change within world_model.py, autonomy.py and viz.py) and live view/gif generation. 
## Features
The implementation of FDE_PilotSearch was focused on efficiency and simple demonstrations of core objectives. The simulation is 2D and runs on a tick loop which provides time synchronization. 
### Autonomous Agents
- Autonomous agents are modeled as drones (UAS) flying over a grid. All drones contain a sensor, world model (offline-first copy of search area and detections), and sync data via simulated Ditto capability. 
	- Agents utilize a lawnmower sweep, dividing the region equally, moving up y-axis first. 
	- Sensors use probabilistic detection, p_detect sets base true-positive probability at a distance of 0, p_false sets false-positive probability when scanning an empty cell.
	- Detection confidence for a cell must cross INVESTIGATE_LOW threshold (e.g. 0.75) for an agent to enter INVESTIGATE state. 
	- A drone must achieve CONFIRM_THRESHOLD (e.g. 0.9) to begin data mule behavior.
	- Once a drone has located the pilot, it acts as a data mule, moving to the last known location of its nearest peer (start locations seeded for all agents, but will update if link established). 
	- Once all peers have been informed, drones converge on known pilot location, end state success depends on all drones being physically in sensing range of pilot. 
### Sync Strategy and Conflict Resolution
- Ditto SDK functionality was simulated for this prototype (ditto.py). Ditto runs "onboard" drones via main.py where the list of drones (and tick value) is passed. Ditto checks each tick whether any agent is in range of their peers. If any two drones are in range, Ditto will implement the CRDT behavior by sending each agent's current state across the link (using drone.py's receive function), thereby abstracting the data and coordination layer.
- The CRDT type implemented for this prototype is a state-based Grow-Only Counter (G-Counter). A G-Counter was used because the drones only care about the highest confidence detection to help locate the pilot as quickly as possible. Therefore, merge conflicts can be resolved by simply taking the max of the two values (commutative, prevents any latest detection discrepancies and allows for idempotent behavior). 
	- CRDT functionality is primarily implemented through the WorldModel class, which is the dataclass that stores each agent's detection map. This class handles the CRDT logic primarily, through the merge function. It also handles the challenges of probabilistic confidence values by flagging pilot_found to a cell that crosses the CONFIRM_THRESHOLD flag.
	- To allow for data mule behavior, merge functionality (in world_model.py) was enhanced to implement Gossip Protocol. It does this by keeping a list of peer statuses and checking during a merge whether the peer has a more recent update for it. If it does, the peer_status structure (dict) is updated and used as the agent reevaluates its own world_model. In effect this creates multi-hop behavior for data propagation. 
- Connectivity and partitions were modeled simply by range-gating the agents. The variable comms_range defines the distance within which ditto.py knows to send states between agents. 
### Visualization & Logging
- 2D Simulated Live-View of Search, Communication & Convergence (MatPlotLib)
	- Pilot (Location unknown to drones) represented as an empty X, fills in red when one drone has confirmed pilot location.
	- Detection confidence aggregate is shown in pilot cell (0.0 - 1.0, e.g. 0.65), updates as readings accumulate. 
	- Green circle appears around pilot once CONFIRM_THRESHOLD is crossed (i.e. drone has confirmed the pilot location).
	- Drones are shown initially as colored circles w/ ID number in center. Once a drone has found the pilot its shape changes to a star.
	- Comms links are drawn as green lines.
	- Visited cells are shown in gray (originally white).
	- Cell detections shown with color range (on right of window), indicating false positives (purple).  
	- Sensor radius (around pilot) shown with red dotted lines to clearly demonstrate end state of all drones in sensor range during convergence. 
	- X-axis, Y-axis labels, CONFIRM_THRESHOLD value, pilot found status, detection confidence all marked on 2D visualizer. 
- Logging of syncs (Up/Down links) and pilot detection per drone, as well as success state (all drones have found and converged on pilot within time window)
- Basic grid modeling (can be toggled in main.py via render function): Outputs and displays grid world in terminal, shows drones as number IDs and pilot as P. Visited cells are represented with asterisks while unvisited cells are represented with a period. 
### Assumptions & Trade-Offs
I chose python as my implementation language for speed of prototyping and AI agent collaboration (less focus on syntax, compiling, etc.). This forced some limitations early, mainly no Ditto SDK implementation. I ultimately accepted this as a trade-off to enhance my understanding of CRDTs and prevent any scope creep from utilizing an SDK I have not worked with before for a short assignment. 

Due to the recommended duration of the assignment I kept the scope for autonomous agents as small as I could to start, implementing a basic lawnmower pattern, having a sensor that (initially) immediately detected the pilot if it is was within the set sensor_radius. I pretty quickly added G-Counter functionality by then expanding the base ditto.py and world_model.py files (as well as light modifications to drone.py). Once I had core functionality: drones searched, data propagating via mesh, I realized a limitation of the lawnmower pattern for this challenge. To demonstrate async behavior in a multi-agent search that equally partitions the search area, link ranges must be less than the corresponding distance between agents. This change necessitates data mule behavior.

Once the core capability was demonstrated (with data mules) I decided to revisit the sensor behavior, making it probabilistic. Doing this involved a revision of world_model, sensor and minor updates to the rest of the architecture. A major trade-off I discovered here while testing was that sensing confirmation now took much longer (if it happened at all, playing around with threshold values became necessary for different grid sizes/agent numbers). 

To increase the probability of detection I decided to make one more update: an investigate mode for each agent. This investigate mode sends a drone towards a target cell with a higher confidence value than a set INVESTIGATE_LOW threshold. This assumes monotonic behavior to work effectively.

My initial decisions to keep the implementation as simple as possible (python, terminal based grid, lawnmower behavior, sensor clarity) helped provide a foundation that could be rapidly implemented and iterated on. However, it necessitated that I make additions later on to truly prove out core objective capabilities (probabilistic sensing, data mule behavior, convergence). 

Final core assumptions:
- No drones will be downed.
- No obstacles or navigation impediments (trajectory planning, wind, terrain changes, current, etc.). 
- Flight deconfliction is unnecessary. 
- No state decay- i.e. agents do not ever lower the confidence assigned to a cell. 
- Bandwidth when connected is not throttled, decayed or limited. 
### Scaling & Limitations
FDE_PilotSearch scales easily to multiple agents and different world sizes due to the 2D simulation and world model. However, it is at its core a **simplified representation** and so does not demonstrate complex autonomy or mutli-agent behaviors, nor would it be directly usable for a ROS2/ArduPilot and/or Ditto SDK implementation. Furthermore, if a drone were to be destroyed during the search, key behaviors would likely breakdown as implemented. In addition, as noted above, the lawnmower pattern behavior in conjunction with the probabilistic sensor could (if untuned) lead to simulation runs in which no drones detect the pilot, or drones do not propagate information and/or converge in time (detecting only near the end of the simulation). Though I added in code that handles corroboration between drones (for sensor detections), the lawnmower pattern prevents this strategy from being demonstrated effectively. Lastly, if running in live view, more agents or a larger world could lead to slower display rates and rendering. 
## Development Notes
This was a really fun challenge, and an interesting one for me as I learned more about CRDTs, Ditto SDK as well as AI assisted development (something my current job does not currently have much scope for).
### AI Usage
Overall, AI assisted development was a force-multiplier for me, helping me quickly generate code for key functionality by following the plan and steps that I had laid out for the project. In particular, once I had developed the foundational code base, Claude was extremely useful in quickly implementing new features, letting me test, debug and modify as needed. After I had the core assignment functionality intact, Claude easily generated a visualizer class for me that represented all the features and functionality I wanted to showcase, providing a much higher level of polish to the simulation from my initial terminal based code. From there, as I made other changes, I was able to quickly trust Claude to make updates accordingly to visualization. For more complex logic like data mule behavior, search and convergence, Claude sometimes made mistakes, either in syntax, small logic errors or incorrect decision making. I'll lay this out and how I used Claude in more detail below: 

To start with, once I had outlined an initial approach and architecture plan, I used Claude to evaluate (along with the assignment notes) to see if there were any gaps in my plan. Claude suggested an alternate and somewhat more distributed approach, but I wanted to keep the code base small so focused on these initial files:
- main.py: Runs the simulation.
- drone.py: Basic drone model, utilizes:
	- sensor.py: Representative sensor.
	- world_model.py: Offline-fist model of the simulated world, representing cells searched and determined pilot location.
	- autonomy.py: Hosts agent search and rescue logic.
- ditto.py: Representation of Ditto SDK.

With this determined, I asked Claude to give me an overview (with some code logic) to get started on these files and used this a foundation to begin my initial work. As mentioned above, I first focused on lawnmower search with three agents, a simple sensor and did not add CRDT functionality or propagation. If an agent found the pilot we were successful. There were some initial growing pains for me here, I used some of Claude's template code but also wrote and revised functionality myself, but this initially led to some variable mismatches that I fixed quickly after running tests. 

The first mistake I caught from Claude was simple, but led to a edge-case render error (in the original 2D terminal grid) in which the drone would go out of bounds and the grid could not generate (going to a y value of the sim's height value instead of height minus 1- since we start at 0). I found the issue within the render function and adjusted the height assignment. 

From here, I solidified my approach for a G-Counter w/ Gossip Protocol, reviewing both Ditto's docs and online information on CRDTs to manage sync and conflict-resolution and asked Claude to implement those changes within my codebase (first ditto sync function, then modifying lawnMower to dataMule in autonomy.py). Claude's edits mostly worked here, but while it suggested a peer_status dict added to WorldModel, it did not initially provide code to actually propagate peer_status changes through merge. I found this through testing in which the dataMule update() function was noting when a pilot was detected (and this propagated through ditto sync()) but it would see the other peers as not knowing the pilot location. In this case I showed Claude the output and it generated the addition for propagation. 

As noted above, visualization was a purely Claude addition with the smallest layer of updates from me (adding fps and changing some display parameters) and an extremely useful addition. 

However when I wanted to add a final converging logic, Claude made a mistake in suggesting I remove the data mule code block within merge() (autonomy.py). 
To add convergence behavior LLM suggested that I would not need to keep dataMule behavior, and that I could just immediately converge on the pilot, like so:
```
	- # Once pilot is confirmed, converge on location
	if model.pilot_found is not None:
		return self.step(pos, model.pilot_found)
```
I flagged this behavior as incorrect, and instead modified the dataMule behavior so that instead of returning to the lawnMower pattern in its final condition, it moved towards the pilot, like so:
```
if model.pilot_found is not None:
# Found the target, act as data mule
	target = self.nearest_uninformed(pos, model, d_id)
		if target is not None:
		#print(f"drone {id} MULING toward uninformed peer at {target}")
			return self.step(pos, target)
		# All known peers are informed, converge on location
		return self.step(pos, model.pilot_found)
```

I tested Claude's code to verify my hypothesis, and sure enough it orphaned the final drone, preventing the success state. So, I modified the existing data mule block as shown above.
### Roadmap & Production 
If I had another day, I'd focus on a couple of additions: 
- sim_cfg.py to make configuration a lot smoother, more uniform across codebase, right now it is unpolished (hosted primarily in main.py). After uploading to git initially, I'd tell git to --assume-unchanged so that the user could play around with configurations without git tracking them as changes. This would be quick and my first add. 
- Downed drone functionality. I believe mostly for this to work drone utilization across the code base would need some quick checks with a running list of downed drones (offline-first that is compared just like world_model). This would require more edge case testing as well as an addition of either event based or user based ability to remove drones.
- Ant Colony Search: A popular multi-agent search mechanism, it would be an interesting challenge to implement (would definitely utilize Claude for implementation assistance) and better display of the core functionality compared to the lawnmower pattern currently implemented. 
- (Time-permitting) Bandwidth realism. 

Finally, if I were to attempt the same work for production I have outlined some of my initial thoughts. In fact, this was where my head first went reading the challenge, and I had to make sure to reel myself in as it is certainly none trivial and well beyond the scope of the intended time frame:
- C++ implementation: Enables both ArduPilot/PX4, ROS2 and Ditto SDK v5 development. 
- ArduPilot SITL as first layer of simulation testing (simple top-down view), that can work alongside ROS2, MAVROS for autonomous system integration. 
- ROS2 integration with autonomy code would enable Gazebo for higher fidelity and 3D rendered simulation of drone (or other uncrewed terrain platform visualizations).
- Translate simulation to surrogate platform field testing.
- Ditto SDK v5 implementation: Using the C++ wrapper, I could enable deeper, more complex data syncing behaviors that will help handle the much wider breadth of edge-case and real world limitations the autonomous systems will have to deal with.

