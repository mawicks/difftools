from __future__ import annotations

from collections.abc import Hashable, Sequence
from dataclasses import dataclass, field

from gaspra.changesets import (
    Changeset,
    ChangesetLeaf,
    find_changeset,
    old_apply_forward,
    apply_forward,
)
from gaspra.revision_tree import Tree
from gaspra.types import TokenSequence


@dataclass
class Versions:
    root_version: TokenSequence = ""
    root_tag: Hashable | None = None

    tree: Tree = field(default_factory=Tree)
    diffs: dict[Hashable, Changeset | ChangesetLeaf] = field(default_factory=dict)

    def save(self, version_id: Hashable, version: TokenSequence):
        required_changesets, expired_changesets, removed_paths = self.tree.insert(
            version_id
        )
        for current_tag, older_tag in required_changesets:
            # The first tag should always match version_id (the version
            # being added).
            if current_tag != version_id:  # pragma: no cover
                raise RuntimeError(f"{current_tag} was expected to be {version_id}")

            # tag_2 should never be version_id.  It will be either
            # the root_tag or the tag associated with old_path.
            if older_tag == self.root_tag:
                older_version = self.root_version
            else:
                old_path = removed_paths[older_tag]
                older_version = self._retrieve_using_path(tuple(old_path))

            self.diffs[current_tag, older_tag] = find_changeset(version, older_version)

        for current_tag, older_tag in expired_changesets:
            del self.diffs[current_tag, older_tag]

        self.root_tag = version_id
        self.root_version = version
        return

    def _retrieve_using_path(self, path: Sequence[Hashable]):
        """
        Function to retrieve a version give its path.

        This is intended for internal use in this module.
        """
        if self.root_version is None:  # pragma: no cover
            raise ValueError("Versions have not been initialized.")

        # Initialize with root_version,
        # then apply all of the patches in the path.
        patched = self.root_version

        for n1, n2 in zip(path, path[1:]):
            changeset = self.diffs[n1, n2]
            reduced_changeset = changeset.reduce()
            patched = apply_forward(reduced_changeset, patched)

        return patched

    def retrieve(self, version_id: Hashable) -> TokenSequence:
        if self.root_version is None:  # pragma: no cover
            raise ValueError("Versions have not been initialized.")

        if version_id == self.root_tag and self.root_version:
            return self.root_version

        path = self.tree.path_to(version_id)

        return self._retrieve_using_path(path)
