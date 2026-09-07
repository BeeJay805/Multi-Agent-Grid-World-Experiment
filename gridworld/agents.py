"""An intentionally simple independent agent and a coordination template."""

from __future__ import annotations

from .models import Action, Direction, Interaction, Percept, Position, Terrain, MessageKind, Message


class ExampleBaselineAgent:
    """A deliberately limited agent for the independent-policy baseline.

    It remembers packages and the base only after seeing them in a local
    percept.  It sends no messages, does not claim work, and has no global map
    or path planner.  Students should use it as a comparison point, not as a
    coordinated solution.
    """

    def __init__(self, exploration_order: tuple[Direction, ...] | None = None) -> None:
        self.exploration_order = exploration_order or (
            Direction.NORTH,
            Direction.EAST,
            Direction.SOUTH,
            Direction.WEST,
        )
        if not self.exploration_order or Direction.WAIT in self.exploration_order:
            raise ValueError("exploration_order must contain non-WAIT directions")
        self.reset("")

    def reset(self, agent_id: str) -> None:
        self.agent_id = agent_id
        self.known_packages: set[Position] = set()
        self.base_location: Position | None = None
        self._exploration_cursor = 0

    def act(self, percept: Percept) -> Action:
        """Choose one purely local, non-communicating action."""

        self._update_memory(percept)

        if percept.carrying:
            if percept.self_position == self.base_location:
                return Action(interaction=Interaction.DROP)
            if self.base_location is not None:
                return Action(move=self._move_toward(percept, self.base_location))
            return Action(move=self._explore(percept))

        current_cell = percept.visible_cells[percept.self_position]
        if current_cell.package_present:
            return Action(interaction=Interaction.PICKUP)

        if self.known_packages:
            target = min(
                self.known_packages,
                key=lambda position: self._manhattan(percept.self_position, position),
            )
            if target != percept.self_position:
                move = self._move_toward(percept, target)
                if move is not Direction.WAIT:
                    return Action(move=move)

        return Action(move=self._explore(percept))

    def _update_memory(self, percept: Percept) -> None:
        for position, cell in percept.visible_cells.items():
            if cell.terrain is Terrain.BASE:
                self.base_location = position
            if cell.package_present:
                self.known_packages.add(position)
            elif position in self.known_packages:
                # This handles packages that another agent has picked up once
                # their former location becomes locally visible.
                self.known_packages.remove(position)

    def _move_toward(self, percept: Percept, target: Position) -> Direction:
        row, column = percept.self_position
        target_row, target_column = target
        preferred: list[Direction] = []
        if target_row < row:
            preferred.append(Direction.NORTH)
        elif target_row > row:
            preferred.append(Direction.SOUTH)
        if target_column < column:
            preferred.append(Direction.WEST)
        elif target_column > column:
            preferred.append(Direction.EAST)

        for direction in (*preferred, *self.exploration_order):
            if self._can_enter(percept, direction):
                return direction
        return Direction.WAIT

    def _explore(self, percept: Percept) -> Direction:
        for offset in range(len(self.exploration_order)):
            index = (self._exploration_cursor + offset) % len(self.exploration_order)
            direction = self.exploration_order[index]
            if self._can_enter(percept, direction):
                self._exploration_cursor = (index + 1) % len(self.exploration_order)
                return direction
        return Direction.WAIT

    @staticmethod
    def _can_enter(percept: Percept, direction: Direction) -> bool:
        row_delta, column_delta = direction.delta
        destination = (
            percept.self_position[0] + row_delta,
            percept.self_position[1] + column_delta,
        )
        cell = percept.visible_cells.get(destination)
        if cell is None or cell.terrain is Terrain.OBSTACLE:
            return False
        return not cell.agent_ids

    @staticmethod
    def _manhattan(first: Position, second: Position) -> int:
        return abs(first[0] - second[0]) + abs(first[1] - second[1])


class CoordinatedAgentTemplate(ExampleBaselineAgent):
    """The baseline movement rules with local discoveries and package claims."""

    def reset(self, agent_id: str) -> None:
        super().reset(agent_id)
        self.claimed_by: dict[Position, str] = {}
        self.current_goal = None
        self.unanounced_packages = set()

    def act(self, percept: Percept) -> Action:
        old_goal = self.current_goal
        # Process yesterday's messages before checking what is visible now.
        for message in percept.messages:
            if message.package_location is None or message.sender is None:
                continue
            if message.kind == MessageKind.RELEASE:
                if self.claimed_by.get(message.package_location) == message.sender:
                    del self.claimed_by[message.package_location]
            elif message.kind == MessageKind.DISCOVER:
                self.known_packages.add(message.package_location)

            elif message.kind == MessageKind.CLAIM:
                owner = self.claimed_by.get(message.package_location, message.sender)
                self.claimed_by[message.package_location] = min(owner, message.sender)

        # Update memory only from the local percept, including the base.
        for position, cell in percept.visible_cells.items():
            if cell.package_present and position not in self.known_packages:
                self.unanounced_packages.add(position)
        self._update_memory(percept)
        self.unanounced_packages.intersection_update(self.known_packages)

        # Choose a target that respects claims.
        if not percept.carrying:

            available_packages: set[Position] = set()
            for position in self.known_packages:
                if position in self.claimed_by:
                    if self.claimed_by[position] == self.agent_id:
                        available_packages.add(position)
                else:
                    available_packages.add(position)
            best_package = None
            best_distance = None
            if available_packages:
                for position in available_packages:
                    distance = self._manhattan(percept.self_position, position)
                    if best_distance is None or distance < best_distance:
                        best_distance = distance
                        best_package = position
                    elif distance == best_distance and position < best_package:
                        best_package = position
            if self.current_goal not in self.known_packages or (
                    self.current_goal in self.claimed_by
                    and self.claimed_by[self.current_goal] != self.agent_id
            ):
                self.current_goal = best_package

        # Send at most one message, with releases taking priority.
        outgoing_message = None
        # RELEASE
        if old_goal is not None and old_goal != self.current_goal:
            if old_goal in self.claimed_by and self.claimed_by[old_goal] == self.agent_id:
                del self.claimed_by[old_goal]
                outgoing_message = Message(MessageKind.RELEASE, old_goal)
        # DISCOVER
        if outgoing_message is None and self.unanounced_packages:
            smallest_package = min(self.unanounced_packages)
            outgoing_message = Message(MessageKind.DISCOVER, smallest_package)
            self.unanounced_packages.remove(smallest_package)
        #CLAIM
        if outgoing_message is None and self.current_goal is not None:
            if self.current_goal not in self.claimed_by:
                self.claimed_by[self.current_goal] = self.agent_id
                outgoing_message = Message(MessageKind.CLAIM, self.current_goal)





        # Reuse the baseline's movement so the comparison isolates coordination.
        if percept.carrying:
            if percept.self_position == self.base_location:
                return Action(interaction=Interaction.DROP, message=outgoing_message)
            if self.base_location is not None:
                return Action(move=self._move_toward(percept, self.base_location),
                              message=outgoing_message)
        elif self.current_goal is not None:
            if percept.self_position == self.current_goal:
                return Action(interaction=Interaction.PICKUP, message=outgoing_message)
            return Action(move=self._move_toward(percept, self.current_goal),
                          message=outgoing_message)

        return Action(move=self._explore(percept), message=outgoing_message)
