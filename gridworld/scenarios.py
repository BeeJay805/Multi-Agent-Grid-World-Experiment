"""A supplied starter map and the independent-policy agents for the demo."""

from __future__ import annotations

from .agents import CoordinatedAgentTemplate, ExampleBaselineAgent
from .environment import GridWorld
from .models import Direction


def starter_world() -> GridWorld:
    """Return the required 8 x 8 world with an intentional bottleneck."""

    return GridWorld(
        width=8,
        height=8,
        base=(0, 0),
        # The column-three wall has only one gap at the south edge, forcing
        # traffic between the two halves of the map through a shared corridor.
        obstacles={
            (0, 3),
            (1, 3),
            (2, 3),
            (3, 3),
            (4, 3),
            (5, 3),
            (6, 3),
            (5, 5),
        },
        packages={(1, 1), (0, 6), (5, 6), (7, 6)},
        agent_positions={"robot-1": (0, 1), "robot-2": (2, 0)},
        horizon=60,
    )


def starter_agents(*, coordinated: bool = False) -> dict[str, ExampleBaselineAgent]:
    """Two distinct but equally limited independent baseline agents."""

    agent_class = CoordinatedAgentTemplate if coordinated else ExampleBaselineAgent
    return {
        "robot-1": agent_class(
            (Direction.NORTH, Direction.EAST, Direction.SOUTH, Direction.WEST)
        ),
        "robot-2": agent_class(
            (Direction.WEST, Direction.SOUTH, Direction.EAST, Direction.NORTH)
        ),
    }


def middle_gap_world() -> GridWorld:
    """A vertical wall with a central opening."""
    return GridWorld(
        width=8, height=8, base=(0, 0),
        obstacles={(row, 3) for row in range(8) if row != 3},
        packages={(1, 1), (2, 2), (3, 5), (6, 6)},
        agent_positions={"robot-1": (0, 1), "robot-2": (2, 0)},
        horizon=60,
    )


def horizontal_gap_world() -> GridWorld:
    """A horizontal wall separating the base from the lower packages."""
    return GridWorld(
        width=8, height=8, base=(0, 0),
        obstacles={(3, column) for column in range(8) if column != 2},
        packages={(1, 2), (2, 1), (5, 2), (6, 5)},
        agent_positions={"robot-1": (0, 1), "robot-2": (2, 0)},
        horizon=60,
    )


EXPERIMENT_MAPS = {
    "starter": starter_world,
    "middle_gap": middle_gap_world,
    "horizontal_gap": horizontal_gap_world,
}
