import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from PIL import Image, ImageDraw

spec = importlib.util.spec_from_file_location('mouse', Path(__file__).resolve().parents[1] / 'tiktok_mouse_auto.py')
mouse = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mouse)


def heart(color=(254, 44, 85)):
    image = Image.new('RGB', (25, 25), (220, 220, 220))
    ImageDraw.Draw(image).polygon([(4,5),(9,3),(12,6),(16,3),(21,5),(22,10),(12,22),(2,10)], fill=color)
    return image


class CoreTests(unittest.TestCase):
    def test_red_gray_and_blank(self):
        template = heart()
        mask = [[x,y] for y in range(25) for x in range(25) if mouse.red(template.getpixel((x,y))) ]
        self.assertEqual(mouse.classify(template, mask), 'red')
        self.assertEqual(mouse.classify(heart((22,24,35)), mask), 'gray')
        self.assertEqual(mouse.classify(Image.new('RGB',(25,25),(220,220,220)),mask), 'unknown')

    def test_shifted_off_center_heart(self):
        template = heart()
        # Deliberately offset the shape to model imperfect pointer calibration.
        shifted = Image.new('RGB',(25,25),(220,220,220))
        shifted.paste(template,(-4,0))
        mask = [[x,y] for y in range(25) for x in range(25) if mouse.red(shifted.getpixel((x,y)))]
        screen = Image.new('RGB',(600,800),'white')
        screen.paste(shifted,(316-12,450-12))
        config = {'x':280,'y':600,'mask':mask}
        with patch.object(mouse,'guard'), patch.object(mouse.ImageGrab,'grab',return_value=screen):
            self.assertTrue(mouse.locate_red_heart(config))
        self.assertEqual((config['x'],config['y']),(316,450))

    def test_links_accept_comments_reject_other_sites(self):
        with tempfile.TemporaryDirectory() as directory:
            source=Path(directory)/'links.txt'
            source.write_text('# comment\n\nhttps://www.tiktok.com/@example/video/123\n')
            self.assertEqual(len(mouse.read_links(source)),1)
            source.write_text('https://www.tiktokv.com/share/video/123/\n')
            self.assertEqual(len(mouse.read_links(source)),1)
            source.write_text('https://example.com/video/123\n')
            with self.assertRaises(RuntimeError):
                mouse.read_links(source)


if __name__ == '__main__':
    unittest.main()
