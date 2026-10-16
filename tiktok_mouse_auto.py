#!/usr/bin/env python3
"""Regular Chrome + native X11 input. Calibrate once on a RED heart."""
import argparse
import fcntl
import json
from pathlib import Path
import subprocess
import time
import os
from urllib.parse import urlsplit
from scipy.signal import fftconvolve
import numpy as np
import tkinter as tk

CLIPBOARD = None
from PIL import ImageGrab

ROOT = Path(os.environ.get('XDG_STATE_HOME', str(Path.home() / '.local/state'))) / 'tiktok-mouse-unliker'
CONFIG = ROOT / '.tiktok_mouse_calibration.json'
DONE = ROOT / 'tiktok_mouse_done.txt'

def xd(*args):
    return subprocess.check_output(['xdotool', *map(str, args)], text=True).strip()

def location():
    return dict(line.split('=', 1) for line in xd('getmouselocation', '--shell').splitlines())

def geometry(window):
    return xd('getwindowgeometry', '--shell', window)

def red(rgb):
    r,g,b = rgb[:3]
    return r > 180 and r-g > 75 and r-b > 45

def patch(x,y):
    return ImageGrab.grab(bbox=(x-12,y-12,x+13,y+13)).convert('RGB')

def classify(im, mask):
    pixels=[im.getpixel(tuple(point)) for point in mask]
    fraction=sum(red(p) for p in pixels)/len(pixels)
    if fraction >= .9:
        return 'red'
    # A solid neutral heart in the calibrated silhouette is required for gray.
    neutral=sum(max(p)-min(p) < 35 for p in pixels)/len(pixels)
    brightness=[sum(p)/3 for p in pixels]
    background=[sum(im.getpixel(p))/3 for p in ((0,0),(24,0),(0,24),(24,24))]
    contrast=abs(sum(brightness)/len(brightness)-sum(background)/4)
    if fraction < .03 and neutral >= .9 and contrast > 45 and max(brightness)-min(brightness) < 65:
        return 'gray'
    return 'unknown'

def guard(config):
    if geometry(config['window']) != config['geometry']:
        raise RuntimeError('Chrome moved or resized. Recalibrate before continuing.')
    if xd('getactivewindow') != config['window']:
        raise RuntimeError('Chrome lost focus. Stopped without another click.')
    pos=location()
    if int(pos['X']) < 5 and int(pos['Y']) < 5:
        raise RuntimeError('Emergency stop: pointer in top-left corner.')

def wait(seconds, config):
    for _ in range(int(seconds*5)):
        guard(config)
        time.sleep(.2)

def state(config):
    readings=[]
    for _ in range(3):
        guard(config)
        readings.append(classify(patch(config['x'],config['y']),config['mask']))
        time.sleep(.15 if config.get('turbo') else .4)
    return readings[0] if len(set(readings)) == 1 else 'unknown'

def navigate(config,url):
    global CLIPBOARD
    guard(config)
    if CLIPBOARD is None:
        CLIPBOARD = tk.Tk()
        CLIPBOARD.withdraw()
    CLIPBOARD.clipboard_clear()
    CLIPBOARD.clipboard_append(url)
    CLIPBOARD.update()
    xd('mousemove',config['address_x'],config['address_y'])
    xd('click','1')
    xd('key','--clearmodifiers','ctrl+a')
    xd('key','--clearmodifiers','ctrl+v')
    # Service X11 clipboard requests while Chrome reads the pasted URL.
    for _ in range(10):
        CLIPBOARD.update()
        time.sleep(.05)
    xd('key','Return')
    xd('mousemove',config['x']+60,config['y'])
    wait(1.6 if config.get("turbo") else (3 if config.get("fast") else 10),config)


def locate_red_heart(config):
    """Match the calibrated silhouette, even if the pointer was off-center."""
    guard(config)
    screen = np.asarray(ImageGrab.grab().convert('RGB')).astype(np.int16)
    redmap = (screen[:,:,0] > 180) & (screen[:,:,0]-screen[:,:,1] > 75) & (screen[:,:,0]-screen[:,:,2] > 45)
    mask = np.zeros((25,25),dtype=bool)
    for px,py in config['mask']:
        mask[py,px]=True
    left=max(12,config['x']-80)
    right=min(screen.shape[1]-13,config['x']+81)
    top=max(12,config['y']-500)
    bottom=min(screen.shape[0]-13,config['y']+501)
    # Compute all silhouette matches together instead of Python pixel loops.
    region=redmap[top-12:bottom+12,left-12:right+12].astype(float)
    intersection=np.rint(fftconvolve(region,mask[::-1,::-1].astype(float),mode='valid'))
    totals=np.rint(fftconvolve(region,np.ones((25,25)),mode='valid'))
    union=np.maximum(1,totals+np.count_nonzero(mask)-intersection)
    scores=intersection/union
    by,bx=np.unravel_index(np.argmax(scores),scores.shape)
    best=(scores[by,bx],left+int(bx),top+int(by)) if scores[by,bx]>=.9 else None
    if best:
        config['x'],config['y']=best[1],best[2]
        print(f'Located calibrated red heart at {best[1]}, {best[2]}.',flush=True)
        return True
    return False


def read_links(path):
    links = []
    for line in path.read_text().splitlines():
        link = line.strip()
        if not link or link.startswith('#'):
            continue
        parsed = urlsplit(link)
        if parsed.scheme != 'https' or parsed.hostname not in ('www.tiktok.com', 'tiktok.com') or '/video/' not in parsed.path:
            raise RuntimeError('Each nonempty line must be a full HTTPS TikTok video URL.')
        links.append(link)
    return links


def main():
    global ROOT, CONFIG, DONE
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--turbo',action='store_true',help='Shortest waits, with extra time if verification is uncertain.')
    parser.add_argument('--fast',action='store_true',help='Shorter waits, retaining saved-state verification.')
    parser.add_argument('--calibrate',action='store_true')
    parser.add_argument('--links',type=Path,default=Path('links.txt'),help='TXT file with one full TikTok video URL per line.')
    parser.add_argument('--state-dir',type=Path,default=ROOT,help='Private local calibration and progress directory.')
    parser.add_argument('--start',type=int,default=1,help='First list position, counting from 1.')
    parser.add_argument('--limit',type=int,default=5,help='Maximum new videos; 0 means all remaining links.')
    args=parser.parse_args()
    args.fast = args.fast or args.turbo
    if os.environ.get('XDG_SESSION_TYPE') != 'x11':
        parser.error('Use an X11 session (Ubuntu on Xorg), not Wayland.')
    ROOT = args.state_dir.expanduser().resolve()
    ROOT.mkdir(parents=True, exist_ok=True)
    CONFIG = ROOT / 'calibration.json'
    DONE = ROOT / 'done.txt'
    lock=(ROOT/'run.lock').open('a')
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    links=read_links(args.links.expanduser())
    if not 1 <= args.start <= len(links) or args.limit < 0:
        parser.error('Invalid start or limit')
    if args.calibrate or not CONFIG.exists():
        input('Open a TikTok video with a RED heart in Chrome. Press Enter, then hover at the CENTER of the heart within 8 seconds: ')
        for n in range(8,0,-1):
            print(f'Calibrating in {n}...',flush=True);time.sleep(1)
        pos=location();window=pos['WINDOW']
        cls=subprocess.check_output(['xprop','-id',window,'WM_CLASS'],text=True).lower()
        if 'google-chrome' not in cls:
            raise RuntimeError('Pointer must be over regular Google Chrome.')
        xd('windowactivate','--sync',window)
        x,y=int(pos['X']),int(pos['Y'])
        im=patch(x,y)
        mask=[[px,py] for py in range(25) for px in range(25) if red(im.getpixel((px,py))) ]
        if not 40 <= len(mask) <= 450:
            raise RuntimeError('No clear red heart at pointer. Calibration cancelled.')
        config={'window':window,'geometry':geometry(window),'x':x,'y':y,'mask':mask}
        im.save(ROOT/'tiktok_heart_calibration.png')
        print('Heart captured. Now move the pointer to the MIDDLE of Chrome address bar within 8 seconds.',flush=True)
        for n in range(8,0,-1):
            print(f'Address bar calibration in {n}...',flush=True);time.sleep(1)
        address=location()
        if address['WINDOW'] != window:
            raise RuntimeError('Address bar must be in the same Chrome window.')
        config['address_x'],config['address_y']=int(address['X']),int(address['Y'])
        CONFIG.write_text(json.dumps(config))
    else:
        config=json.loads(CONFIG.read_text())
        if 'address_x' not in config:
            raise RuntimeError('Run again with --calibrate to capture the address bar position.')
        print('Switch to the calibrated Chrome window within 5 seconds.',flush=True);time.sleep(5)
    config['turbo']=args.turbo
    config['fast']=args.fast
    xd('mousemove',config['x']+60,config['y'])
    done=set(DONE.read_text().splitlines()) if DONE.exists() else set()
    selected=[]
    seen=set(done)
    for n,link in enumerate(links,1):
        if n>=args.start and link not in seen:
            selected.append((n,link))
            seen.add(link)
    if args.limit:
        selected=selected[:args.limit]
    for num,link in selected:
        print(f'Opening #{num}: {link}',flush=True)
        navigate(config,link)
        locate_red_heart(config)
        initial=state(config)
        if args.fast and initial == 'unknown':
            for _ in range(3):
                wait(1 if args.turbo else 2,config)
                locate_red_heart(config)
                initial=state(config)
                if initial != 'unknown':
                    break
        print(f'Heart: {initial}',flush=True)
        if initial == 'unknown':
            patch(config['x'],config['y']).save(ROOT/'tiktok_heart_unknown.png')
            raise RuntimeError('Cannot identify the heart. No click sent.')
        if initial == 'red':
            guard(config)
            if state(config) != 'red':
                raise RuntimeError('Heart changed before click. Stopped.')
            xd('mousemove',config['x'],config['y'])
            xd('click','1')
            xd('mousemove',config['x']+60,config['y'])
            print('Sent one click.',flush=True)
            wait(1.6 if args.turbo else (3 if args.fast else 10),config)
        print('Reopening the same URL using address-bar mouse click and paste...',flush=True)
        navigate(config,link)
        verified=state(config)
        if args.fast and verified != 'gray':
            wait(5,config)
            verified=state(config)
        if verified != 'gray':
            raise RuntimeError('Unlike not confirmed after refresh. No retry click sent.')
        with DONE.open('a') as out:
            out.write(link+'\n')
        print('Confirmed gray after refresh; recorded done.',flush=True)
        wait(.4 if args.turbo else (1 if args.fast else 3),config)
    print('Run finished.',flush=True)

if __name__ == '__main__':
    try:
        main()
    except (KeyboardInterrupt,RuntimeError,OSError,subprocess.CalledProcessError,BlockingIOError) as exc:
        print(f'\nSTOPPED: {exc}',flush=True)
        raise SystemExit(1)
