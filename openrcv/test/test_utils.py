
from openrcv.utils import ReprMixin, StringInfo
from openrcv.parsing import parse_internal_ballot
from openrcv.utiltest.helpers import UnitCase


class ModuleTest(UnitCase):

    def test_parse_internal_ballot(self):
        cases = [
            ("1 2", (1, (2, ))),
            ("1", (1, ())),
            # Leading and trailing space are okay
            (" 1 2", (1, (2, ))),
            ("1 2 \n", (1, (2, ))),
        ]
        for line, expected in cases:
            with self.subTest(line=line, expected=expected):
                self.assertEqual(parse_internal_ballot(line), expected)

    def test_parse_internal_ballot__non_integer(self):
        with self.assertRaises(ValueError):
            parse_internal_ballot("f 2 \n")


class ReprMixinTest(UnitCase):

    class ReprSample(ReprMixin):

        def repr_desc(self):
            return "foo"

    def test_repr(self):
        obj = ReprMixin()
        expected = "<ReprMixin: [--] %s>" % hex(id(obj))
        self.assertEqual(repr(obj), expected)

    def test_repr__implemented(self):
        obj = ReprMixinTest.ReprSample()
        expected = "<ReprSample: [foo] %s>" % hex(id(obj))
        self.assertEqual(repr(obj), expected)


class StringInfoTest(UnitCase):

    def test_init(self):
        stream = StringInfo("abc")
        self.assertEqual(stream.value, "abc")

    def test_init__no_args(self):
        stream = StringInfo()
        self.assertEqual(stream.value, None)

    def test_open__read(self):
        stream = StringInfo("abc")
        with stream.open() as f:
            out = f.read()
        self.assertEqual(out, "abc")
        # The value is also still available as an attribute.
        self.assertEqual(stream.value, "abc")

    def test_open__write(self):
        stream = StringInfo()
        with stream.open("w") as f:
            f.write("abc")
        # The value can be obtained from the attribute.
        self.assertEqual(stream.value, "abc")

    def test_open__write__non_none(self):
        """Test writing to a StringInfo initialized to a string."""
        stream = StringInfo()
        stream.value = ""  # Even an empty string triggers the ValueError.
        with self.assertRaises(ValueError):
            stream.open("w")
