#!/usr/bin/env python3
"""Generate the Dreshey hub and its nine sub-sections.

Three of them can be filled from the magazine's own material — the archive,
a reading selection, and the figures and tables drawn from the articles. The
rest have no source content yet and get an honest empty state.

    python3 tools/build_deyshal.py

Writes content/dreshey-hub/ and content/dreshey/<slug>.html; run tools/build.py
afterwards to assemble the pages. Run from the site root, after the articles.
"""

import html, json, os, re, sys
import content as C
import paths as P
import sections as S

MONTH = {'01': 'January', '02': 'February', '03': 'March', '04': 'April', '05': 'May',
         '06': 'June', '07': 'July', '08': 'August', '09': 'September',
         '10': 'October', '11': 'November', '12': 'December'}

# slug, title, description shown on the hub card
SUBS = [
    ('from-the-archives', 'From the Archives',
     'Everything TransHimalaya has published, by date.'),
    ('data-visuals', 'Data &amp; Visuals',
     'Maps, charts and tables drawn from the essays.'),
    ('recommended-readings', 'Recommended Readings',
     'A standing selection of the pieces to start with.'),
    ('trans-himalaya-lexicon', 'Trans Himalaya Lexicon',
     'Tibetan, Chinese and policy terms, defined.'),
    ('decoding-beijings-terminology', 'Decoding Beijing’s Terminology',
     'The vocabulary of Party documents, translated and explained.'),
    ('book-reviews', 'Book Reviews',
     'New writing on Tibet, China and the Himalaya.'),
    ('snippets-of-interesting-info', 'Snippets of Interesting Info.',
     'Short items of note from across the region.'),
    ('tibet-highlights', 'Tibet Highlights',
     'International developments on Tibet, and happenings in Dharamshala.'),
    ('photographs-then-and-now', 'Photographs Then and Now',
     'Visual records of a changing plateau.'),
]

FILLED = {'from-the-archives', 'data-visuals', 'recommended-readings'}


def esc(s):
    return html.escape(s, quote=False)


def pretty(d):
    return f"{int(d[8:10])} {MONTH[d[5:7]]} {d[:4]}"


def page(page_type, slug, title, desc, body):
    """Register one Dreshey page's content. The chrome is added by build.py."""
    C.write(page_type, slug, esc(title), esc(re.sub('&amp;', '&', desc)),
            f'\n{body}\n', manifest=MANIFEST)
    return 'ok'


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
            'Browse the <a href="/dreshey/from-the-archives/">archive</a> or read the '
            '<a href="/journal-editions/">current issue</a> in the meantime.</p>\n'
            '        </div>\n')


def main():
    global MANIFEST
    if not os.path.exists('content/manifest.json'):
        sys.exit('run this from the site root')
    MANIFEST = C.load()
    arts = sorted(json.load(open('tools/articles.json')),
                  key=lambda a: a['date'], reverse=True)

    # ---------------------------------------------------------------- hub
    cards = '\n'.join(f'''          <li class="dy-card{'' if s in FILLED else ' is-soon'}">
            <a href="{P.url('dreshey', s)}">
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
    print(f"  {'deyshal':26} hub            {page('dreshey-hub', '', 'Dreshey', 'The Foundation reference shelf: archive, data, glossary and reading.', hub)}")

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
                f'            <li><a href="{S.piece_url(a)}">'
                f'<span class="dt">{int(a["date"][8:10])}</span>'
                f'<span class="tt">{esc(a["title"])}</span>'
                f'<span class="mt">{S.by_line(a, esc(a["section"]))}</span></a></li>')
        rows.append('          </ul>')
    archive = f'''      <div class="dy">
{head('Dreshey', 'From the Archives', 'Everything TransHimalaya has published, most recent first.',
      f'<p class="dy-count">{len(arts)} articles</p>')}
        <div class="dy-archive">
{chr(10).join(rows)}
        </div>
      </div>
'''
    print(f"  {'from-the-archives':26} {len(arts):3d} articles  {page('dreshey', 'from-the-archives', 'From the Archives', 'The complete TransHimalaya archive.', archive)}")

    # ---------------------------------------------------------------- must reads
    picks, seen = [], set()
    for a in arts:                       # one from each section, longest first
        if a['section'] in seen:
            continue
        seen.add(a['section'])
        picks.append(a)
    picks += [a for a in arts if a not in picks][:1]
    items = '\n'.join(f'''          <li class="dy-pick">
            <a class="ph" href="{S.piece_url(a)}" style="background-image:url({P.asset(S.card_image(a))})"></a>
            <div class="b">
              <p class="k">{esc(a['section'])}</p>
              <h2><a href="{S.piece_url(a)}">{esc(a['title'])}</a></h2>
              <p class="mt">{S.by_line(a, pretty(a['date']))}</p>
            </div>
          </li>''' for a in picks)
    must = f'''      <div class="dy">
{head('Dreshey', 'Recommended Readings', 'Where to begin — one essay from each section of the magazine.')}
        <ul class="dy-picks">
{items}
        </ul>
      </div>
'''
    print(f"  {'recommended-readings':26} {len(picks):3d} picks     {page('dreshey', 'recommended-readings', 'Recommended Readings', 'Where to begin with TransHimalaya.', must)}")

    # ---------------------------------------------------------------- data & visuals
    figs = []
    for a in arts:
        path = S.fragment(a['slug'])
        if not path:
            continue
        s = open(path, encoding='utf-8').read()
        for m in re.finditer(r'<figure class="art-fig">\s*<img src="([^"]+)"[^>]*>\s*'
                             r'<figcaption>(.*?)</figcaption>', s, re.S):
            cap = re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', '', m.group(2)))).strip()
            figs.append((a, m.group(1), cap))
        for _ in re.finditer(r'<figure class="art-table">', s):
            figs.append((a, None, 'Table'))
    tiles = '\n'.join(
        (f'''          <li class="dy-fig">
            <a href="{S.piece_url(a)}">
              <span class="im" style="background-image:url({P.asset(src)})"></span>
              <span class="cp">{esc(cap)}</span>
              <span class="src">{esc(a['title'])}</span>
            </a>
          </li>''' if src else f'''          <li class="dy-fig is-table">
            <a href="{S.piece_url(a)}">
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
    print(f"  {'data-visuals':26} {len(figs):3d} items     {page('dreshey', 'data-visuals', 'Data & Visuals', 'Maps, charts and tables from the essays.', dv)}")

    # ---------------------------------------------------------------- the rest
    for s, t, d in SUBS:
        if s in FILLED:
            continue
        plain = re.sub('&amp;', '&', t)
        body = f'''      <div class="dy">
{head('Dreshey', t, d)}
{empty(plain)}      </div>
'''
        print(f"  {s:26} empty          {page('dreshey', s, plain, d, body)}")

    C.prune('dreshey', {sub[0] for sub in SUBS}, MANIFEST)
    C.save(MANIFEST)


if __name__ == '__main__':
    main()
