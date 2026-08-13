#!/usr/bin/env python3
"""Generate the Dreshey hub and its nine sub-sections.

Three of them can be filled from the magazine's own material — the archive,
a reading selection, and the figures and tables drawn from the articles. The
rest have no source content yet and get an honest empty state.

    python3 tools/build_deyshal.py

Run from the site root, after build_articles.py.
"""

import html, json, os, re, sys

MONTH = {'01': 'January', '02': 'February', '03': 'March', '04': 'April', '05': 'May',
         '06': 'June', '07': 'July', '08': 'August', '09': 'September',
         '10': 'October', '11': 'November', '12': 'December'}

# slug, title, description shown on the hub card
SUBS = [
    ('archives', 'Archives',
     'Everything TransHimalaya has published, by date.'),
    ('data-visuals', 'Data &amp; Visuals',
     'Maps, charts and tables drawn from the essays.'),
    ('must-reads', 'Must Reads',
     'A standing selection of the pieces to start with.'),
    ('glossary-of-terms', 'Glossary of Terms',
     'Tibetan, Chinese and policy terms, defined.'),
    ('china-jargon', 'China Jargon',
     'The vocabulary of Party documents, translated and explained.'),
    ('book-reviews', 'Book Reviews',
     'New writing on Tibet, China and the Himalaya.'),
    ('snippets', 'Snippets',
     'Short items of note from across the region.'),
    ('dharamshala', 'Developments in Dharamshala',
     'International developments and happenings in Dharamshala.'),
    ('tibet-then-and-now', 'Tibet Then and Now',
     'Visual records of a changing plateau.'),
]

FILLED = {'archives', 'data-visuals', 'must-reads'}


def esc(s):
    return html.escape(s, quote=False)


def pretty(d):
    return f"{int(d[8:10])} {MONTH[d[5:7]]} {d[:4]}"


def chrome():
    idx = open('index.html', encoding='utf-8').read()
    return (re.search(r'  <svg width="0" height="0".*?</svg>\n', idx, re.S).group(0),
            re.search(r'      <!-- Header -->.*?</nav>\n', idx, re.S).group(0),
            re.search(r'      <!-- Subscription · Razorpay -->.*?</footer>\n', idx, re.S).group(0))


def page(fn, title, desc, css, body):
    sprite, header, tail = CHROME
    s = (f'<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
         '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
         f'<title>{esc(title)} — TransHimalaya</title>\n'
         f'<meta name="description" content="{esc(re.sub("&amp;", "&", desc))}">\n'
         '<link rel="icon" href="assets/img/logo-mark.png">\n'
         '<link rel="stylesheet" href="assets/css/base.css">\n'
         f'<link rel="stylesheet" href="assets/css/{css}">\n</head>\n<body>\n<div class="th-site">\n'
         f'{sprite}{header}\n{body}\n{tail}</div>\n'
         '<script src="assets/js/site.js"></script>\n</body>\n</html>\n')
    open(fn, 'w', encoding='utf-8').write(s)
    o, c = s.count('<div'), s.count('</div>')
    return 'OK' if o == c else f'MISMATCH {o}/{c}'


def head(kicker, title, lede, extra=''):
    return (f'''        <header class="dy-head">
          <p class="k">{kicker}</p>
          <h1>{title}</h1>
          <p class="lede">{lede}</p>
          {extra}
        </header>''')


def empty(title):
    return ('        <div class="cat-empty">\n'
            '          <p class="ttl">Nothing published here yet</p>\n'
            f'          <p>{title} is part of Dreshey but has no entries so far. '
            'Browse the <a href="archives.html">archive</a> or read the '
            '<a href="issues.html">current issue</a> in the meantime.</p>\n'
            '        </div>\n')


def main():
    global CHROME
    if not os.path.exists('index.html'):
        sys.exit('run this from the site root')
    CHROME = chrome()
    arts = sorted(json.load(open('tools/articles.json')),
                  key=lambda a: a['date'], reverse=True)

    # ---------------------------------------------------------------- hub
    cards = '\n'.join(f'''          <li class="dy-card{'' if s in FILLED else ' is-soon'}">
            <a href="{s}.html">
              <span class="nm">{t}</span>
              <span class="ds">{d}</span>
              <span class="go">{'Open' if s in FILLED else 'Coming soon'}</span>
            </a>
          </li>''' for s, t, d in SUBS)
    hub = f'''      <div class="dy">
{head('Dreshey', 'Dreshey', 'The Foundation&#39;s reference shelf — the archive, the data behind the essays, and the reading and reference material that supports our research.')}
        <ul class="dy-grid">
{cards}
        </ul>
      </div>
'''
    print(f"  {'deyshal':26} hub            {page('dreshey.html', 'Dreshey', 'The Foundation reference shelf: archive, data, glossary and reading.', 'deyshal.css', hub)}")

    # ---------------------------------------------------------------- archive
    by_month = {}
    for a in arts:
        by_month.setdefault(a['date'][:7], []).append(a)
    rows = []
    for ym in sorted(by_month, reverse=True):
        rows.append(f'          <h2 class="dy-month">{MONTH[ym[5:7]]} {ym[:4]}</h2>')
        rows.append('          <ul class="dy-list">')
        for a in by_month[ym]:
            rows.append(
                f'            <li><a href="{a["slug"]}.html">'
                f'<span class="dt">{int(a["date"][8:10])}</span>'
                f'<span class="tt">{esc(a["title"])}</span>'
                f'<span class="mt">{esc(a["author"])} · {esc(a["section"])}</span></a></li>')
        rows.append('          </ul>')
    archive = f'''      <div class="dy">
{head('Dreshey', 'Archives', 'Everything TransHimalaya has published, most recent first.',
      f'<p class="dy-count">{len(arts)} articles</p>')}
        <div class="dy-archive">
{chr(10).join(rows)}
        </div>
      </div>
'''
    print(f"  {'archives':26} {len(arts):3d} articles  {page('archives.html', 'Archives', 'The complete TransHimalaya archive.', 'deyshal.css', archive)}")

    # ---------------------------------------------------------------- must reads
    picks, seen = [], set()
    for a in arts:                       # one from each section, longest first
        if a['section'] in seen:
            continue
        seen.add(a['section'])
        picks.append(a)
    picks += [a for a in arts if a not in picks][:1]
    items = '\n'.join(f'''          <li class="dy-pick">
            <a class="ph" href="{a['slug']}.html" style="background-image:url({a['lede']})"></a>
            <div class="b">
              <p class="k">{esc(a['section'])}</p>
              <h2><a href="{a['slug']}.html">{esc(a['title'])}</a></h2>
              <p class="mt">By {esc(a['author'])} · {pretty(a['date'])}</p>
            </div>
          </li>''' for a in picks)
    must = f'''      <div class="dy">
{head('Dreshey', 'Must Reads', 'Where to begin — one essay from each section of the magazine.')}
        <ul class="dy-picks">
{items}
        </ul>
      </div>
'''
    print(f"  {'must-reads':26} {len(picks):3d} picks     {page('must-reads.html', 'Must Reads', 'Where to begin with TransHimalaya.', 'deyshal.css', must)}")

    # ---------------------------------------------------------------- data & visuals
    figs = []
    for a in arts:
        s = open(a['slug'] + '.html', encoding='utf-8').read()
        for m in re.finditer(r'<figure class="art-fig">\s*<img src="([^"]+)"[^>]*>\s*'
                             r'<figcaption>(.*?)</figcaption>', s, re.S):
            cap = re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', '', m.group(2)))).strip()
            figs.append((a, m.group(1), cap))
        for _ in re.finditer(r'<figure class="art-table">', s):
            figs.append((a, None, 'Table'))
    tiles = '\n'.join(
        (f'''          <li class="dy-fig">
            <a href="{a['slug']}.html">
              <span class="im" style="background-image:url({src})"></span>
              <span class="cp">{esc(cap)}</span>
              <span class="src">{esc(a['title'])}</span>
            </a>
          </li>''' if src else f'''          <li class="dy-fig is-table">
            <a href="{a['slug']}.html">
              <span class="im"><span class="lbl">Table</span></span>
              <span class="cp">Data table</span>
              <span class="src">{esc(a['title'])}</span>
            </a>
          </li>''') for a, src, cap in figs)
    dv = f'''      <div class="dy">
{head('Dreshey', 'Data &amp; Visuals', 'The maps, charts, photographs and tables that appear in the essays, gathered in one place.',
      f'<p class="dy-count">{len(figs)} items</p>')}
        <ul class="dy-figs">
{tiles}
        </ul>
      </div>
'''
    print(f"  {'data-visuals':26} {len(figs):3d} items     {page('data-visuals.html', 'Data & Visuals', 'Maps, charts and tables from the essays.', 'deyshal.css', dv)}")

    # ---------------------------------------------------------------- the rest
    for s, t, d in SUBS:
        if s in FILLED:
            continue
        plain = re.sub('&amp;', '&', t)
        body = f'''      <div class="dy">
{head('Dreshey', t, d)}
{empty(plain)}      </div>
'''
        print(f"  {s:26} empty          {page(s + '.html', plain, d, 'deyshal.css', body)}")


if __name__ == '__main__':
    main()
