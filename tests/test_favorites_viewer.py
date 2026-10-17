from pathlib import Path
import sys
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import tiktok_favorites_viewer as viewer


class FavoritesViewerTests(unittest.TestCase):
    def exercise(self,states):
        config={'x':100,'y':200}
        with patch.object(viewer.base,'guard'),patch.object(viewer.base,'wait'),patch.object(viewer,'confirm_gray',return_value=True),patch.object(viewer.base,'state',side_effect=states),patch.object(viewer.base,'xd') as xd:
            result=viewer.run_step(config,3)
            return result,xd.call_args_list

    def test_one_click_with_postclick_confirmation(self):
        result,calls=self.exercise(['yellow','yellow','gray'])
        self.assertEqual(result,'clicked_then_gray')
        self.assertEqual(sum(c.args==('click','1') for c in calls),1)
        self.assertFalse(any(c.args[0]=='key' for c in calls))

    def test_loading_heart_is_relocated(self):
        with patch.object(viewer.base,'guard'),patch.object(viewer.base,'state',side_effect=['unknown','yellow']),patch.object(viewer.base,'locate_yellow_bookmark') as locate:
            self.assertEqual(viewer.viewer_state({'x':100,'y':200}),'yellow')
            locate.assert_called_once()

    def test_gray_sends_no_click(self):
        result,calls=self.exercise(['gray'])
        self.assertEqual(result,'already_gray')
        self.assertEqual(calls,[])

    def test_unknown_stops(self):
        with patch.object(viewer,'viewer_state',return_value='unknown'):
            with self.assertRaises(RuntimeError):self.exercise([])

    def test_failed_confirmation_stops_without_second_click(self):
        with patch.object(viewer.base,'guard'),patch.object(viewer.base,'wait'),patch.object(viewer,'confirm_gray',return_value=False),patch.object(viewer.base,'state',side_effect=['yellow','yellow']),patch.object(viewer.base,'xd') as xd:
            with self.assertRaises(RuntimeError):
                viewer.run_step({'x':100,'y':200},.5)
            self.assertEqual(sum(c.args==('click','1') for c in xd.call_args_list),1)

    def test_confirmation_needs_two_gray_readings(self):
        with patch.object(viewer.base,'guard'),patch.object(viewer.base,'patch'),patch.object(viewer.base,'classify',side_effect=['yellow','gray','gray']),patch.object(viewer.base,'wait') as wait:
            self.assertTrue(viewer.confirm_gray({'x':100,'y':200,'mask':[]},.5))
            self.assertEqual(wait.call_count,2)
