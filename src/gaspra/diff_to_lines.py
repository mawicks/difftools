from collections.abc import Hashable, Iterable, Sequence
import io

from gaspra.types import Change


def split_and_add_fragment(
    partial_line_into: list[str | Change],
    partial_line_from: list[str | Change],
    fragment: Change,
):
    if fragment.a:
        partial_line_into.append(Change(fragment.a, ""))

    if fragment.b:
        partial_line_from.append(Change("", fragment.b))


def update_partials(partial_line_into, partial_line_from, input_fragment):
    if (partial_line_into and partial_line_into[-1] != "\n") or (
        partial_line_from and partial_line_from[-1] != "\n"
    ):
        if input_fragment:
            partial_line_into.append(input_fragment)
            partial_line_from.append(input_fragment)
        input_fragment = ""
    return input_fragment


def finish_conflict(partial_line_into, partial_line_from, input_fragment):
    input_fragment = input_fragment
    input_fragment = update_partials(
        partial_line_into, partial_line_from, input_fragment
    )

    yield Change(
        tuple(partial_line_into),
        tuple(partial_line_from),
    )

    if input_fragment:
        yield input_fragment


def to_line_diff(
    fragment_sequence: Iterable[Sequence[Hashable]],
):
    in_conflict = False
    no_output = True
    partial_line_into: list[str | Change] = []
    partial_line_from: list[str | Change] = []
    for fragment in fragment_sequence:
        if isinstance(fragment, Change):
            in_conflict = True
            split_and_add_fragment(
                partial_line_into,
                partial_line_from,
                fragment,
            )
        elif isinstance(fragment, str):
            lines = fragment.split("\n")
            if len(lines) > 1:  # Have a newline
                if in_conflict:
                    yield from finish_conflict(
                        partial_line_into,
                        partial_line_from,
                        lines[0] + "\n",
                    )
                    if _ := join_with_newline(lines[1:-1]):
                        yield _
                    no_output = False
                else:
                    if _ := join_with_newline(lines[:-1]):
                        yield _
                        no_output = False
                in_conflict = False
                partial_line_into = []
                partial_line_from = []
                if lines[-1]:
                    partial_line_into.append(lines[-1])
                    partial_line_from.append(lines[-1])
            elif lines[0]:
                partial_line_into.append(lines[0])
                partial_line_from.append(lines[0])

    if in_conflict:
        if (
            isinstance(partial_line_into[-1], Change)
            and partial_line_into[-1].a[-1:] != "\n"
        ) or (
            isinstance(partial_line_from[-1], Change)
            and partial_line_from[-1].b[-1:] != "\n"
        ):
            tail = "\n"
        else:
            tail = ""
        yield from finish_conflict(partial_line_into, partial_line_from, tail)
    elif partial_line_from and partial_line_from[0]:
        # If not in a conflict, partial_line_into should be
        # exactly the same as partial_line_from.
        partial_line_from.append("\n")
        yield "".join(partial_line_from)  # type: ignore
    elif no_output:
        yield ""


def join_with_newline(lines):
    if len(lines) > 0:
        return "\n".join(line for line in lines) + "\n"
    else:
        return ""