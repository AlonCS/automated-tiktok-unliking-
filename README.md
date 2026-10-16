# TikTok mouse unliker

An Ubuntu/X11 desktop script that opens TikTok video links in regular Google Chrome, locates a calibrated red heart in a screenshot, sends one native mouse click, and reopens the URL through the address bar to verify the heart is gray. It uses `xdotool`, screenshots, and clipboard paste; it does not use Playwright.

This is a screen-position-dependent personal utility. Keep Chrome focused and its position, size, zoom, display scaling, and layout unchanged during a run. Unknown heart states, lost focus, moved windows, and failed verification stop the run. A stopped verification can be a false negative: check that video manually before retrying. The tool does not bypass TikTok error pages or CAPTCHA challenges.

## Set up the other Ubuntu laptop

1. Use an **X11** desktop session. `echo "$XDG_SESSION_TYPE"` must print `x11`. If necessary, sign out and select **Ubuntu on Xorg** on the login screen.
2. Install regular Google Chrome from its official source and sign in to TikTok normally.
3. Install the desktop and Python dependencies:

```bash
sudo apt update
sudo apt install git python3-venv python3-tk xdotool x11-utils gnome-screenshot
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

Run these commands from the cloned repository directory. `gnome-screenshot` provides a screenshot fallback on Ubuntu; the script also uses Pillow's X11 screenshot support.

## Supply your list

```bash
cp links.example.txt links.txt
```

Edit `links.txt` to contain full HTTPS TikTok video URLs, one per line. A list of confirmed liked videos gives fewer uncertain states. Blank lines and lines starting with `#` are ignored. Personal links are ignored by Git.

## Calibrate and test one video

Open a TikTok video whose heart is red in your regular Chrome window. Keep that window at its intended position, size, and zoom.

```bash
.venv/bin/python tiktok_mouse_auto.py --links links.txt --calibrate --limit 1
```

Press Enter in the terminal, then hover over the center of the red heart during the first eight-second countdown. During the second countdown, hover over the middle of Chrome's address bar. The script then starts the trial. A calibration belongs to that laptop and Chrome window; recalibrate after moving/resizing or reopening the window.

## Continue

```bash
# Five-video trial with shorter waits
.venv/bin/python tiktok_mouse_auto.py --links links.txt --turbo --limit 5

# All remaining links, skipping completed URLs
.venv/bin/python tiktok_mouse_auto.py --links links.txt --turbo --limit 0

# Start at a particular position in this exact list
.venv/bin/python tiktok_mouse_auto.py --links links.txt --turbo --start 3040 --limit 25
```

Switch to the calibrated Chrome window within five seconds of starting a run. `--fast` is an intermediate speed; omitting both speed flags gives longer waits. Turbo may stop more often on slow pages. It still verifies each result after reopening the URL and never automatically sends a second click to retry a failed verification.

**Stop:** move the pointer to the physical screen's top-left corner, switch focus away from Chrome, or press Ctrl+C in the terminal. Stop checks happen between operations, so these are not instantaneous interrupt guarantees. Do not use the laptop for other work during a run.

## Progress and moving between laptops

Calibration, screenshot crops, lock, and completed URLs live locally under:

```text
~/.local/state/tiktok-mouse-unliker/
```

`XDG_STATE_HOME` is respected, and `--state-dir` overrides this location. Share code through GitHub; transfer the private list and progress separately. Do not transfer calibration: recalibrate on the other laptop.

To migrate progress from the original home-directory script, copy `~/tiktok_mouse_done.txt` into `~/.local/state/tiktok-mouse-unliker/done.txt` on the other laptop (create the directory first). Transfer the source file privately; it contains your video links. Completed entries match exact URLs, independent of list order. `--start` refers to positions in the list you supply, so a newly exported list may use different positions.

Keep browser profiles, cookies, passwords, personal lists, progress, screenshots, and calibration out of the repository. No browser login data is required by this tool.

## Checks

```bash
.venv/bin/python -m unittest discover -s tests -v
```

These tests exercise image matching, color classification, and link validation without opening a browser or sending clicks. Live behavior still depends on the desktop layout and TikTok UI.

## Favorites branch: remove saved videos

The `codex/favorites` branch adds `tiktok_favorites_auto.py`. It targets the **yellow bookmark**, not the red heart. The unliker script remains available unchanged.

After cloning, switch to this branch:

```bash
git fetch origin
git switch codex/favorites
cp favorites.example.txt favorites.txt
```

Add your saved-video URLs to `favorites.txt`, one per line. Open a saved video in regular Chrome and calibrate on the center of its **yellow bookmark**, then on the address bar:

```bash
.venv/bin/python tiktok_favorites_auto.py --calibrate --limit 1
```

The script clicks a yellow bookmark once, reopens the URL using the calibrated address bar, and records completion only if the bookmark is gray. It stops on an unknown state or failed verification. Color and movement checks have automated coverage; the favorites script still needs a one-video live trial before a long run.

```bash
# Five-video trial after confirming the first test worked
.venv/bin/python tiktok_favorites_auto.py --turbo --limit 5

# All remaining favorites
.venv/bin/python tiktok_favorites_auto.py --turbo --limit 0
```

Favorites use a separate local state directory, `~/.local/state/tiktok-mouse-unfavoriter/` (or under `XDG_STATE_HOME`), so liked-video progress and calibration are not reused. Do not run the favorites and likes scripts simultaneously: both control the same desktop mouse and clipboard. The same stop controls and fixed-window requirements apply.
