import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch
from PIL import Image, ImageDraw

spec=importlib.util.spec_from_file_location('favorites',Path(__file__).resolve().parents[1]/'tiktok_favorites_auto.py')
favorites=importlib.util.module_from_spec(spec)
spec.loader.exec_module(favorites)


def bookmark(color):
    image=Image.new('RGB',(25,25),(220,220,220))
    ImageDraw.Draw(image).polygon([(5,3),(19,3),(19,22),(12,17),(5,22)],fill=color)
    return image


class FavoritesTests(unittest.TestCase):
    def setUp(self):
        self.template=bookmark((250,206,21))
        self.mask=[[x,y] for y in range(25) for x in range(25) if favorites.yellow(self.template.getpixel((x,y)))]

    def test_saved_unsaved_unknown_and_red(self):
        self.assertEqual(favorites.classify(self.template,self.mask),'yellow')
        self.assertEqual(favorites.classify(bookmark((22,24,35)),self.mask),'gray')
        self.assertEqual(favorites.classify(bookmark((254,44,85)),self.mask),'unknown')
        self.assertEqual(favorites.classify(Image.new('RGB',(25,25),'white'),self.mask),'unknown')

    def test_moved_yellow_bookmark(self):
        screen=Image.new('RGB',(600,800),'white')
        screen.paste(self.template,(320-12,400-12))
        config={'x':280,'y':550,'mask':self.mask}
        with patch.object(favorites,'guard'),patch.object(favorites.ImageGrab,'grab',return_value=screen):
            self.assertTrue(favorites.locate_yellow_bookmark(config))
        self.assertEqual((config['x'],config['y']),(320,400))

    def test_separate_state(self):
        self.assertEqual(favorites.ROOT.name,'tiktok-mouse-unfavoriter')


if __name__=='__main__':
    unittest.main()
