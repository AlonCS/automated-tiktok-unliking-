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

Edit `links.txt` to contain full HTTPS TikTok video URLs, one per line. A list of confirmed liked videos gives fewer uncertain states. Blank lines and lines starting with `#` are ignored. Custom `links.txt` files are ignored by Git; the explicitly shared export lists are under `lists/`.

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

`XDG_STATE_HOME` is respected, and `--state-dir` overrides this location. Share code and the included `lists/` files through GitHub; transfer any additional private lists and progress separately. Do not transfer calibration: recalibrate on the other laptop.

To migrate progress from the original home-directory script, copy `~/tiktok_mouse_done.txt` into `~/.local/state/tiktok-mouse-unliker/done.txt` on the other laptop (create the directory first). Transfer the source file privately; it contains your video links. Completed entries match exact URLs, independent of list order. `--start` refers to positions in the list you supply, so a newly exported list may use different positions.

Keep browser profiles, cookies, passwords, additional private lists, progress, screenshots, and calibration out of the repository. Only the explicitly shared export lists under `lists/` are committed. No browser login data is required by this tool.

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

Add your saved-video URLs to `favorites.txt`, one per line. Favorites also accepts the `https://www.tiktokv.com/share/video/.../` URLs found in TikTok TXT exports. Open a saved video in regular Chrome and calibrate on the center of its **yellow bookmark**, then on the address bar:

```bash
.venv/bin/python tiktok_favorites_auto.py --calibrate --limit 1
```

The script clicks a yellow bookmark once, reopens the URL using the calibrated address bar, and records completion only if the bookmark is gray. It stops on an unknown state or failed verification. Color and movement checks have automated coverage. On October 16, 2026, a live one-video test and a five-video turbo batch both passed on Ubuntu/X11: each yellow bookmark was clicked once and confirmed gray after reopening the URL. New laptops and Chrome layouts still require calibration and a small trial.

```bash
# Five-video trial after confirming the first test worked
.venv/bin/python tiktok_favorites_auto.py --turbo --limit 5

# All remaining favorites
.venv/bin/python tiktok_favorites_auto.py --turbo --limit 0
```

Favorites use a separate local state directory, `~/.local/state/tiktok-mouse-unfavoriter/` (or under `XDG_STATE_HOME`), so liked-video progress and calibration are not reused. Do not run the favorites and likes scripts simultaneously: both control the same desktop mouse and clipboard. The same stop controls and fixed-window requirements apply.

### Resume a full favorites run on this laptop

With the export-derived list at `~/favorites.txt` and the repository at `~/Documents/tiktok-mouse-unliker`, the tested system Python command is:

```bash
python3 ~/Documents/tiktok-mouse-unliker/tiktok_favorites_auto.py --links ~/favorites.txt --turbo --limit 0
```

`--limit 0` processes all remaining links, skipping URLs already recorded as complete. Switch to the calibrated Chrome window within five seconds and leave its position, size, and zoom unchanged. Move the pointer to the screen's top-left corner to stop. The script also stops on lost focus, a moved window, unknown bookmark state, or failed verification.

If Chrome was moved or resized, recalibrate and test five videos before resuming the full run:

```bash
python3 ~/Documents/tiktok-mouse-unliker/tiktok_favorites_auto.py --links ~/favorites.txt --calibrate --turbo --limit 5
```

During the first countdown hover at the yellow bookmark's center; during the second hover at the middle of Chrome's address bar. On another laptop, use the repository-relative `.venv/bin/python` commands above after installing dependencies. Use the included `lists/favorites.txt` on another laptop; transfer any additional private list and optional progress file separately.

### Latest local export snapshot — October 16, 2026

The latest supplied export contains **6,402 favorite videos** and **3,671 liked videos**. These are snapshot counts, not live account counts. The previous supplied export contained 6,404 favorites and 6,000 likes.

The extracted lists on the working laptop are:

- `~/favorites.txt`: latest favorite-video links.
- `~/likes-export.txt`: latest liked-video links.
- `~/favorites-recheck.txt`: six videos still listed in the latest export despite existing completed-favorite records. This discrepancy requires checking; the export alone does not establish its cause.

Previous list versions were backed up locally, and progress was preserved. No batch was automatically started when the lists were updated. Both scripts on this branch accept TikTok's `tiktokv.com/share/video/.../` export links. Copies of these three lists are included under `lists/` for use on another laptop; calibration and completion files stay local. Existing completion records still cause matching URLs to be skipped, including the six recheck entries. A recheck needs deliberate inspection rather than assuming a normal resumed run will revisit them.

Use the latest favorites list with:

```bash
python3 ~/Documents/tiktok-mouse-unliker/tiktok_favorites_auto.py --links ~/favorites.txt --turbo --limit 5
```

For the latest liked-video list, use the portable script on this branch:

```bash
python3 ~/Documents/tiktok-mouse-unliker/tiktok_mouse_auto.py --links ~/likes-export.txt --calibrate --turbo --limit 1
```

The portable likes workflow uses `~/.local/state/tiktok-mouse-unliker/`, separate from the original home-directory script's calibration and progress. Follow the migration instructions above before relying on old completion records. Favorites and likes require their own bookmark/heart calibration; do not run them together.

## Download the shared video lists on another laptop

The October 16, 2026 export lists are now intentionally included in this branch:

- [Favorites — 6,402 URLs](lists/favorites.txt)
- [Likes — 3,671 URLs](lists/likes.txt)
- [Favorites to recheck — 6 URLs](lists/favorites-recheck.txt)

These three video-link files are committed; the original ZIP, browser profiles, cookies, calibration, screenshots, and completion files are still excluded.

On the other laptop, clone the branch (or fetch and switch to it in an existing clone), then follow the dependency setup above:

```bash
git clone --branch codex/favorites https://github.com/AlonCS/automated-tiktok-unliking-.git
cd automated-tiktok-unliking-
```

Calibrate and test favorites using the included list:

```bash
.venv/bin/python tiktok_favorites_auto.py --links lists/favorites.txt --calibrate --turbo --limit 1
```

After a successful small trial, process all remaining favorites:

```bash
.venv/bin/python tiktok_favorites_auto.py --links lists/favorites.txt --turbo --limit 0
```

For likes, calibrate separately on a red heart and test one:

```bash
.venv/bin/python tiktok_mouse_auto.py --links lists/likes.txt --calibrate --turbo --limit 1
```

New laptops start with fresh local progress. The included lists represent the export snapshot, so some videos may already be unliked or unfavorited. Do not run both scripts simultaneously.

### Unavailable liked videos

The likes script checks an unknown-heart page for an explicit unavailable-video message by copying the page text through native keyboard input. Confirmed unavailable links are skipped without a heart click and recorded separately in the likes state directory's `unavailable.txt`; normal resumed runs skip them. Remove an entry from that file to retry it later. Generic loading, access errors, and uncertain heart states still stop the run. This text check changes the clipboard; it does not use Playwright.

## Likes viewer mode: heart, then next arrow

`tiktok_likes_viewer.py` works inside the profile Likes video viewer using only calibrated mouse clicks. It does not open list URLs, touch the address bar, or reload the page. Open the viewer manually on a video with a red heart, then run:

```bash
.venv/bin/python tiktok_likes_viewer.py --calibrate --limit 5
```

First calibrate the red heart; then calibrate the lower next-video arrow, each with its own eight-second countdown. Keep the window and layout fixed. After calibration it clicks a red heart once, waits three seconds, checks for gray, and clicks next. Gray hearts are skipped without a heart click; unknown states and failed changes stop the batch. Move the pointer to the screen's top-left corner or change focus to stop between operations.

This mode observes the visible heart only. It does not prove the unlike persisted on TikTok's server or prove that the next arrow advanced to a different video. Confirm the first batch on your phone before increasing the batch size. It keeps observations separately under `~/.local/state/tiktok-likes-viewer/` and does not mark URL-list entries as verified complete. Tests cover click counts and stop behavior; a live trial is required for the new viewer layout.

To run another bounded batch without recalibrating:

```bash
.venv/bin/python tiktok_likes_viewer.py --limit 5
```
