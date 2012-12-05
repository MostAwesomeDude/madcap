from unittest import TestCase

from madcap.utilities import b32d, b32e


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
