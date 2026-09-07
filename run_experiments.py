"""Run both policies on three fixed maps and save the lab evidence."""

import csv
import json
from dataclasses import asdict
from enum import Enum
from pathlib import Path

from gridworld.models import Direction, InteractionResult, MovementResult
from gridworld.runner import run_episode
from gridworld.scenarios import EXPERIMENT_MAPS, starter_agents


def main():
    output = Path(__file__).parent / "results"
    output.mkdir(exist_ok=True)
    rows = []
    for name, make_world in EXPERIMENT_MAPS.items():
        for policy in ("baseline", "coordinated"):
            world = make_world()
            result = run_episode(world, starter_agents(coordinated=policy == "coordinated"))
            moves = sum(e.action.move is not Direction.WAIT for e in result.events)
            invalid = sum(
                (e.result.movement is MovementResult.INVALID_MOVE)
                + (e.result.interaction is InteractionResult.INVALID_INTERACTION)
                for e in result.events
            )
            undelivered = len(world.initial_packages) - result.delivered_count
            assert result.score == (10 * result.delivered_count - moves - 2 * invalid
                                    - 3 * result.collision_attempts - 5 * undelivered)
            row = dict(map=name, policy=policy, deliveries=result.delivered_count,
                       score=result.score, collisions=result.collision_attempts,
                       steps=result.steps, moves=moves, invalid=invalid,
                       undelivered=undelivered)
            rows.append(row)
            evidence = {
                "map": name, "policy": policy, "horizon": world.horizon,
                "initial_state": {
                    "width": world.width, "height": world.height, "base": world.base,
                    "obstacles": sorted(world.obstacles),
                    "packages": sorted(world.initial_packages),
                    "agents": world.initial_agent_positions,
                },
                "results": row, "events": [asdict(e) for e in result.events],
            }
            (output / f"{name}_{policy}.json").write_text(
                json.dumps(evidence, indent=2,
                           default=lambda value: value.name if isinstance(value, Enum) else value)
                + "\n", encoding="utf-8",
            )
            print(f"{name:16} {policy:11} delivered={result.delivered_count} "
                  f"score={result.score} collisions={result.collision_attempts} steps={result.steps}")
    with (output / "summary.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()
