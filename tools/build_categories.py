#!/usr/bin/env python3
"""Generate the section (category) pages for TransHimalaya.

Each section gets a page listing its articles: the most recent as a lead,
the rest as cards. Sections with nothing published yet get an honest empty
state rather than an empty grid.

    python3 tools/build_categories.py

Writes content/section/<slug>.html; run tools/build.py afterwards to assemble
the pages. Run from the site root. Reads tools/articles.json.
"""

import html, json, os, re, sys
import content as C
import paths as P
import sections as S

# slug -> (page title, standfirst). The standfirst copy is ours, not the
# client's, and should be approved before launch.
SECTIONS = [
    ('in-focus', 'In Focus',
     'The journal&#39;s long-form scholarship on Tibet and the Himalaya — history, '
     'politics, economy and society.',
     S.IN_FOCUS),

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


def data_attrs(a):
    """Filter/search hooks used by the In Focus filter bar."""
    hay = f"{a['title']} {a['author']} {a['section']}".lower()
    return (f' data-topic="{S.slug(a["section"])}"'
            f' data-search="{esc(hay)}"')


def lead_card(a):
    return f'''        <article class="cat-lead"{data_attrs(a)}>
          <a class="ph" href="{S.article_url(a['slug'])}" style="background-image:url({P.asset(a['lede'])})"></a>
          <div class="b">
            <p class="k">{esc(a['section'])}</p>
            <h2><a href="{S.article_url(a['slug'])}">{esc(a['title'])}</a></h2>
            <div class="meta">
              <span><svg class="ic" aria-hidden="true"><use href="#ic-cal"/></svg> {pretty(a['date'])}</span>
              <span>·</span><span>By {esc(a['author'])}</span>
            </div>
          </div>
        </article>'''


def card(a):
    return f'''          <article class="th-card"{data_attrs(a)}>
            <a class="ph" href="{S.article_url(a['slug'])}" style="background-image:url({P.asset(a['lede'])})"></a>
            <div class="b">
              {S.chip(a['section'], 'th-chip card-chip')}
              <h3><a href="{S.article_url(a['slug'])}">{esc(a['title'])}</a></h3>
              <p>{esc(S.excerpt(a['slug']))}</p>
              <div class="meta">
                <span><svg class="ic" aria-hidden="true"><use href="#ic-cal"/></svg> {short(a['date'])}</span>
                <span>·</span><span>By {esc(a['author'])}</span>
              </div>
            </div>
          </article>'''



def initials(name):
    parts = [w for w in re.split(r'\s+', name) if w]
    return esc((parts[0][:1] + (parts[-1][:1] if len(parts) > 1 else '')).upper())


def people_grid(items):
    """Youth Voices is a set of contributors answering one question, so its
    section page introduces the people rather than listing headlines."""
    cards = []
    for a in items:
        img = a.get('lede')
        av = (f'<span class="pt"><img src="{P.asset(img)}" alt="" width="96" '
              f'height="96" loading="lazy"></span>' if img else
              f'<span class="pt ini" aria-hidden="true">{initials(a["title"])}</span>')
        cards.append(f"""          <li class="cat-person">
            <a href="{S.article_url(a['slug'])}">
              {av}
              <span class="nm">{esc(a['title'])}</span>
              <span class="rl">{esc(a.get('place') or a['author'])}</span>
            </a>
          </li>""")
    return ('        <ul class="cat-people">\n' + '\n'.join(cards)
            + '\n        </ul>\n')


def filter_bar(items):
    """Topic filter + search, shown on In Focus where several topics gather."""
    topics = []
    for a in items:
        if a['section'] not in topics:
            topics.append(a['section'])
    topics.sort()
    buttons = '\n'.join(
        f'            <button type="button" class="cf-btn cat-{S.slug(t)}" '
        f'data-filter="{S.slug(t)}">{esc(t)}</button>' for t in topics)
    return f'''        <div class="cat-filter" data-catfilter>
          <div class="cf-topics">
            <button type="button" class="cf-btn is-on" data-filter="all">All</button>
{buttons}
          </div>
          <div class="cf-search">
            <input type="search" placeholder="Search this section…" aria-label="Search articles">
          </div>
          <p class="cf-count" aria-live="polite"></p>
        </div>
'''


def main():
    if not os.path.exists('content/manifest.json'):
        sys.exit('run this from the site root')
    arts = json.load(open('tools/articles.json'))
    manifest = C.load()

    for slug, title, lede, children in SECTIONS:
        if children:                       # a parent section gathers its children
            items = [a for a in arts if a['section'] in children or a['section'] == title]
        else:
            items = [a for a in arts if a['section'] == title]
        items.sort(key=lambda a: a['date'], reverse=True)

        if items and slug == 'youth':
            body = people_grid(items)
            count = (f'<p class="cat-count">{len(items)} '
                     f'{"contributor" if len(items) == 1 else "contributors"}</p>')
        elif items and children:
            # a gathering page (In Focus): filter + search over uniform cards,
            # newest first, so more topics can be added in later editions
            grid = ('        <div class="th-cards cat-grid">\n' +
                    '\n'.join(card(a) for a in items) + '\n        </div>\n')
            body = f'{filter_bar(items)}\n{grid}'
            count = (f'<p class="cat-count">{len(items)} '
                     f'{"article" if len(items) == 1 else "articles"}</p>')
        elif items:
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
                    'meantime, read the <a href="/journal-editions/">current edition</a> or browse '
                    '<a href="/sections/in-focus/">In Focus</a>.</p>\n'
                    '        </div>\n')
            count = ''

        fragment = f"""
      <div class="cat">
        <header class="cat-head">
          <p class="k">Section</p>
          <h1>{esc(title)}</h1>
          <p class="lede">{lede}</p>
          {count}
        </header>

{body}      </div>

"""
        C.write('section', slug, title, re.sub(r'&#39;', "'", lede), fragment,
                manifest=manifest)
        print(f"  {slug:26} {len(items):3d} articles")

    C.save(manifest)


if __name__ == '__main__':
    main()
