#!/usr/bin/env python3
"""Generate a page for every TransHimalaya author, plus the authors index.

Bios come from the "About the author" note at the end of each article in the
WordPress export; portraits from assets/img/au-<slug>.jpg where one exists.

    python3 tools/build_authors.py

Run from the site root, after build_articles.py.
"""

import html, json, os, re, sys, unicodedata
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

    bios = {}
    for it in ch.findall('item'):
        if it.findtext('wp:post_type', default='', namespaces=NS) != 'post':
            continue
        if it.findtext('wp:status', default='', namespaces=NS) != 'publish':
            continue
        if not it.findtext('wp:post_date', default='', namespaces=NS).startswith('2026'):
            continue
        who = it.findtext('dc:creator', default='', namespaces=NS)
        raw = re.sub(r'<!--.*?-->', '',
                     it.findtext('content:encoded', default='', namespaces=NS) or '', flags=re.S)
        m = re.search(r'ABOUT THE AUTHOR(.*)$', raw, re.S)
        if m and who:
            bio = re.sub(r'^[:\s]+', '', text(m.group(1)))
            if len(bio) > len(bios.get(who, '')):
                bios[who] = bio

    # group articles by author
    by_author = {}
    for a in arts:
        by_author.setdefault(a['author'], []).append(a)
    for v in by_author.values():
        v.sort(key=lambda a: a['date'], reverse=True)

    idx = open('index.html', encoding='utf-8').read()
    sprite = re.search(r'  <svg width="0" height="0".*?</svg>\n', idx, re.S).group(0)
    header = re.search(r'      <!-- Header -->.*?</nav>\n', idx, re.S).group(0)
    tail = re.search(r'      <!-- Subscription · Razorpay -->.*?</footer>\n', idx, re.S).group(0)

    def shell(fn, title, desc, body):
        s = ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
             '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
             f'<title>{esc(title)} — TransHimalaya</title>\n'
             f'<meta name="description" content="{esc(desc)}">\n'
             '<link rel="icon" href="assets/img/logo-mark.png">\n'
             '<link rel="stylesheet" href="assets/css/base.css">\n'
             '<link rel="stylesheet" href="assets/css/authors.css">\n</head>\n'
             f'<body>\n<div class="th-site">\n{sprite}{header}\n{body}\n{tail}</div>\n'
             '<script src="assets/js/site.js"></script>\n</body>\n</html>\n')
        open(fn, 'w', encoding='utf-8').write(s)
        o, c = s.count('<div'), s.count('</div>')
        return 'OK' if o == c else f'MISMATCH {o}/{c}'

    names = sorted(set(list(bios) + list(by_author)), key=sortkey)
    cards = []

    for name in names:
        slug = slugify(name)
        bio = bios.get(name, '')
        role = role_from(bio, name)
        works = by_author.get(name, [])
        photo = f'assets/img/au-{slug}.jpg'
        has_photo = os.path.exists(photo)

        portrait = (f'<img class="portrait" src="{photo}" alt="" width="180" height="180">'
                    if has_photo else
                    f'<span class="portrait is-initials" aria-hidden="true">'
                    f'{esc(first_name(name)[0])}{esc(name.split()[-1][0])}</span>')

        items = '\n'.join(f'''          <li>
            <a href="{a['slug']}.html">
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
        <p class="crumb"><a href="authors.html">Authors</a></p>
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
        flag = shell(f'author-{slug}.html', name,
                     bio[:150] or f'{name}, contributor to TransHimalaya.', body)
        n = len(works)
        print(f"  author-{slug:34} {n} article{'' if n == 1 else 's':<2} "
              f"{'photo' if has_photo else 'initials':>8}  {flag}")

        av = (f'<span class="av"><img src="{photo}" alt="" width="120" height="120" loading="lazy"></span>'
              if has_photo else
              f'<span class="av is-initials" aria-hidden="true">'
              f'{esc(first_name(name)[0])}{esc(name.split()[-1][0])}</span>')
        blurb = (bio[:118] + '…') if len(bio) > 118 else bio
        cards.append(f'''        <li class="au-card">
          <a href="author-{slug}.html">
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
    print(f"\n  authors.html  {len(cards)} authors  "
          f"{shell('authors.html', 'Authors', 'Everyone writing for TransHimalaya.', index_body)}")


if __name__ == '__main__':
    main()
