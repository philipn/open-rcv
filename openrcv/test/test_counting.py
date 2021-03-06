
from textwrap import dedent
import unittest

from openrcv.counting import (count_internal_ballots, get_lowest, get_majority,
                              get_winner, normalized_ballots, InternalBallotsNormalizer)
from openrcv.models import RoundResults
from openrcv.utils import StringInfo
from openrcv.utiltest.helpers import UnitCase


class ModuleTest(UnitCase):

    def test_normalized_ballots(self):
        # This test case simultaneously checks all of (1) "compressing" (by
        # weight), (2) lexicographically ordering by choice (and not
        # by weight), and (3) ballots with no choices (aka undervotes).
        lines = dedent("""\
            1 2
            1
            1 3
            2
            4 1
            1 2
            """).splitlines(keepends=True)
        normalized = normalized_ballots(lines)
        # Check that it returns a generator iterator and not a concrete
        # list/tuple/etc.
        self.assertEqual(type(normalized), type((x for x in ())))
        self.assertEqual(list(normalized), [(3, ()), (4, (1,)), (2, (2,)), (1, (3,))])

    def test_count_internal_ballots(self):
        internal_ballots = dedent("""\
        1 2
        3 1 4
        1 2
        """)
        openable = StringInfo(internal_ballots)
        result = count_internal_ballots(openable, (1, 2, 4))
        self.assertEqual(type(result), RoundResults)
        self.assertEqual(result.totals, {1: 3, 2: 2, 4: 0})

    def test_get_majority(self):
        cases = [
            (0, 1),
            (1, 1),
            (2, 2),
            (3, 2),
            (4, 3),
            (100, 51),
        ]
        for total, expected in cases:
            with self.subTest(total=total, expected=expected):
                self.assertEqual(get_majority(total), expected)

    def test_get_winner(self):
        self.assertIs(get_winner({1: 5, 2: 5}), None)
        cases = [
            ({1: 6, 2: 5}, 1),
            ({1: 5, 2: 6}, 2),
            ({1: 1, 2: 6, 3: 4}, 2),
        ]
        for totals, winner in cases:
            with self.subTest(totals=totals, winner=winner):
                self.assertEqual(get_winner(totals), winner)

    def test_get_lowest__no_totals(self):
        """Test passing an empty totals dict."""
        with self.assertRaises(ValueError):
            get_lowest({})

    def test_get_lowest(self):
        cases = [
            ({1: 6, 2: 5}, {2}),
            ({1: 5, 2: 6}, {1}),
            ({1: 1, 2: 6, 3: 4}, {1}),
            # Test ties.
            ({1: 5, 2: 5}, {1, 2}),
            ({1: 5, 2: 6, 3: 5}, {1, 3}),
        ]
        for totals, lowest in cases:
            with self.subTest(totals=totals, lowest=lowest):
                self.assertEqual(get_lowest(totals), lowest)


class InternalBallotsNormalizerTest(UnitCase):

    def test_parse(self):
        internal_ballots = dedent("""\
        1 2
        1 3
        4 1
        3
        1 2
        """)
        expected = dedent("""\
        3
        4 1
        2 2
        1 3
        """)
        output_stream = StringInfo()
        parser = InternalBallotsNormalizer(output_stream)
        ballot_stream = StringInfo(internal_ballots)
        parser.parse(ballot_stream)
        self.assertEqual(output_stream.value, expected)
