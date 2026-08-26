#!/usr/bin/env python3
"""The filmed pieces, and how their video is presented.

One place, because both the interview page and the home page show the same
thumbnail and must agree on where it points.

`youtube` is the video id. Until a real one is supplied the panel is drawn as
a placeholder — a dark 16:9 frame with a play badge — so the layout can be
judged without a photograph standing in for a video that is not there. Set
`youtube` and the panel switches to YouTube's own still, downloaded into
assets/img/ by `fetch_thumb` so the page carries no external dependency.
"""

import os
import subprocess
import urllib.request

import paths as P

THUMB_DIR = 'assets/img/video'

VIDEOS = {
    'interview-with-sikyong-penpa-tsering': dict(
        youtube='',        # <- the video id goes here
        caption='Sikyong Penpa Tsering in conversation at the India '
                'International Centre, New Delhi.',
    ),
}


def has(slug):
    return slug in VIDEOS


def watch_url(slug):
    """Where the play badge sends a reader."""
    vid = VIDEOS.get(slug, {}).get('youtube')
    return f'https://www.youtube.com/watch?v={vid}' if vid else 'https://www.youtube.com/'


def thumb(slug):
    """The local path of the downloaded still, or '' while there is no video."""
    vid = VIDEOS.get(slug, {}).get('youtube')
    if not vid:
        return ''
    path = f'{THUMB_DIR}/{slug}.jpg'
    return path if os.path.exists(path) else ''


def fetch_thumb(slug):
    """Download YouTube's still once, and size it to 1280x720."""
    vid = VIDEOS.get(slug, {}).get('youtube')
    if not vid:
        return ''
    os.makedirs(THUMB_DIR, exist_ok=True)
    path = f'{THUMB_DIR}/{slug}.jpg'
    if os.path.exists(path):
        return path
    for name in ('maxresdefault', 'hqdefault'):
        url = f'https://i.ytimg.com/vi/{vid}/{name}.jpg'
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=20) as r, open('/tmp/_yt', 'wb') as fh:
                fh.write(r.read())
        except Exception as e:
            print(f'    ! {name} for {slug}: {e}')
            continue
        subprocess.run(['magick', '/tmp/_yt', '-resize', '1280x720^',
                        '-gravity', 'center', '-extent', '1280x720',
                        '-strip', '-quality', '82', path], capture_output=True)
        if os.path.exists(path):
            return path
    return ''


def panel(slug, cls='art-video', caption=True):
    """The video, as a link carrying a play badge over its still.

    With no still to show, the same markup is drawn as an empty frame: the
    badge and the proportions are what matter for judging the layout.
    """
    if slug not in VIDEOS:
        return ''
    v = VIDEOS[slug]
    img = thumb(slug)
    inner = (f'<img src="{P.asset(img)}" alt="" width="1280" height="720">'
             if img else '')
    cap = ''
    if caption and v.get('caption'):
        from build_issue import esc
        cap = f'\n          <figcaption>{esc(v["caption"])}</figcaption>'
    frame = 'frame' if not img else ''
    return (f'        <figure class="{cls}">\n'
            f'          <a class="play {frame}" href="{watch_url(slug)}" '
            f'target="_blank" rel="noopener" aria-label="Watch on YouTube">'
            f'{inner}<span class="badge" aria-hidden="true"></span></a>{cap}\n'
            f'        </figure>\n')
