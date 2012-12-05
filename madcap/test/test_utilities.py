from unittest import TestCase

from madcap.utilities import (EscapeError, b32d, b32e, escape, flag_dict,
                              unescape)


class TestB32d(TestCase):

    def test_b32d_as(self):
        i = "AAAAAAAA"
        o = "\x00" * 5
        self.assertEqual(b32d(i), o)

    def test_b32d_as_short(self):
        i = "AAAAAAA"
        o = "\x00" * 4
        self.assertEqual(b32d(i), o)


class TestB32e(TestCase):

    def test_b32e_nulls(self):
        i = "\x00" * 5
        o = "AAAAAAAA"
        self.assertEqual(b32e(i), o)

    def test_b32e_nulls_short(self):
        i = "\x00" * 4
        o = "AAAAAAA"
        self.assertEqual(b32e(i), o)


class TestEscape(TestCase):

    def test_escape_space(self):
        i = "test escape"
        o = "test\\sescape"
        self.assertEqual(escape(i), o)

    def test_escape_ordering(self):
        i = "\\s"
        o = "\\\\s"
        self.assertEqual(escape(i), o)


class TestUnescape(TestCase):

    def test_unescape_space(self):
        i = "test\\sunescape"
        o = "test unescape"
        self.assertEqual(unescape(i), o)

    def test_unescape_ordering(self):
        i = "\\\\s"
        o = "\\s"
        self.assertEqual(unescape(i), o)

    def test_unescape_invalid(self):
        i = "\\t"
        self.assertRaises(EscapeError, unescape, i)


class TestFlagDict(TestCase):

    def test_flag_dict_single(self):
        i = "FS0"
        o = {"FS": "0"}
        self.assertEqual(flag_dict(i), o)

    def test_flag_dict_multiple(self):
        i = "HU1 HI1"
        o = {"HU": "1", "HI": "1"}
        self.assertEqual(flag_dict(i), o)

    def test_flag_dict_escaped(self):
        i = "DEcurrent\\stopic"
        o = {"DE": "current topic"}
        self.assertEqual(flag_dict(i), o)
