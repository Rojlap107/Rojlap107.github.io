#!/usr/bin/env python3
"""One-time migration: the flat root pages become content/ + a manifest.

Each existing page is split into the part that is unique to it (title,
description, body) and the part every page repeats (sprite, masthead, nav,
newsletter, footer). The unique part is written to content/<type>/<slug>.html;
the repeated part becomes the partials under templates/partials/ and is never
stored per-page again.

Links are rewritten from the flat `foo.html` form to the new site-absolute
slug URLs as they are extracted, so content/ is already canonical.

    python3 tools/extract.py            # report only
    python3 tools/extract.py --write    # write content/ and the manifest

Kept for the record. It has already been run: content/ is now the source of
truth and the flat pages it read are gone, so re-running it would classify only
index.html and overwrite the manifest. It refuses to write over an existing
content/manifest.json unless you pass --force.

Run from the site root.
"""

import argparse, json, os, re, sys
import paths as P

SPECIAL = {
    'index.html':            ('home', ''),
    'journal-editions.html': ('issue', ''),
    'authors.html':          ('authors-index', ''),
    'team.html':             ('team-index', ''),
    'dreshey.html':          ('dreshey-hub', ''),
}
FLAT_PAGES = {'about', 'career', 'contact'}
BY_CSS = {'category.css': 'section', 'dreshey.css': 'dreshey', 'article.css': 'article'}

RE_SPRITE = re.compile(r'  <svg width="0" height="0".*?</svg>\n', re.S)
RE_HEADER = re.compile(r'      <!-- Header -->.*?</nav>\n', re.S)
RE_FOOTER = re.compile(r'      <!-- Newsletter -->.*?</footer>\n', re.S)
RE_TITLE = re.compile(r'<title>(.*?)</title>', re.S)
RE_DESC = re.compile(r'<meta name="description" content="(.*?)">', re.S)
RE_BODY = re.compile(r'</nav>\n(.*?)      <!-- Newsletter -->', re.S)


def classify(fn, html):
    """(type, slug) for a root page — filename rules first, stylesheet last."""
    if fn in SPECIAL:
        return SPECIAL[fn]
    stem = fn[:-5]
    if stem.startswith('author-'):
        return 'author', stem[len('author-'):]
    if stem.startswith('member-'):
        return 'member', stem[len('member-'):]
    if stem in FLAT_PAGES:
        return 'page', stem
    css = re.search(r'css/([a-z]+\.css)"', html.split('</head>')[0])
    css = [c for c in re.findall(r'css/([a-z]+\.css)', html.split('</head>')[0])
           if c != 'base.css']
    if css and css[0] in BY_CSS:
        return BY_CSS[css[0]], stem
    sys.exit(f'cannot classify {fn}')


def link_map(entries):
    """old flat filename -> new site-absolute URL."""
    return {f"{e['file'][:-5]}.html": P.url(e['type'], e['slug']) for e in entries}


def rewrite(html, lmap, where=''):
    """Point every internal reference at the new scheme."""
    missing = set()

    def href(m):
        attr, target, frag = m.group(1), m.group(2), m.group(3) or ''
        if target not in lmap:
            missing.add(target)
            return m.group(0)
        return f'{attr}="{lmap[target]}{frag}"'

    html = re.sub(r'\b(href|src)="([A-Za-z0-9._-]+\.html)(#[^"]*)?"', href, html)
    # assets become site-absolute so a page at any depth resolves them
    html = re.sub(r'\b(href|src)="assets/', r'\1="/assets/', html)
    html = html.replace('url(assets/', 'url(/assets/')
    for t in sorted(missing):
        print(f'    ! {where}: unmapped link {t}')
    return html


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--write', action='store_true')
    ap.add_argument('--force', action='store_true',
                    help='allow overwriting an existing content/manifest.json')
    args = ap.parse_args()
    if not os.path.exists('index.html'):
        sys.exit('run from the site root')
    if args.write and os.path.exists('content/manifest.json') and not args.force:
        sys.exit('content/manifest.json already exists — this migration has already '
                 'run. Pass --force only if you mean to rebuild it from flat pages.')

    files = sorted(f for f in os.listdir('.') if f.endswith('.html'))
    raw = {f: open(f, encoding='utf-8').read() for f in files}

    entries = []
    for f in files:
        t, slug = classify(f, raw[f])
        entries.append({'file': f, 'type': t, 'slug': slug})
    lmap = link_map(entries)

    # the chrome — identical on every page, so any page can supply it. index.html
    # carries the fullest sprite (it alone uses ic-download).
    idx = raw['index.html']
    chrome = {
        'sprite': RE_SPRITE.search(idx).group(0),
        'header': RE_HEADER.search(idx).group(0).replace(' class="active"', ''),
        'footer': RE_FOOTER.search(idx).group(0),
    }

    for e in entries:
        html = raw[e['file']]
        e['head_title'] = RE_TITLE.search(html).group(1).strip()
        m = RE_DESC.search(html)
        e['description'] = m.group(1).strip() if m else ''
        e['url'] = P.url(e['type'], e['slug'])
        e['out'] = P.out_path(e['type'], e['slug'])
        body = RE_BODY.search(html).group(1)
        e['body'] = rewrite(body, lmap, e['file'])

    by_type = {}
    for e in entries:
        by_type.setdefault(e['type'], []).append(e)
    for t in sorted(by_type):
        print(f"  {t:14} {len(by_type[t]):3d}  e.g. {by_type[t][0]['url']}")

    if not args.write:
        print('\n  (report only — pass --write to create content/)')
        return

    os.makedirs('templates/partials', exist_ok=True)
    for name, text in chrome.items():
        ext = 'svg' if name == 'sprite' else 'html'
        open(f'templates/partials/{name}.{ext}', 'w', encoding='utf-8').write(
            rewrite(text, lmap, f'partial:{name}'))

    manifest = []
    for e in entries:
        d = f"content/{e['type']}"
        os.makedirs(d, exist_ok=True)
        name = e['slug'] or e['type']
        open(f'{d}/{name}.html', 'w', encoding='utf-8').write(e['body'])
        manifest.append({k: e[k] for k in
                         ('type', 'slug', 'url', 'out', 'head_title', 'description')}
                        | {'content': f"{e['type']}/{name}.html", 'legacy': e['file']})
    json.dump(manifest, open('content/manifest.json', 'w'), indent=1, ensure_ascii=False)
    print(f'\n  wrote content/ ({len(manifest)} pages) and templates/partials/')


if __name__ == '__main__':
    main()
