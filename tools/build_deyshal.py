#!/usr/bin/env python3
"""Generate the Dreshey hub; the nine sub-sections are hand-maintained.

All nine sub-sections are curated from the 1st issue's own Dreshey source
material (~/Desktop/Tenzin Paljor/FNVA/1st Issue/S9_ Dreshey) and are
hand-maintained fragments under content/dreshey/ — this script registers
their manifest entries once but does not regenerate their bodies, the same
way content/page/about.html is hand-maintained. A sub-section with no source
content yet gets an honest empty state instead.

    python3 tools/build_deyshal.py

Writes content/dreshey-hub/index.html (the hub is the only page this script
generates); run tools/build.py afterwards to assemble the pages. Run from the
site root, after the articles.
"""

import html, os, re, sys
import content as C
import paths as P

# slug, title, description shown on the hub card
SUBS = [
    ('from-the-archives', 'From the Archives',
     'Primary documents that frame the dispute over Tibet&#39;s status.'),
    ('data-visuals', 'Data &amp; Visuals',
     'Organograms and reference diagrams on the CTA&#39;s institutional structure.'),
    ('recommended-readings', 'Recommended Readings',
     'Seven books on Tibet, China and the wider Himalaya.'),
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

# hub card status: every sub-section has real content now, bar none still
# awaiting its source material — kept as a set in case that changes again
FILLED = {s for s, _, _ in SUBS}


def esc(s):
    return html.escape(s, quote=False)


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

    # ------------------------------------------------- still awaiting content
    # only reached by a sub-section that is neither generated above nor
    # already a hand-maintained fragment — i.e. one with no source material
    # yet, same as Youth and Tibet Monitor elsewhere on the site
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
