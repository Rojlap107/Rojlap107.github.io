#!/usr/bin/env python3
"""Assemble the site: content/ + templates/ -> the served pages.

Every page is content (unique) wrapped in chrome (shared). The chrome comes
from templates/partials/, so changing the masthead, the navigation or the
footer is a single edit to a single file, and this rebuild propagates it to
all ~90 pages.

    python3 tools/build.py                  # build everything
    python3 tools/build.py --only about     # one page, by slug or type
    python3 tools/build.py --clean          # remove built pages first

Run from the site root.
"""

import argparse, glob, hashlib, json, os, shutil, subprocess, sys
import paths as P
import render as R
import sections as S


def load_manifest():
    return json.load(open('content/manifest.json', encoding='utf-8'))


def asset_version():
    """A short digest of every stylesheet and script.

    Appended to their URLs so that changing one is enough — a browser holding
    the previous copy fetches the new one instead of showing stale styling,
    which is otherwise indistinguishable from the change not having worked.
    """
    h = hashlib.sha256()
    for f in sorted(glob.glob('assets/css/*.css') + glob.glob('assets/js/*.js')):
        h.update(open(f, 'rb').read())
    return h.hexdigest()[:8]


# what a share card shows for a page with no picture of its own
DEFAULT_SHARE_IMAGE = 'assets/img/hero-bg.jpg'
SUFFIX = ' — TransHimalaya'
_dims = {}


def image_size(path):
    """(width, height) of a local image, measured once per file."""
    if path not in _dims:
        out = subprocess.run(['magick', 'identify', '-format', '%w %h', path],
                             capture_output=True, text=True).stdout.split()
        _dims[path] = tuple(out[:2]) if len(out) >= 2 else ('', '')
    return _dims[path]


def share_card(entry, arts):
    """The Open Graph values for one page.

    Stated outright rather than left to the crawler, which otherwise takes the
    first large image in the document — the author's portrait in the byline.
    """
    piece = arts.get(entry['slug']) if entry['type'] in ('article', 'interview') else None
    img = (S.card_image(piece) if piece else '') or DEFAULT_SHARE_IMAGE
    if not os.path.exists(img.lstrip('/')):
        img = DEFAULT_SHARE_IMAGE
    w, h = image_size(img.lstrip('/'))
    title = entry['head_title']
    if title.endswith(SUFFIX):
        title = title[:-len(SUFFIX)]
    # A wide lede fills a large card; a square portrait would be cropped
    # through the face by one, so it gets the small card instead.
    wide = w and h and (int(w) / int(h)) >= 1.45
    return {
        'OG_TYPE': 'article' if piece else 'website',
        'OG_TITLE': title,
        'OG_URL': P.absolute(entry['url']),
        'OG_IMAGE': P.absolute(img),
        'OG_W': w,
        'OG_H': h,
        'TW_CARD': 'summary_large_image' if wide else 'summary',
    }


def build_page(entry, version='', arts=None):
    body = open(f"content/{entry['content']}", encoding='utf-8').read()
    tpl = R.template(P.template(entry['type'])) or R.template('base.html')
    css = P.stylesheet(entry['type'])
    page = R.render(tpl, {
        **share_card(entry, arts or {}),
        'HEAD_TITLE': entry['head_title'],
        'DESCRIPTION': entry['description'],
        'URL': entry['url'],
        'PAGE_CSS': (f'<link rel="stylesheet" href="/assets/css/{css}?v={version}">'
                     if css else ''),
        'ASSETVER': version,
        'BODY': body,
    })
    page = R.mark_active(page, P.nav_active(entry['type'], entry['slug']))
    out = entry['out']
    os.makedirs(os.path.dirname(out) or '.', exist_ok=True)
    open(out, 'w', encoding='utf-8').write(page)
    return page


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--only', help='slug or type to build')
    ap.add_argument('--clean', action='store_true', help='delete built dirs first')
    args = ap.parse_args()
    if not os.path.exists('content/manifest.json'):
        sys.exit('no content/manifest.json — run tools/extract.py --write first')

    manifest = load_manifest()
    if args.clean:
        for d in sorted({e['out'].split('/')[0] for e in manifest
                         if '/' in e['out']}):
            shutil.rmtree(d, ignore_errors=True)
        print(f'  cleaned built directories')

    todo = [e for e in manifest
            if not args.only or args.only in (e['slug'], e['type'])]
    if not todo:
        sys.exit(f'nothing matches --only {args.only}')

    version = asset_version()
    arts = {a['slug']: a for a in json.load(open('tools/articles.json', encoding='utf-8'))}
    bad = 0
    for e in todo:
        page = build_page(e, version, arts)
        o, c = page.count('<div'), page.count('</div>')
        if o != c:
            print(f"  MISMATCH {o}/{c}  {e['out']}")
            bad += 1
    print(f'  built {len(todo)} pages at asset version {version}' + (f', {bad} with unbalanced divs' if bad else ', divs balanced'))
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
