# CSC4880 Cooperative Multi-Agent Gridworld — Starter Code

This package accompanies the **Cooperative Multi-Agent Gridworld** lab.  It
implements a small environment in which two robots collect packages and return
them to a common base.  The design follows the Russell and Norvig agent model:
each agent receives a local percept, retains any internal state it chooses,
and returns one action at each time step.

The included `ExampleBaselineAgent` is an intentionally weak, independent
agent.  It has local memory and a simple exploration rule, but it does **not**
communicate, claim packages, or coordinate traffic.  It is a comparison point,
not a solution to the lab. `CoordinatedAgentTemplate` adds discoveries and
claims while keeping the same movement rules.

## Run it

The project uses only the Python standard library and Python 3.10 or later.
From this directory, run:

```bash
python run_demo.py
python run_experiments.py
python -m unittest discover -s tests -v
```

## What is included

| Path | Purpose |
| --- | --- |
| `gridworld/environment.py` | Environment mechanics, scoring, local perception, simultaneous moves, messages, and event logs. |
| `gridworld/models.py` | The `Percept`, `Action`, `Message`, and result data structures. |
| `gridworld/agents.py` | Independent baseline and coordinated policy. |
| `gridworld/runner.py` | A loop that asks each agent for its own action, then advances the world. |
| `gridworld/scenarios.py` | Starter map and two additional fixed 8 x 8 maps. |
| `tests/test_environment.py` | Mechanics checks students can run while extending their policy. |
| `tests/test_coordination.py` | Claim, stale-message, delivery-release, and reproducibility checks. |
| `run_experiments.py` | Saves all six runs to `results/`, including maps, score terms, and full logs. |

## Environment contract

- Coordinates are `(row, column)`; row 0 is north and column 0 is west.
- Each agent sees only in-bounds cells in a local 3 x 3 window, its carrying
  state, its last action result, the current time, and any incoming messages.
- An `Action` can request a move, a pickup/drop interaction, and one optional
  broadcast message in the same time step.
- Moves resolve simultaneously.  Same-destination moves, swaps, and moves into
  an agent that stays in place are blocked and logged as collision attempts.
- A message sent in time `t` is available when the recipient next chooses an
  action at time `t + 1`.
- The team score is: `+10` per delivered package, `-1` per attempted move,
  `-2` per invalid move or interaction, `-3` per collision attempt, and `-5`
  per unfinished package at the end of the episode.

`run_demo.py` prints a short event log.  The full log is available as
`EpisodeResult.events`; each event records the time, agent, percept summary,
received/sent messages, action, result, and final position.

## PEAS and policies

Performance: deliveries, team score, collisions, and steps. Environment: two
robots, one base, four packages, and obstacles on an 8 x 8 grid. Actuators:
N/S/E/W, wait, pickup, drop, and a message. Sensors: local 3 x 3 cells,
position, carrying status, previous result, time, and incoming messages.

The task is discrete and sequential: each turn changes the next decision.
It is partially observable because the rest of the map is hidden. It is
dynamic from each robot's view because the other robot can move or take a
package each step, though the simulator does not advance during `act()`.
It is cooperative because both robots contribute to one score.

`run_episode` calls `observe` for each robot, gets their separate `act`
decisions, and calls `environment.step`. The environment resolves movement
and collisions, then pickup/drop, then messages for the next turn.

The baseline remembers seen packages and the base. It collects a package
underfoot, carries it home, or heads toward the nearest known package.
Otherwise it cycles through directions. It ignores messages and has no
global map. Both policies use the same per-robot direction orders.

The coordinated policy also remembers a goal, package owners, and pending
discoveries. DISCOVER shares a location; CLAIM reserves a target; RELEASE
clears the sender's claim after delivery or abandoning a goal. Equal-distance
packages use coordinate order. Conflicting claims use the lower robot ID.
Current sight overrides delayed messages. Agents avoid occupied neighboring
cells, but cannot predict simultaneous moves into an empty cell.

## Recorded results

Both unchanged policies ran on the same three maps with a 60-step horizon.
All maps have at least five obstacles, four reachable packages, and a
one-cell gap in a wall. Exact coordinates are in each saved JSON file.

| Map | Policy | Delivered | Score | Collisions | Steps |
| --- | --- | ---: | ---: | ---: | ---: |
| starter | baseline | 1 | -123 | 0 | 60 |
| starter | coordinated | 1 | -123 | 0 | 60 |
| middle_gap | baseline | 2 | -106 | 0 | 60 |
| middle_gap | coordinated | 2 | -112 | 2 | 60 |
| horizontal_gap | baseline | 2 | -106 | 0 | 60 |
| horizontal_gap | coordinated | 2 | -106 | 0 | 60 |

In `middle_gap_coordinated.json`, robot-1 announces (2, 2) at t=1.
Robot-2 receives it at t=2 and moves east toward a package outside its view.
At t=8 both robots try to enter the base and are blocked. Those two
collision penalties explain the six-point loss. Coordination changed the
route, but did not increase deliveries. Greedy movement and repeated local
exploration still leave packages undelivered. Better route memory and a
rule for yielding near the base are possible extensions.

The syntax fix and claim fixes are in `gridworld/agents.py`; environment
mechanics and baseline behavior were left as supplied. The Google Doc holds
the lab report, results table, and 791-word comparative analysis:
https://docs.google.com/document/d/1wP7iS77UEllB9xcn6vrKhwlZgrHHNGpQz1VokJLk-HI/edit
