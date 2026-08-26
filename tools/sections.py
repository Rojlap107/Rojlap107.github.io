#!/usr/bin/env python3
"""One source of truth for section identity: order, slug and colour.

Every card across the site (section pages, In Focus, the homepage, the
"You may also like" rail) labels its article with the same coloured chip, so a
reader can tell a History piece from a Tibet Today piece at a glance.

Colours are defined once here and emitted as CSS custom properties by
`css_block()`; the chips themselves carry a class, never an inline colour.
"""

import html
import os
import re
import unicodedata

import paths as P
import videos as V

# section name -> (chip colour, text colour on that chip)
COLOURS = {
    'History':                 ('#8C6239', '#fff'),   # sepia — the record
    'Tibet Today':             ('#2B7A99', '#fff'),   # teal
    'Tibet Beyond Borders':    ('#E68A2E', '#fff'),   # orange
    'The Strategic Triangle':  ('#1B3A4B', '#fff'),   # deep navy
    'Global Perspectives':     ('#3F7A5E', '#fff'),   # green
    'Youth':                   ('#7B5EA7', '#fff'),   # violet
    'Interviews':              ('#B3477A', '#fff'),   # rose
    'Tibet Monitor':           ('#C0392B', '#fff'),   # red
    # opening pieces
    'Foreword':                ('#5A6B73', '#fff'),
    'Editor’s Note':           ('#5A6B73', '#fff'),
    'Strategic Foresight':     ('#4B6A8A', '#fff'),
    'Policy':                  ('#6B7F4B', '#fff'),
}

DEFAULT = ('#5A6B73', '#fff')

# the topics gathered under In Focus
IN_FOCUS = ['Tibet Today', 'Tibet Beyond Borders', 'History']

# section -> the slug of the page that lists it. Opening pieces have no section
# page of their own, so they point back at the edition.
PAGES = {
    'History': 'history',
    'Tibet Today': 'tibet-today',
    'Tibet Beyond Borders': 'tibet-beyond-borders',
    'The Strategic Triangle': 'the-strategic-triangle',
    'Global Perspectives': 'global-perspectives',
    'Youth': 'youth',
    'Interviews': 'interviews',
    'Tibet Monitor': 'tibet-monitor',
}


def page_for(section):
    """The URL of the page that lists this section."""
    slug = PAGES.get(section)
    return P.url('section', slug) if slug else P.url('issue')


def article_url(slug):
    return P.url('article', slug)


def piece_url(article):
    """Where one published piece lives.

    Interviews are on their own branch, so every card, rail and list has to
    ask here rather than assume /articles/.
    """
    if article.get('section') == 'Interviews':
        return P.url('interview', article['slug'])
    return P.url('article', article['slug'])


def card_image(article):
    """The picture a card shows for a piece.

    A filmed conversation shows its video still, so the card matches what
    the piece itself opens with. Everything else shows its lede.
    """
    return V.thumb(article['slug']) or article.get('lede') or ''

def by_meta(article):
    """The "By <author>" half of a card's meta line.

    Empty for a piece with no author — a filmed interview stands on its own
    rather than being credited to whoever conducted it.
    """
    who = (article.get('author') or '').strip()
    return f'<span>·</span><span>By {esc(who)}</span>' if who else ''


def by_line(article, tail=''):
    """Author and one more field for a compact list row, author omitted
    where there is none."""
    who = (article.get('author') or '').strip()
    return ' · '.join(x for x in (esc(who), tail) if x)

def fragment(slug):
    """The content fragment for a piece, whichever branch it is filed under."""
    for kind in ('article', 'interview'):
        path = f'content/{kind}/{slug}.html'
        if os.path.exists(path):
            return path
    return ''


def chip_link(section, cls='th-chip'):
    """A coloured section label that navigates to that section's page."""
    return (f'<a class="{cls} cat-{slug(section)}" href="{page_for(section)}">'
            f'{esc(section)}</a>')


def esc(s):
    return html.escape(s or '', quote=False)


def slug(name):
    n = ''.join(c for c in unicodedata.normalize('NFD', name or '')
                if not unicodedata.combining(c))
    return re.sub(r'-+', '-', re.sub(r'[^a-z0-9]+', '-', n.lower())).strip('-')


def chip(section, cls='th-chip'):
    """A coloured section label, e.g. for a card."""
    return (f'<span class="{cls} cat-{slug(section)}">{esc(section)}</span>')


_EXCERPT_CACHE = {}


def excerpt(slug, limit=115):
    """The article's stand-first, trimmed — used as a card's summary line so
    cards are not left with an empty gap above the date."""
    if slug in _EXCERPT_CACHE:
        return _EXCERPT_CACHE[slug]
    out = ''
    try:
        path = fragment(slug)
        if not path:
            raise FileNotFoundError(slug)
        page = open(path, encoding='utf-8').read()
        m = re.search(r'<p class="art-standfirst">(.*?)</p>', page, re.S)
        if m:
            t = re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', m.group(1))).strip()
            if len(t) > limit:
                cut = t[:limit].rsplit(' ', 1)[0]
                t = cut.rstrip('.,;:—- ') + '…'
            out = t
    except FileNotFoundError:
        pass
    _EXCERPT_CACHE[slug] = out
    return out


def css_block():
    """CSS for every chip colour — appended to components.css by build_sections_css."""
    rows = []
    for name, (bg, fg) in COLOURS.items():
        # --cat lets other components (filter pills, rules) reuse the colour
        # without inheriting the chip's background.
        rows.append(f'.cat-{slug(name)}{{ --cat:{bg}; --cat-fg:{fg}; '
                    f'background:{bg}; color:{fg}; }}')
    return ('/* section colours — one colour per topic, shared by every card */\n'
            + '\n'.join(rows) + '\n')
