#!/usr/bin/env python3
"""Rebuild the dynamic middle of the home page from tools/articles.json.

Replaces everything between the "Featured stories" marker and the
"About + Photo essay band" marker with:

    Opening            — Foreword, Editor's Note, Strategic Foresight
    Featured Stories   — one piece each from History, Tibet Today,
                         Tibet Beyond Borders (the newest of each)
    From the Field     — the most recent essays, with their topic chips

    python3 tools/build_home.py

Writes content/home/home.html; run tools/build.py afterwards to reassemble
index.html. Run from the site root.
"""

import html, json, os, re, sys
import paths as P
import sections as S

# The generated region runs from the first of these markers to END. "Opening"
# is preferred because it is the first thing this script emits — anchoring on
# "Featured stories" instead would leave the previous Opening block behind and
# duplicate it on every rerun.
START_MARKERS = ['      <!-- Opening -->', '      <!-- Featured stories -->']
END = '      <!-- About + Photo essay band -->'

MONTH = {'01': 'Jan', '02': 'Feb', '03': 'Mar', '04': 'Apr', '05': 'May',
         '06': 'Jun', '07': 'Jul', '08': 'Aug', '09': 'Sep',
         '10': 'Oct', '11': 'Nov', '12': 'Dec'}

# the three opening pieces, in the order the edition presents them
OPENING = ['foreword', 'editors-note', 'tibet-in-the-year-2048']

# Featured Stories: newest piece from each of these, in this order
FEATURED = ['History', 'Tibet Today', 'Tibet Beyond Borders']

def esc(s):
    return html.escape(s or '', quote=False)


def short(d):
    return f"{MONTH[d[5:7]]} {int(d[8:10])}, {d[:4]}"


def opening_card(a):
    return featured_card(a)          # the Opening uses the same card as Featured


def featured_card(a):
    return f'''          <article class="th-card">
            <a class="ph" href="{S.piece_url(a)}" style="background-image:url({P.asset(a['lede'])})"></a>
            <div class="b">
              {S.chip(a['section'], 'th-chip card-chip')}
              <h3><a href="{S.piece_url(a)}">{esc(a['title'])}</a></h3>
              <p>{esc(S.excerpt(a['slug']))}</p>
              <div class="meta"><span><svg class="ic" aria-hidden="true"><use href="#ic-cal"/></svg> {short(a['date'])}</span>{S.by_meta(a)}</div>
            </div>
          </article>'''


def field_item(a):
    return (f'            <div class="item"><div class="thumb" style="background-image:url({P.asset(a["lede"])})"></div>'
            f'<div><h4><a href="{S.piece_url(a)}">{esc(a["title"])}</a></h4>'
            f'<div class="r">{S.chip(a["section"])}'
            f'<span class="date">{short(a["date"])}</span></div></div></div>')


def main():
    if not os.path.exists('content/manifest.json'):
        sys.exit('run this from the site root')
    arts = json.load(open('tools/articles.json'))
    by_slug = {a['slug']: a for a in arts}
    newest = sorted(arts, key=lambda a: a['date'], reverse=True)

    # ---- Opening -------------------------------------------------------
    opening = [by_slug[s] for s in OPENING if s in by_slug]
    op_html = '\n'.join(opening_card(a) for a in opening)

    # ---- Featured: newest of each of the three In Focus topics ----------
    feat = []
    for sec in FEATURED:
        pick = next((a for a in newest if a['section'] == sec), None)
        if pick:
            feat.append(pick)
    feat_html = '\n'.join(featured_card(a) for a in feat)

    # ---- From the Field: newest essays, excluding the opening pieces ----
    skip = set(OPENING) | {a['slug'] for a in feat}
    field = [a for a in newest
             if a['slug'] not in skip and a['section'] in S.PAGES][:4]
    field_html = '\n'.join(field_item(a) for a in field)

    block = f'''      <!-- Opening -->
      <section class="th-sec th-opening-sec">
        <h2 class="th-h2">Opening</h2>
        <div class="th-div"><i></i><b></b><i></i></div>
        <div class="th-cards">
{op_html}
        </div>
      </section>

      <!-- Featured stories -->
      <section class="th-sec" style="padding-top:0">
        <h2 class="th-h2">Featured Stories</h2>
        <div class="th-div"><i></i><b></b><i></i></div>
        <div class="th-cards">
{feat_html}
        </div>
      </section>

      <!-- From the field -->
      <section class="th-sec" style="padding-top:0">
        <div class="th-field">
          <h3 class="th-h3">From the Field</h3>
          <div class="th-divL"><i></i><b></b></div>
          <div class="th-fieldlist">
{field_html}
          </div>
          <div style="margin-top:16px"><a href="/sections/in-focus/" style="color:var(--teal);font-weight:600;font-size:14px;text-decoration:none">Browse In Focus →</a></div>
        </div>
      </section>

'''

    src = 'content/home/home.html'
    page = open(src, encoding='utf-8').read()
    start = next((m for m in START_MARKERS if m in page), None)
    if not start or END not in page:
        sys.exit(f'home page markers not found in {src}')
    head = page.split(start, 1)[0]
    tail = page.split(END, 1)[1]
    open(src, 'w', encoding='utf-8').write(head + block + END + tail)

    print(f"  opening   {len(opening)} pieces: " + ', '.join(a['section'] for a in opening))
    print(f"  featured  {len(feat)} cards:   " + ', '.join(a['section'] for a in feat))
    print(f"  field     {len(field)} items")


if __name__ == '__main__':
    main()
