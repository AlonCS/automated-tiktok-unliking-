#!/usr/bin/env python3
"""Unlike in the profile's video viewer using native heart and next-arrow clicks."""
import argparse
import fcntl
import json
import itertools
import os
from pathlib import Path
import subprocess
import time
import tiktok_mouse_auto as base

ROOT=Path(os.environ.get('XDG_STATE_HOME',str(Path.home()/'.local/state')))/'tiktok-likes-viewer'


def capture_point(label):
    input(f'Press Enter, then hover over {label} during the eight-second countdown: ')
    for n in range(8,0,-1):
        print(f'Capturing {label} in {n}...',flush=True)
        time.sleep(1)
    point=base.location()
    return point['WINDOW'],int(point['X']),int(point['Y'])


def viewer_state(config):
    # A new video can hydrate slowly or shift the action controls.
    for attempt in range(6):
        base.guard(config)
        current=base.state(config)
        if current != 'unknown':
            return current
        base.locate_red_heart(config)
        current=base.state(config)
        if current != 'unknown':
            return current
        if attempt < 5:
            print('Waiting for the next video heart...',flush=True)
            base.wait(1,config)
    return 'unknown'


def run_step(config,delay):
    base.guard(config)
    current=viewer_state(config)
    if current=='unknown':
        raise RuntimeError('Heart is uncertain. Stopped without clicking or advancing.')
    if current=='red':
        base.guard(config)
        if base.state(config)!='red':
            raise RuntimeError('Heart changed before click; stopped.')
        base.xd('mousemove',config['x'],config['y'])
        base.xd('click','1')
        base.xd('mousemove',config['x']+40,config['y'])
        base.wait(delay,config)
        if base.state(config)!='gray':
            raise RuntimeError('Unlike did not remain gray. No second heart click sent.')
        print('One unlike click; heart observed gray. Persistence is not verified by reload.',flush=True)
        return 'clicked_then_gray'
    print('Heart already gray; no heart click sent.',flush=True)
    return 'already_gray'


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--calibrate',action='store_true')
    parser.add_argument('--limit',type=int,default=5,help='Number of videos; 0 continues until stopped.')
    parser.add_argument('--delay',type=float,default=3,help='Wait after a heart click and after advancing (minimum 2 seconds).')
    args=parser.parse_args()
    if args.limit<0 or args.delay<2:parser.error('Use a nonnegative limit and a delay of at least 2 seconds.')
    if os.environ.get('XDG_SESSION_TYPE')!='x11':parser.error('Requires Ubuntu on Xorg/X11.')
    ROOT.mkdir(parents=True,exist_ok=True)
    lock=(ROOT/'run.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    config_path=ROOT/'calibration.json'
    if args.calibrate or not config_path.exists():
        print('Open your profile Likes viewer on a video with a RED heart. Keep Chrome fixed.',flush=True)
        window,x,y=capture_point('the CENTER of the RED heart')
        cls=subprocess.check_output(['xprop','-id',window,'WM_CLASS'],text=True).lower()
        if 'google-chrome' not in cls:raise RuntimeError('Heart must be in regular Google Chrome.')
        base.xd('windowactivate','--sync',window)
        im=base.patch(x,y)
        mask=[[px,py] for py in range(25) for px in range(25) if base.red(im.getpixel((px,py)))]
        if not 40<=len(mask)<=450:raise RuntimeError('No clear red heart. Calibration cancelled.')
        config={'window':window,'geometry':base.geometry(window),'x':x,'y':y,'mask':mask}
        other,nx,ny=capture_point('the LOWER next-video arrow')
        if other!=window:raise RuntimeError('Both controls must be in the same Chrome window.')
        if abs(nx-x)<25 and abs(ny-y)<25:raise RuntimeError('Next arrow overlaps heart; recalibrate.')
        config.update(next_x=nx,next_y=ny)
        base.xd('windowactivate','--sync',window)
        config_path.write_text(json.dumps(config))
    else:
        config=json.loads(config_path.read_text())
        print('Switch to the calibrated Chrome viewer within five seconds.',flush=True);time.sleep(5)
    config['turbo']=True
    base.xd('mousemove',config['x']+40,config['y'])
    for i in (itertools.count() if args.limit == 0 else range(args.limit)):
        print(f'Video {i+1}' + (f'/{args.limit}' if args.limit else ' (continuous)'),flush=True)
        result=run_step(config,args.delay)
        with (ROOT/'observations.jsonl').open('a') as out:
            out.write(json.dumps({'time':time.time(),'result':result,'saved_state_verified':False})+'\n')
        if args.limit == 0 or i+1<args.limit:
            base.guard(config)
            base.xd('mousemove',config['next_x'],config['next_y'])
            base.xd('click','1')
            base.xd('mousemove',config['x']+40,config['y'])
            base.wait(args.delay,config)
    print('Batch finished. Verify saved results on your iPhone.',flush=True)


if __name__=='__main__':
    try:main()
    except (KeyboardInterrupt,RuntimeError,OSError,subprocess.CalledProcessError) as exc:
        print(f'\nSTOPPED: {exc}',flush=True)
        raise SystemExit(1)
