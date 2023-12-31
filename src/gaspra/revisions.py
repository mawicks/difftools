from __future__ import annotations
from enum import Enum
from dataclasses import dataclass, field


class Direction(Enum):
    NONE = 0
    LEFT = 1
    RIGHT = 2


@dataclass
class Tree:
    """
    Implement a tree having several properties useful for revision
    control.  Edges represent diffs.  The idea is to have a path from
    the current version, which is stored verbatime in the root node, to
    the previous version.  Only the changes are stored for non-root
    versions.  The idea was to keep the path from the root to any
    version "short" and the number of diffs stored "small".  When adding
    a node we wnat to minimize the number of diffs to recompute.  A
    number of constraints make this different from a typical binary tree
    implementation.  One is the requirement that the most recent node
    needs to be at the root.  Also, recent versions needs to be near the
    top, so one child of the root node is the previous version.  The
    second child of the root node is a branch of the tree that is split
    off to "balance" the tree's path length.  From the construction of
    the tree it's easy to show that construction is O(n) in storage.
    The max path length appears to be O(n^(1/2) (unproven).  If that's
    true, finding the branch to split and splitting it would be
    O(n^(1/2)), making construction potentially as O(n^{3/2).  Also, the
    reevaluate() call, which is only necessary when initializing a
    pre-existing tree, would be O(n).
    """

    root: Node | None = None
    index: dict[int | str, Node] = field(default_factory=dict)

    def add(self, node_id: int | str):
        old_root = self.root
        new_root = Node(node_id)
        new_root.set_left(old_root)

        # Link in the other direction
        if old_root:
            best_split, direction = find_and_detach_best_split(old_root)
            # Detach best_split from tree
            if best_split and best_split.parent:
                if direction == Direction.LEFT:
                    best_split.parent.set_left(None)
                else:
                    best_split.parent.set_right(None)
            if best_split != old_root:
                new_root.set_right(best_split)

        self.root = new_root
        self.index[node_id] = new_root

    def edges(self):
        if self.root:
            yield from self.root.edges()

    def path_to(self, node_id) -> tuple[int | str, ...]:
        path = []
        current = self.index[node_id]
        while current:
            path.append(current.node_id)
            current = current.parent
        return tuple(reversed(path))

    def reevaluate(self):
        for node in self.index.values():
            # For each terminal node, ripple up the tree.
            if node.left is None and node.right is None:
                current = node
                while current:
                    current.update_states()
                    current = current.parent

    def _invalidate(self):
        """This exists only for testing reevaluate().  Don't call outside of a test."""
        for node in self.index.values():
            node._clear_state()

    def _get_state(self, node_id) -> tuple[int, int] | None:
        """
        This shouldn't be very useful except in testing. To avoid
        exposing the implementaiton, we avoid returning a Node type to
        the user and nol return the data.
        """
        node = self.index.get(node_id)
        if node:
            return node.count, node.length

        return None


@dataclass
class Node:
    node_id: int | str
    left: Node | None = None
    right: Node | None = None
    parent: Node | None = None

    length: int = 1
    count: int = 1

    def update_states(self):
        # Can't update just a single node.
        # If we change a node's state we must also
        # propagate the state up the tree.
        current = self
        while current:
            count = 1
            length = 1

            if current.left:
                count += current.left.count
                length += current.left.length

            if current.right:
                count += current.right.count
                length += current.right.length

            current.count = count
            current.length = length
            current = current.parent

    def _clear_state(self):
        """This exists only for testing.  Don't call outside of a test."""

        self.count = 0
        self.length = 0

    def set_left(self, node):
        self.left = node
        if node:
            node.parent = self
        self.update_states()

    def set_right(self, node):
        self.right = node
        if node:
            node.parent = self
        self.update_states()

    def edges(self):
        if self.left:
            yield (self.node_id, self.left.node_id)
            yield from self.left.edges()
        if self.right:
            yield (self.node_id, self.right.node_id)
            yield from self.right.edges()


def find_and_detach_best_split(current: Node):
    depth = 1
    direction = Direction.NONE
    while current is not None and depth < current.length:
        if current.right is not None and current.left is not None:
            if current.right.length > current.left.length:
                current = current.right
                direction = Direction.RIGHT
            elif current.left.length > current.right.length:
                current = current.left
                direction = Direction.LEFT
            elif current.right.node_id > current.left.node_id:
                current = current.right
                direction = Direction.RIGHT
            else:
                current = current.left
                direction = Direction.LEFT
            depth += 1
        elif current.right is not None:
            current = current.right
            direction = Direction.RIGHT
            depth += 1
        elif current.left is not None:
            current = current.left
            direction = Direction.LEFT
            depth += 1
        else:
            raise RuntimeError("This should not happen!")
    return current, direction
