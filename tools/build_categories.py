#!/usr/bin/env python3
"""Generate the section (category) pages for TransHimalaya.

Each section gets a page listing its articles: the most recent as a lead,
the rest as cards. Sections with nothing published yet get an honest empty
state rather than an empty grid.

    python3 tools/build_categories.py

Run from the site root. Reads tools/articles.json, written by build_articles.py.
"""

import html, json, os, re, sys

# slug -> (page title, standfirst). The standfirst copy is ours, not the
# client's, and should be approved before launch.
SECTIONS = [
    ('main-essays', 'Main Essays',
     'The magazine&#39;s long-form scholarship on Tibet and the Himalaya — history, '
     'politics, economy and society.',
     ['Tibet Today', 'Tibet Beyond Borders', 'History']),

    ('tibet-today', 'Tibet Today',
     'Reporting and analysis on conditions inside Tibet: governance, surveillance, '
     'economy and the texture of daily life.', None),

    ('tibet-beyond-borders', 'Tibet Beyond Borders',
     'Exile and diaspora — the institutions, language and political thought that carry '
     'Tibetan life beyond the plateau.', None),

    ('history', 'History',
     'The record: treaties, frontiers and the long relationship between Tibet, India '
     'and China.', None),

    ('the-strategic-triangle', 'The Strategic Triangle',
     'India, Tibet and the PRC — security, diplomacy and the contested Himalayan '
     'frontier.', None),

    ('global-perspectives', 'Global Perspectives',
     'The region read from beyond it: Xinjiang, Southern Mongolia, Nepal, Bhutan and '
     'the wider Asian landscape.', None),

    ('youth', 'Youth',
     'Younger voices on Tibet and the Himalaya — new writing, new questions.', None),

    ('interviews', 'Interviews',
     'Conversations with the leaders, scholars and practitioners shaping Tibet&#39;s '
     'future.', None),

    ('tibet-monitor', 'Tibet Monitor',
     'A running record of developments inside Tibet, gathered and verified by the '
     'Foundation&#39;s researchers.', None),
]

MONTH = {'01': 'January', '02': 'February', '03': 'March', '04': 'April', '05': 'May',
         '06': 'June', '07': 'July', '08': 'August', '09': 'September',
         '10': 'October', '11': 'November', '12': 'December'}


def esc(s):
    return html.escape(s, quote=False)


def pretty(d):
    return f"{int(d[8:10])} {MONTH[d[5:7]]} {d[:4]}"


def short(d):
    return f"{int(d[8:10])} {MONTH[d[5:7]][:3]} {d[:4]}"


def lead_card(a):
    return f'''        <article class="cat-lead">
          <a class="ph" href="{a['slug']}.html" style="background-image:url({a['lede']})"></a>
          <div class="b">
            <p class="k">{esc(a['section'])}</p>
            <h2><a href="{a['slug']}.html">{esc(a['title'])}</a></h2>
            <div class="meta">
              <span><svg class="ic" aria-hidden="true"><use href="#ic-cal"/></svg> {pretty(a['date'])}</span>
              <span>·</span><span>By {esc(a['author'])}</span>
            </div>
          </div>
        </article>'''


def card(a):
    return f'''          <article class="th-card">
            <a class="ph" href="{a['slug']}.html" style="background-image:url({a['lede']})"></a>
            <div class="b">
              <h3><a href="{a['slug']}.html">{esc(a['title'])}</a></h3>
              <div class="meta">
                <span><svg class="ic" aria-hidden="true"><use href="#ic-cal"/></svg> {short(a['date'])}</span>
                <span>·</span><span>By {esc(a['author'])}</span>
              </div>
            </div>
          </article>'''


def main():
    if not os.path.exists('index.html'):
        sys.exit('run this from the site root')
    arts = json.load(open('tools/articles.json'))

    idx = open('index.html', encoding='utf-8').read()
    sprite = re.search(r'  <svg width="0" height="0".*?</svg>\n', idx, re.S).group(0)
    header = re.search(r'      <!-- Header -->.*?</nav>\n', idx, re.S).group(0)
    tail = re.search(r'      <!-- Newsletter -->.*?</footer>\n', idx, re.S).group(0)

    for slug, title, lede, children in SECTIONS:
        if children:                       # a parent section gathers its children
            items = [a for a in arts if a['section'] in children or a['section'] == title]
        else:
            items = [a for a in arts if a['section'] == title]
        items.sort(key=lambda a: a['date'], reverse=True)

        if items:
            rest = items[1:]
            grid = ('' if not rest else
                    '        <div class="th-cards cat-grid">\n' +
                    '\n'.join(card(a) for a in rest) + '\n        </div>\n')
            body = (f'{lead_card(items[0])}\n\n{grid}')
            count = (f'<p class="cat-count">{len(items)} '
                     f'{"article" if len(items) == 1 else "articles"}</p>')
        else:
            body = ('        <div class="cat-empty">\n'
                    '          <p class="ttl">Nothing published here yet</p>\n'
                    f'          <p>{title} will carry its first pieces shortly. In the '
                    'meantime, read the <a href="journal-issue.html">current issue</a> or browse '
                    '<a href="main-essays.html">Main Essays</a>.</p>\n'
                    '        </div>\n')
            count = ''

        page = f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)} — TransHimalaya</title>
<meta name="description" content="{re.sub(r'&#39;', "'", lede)}">
<link rel="icon" href="assets/img/logo-mark.png">
<link rel="stylesheet" href="assets/css/base.css">
<link rel="stylesheet" href="assets/css/category.css">
</head>
<body>
<div class="th-site">
{sprite}{header}
      <div class="cat">
        <header class="cat-head">
          <p class="k">Section</p>
          <h1>{esc(title)}</h1>
          <p class="lede">{lede}</p>
          {count}
        </header>

{body}      </div>

{tail}</div>
<script src="assets/js/site.js"></script>
</body>
</html>
'''
        with open(f'{slug}.html', 'w', encoding='utf-8') as fh:
            fh.write(page)
        o, c = page.count('<div'), page.count('</div>')
        flag = 'OK' if o == c else f'MISMATCH {o}/{c}'
        print(f"  {slug:26} {len(items):3d} articles  {flag}")


if __name__ == '__main__':
    main()
