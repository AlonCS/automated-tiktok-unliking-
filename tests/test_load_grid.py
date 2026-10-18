from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import tiktok_load_grid as grid


class GridTests(unittest.TestCase):
    def test_whitespace_does_not_count_as_growth(self):
        self.assertEqual(grid.fingerprint('video 1\n\nvideo 2'),grid.fingerprint(' video 1 video 2 '))

    def test_same_length_changed_tiles_are_detected(self):
        self.assertNotEqual(grid.fingerprint('video 1 video 2'),grid.fingerprint('video 3 video 4'))
