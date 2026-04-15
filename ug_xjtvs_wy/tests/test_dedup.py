import unittest

from ug_xjtvs_wy.dedup import Deduplicator


class TestDedup(unittest.TestCase):
    def test_url_and_text_and_near(self):
        d = Deduplicator(near_duplicate_hamming_distance=24)
        t1 = "بۇ بىر خەۋەر تېكىستى بولۇپ نۇمۇنىۋى جۈملىلەرنى ئۆز ئىچىگە ئالىدۇ"
        t2 = "بۇ بىر خەۋەر تېكىستى بولۇپ نۇمۇنىۋى جۈملىلەرنى ئۆز ئىچىگە ئالىدۇ"
        t3 = "بۇ بىر خەۋەر تېكىستى بولۇپ نۇمۇنىۋى جۈملىلەرنى ئۆز ئىچىگە ئالىدۇ ۋە ئازراق ئۆزگەرگەن"

        self.assertTrue(d.check("https://a.com/1", t1).keep)
        self.assertFalse(d.check("https://a.com/1", t1).keep)
        self.assertFalse(d.check("https://a.com/2", t2).keep)
        self.assertFalse(d.check("https://a.com/3", t3).keep)
