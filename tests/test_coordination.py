"""Checks for the claim rules and the three lab maps."""

import unittest
from dataclasses import replace

from gridworld.agents import CoordinatedAgentTemplate
from gridworld.environment import GridWorld
from gridworld.models import Message, MessageKind, Direction
from gridworld.runner import run_episode
from gridworld.scenarios import EXPERIMENT_MAPS, starter_agents


class CoordinationTests(unittest.TestCase):
    def setUp(self):
        self.world = GridWorld(width=8, height=8, base=(0, 0), obstacles=set(),
                               packages={(1, 1), (2, 2)},
                               agent_positions={"robot-1": (0, 1), "robot-2": (2, 0)})
        self.agent = starter_agents(coordinated=True)["robot-2"]
        self.agent.reset("robot-2")

    def test_conflicting_claims_converge_on_lower_id(self):
        agents = starter_agents(coordinated=True)
        for agent_id, agent in agents.items():
            agent.reset(agent_id)
            agent.current_goal = (1, 1)
            agent.claimed_by[(1, 1)] = agent_id
            other_id = "robot-2" if agent_id == "robot-1" else "robot-1"
            percept = replace(self.world.observe(agent_id), messages=(
                Message(MessageKind.CLAIM, (1, 1), other_id),))
            agent.act(percept)
        self.assertEqual(agents["robot-1"].claimed_by[(1, 1)], "robot-1")
        self.assertEqual(agents["robot-2"].claimed_by[(1, 1)], "robot-1")
        self.assertNotEqual(agents["robot-2"].current_goal, (1, 1))

    def test_non_owner_release_does_not_remove_claim(self):
        self.agent.claimed_by[(1, 1)] = "robot-1"
        percept = replace(self.world.observe("robot-2"), messages=(
            Message(MessageKind.RELEASE, (1, 1), "robot-2"),))
        self.agent.act(percept)
        self.assertEqual(self.agent.claimed_by[(1, 1)], "robot-1")

    def test_current_sight_overrides_stale_discovery(self):
        self.world.remaining_packages.remove((1, 1))
        percept = replace(self.world.observe("robot-2"), messages=(
            Message(MessageKind.DISCOVER, (1, 1), "robot-1"),))
        self.agent.act(percept)
        self.assertNotIn((1, 1), self.agent.known_packages)
        self.assertNotIn((1, 1), self.agent.unanounced_packages)

    def test_release_is_not_overwritten_by_discovery(self):
        self.agent.current_goal = (1, 0)
        self.agent.claimed_by[(1, 0)] = "robot-2"
        action = self.agent.act(self.world.observe("robot-2"))
        self.assertEqual(action.message, Message(MessageKind.RELEASE, (1, 0)))
        self.assertIn((1, 1), self.agent.unanounced_packages)

    def test_delivery_releases_claim_on_next_decision(self):
        world = GridWorld(width=3, height=3, base=(0, 0), obstacles=set(),
                          packages={(1, 1)},
                          agent_positions={"robot-1": (1, 1), "robot-2": (2, 2)})
        agent = CoordinatedAgentTemplate()
        agent.reset("robot-1")
        agent.current_goal = (1, 1)
        agent.claimed_by[(1, 1)] = "robot-1"
        agent.known_packages.add((1, 1))
        for _ in range(4):
            world.step({"robot-1": agent.act(world.observe("robot-1"))})
        self.assertEqual(world.delivered_packages, [(1, 1)])
        action = agent.act(world.observe("robot-1"))
        self.assertEqual(action.message, Message(MessageKind.RELEASE, (1, 1)))
        self.assertNotIn((1, 1), agent.claimed_by)

    def test_claim_changes_later_action(self):
        # Same percept and memory, with and without the other agent's claim.
        percept = self.world.observe("robot-2")
        without = self.agent.act(percept)
        self.agent.reset("robot-2")
        with_claim = self.agent.act(replace(percept, messages=(
            Message(MessageKind.CLAIM, (1, 1), "robot-1"),)))
        self.assertEqual(without.move, Direction.NORTH)
        self.assertEqual(with_claim.move, Direction.SOUTH)

    def test_maps_are_reachable_and_runs_are_reproducible(self):
        for make_world in EXPERIMENT_MAPS.values():
            world = make_world()
            self.assertEqual((world.width, world.height, world.horizon), (8, 8, 60))
            self.assertGreaterEqual(len(world.obstacles), 5)
            self.assertGreaterEqual(len(world.initial_packages), 4)
            reached, pending = {world.base}, [world.base]
            while pending:
                row, column = pending.pop()
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    pos = (row + dr, column + dc)
                    if (0 <= pos[0] < 8 and 0 <= pos[1] < 8
                            and pos not in world.obstacles and pos not in reached):
                        reached.add(pos)
                        pending.append(pos)
            self.assertTrue(world.initial_packages <= reached)
            for coordinated in (False, True):
                first = run_episode(make_world(), starter_agents(coordinated=coordinated))
                second = run_episode(make_world(), starter_agents(coordinated=coordinated))
                self.assertEqual(first, second)
                self.assertLessEqual(first.steps, 60)


if __name__ == "__main__":
    unittest.main()
