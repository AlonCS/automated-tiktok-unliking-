from pathlib import Path
import sys
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import tiktok_likes_viewer as viewer


class ViewerTests(unittest.TestCase):
    def exercise(self,states):
        config={'x':100,'y':200}
        with patch.object(viewer.base,'guard'),patch.object(viewer.base,'wait'),patch.object(viewer.base,'state',side_effect=states),patch.object(viewer.base,'xd') as xd:
            result=viewer.run_step(config,3)
            return result,xd.call_args_list

    def test_one_click_for_red_then_gray(self):
        result,calls=self.exercise(['red','red','gray'])
        self.assertEqual(result,'clicked_then_gray')
        self.assertEqual(sum(c.args==('click','1') for c in calls),1)
        self.assertFalse(any(c.args[0]=='key' for c in calls))

    def test_loading_heart_is_relocated(self):
        with patch.object(viewer.base,'guard'),patch.object(viewer.base,'state',side_effect=['unknown','red']),patch.object(viewer.base,'locate_red_heart') as locate:
            self.assertEqual(viewer.viewer_state({'x':100,'y':200}),'red')
            locate.assert_called_once()

    def test_gray_sends_no_click(self):
        result,calls=self.exercise(['gray'])
        self.assertEqual(result,'already_gray')
        self.assertEqual(calls,[])

    def test_unknown_stops(self):
        with patch.object(viewer,'viewer_state',return_value='unknown'):
            with self.assertRaises(RuntimeError):self.exercise([])

    def test_failed_unlike_never_reclicks(self):
        with patch.object(viewer.base,'guard'),patch.object(viewer.base,'wait'),patch.object(viewer.base,'state',side_effect=['red','red','red']),patch.object(viewer.base,'xd') as xd:
            with self.assertRaises(RuntimeError):viewer.run_step({'x':100,'y':200},3)
            self.assertEqual(sum(c.args==('click','1') for c in xd.call_args_list),1)
