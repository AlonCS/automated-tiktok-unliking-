#!/usr/bin/env python3
"""Scroll a TikTok profile grid until its copied page text stops changing."""
import argparse
import hashlib
import os
from pathlib import Path
import subprocess
import time
import tkinter as tk

import tiktok_mouse_auto as base


def fingerprint(text):
    return hashlib.sha256(' '.join(text.split()).encode()).hexdigest()


def read_page_text(clipboard,config):
    base.guard(config)
    sentinel='tiktok-grid-loader-pending'
    clipboard.clipboard_clear()
    clipboard.clipboard_append(sentinel)
    clipboard.update()
    base.xd('key','--clearmodifiers','ctrl+a')
    base.xd('key','--clearmodifiers','ctrl+c')
    for _ in range(20):
        clipboard.update()
        time.sleep(.05)
        try:text=clipboard.clipboard_get()
        except tk.TclError:continue
        if text!=sentinel and text.strip():
            base.xd('key','Right')
            return text
    base.xd('key','Escape')
    raise RuntimeError('Could not copy page text. Click an empty part of the profile grid and restart.')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--interval',type=float,default=2,help='Seconds to allow each scroll to load (minimum 1).')
    parser.add_argument('--stable',type=int,default=8,help='Consecutive unchanged checks before stopping (minimum 3).')
    parser.add_argument('--max-scrolls',type=int,default=2000)
    args=parser.parse_args()
    if args.interval<1 or args.stable<3 or args.max_scrolls<1:parser.error('Invalid interval, stable count, or max-scrolls.')
    if os.environ.get('XDG_SESSION_TYPE')!='x11':parser.error('Requires Ubuntu on Xorg/X11.')
    print('Open your profile Likes or Favorites GRID, not a video. Click empty page space to focus it.',flush=True)
    print('Switch to regular Chrome within 8 seconds. No video or bookmark clicks will be sent.',flush=True)
    time.sleep(8)
    window=base.xd('getactivewindow')
    cls=subprocess.check_output(['xprop','-id',window,'WM_CLASS'],text=True).lower()
    if 'google-chrome' not in cls:raise RuntimeError('Regular Chrome must be active.')
    config={'window':window,'geometry':base.geometry(window)}
    clipboard=tk.Tk();clipboard.withdraw()
    previous=None;unchanged=0
    try:
        for n in range(1,args.max_scrolls+1):
            base.guard(config)
            base.xd('key','--clearmodifiers','ctrl+End')
            base.wait(args.interval,config)
            text=read_page_text(clipboard,config)
            lowered=' '.join(text.lower().split())
            if any(message in lowered for message in ('oops! something went wrong','access denied','verify to continue','too many requests')):
                raise RuntimeError('Page error or verification message detected; stopped.')
            current=fingerprint(text)
            unchanged=unchanged+1 if current==previous else 0
            previous=current
            print(f'Scroll {n}: {len(text):,} page-text characters; unchanged {unchanged}/{args.stable}.',flush=True)
            if unchanged>=args.stable:
                print('Page stopped growing. Loader stopped at the bottom; scroll back up and calibrate.',flush=True)
                print('This is a loading heuristic, not proof that every video is loaded; TikTok may virtualize its grid.',flush=True)
                return
        print('Maximum scroll count reached; stopped. Full loading is not confirmed.',flush=True)
    finally:
        clipboard.destroy()


if __name__=='__main__':
    try:main()
    except (KeyboardInterrupt,RuntimeError,OSError,subprocess.CalledProcessError) as exc:
        print(f'\nSTOPPED: {exc}',flush=True)
        raise SystemExit(1)
