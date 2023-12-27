import pytest

from gaspra.suffix_automaton import (
    build,
    all_suffixes,
    find_substring,
    find_substring_all,
    find_lcs,
)

from gaspra.test_helpers.random_strings import random_string, random_tokens


def test_build_empty_string():
    """
    Ensure that an empty string is handled correctly.
    """
    automaton = build("")
    for string in all_suffixes(automaton):
        assert string == ""


def test_build_empty_tuple():
    """
    Ensure that an empty string is handled correctly.
    """
    empty = ()
    automaton = build(empty, empty=empty)
    for suffix in all_suffixes(automaton):
        assert tuple(suffix) == ()


BUILD_AND_EXTRACT_TEST_STRINGS = [
    "bananas",
    "abcbc",
    random_string("abc", 20, 42),
]

BUILD_AND_EXTRACT_TEST_TOKEN_SEQUENCES = [
    (1, 2, 3, 2, 3, 2, 4),
    (1, 2, 3, 2, 1),
    random_tokens([1, 2, 3], 20, 42),
]


@pytest.mark.parametrize(
    "token_sequence",
    [
        *BUILD_AND_EXTRACT_TEST_STRINGS,
        *BUILD_AND_EXTRACT_TEST_TOKEN_SEQUENCES,
    ],
)
def test_automaton_generates_only_suffixes(token_sequence):
    """
    Ensure that everything produced by the automaton is a suffix.
    Passing this along with the companion test
    test_automaton_generates_each_length_once() ensures that all
    suffixes are generated, each only once.
    """
    automaton = build(token_sequence, empty=token_sequence[0:0])
    for suffix_sequence in all_suffixes(automaton):
        # Assert that suffix_sequence is indeed a suffix
        suffix_len = len(suffix_sequence)
        if suffix_len > 0:
            assert suffix_sequence == token_sequence[-suffix_len:]
        else:
            assert suffix_sequence == token_sequence[0:0]


@pytest.mark.parametrize(
    "token_sequence",
    [*BUILD_AND_EXTRACT_TEST_STRINGS, *BUILD_AND_EXTRACT_TEST_TOKEN_SEQUENCES],
)
def test_automaton_generates_each_length_once(token_sequence):
    """
    Ensure that a string of every possible suffix length is generated
    by the automaton once and only once. Passing this along with the
    companion test test_automaton_generates_only_suffixes ensures that
    the automaton generates all of the suffixes are generated, each
    only once.
    """
    lengths = set(range(len(token_sequence) + 1))
    automaton = build(token_sequence, empty=token_sequence[0:0])

    for suffix_sequence in all_suffixes(automaton):
        assert len(suffix_sequence) in lengths
        # Remove len(string) so that repeats are detected.
        lengths.remove(len(suffix_sequence))

    # Check that every possible length was generated.
    assert len(lengths) == 0


@pytest.mark.parametrize(
    ["automaton_string", "query_string", "position"],
    [
        ("", "anything", None),
        ("bananas", "bananasx", None),
        ("bananas", "xbananas", None),
        ((), (1, 2, 3, 4, 5, 6, 7, 8), None),
        ((1, 2, 3, 2, 3, 2, 4), (1, 2, 3, 2, 3, 2, 4, 5), None),
        ((1, 2, 3, 2, 3, 2, 4), (5, 1, 2, 3, 2, 3, 2, 4), None),
        # Below are technically true substring cases which are also tested separately.
        ("anything", "", 0),
        ("", "", 0),
        ((1, 2, 3, 4, 5, 6, 7, 8), (), 0),
        ((), (), 0),
    ],
)
def test_find_substring(automaton_string, query_string, position):
    """
    We have a separate test that all substrings work, so this test is mostly focused on non-substrings.
    """
    root = build(automaton_string, automaton_string[0:0])
    assert position == find_substring(root, query_string)


@pytest.mark.parametrize(
    "token_sequence",
    [
        *BUILD_AND_EXTRACT_TEST_STRINGS,
        *BUILD_AND_EXTRACT_TEST_TOKEN_SEQUENCES,
    ],
)
def test_find_substring_is_true_on_all_substrings(token_sequence):
    """
    Build automaton for "string" and check that every non-trivial
    substring is correctly detected.
    """
    root = build(token_sequence, empty=token_sequence[0:0])

    for start in range(len(token_sequence)):
        for end in range(start + 1, len(token_sequence)):
            subsequence = token_sequence[start:end]
            position = find_substring(root, subsequence)
            assert position is not None
            end_position = position + len(subsequence)
            assert token_sequence[position:end_position] == subsequence


@pytest.mark.parametrize("string", BUILD_AND_EXTRACT_TEST_STRINGS)
def test_find_substring_is_correct_on_random_letters(string):
    """
    Build automaton for "string" and check that non-trivial
    random strings of different lengths selected from characters
    of "string" are detected (or not detected) correctly.
    """
    root = build(string)

    for k in range(len(string)):
        candidate = random_string(string, k + 1, k)
        position = find_substring(root, candidate)
        assert string.find(candidate) == position or position is None


@pytest.mark.parametrize("token_sequence", BUILD_AND_EXTRACT_TEST_TOKEN_SEQUENCES)
def test_find_substring_is_correct_on_random_tokens(token_sequence):
    """
    Build automaton for "string" and check that non-trivial
    random strings of different lengths selected from characters
    of "string" are detected (or not detected) correctly.
    """
    root = build(token_sequence, empty=token_sequence[0:0])

    for k in range(len(token_sequence)):
        candidate = random_tokens(token_sequence, k + 1, k)
        position = find_substring(root, candidate)
        # This test is a bit different than the string version.  We
        # don't have an efficient alternative to str.find() so we'll
        # only check the ones that find_substring() determines to be
        # present.  In other words, we don't check that string reported
        # as missing are actually missing.  The algorithms are exactly
        # the same for tuple[int.,,,] and str so this should be
        # sufficient.

        if position is not None:
            end_position = position + len(candidate)
            assert token_sequence[position:end_position] == candidate


@pytest.mark.parametrize(
    ["automaton_sequence", "query_sequence", "positions"],
    [
        # Substring cases
        ("abcdefg", "def", (3,)),
        ("anything", "", (0, 1, 2, 3, 4, 5, 6, 7, 8)),
        ("", "", (0,)),
        ("abcabc", "abc", (0, 3)),
        ((3, 4, 5, 6, 7, 8, 9), (6, 7, 8), (3,)),
        ((1, 2, 3, 4, 5, 6, 7, 8), (), (0, 1, 2, 3, 4, 5, 6, 7, 8)),
        ((), (), (0,)),
        ((1, 2, 3, 1, 2, 3), (1, 2, 3), (0, 3)),
        # Non-substring cases
        ("", "anything", ()),
        ("bananas", "sana", ()),
        ("bananas", "bananasx", ()),
        ("bananas", "xbananas", ()),
    ],
)
def test_find_substring_all(automaton_sequence, query_sequence, positions):
    """
    We have a separate test that all substrings work, so this test is mostly focused on non-substrings.
    """
    root = build(automaton_sequence, empty=automaton_sequence[0:0])
    assert positions == tuple(find_substring_all(root, query_sequence))


COMMON = random_string("abc", 17, 41)
NOT_COMMON1 = random_string("abc", 13, 42)
NOT_COMMON2 = random_string("abc", 13, 43)
S1 = NOT_COMMON1[:3] + COMMON + NOT_COMMON1[3:]
S2 = NOT_COMMON2[:6] + COMMON + NOT_COMMON1[6:]

LCS_TEST_STRINGS = [
    ("bananas", "xnanananx", 5),
    ("abcabcxyzfoo", "xyzafabcxyzfaz", 7),
    # Since these longer strings are randomly generated,
    # we don't know the exact length of the common string.
    # We know that it's *at least* len(common).
    (S1, S2, len(COMMON)),
]

COMMON_SEQ = random_tokens((1, 2, 3), 17, 41)
NOT_COMMON1_SEQ = random_tokens((1, 2, 3), 13, 42)
NOT_COMMON2_SEQ = random_tokens((1, 2, 3), 13, 43)
S1_SEQ = NOT_COMMON1_SEQ[:3] + COMMON_SEQ + NOT_COMMON1_SEQ[3:]
S2_SEQ = NOT_COMMON2_SEQ[:6] + COMMON_SEQ + NOT_COMMON1_SEQ[6:]

LCS_TEST_SEQS = [
    ("bananas", "xnanananx", 5),
    ((1, 2, 3, 2, 3, 2, 4), (5, 3, 2, 3, 2, 3, 2, 3, 5), 5),
    ("abcabcxyzfoo", "xyzafabcxyzfaz", 7),
    (
        (1, 2, 3, 1, 2, 3, 4, 5, 6, 7, 8, 8),
        (4, 5, 6, 1, 7, 1, 2, 3, 4, 5, 6, 7, 1, 9),
        7,
    ),
    # Since these longer strings are randomly generated,
    # we don't know the exact length of the common string.
    # We know that it's *at least* len(common).
    (S1_SEQ, S2_SEQ, len(COMMON_SEQ)),
]


@pytest.mark.parametrize(
    ["s1", "s2", "__lcs_length__"],
    [
        *LCS_TEST_STRINGS,
        *LCS_TEST_SEQS,
    ],
)
def test_find_lcs_finds_a_common_sequence(
    s1: str | tuple[int, ...],
    s2: str | tuple[int, ...],
    __lcs_length__: int,
):
    """
    Since some test strings are generated randomly,
    the parameter lcs_length is a lower bound on the lcs.
    We check that the computed lcs is 1) common; 2) locally maximal;
    and 3) at *least* lcs_length in length.
    """
    root = build(s1, empty=s1[0:0])

    start1, start2, length = find_lcs(root, s2)
    end1 = start1 + length
    end2 = start2 + length
    # Check that returned result is a common substring
    assert s1[start1:end1] == s2[start2:end2]


@pytest.mark.parametrize(
    ["s1", "s2", "lcs_length"],
    [
        *LCS_TEST_STRINGS,
        *LCS_TEST_SEQS,
    ],
)
def test_longest_common_string_finds_a_maximal_common_string(
    s1: str, s2: str, lcs_length: int
):
    """
    Since some test strings are generated randomly,
    the parameter lcs_legnth is a lower bound on the lcs.
    We check that the computed lcs is 1) common; 2) locally maximal;
    and 3) at *least* lcs_length in length.
    """
    root = build(s1, empty=s1[0:0])

    start1, start2, length = find_lcs(root, s2)

    # Make sure it's at least as long as the expected length.
    assert length >= lcs_length

    # Check that it's locally maximal in the sense that
    # if we extend it by one in either direction, it fails
    # to be a common substring in at least one direction:
    pre_start1 = max(start1 - 1, 0)
    pre_start2 = max(start2 - 1, 0)
    end1 = start1 + length
    end2 = start2 + length
    post_end1 = end1 + 1
    post_end2 = end2 + 1

    assert (
        s1[pre_start1:end1] != s2[pre_start2:end2]
        or s1[start1:post_end1] != s2[start2:post_end2]
    )


@pytest.mark.parametrize(
    ["build_sequence", "query_sequence"],
    (
        ("abc", "xyz"),
        ("", "xyz"),
        ("abc", ""),
        ("", ""),
        ((1, 2, 3), (4, 5, 6)),
        ((), (1, 2, 3)),
        ((1, 2, 3), ()),
        ((), ()),
    ),
)
def test_find_lcs_returns_all_zeros_when_nothing_in_common_or_empty_query(
    build_sequence, query_sequence
):
    root = build(build_sequence, empty=build_sequence[0:0])
    start1, start2, length = find_lcs(root, query_sequence)

    assert start1 == 0
    assert start2 == 0
    assert length == 0
