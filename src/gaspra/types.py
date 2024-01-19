from collections.abc import Hashable, Iterable, Sequence
from collections import namedtuple
from typing import TypeVar

Token = Hashable
TokenVar = TypeVar("TokenVar", bound=Hashable)
Tag = TypeVar("Tag", bound=Hashable)
TokenSequence = Sequence[Token]
TokenIterable = Iterable[Token]
TokenSequenceVar = TypeVar("TokenSequenceVar", str, bytes, Sequence[int])

StringIterable = Iterable[str]
BytesIterable = Iterable[bytes]
TokenSequenceIterable = Iterable[TokenSequence]

Separator = namedtuple("Separator", "index")
Change = namedtuple("Change", ["a", "b"])
CommonSlice = namedtuple("Common", ["a_slice", "b_slice"])

# ReducedChangeIterable is agnostic about direction.  It can be used to
# apply changes in either direction.
ReducedChangeIterable = Iterable[CommonSlice | Change]

# StrippedChangeIterable/Sequence is used where a direction has been
# selected and stripped out of a ReducedChangeIterable. It represents
# only slices are used for common sections under the assumption
# that the original sequence is available for slicing.
StrippedChangeIterable = Iterable[slice | TokenSequence]
StrippedChangeSequence = Sequence[slice | TokenSequence]

# DiffIterable is different from StrippedChangeIterable in the sense
# that slices have been replaced by token sqeuences and that both
# directions of the change are available so that they can be displayed
# as a diff.  In other words, StrippedChangeIterable is a compact diff
# that can be *applied* in one direction. DiffIterable is a human
# readable diff intended for display.
DiffIterable = Iterable[TokenSequence | Change]
