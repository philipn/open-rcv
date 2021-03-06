
from contextlib import contextmanager
from textwrap import dedent

from openrcv.jsonlib import JsonObjError, JS_NULL
from openrcv.jsmodels import (from_jsobj, JsonBallot, JsonContest,
                              JsonRoundResults, JsonTestCaseOutput)
from openrcv.utils import StreamInfo, StringInfo
from openrcv.utiltest.helpers import UnitCase


@contextmanager
def change_attr(obj, name, value):
    """Context manager to temporarily change the value of an attribute.

    This is useful for testing __eq__() by modifying one attribute
    at a time.

    """
    initial_value = getattr(obj, name)
    setattr(obj, name, value)
    yield
    setattr(obj, name, initial_value)


class JsonBallotTest(UnitCase):

    def make_ballot(self):
        return JsonBallot(choices=[1, 2], weight=3)

    def test_init(self):
        ballot = self.make_ballot()
        self.assertEqual(ballot.choices, (1, 2))
        self.assertEqual(ballot.weight, 3)

    def test_init__defaults(self):
        ballot = JsonBallot()
        self.assertEqual(ballot.choices, ())
        self.assertEqual(ballot.weight, 1)

    def test_init__tuple(self):
        """Check that JsonBallot converts lists to tuples."""
        ballot = JsonBallot(choices=[])
        self.assertEqual(ballot.choices, ())
        ballot = JsonBallot(choices=[1, 2])
        self.assertEqual(ballot.choices, (1, 2))

    def test_repr_desc(self):
        cases = [
            (3, (1, 2), "weight=3 choices=(1, 2)"),
            (None, None, "weight=None choices=None"),
        ]
        for weight, choices, expected in cases:
            with self.subTest(weight=weight, choices=choices, expected=expected):
                ballot = JsonBallot()
                ballot.choices = choices
                ballot.weight = weight
                self.assertEqual(ballot.repr_desc(), expected)

    def test_repr(self):
        ballot = self.make_ballot()
        expected = "<JsonBallot: [weight=3 choices=(1, 2)] %s>" % hex(id(ballot))
        self.assertEqual(repr(ballot), expected)

    def test_eq(self):
        ballot1 = self.make_ballot()
        ballot2 = self.make_ballot()
        self.assertEqual(ballot1, ballot2)
        with change_attr(ballot2, "choices", [1]):
            self.assertNotEqual(ballot1, ballot2)
        with change_attr(ballot2, "weight", 100):
            self.assertNotEqual(ballot1, ballot2)
        self.assertEqual(ballot1, ballot2)  # sanity check

    def test_to_jsobj(self):
        ballot = JsonBallot(choices=[1, 2], weight=3)
        jsobj = ballot.to_jsobj()
        self.assertEqual(jsobj, "3 1 2")

    def test_to_jsobj__choices_tuple(self):
        """Check using a tuple for choices."""
        ballot = JsonBallot(choices=(1, 2), weight=3)
        jsobj = ballot.to_jsobj()
        self.assertEqual(jsobj, "3 1 2")

    def test_to_jsobj__undervote(self):
        ballot = JsonBallot(weight=3)
        jsobj = ballot.to_jsobj()
        self.assertEqual(jsobj, "3")

    def test_to_jsobj__none_choices(self):
        """Test having None for choices."""
        ballot = JsonBallot(weight=3)
        ballot.choices = None
        jsobj = ballot.to_jsobj()
        self.assertEqual(jsobj, "3")

    def test_load_jsobj(self):
        ballot = JsonBallot()
        ballot.load_jsobj("2")
        self.assertEqual(ballot, JsonBallot(weight=2))

    # TODO: add tests for pure from_jsobj() function.

    def test_load_jsobj(self):
        ballot = JsonBallot()
        ballot.load_jsobj("2 3 4")
        self.assertEqual(ballot, JsonBallot(choices=(3, 4), weight=2))

    def test_load_jsobj__bad_format(self):
        """Check a string that does not parse."""
        ballot = JsonBallot()
        with self.assertRaises(JsonObjError):
            ballot.load_jsobj("1 a 2")

    def test_to_ballot_stream(self):
        ballots = [JsonBallot(weight=3),
                   JsonBallot(choices=[1, 2])]
        stream = JsonBallot.to_ballot_stream(ballots)
        self.assertTrue(isinstance(stream, StreamInfo))
        self.assertEqual(stream.value, "3\n1 1 2\n")

    def test_from_ballot_stream(self):
        ballot_stream = StringInfo(dedent("""\
        2
        3 1 2
        """))
        ballots = JsonBallot.from_ballot_stream(ballot_stream)
        expected = [JsonBallot(weight=2),
                    JsonBallot(weight=3, choices=(1, 2))]
        self.assertEqual(ballots, expected)


class JsonContestTest(UnitCase):

    def make_ballots(self):
        ballots = [JsonBallot(choices=[1, 2]),
                   JsonBallot(choices=[2], weight=3)]
        return ballots

    def make_contest(self, ballots=None):
        """Return a test contest."""
        if ballots is None:
            ballots = self.make_ballots()
        contest = JsonContest(candidate_count=2, ballots=ballots, id_=3, notes="foo")
        return contest

    def test_init(self):
        ballots = [JsonBallot(choices=[1, 2]),
                   JsonBallot(choices=[2], weight=3)]
        contest = self.make_contest(ballots=ballots)
        cases = [
            ("candidate_count", 2),
            ("ballots", ballots),
            ("id", 3),
            ("notes", "foo"),
        ]
        for attr, expected in cases:
            with self.subTest(attr=attr, expected=expected):
                actual = getattr(contest, attr)
                self.assertEqual(actual, expected)

    def test_init__defaults(self):
        contest = JsonContest()
        cases = [
            ("candidate_count", None),
            ("ballots", None),
            ("id", None),
            ("notes", None),
        ]
        for attr, expected in cases:
            with self.subTest(attr=attr, expected=expected):
                actual = getattr(contest, attr)
                self.assertEqual(actual, expected)

    def test_repr(self):
        contest = self.make_contest()
        self.assertEqual(repr(contest), "<JsonContest: [id=3 candidate_count=2] %s>" %
                         hex(id(contest)))

    def test_eq(self):
        contest1 = self.make_contest()
        contest2 = self.make_contest()
        self.assertEqual(contest1, contest2)

        # Check that each attribute can trigger inequality.
        cases = [
            ("candidate_count", 3),
            ("ballots", []),
            ("id", 4),
            ("notes", "foo2"),
        ]
        for attr, value in cases:
            with self.subTest(attr=attr, value=value):
                with change_attr(contest2, attr, value):
                    self.assertNotEqual(contest1, contest2)
        self.assertEqual(contest1, contest2)  # sanity check

    def test_load_jsobj(self):
        contest = JsonContest()
        self.assertEqual(contest.candidate_count, None)
        # Check loading an empty dict.
        # In particular, attributes should not get set to JS_NULL.
        contest.load_jsobj({})
        self.assertEqual(contest.candidate_count, None)

        # Check loading metadata.
        # Check that the id needs to be in the meta dict.
        contest.load_jsobj({"id": 5})
        self.assertEqual(contest.id, None)
        contest.load_jsobj({"_meta": {"id": 5}})
        self.assertEqual(contest.id, 5)
        # Check explicit None (to which the json module converts Javascript null).
        contest.load_jsobj({"_meta": {"id": None}})
        self.assertEqual(contest.id, JS_NULL)

        contest.load_jsobj({"candidate_count": 5})
        self.assertEqual(contest.candidate_count, 5)

    def test_load_jsobj__ballots(self):
        """Check that ballots deserialize okay."""
        contest = JsonContest()
        # Check that objects deserialize okay.
        expected_ballots = self.make_ballots()
        contest.load_jsobj({"ballots": ["3 2 1"]})
        # TODO
        # self.assertEqual(contest.ballots, expected_ballots)

    def test_to_jsobj(self):
        # TODO
        pass


class JsonRoundResultsTest(UnitCase):

    def test_to_jsobj(self):
        results = JsonRoundResults(totals={1: 2})
        self.assertEqual(results.to_jsobj(), {'totals': {1: 2}})


class JsonTestCaseOutputTest(UnitCase):

    def test_to_jsobj(self):
        rounds = [
            JsonRoundResults(totals={1: 2}),
            JsonRoundResults(totals={3: 4})
        ]
        results = JsonTestCaseOutput(rounds=rounds)
        self.assertEqual(results.to_jsobj(),
                         {'rounds': [{'totals': {1: 2}}, {'totals': {3: 4}}]})
