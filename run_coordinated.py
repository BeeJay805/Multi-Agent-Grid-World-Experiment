from gridworld.agents import CoordinatedAgentTemplate
from gridworld.runner import run_episode
from gridworld.scenarios import starter_world


def main():
    world = starter_world()

    agents = {
        "robot-1": CoordinatedAgentTemplate(),
        "robot-2": CoordinatedAgentTemplate(),
    }

    result = run_episode(world, agents)

    print("Coordinated policy")
    print()
    print(f"Steps: {result.steps}")
    print(f"Packages delivered: {result.delivered_count}")
    print(f"Collision attempts: {result.collision_attempts}")
    print(f"Team score: {result.score}")

    print()
    print("First 30 event-log entries")

    for event in result.events[:]:
        print(
            f"t={event.time:02d} "
            f"{event.agent_id:7} "
            f"action=({event.action.move.name},{event.action.interaction.name}) "
            f"sent={event.sent_message} "
            f"received={event.received_messages} "
            f"result=({event.result.movement.value},{event.result.interaction.value}) "
            f"pos={event.final_position}"
        )


if __name__ == "__main__":
    main()