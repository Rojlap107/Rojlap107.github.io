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

import argparse, json, os, shutil, sys
import paths as P
import render as R


def load_manifest():
    return json.load(open('content/manifest.json', encoding='utf-8'))


def build_page(entry):
    body = open(f"content/{entry['content']}", encoding='utf-8').read()
    tpl = R.template(P.template(entry['type'])) or R.template('base.html')
    css = P.stylesheet(entry['type'])
    page = R.render(tpl, {
        'HEAD_TITLE': entry['head_title'],
        'DESCRIPTION': entry['description'],
        'URL': entry['url'],
        'PAGE_CSS': f'<link rel="stylesheet" href="/assets/css/{css}">' if css else '',
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

    bad = 0
    for e in todo:
        page = build_page(e)
        o, c = page.count('<div'), page.count('</div>')
        if o != c:
            print(f"  MISMATCH {o}/{c}  {e['out']}")
            bad += 1
    print(f'  built {len(todo)} pages' + (f', {bad} with unbalanced divs' if bad else ', divs balanced'))
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
