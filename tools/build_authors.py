#!/usr/bin/env python3
"""Generate a page for every TransHimalaya author, plus the authors index.

Bios come from the "About the author" note at the end of each article in the
WordPress export; portraits from assets/img/au-<slug>.jpg where one exists.

    python3 tools/build_authors.py

Writes content/author/<slug>.html and content/authors-index/; run
tools/build.py afterwards. Run from the site root, after the articles.
"""

import html, json, os, re, sys, unicodedata
import bios as B
import content as C
import paths as P
import xml.etree.ElementTree as ET

XML = os.path.expanduser("~/Downloads/transhimalaya.WordPress.2026-08-03.xml")
NS = {'wp': 'http://wordpress.org/export/1.2/',
      'dc': 'http://purl.org/dc/elements/1.1/',
      'content': 'http://purl.org/rss/1.0/modules/content/'}

MONTH = {'01': 'January', '02': 'February', '03': 'March', '04': 'April', '05': 'May',
         '06': 'June', '07': 'July', '08': 'August', '09': 'September',
         '10': 'October', '11': 'November', '12': 'December'}

HONORIFICS = ('lt general', 'lt gen', 'general', 'prof.', 'prof', 'dr.', 'dr',
              'amb.', 'amb', 'ven.', 'ven', 'mr.', 'ms.')


def text(x):
    return re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', '', x or ''))).strip()


def esc(s):
    return html.escape(s, quote=False)


def slugify(name):
    n = ''.join(c for c in unicodedata.normalize('NFD', name) if not unicodedata.combining(c))
    return re.sub(r'-+', '-', re.sub(r'[^a-z0-9]+', '-', n.lower())).strip('-')


def sortkey(name):
    low = name.lower()
    for h in HONORIFICS:                     # a title should not decide the position
        if low.startswith(h + ' '):
            name = name[len(h) + 1:]
            break
    return ''.join(c for c in unicodedata.normalize('NFD', name)
                   if not unicodedata.combining(c)).lower()


def pretty(d):
    return f"{int(d[8:10])} {MONTH[d[5:7]]} {d[:4]}"


def role_from(bio, name):
    """The opening description, used as a one-line role under the name."""
    m = re.match(r'^.{0,60}?\b(?:is|was|serves as|heads)\b\s+(.{5,110}?)(?:[.,;]| and | who )', bio)
    if not m:
        return ''
    r = m.group(1).strip().rstrip(',')
    r = re.sub(r'^(a|an|the|currently|now)\s+', '', r, flags=re.I)
    return r[:1].upper() + r[1:] if r else ''


def first_name(name):
    low = name.lower()
    for h in HONORIFICS:
        if low.startswith(h + ' '):
            name = name[len(h) + 1:]
            break
    return name.split()[0]


def main():
    if not os.path.exists('index.html'):
        sys.exit('run this from the site root')

    arts = json.load(open('tools/articles.json'))
    ch = ET.parse(XML).getroot().find('channel')

    # Every bio known, from the export and from the supplied set, before any
    # page is written — see tools/bios.py.
    BIOS = B.seed()
    bios = {}
    for a in arts:
        k = B.slug(a['author'])
        if BIOS.get(k):
            bios[a['author']] = BIOS[k]

    # group articles by author
    by_author = {}
    for a in arts:
        by_author.setdefault(a['author'], []).append(a)
    for v in by_author.values():
        v.sort(key=lambda a: a['date'], reverse=True)

    manifest = C.load()

    def shell(page_type, slug, title, desc, body):
        """Register the page's content; build.py wraps it in the chrome."""
        C.write(page_type, slug, esc(title), esc(desc), f'\n{body}\n',
                manifest=manifest)
        return 'ok'

    SKIP_AUTHORS = {'Youth Voices'}
    names = [n for n in sorted(set(list(bios) + list(by_author)), key=sortkey)
             if n not in SKIP_AUTHORS]
    cards = []

    for name in names:
        slug = slugify(name)
        bio = B.best(slug, bios.get(name, ''), BIOS)
        role = role_from(bio, name)
        works = by_author.get(name, [])
        photo = f'assets/img/au-{slug}.jpg'
        has_photo = os.path.exists(photo)

        portrait = (f'<img class="portrait" src="{P.asset(photo)}" alt="" width="180" height="180">'
                    if has_photo else
                    f'<span class="portrait is-initials" aria-hidden="true">'
                    f'{esc(first_name(name)[0])}{esc(name.split()[-1][0])}</span>')

        items = '\n'.join(f'''          <li>
            <a href="{P.url('article', a['slug'])}">
              <span class="sec">{esc(a['section'])}</span>
              <span class="t">{esc(a['title'])}</span>
              <span class="d"><svg class="ic" aria-hidden="true"><use href="#ic-cal"/></svg> {pretty(a['date'])}</span>
            </a>
          </li>''' for a in works)
        works_html = ('' if not works else f'''
        <div class="au-works">
          <h2 class="th-h3">Articles by {esc(first_name(name))}</h2>
          <div class="th-divL"><i></i><b></b></div>
          <ol class="au-list">
{items}
          </ol>
        </div>''')

        body = f'''      <section class="au-profile">
        <p class="crumb"><a href="/authors/">Authors</a></p>
        <div class="au-hero">
          {portrait}
          <div>
            <p class="k">Author</p>
            <h1>{esc(name)}</h1>
            {f'<p class="rl">{esc(role)}</p>' if role else ''}
            <p class="bio">{esc(bio) or 'Contributor to TransHimalaya.'}</p>
          </div>
        </div>
{works_html}
      </section>
'''
        flag = shell('author', slug, name,
                     bio[:150] or f'{name}, contributor to TransHimalaya.', body)
        n = len(works)
        print(f"  author-{slug:34} {n} article{'' if n == 1 else 's':<2} "
              f"{'photo' if has_photo else 'initials':>8}  {flag}")

        av = (f'<span class="av"><img src="{P.asset(photo)}" alt="" width="120" height="120" loading="lazy"></span>'
              if has_photo else
              f'<span class="av is-initials" aria-hidden="true">'
              f'{esc(first_name(name)[0])}{esc(name.split()[-1][0])}</span>')
        blurb = (bio[:118] + '…') if len(bio) > 118 else bio
        cards.append(f'''        <li class="au-card">
          <a href="{P.url('author', slug)}">
            {av}
            <span class="nm">{esc(name)}</span>
            <span class="rl">{esc(blurb)}</span>
            <span class="ct">{n} article{'' if n == 1 else 's'}</span>
          </a>
        </li>''')

    index_body = f'''      <section class="au-index">
        <header class="au-head">
          <p class="k">About</p>
          <h1>Authors</h1>
          <p class="lede">The scholars, journalists and practitioners writing for TransHimalaya on Tibet, the Himalaya and Inner Asia.</p>
        </header>
        <ul class="au-grid">
{chr(10).join(cards)}
        </ul>
      </section>
'''
    print(f"\n  /authors/  {len(cards)} authors  "
          f"{shell('authors-index', '', 'Authors', 'Everyone writing for TransHimalaya.', index_body)}")
    C.prune('author', {slugify(n) for n in names}, manifest)
    C.save(manifest)
    B.save(BIOS)


if __name__ == '__main__':
    main()
