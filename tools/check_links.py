#!/usr/bin/env python3
"""Check every internal reference on the built site.

Pages now live at /articles/<slug>/ rather than /article.html, so a *relative*
reference resolves against the page's own directory and quietly 404s. This
catches that as well as plain missing targets, and is the check to run after
touching a generator or a partial.

    python3 tools/check_links.py

Exits non-zero if anything is wrong. Run from the site root.
"""

import json, os, re, sys
from collections import defaultdict

# not ours to resolve
EXTERNAL = ('http://', 'https://', 'mailto:', 'tel:', 'data:', '//')
# referenced but supplied later by FNVA — see README
EXPECTED_MISSING = {'/assets/pdf/transhimalaya-issue-1-august-2026.pdf'}

REFS = re.compile(r'\b(?:href|src)="([^"]+)"')
URLS = re.compile(r'url\(([^)]+)\)')


def targets(html):
    for m in REFS.finditer(html):
        yield m.group(1)
    for m in URLS.finditer(html):
        yield m.group(1).strip('\'"')


def main():
    if not os.path.exists('content/manifest.json'):
        sys.exit('run from the site root')
    manifest = json.load(open('content/manifest.json', encoding='utf-8'))

    problems = defaultdict(list)
    checked = 0
    for e in manifest:
        if not os.path.exists(e['out']):
            problems['page not built'].append(e['out'])
            continue
        html = open(e['out'], encoding='utf-8').read()
        for t in set(targets(html)):
            if t.startswith(EXTERNAL) or t.startswith('#') or t.startswith('%'):
                continue
            checked += 1
            if not t.startswith('/'):
                problems['relative reference (breaks under slug URLs)'].append(
                    f"{e['url']}  ->  {t}")
                continue
            path = t.split('#')[0].split('?')[0]
            local = 'index.html' if path == '/' else (
                path.strip('/') + '/index.html' if path.endswith('/') else path.lstrip('/'))
            if not os.path.exists(local) and path not in EXPECTED_MISSING:
                problems['target does not exist'].append(f"{e['url']}  ->  {t}")

    print(f'  {checked} internal references across {len(manifest)} pages')
    for kind, items in sorted(problems.items()):
        print(f'\n  {kind} ({len(items)}):')
        for i in items[:15]:
            print(f'    {i}')
        if len(items) > 15:
            print(f'    … and {len(items) - 15} more')
    if problems:
        return 1
    skipped = ', '.join(sorted(EXPECTED_MISSING))
    print(f'  all resolve (not yet supplied, allowed: {skipped})')
    return 0


if __name__ == '__main__':
    sys.exit(main())
