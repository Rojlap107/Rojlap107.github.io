#!/usr/bin/env python3
"""Rebuild the dynamic middle of the home page from tools/articles.json.

Replaces everything between the "Featured stories" marker and the
"About + Photo essay band" marker with:

    Opening            — Foreword, Editor's Note, Strategic Foresight
    Featured Stories   — one piece each from History, Tibet Today,
                         Tibet Beyond Borders (the newest of each)
    In Conversation    — the most recent filmed interview
    Youth Voices       — the contributors, as people rather than titles

    python3 tools/build_home.py

Writes content/home/home.html; run tools/build.py afterwards to reassemble
index.html. Run from the site root.
"""

import html, json, os, re, sys
import paths as P
import sections as S
import videos as V

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
            <a class="ph" href="{S.piece_url(a)}" style="background-image:url({P.asset(S.card_image(a))})"></a>
            <div class="b">
              {S.chip(a['section'], 'th-chip card-chip')}
              <h3><a href="{S.piece_url(a)}">{esc(a['title'])}</a></h3>
              <p>{esc(S.excerpt(a['slug']))}</p>
              <div class="meta"><span><svg class="ic" aria-hidden="true"><use href="#ic-cal"/></svg> {short(a['date'])}</span>{S.by_meta(a)}</div>
            </div>
          </article>'''


def initials(name):
    parts = [w for w in name.split() if w]
    return esc((parts[0][:1] + (parts[-1][:1] if len(parts) > 1 else '')).upper())


def voice_card(a):
    """A Youth Voices contributor: portrait or initials, name, host country."""
    img = S.card_image(a)
    face = (f'<span class="pt"><img src="{P.asset(img)}" alt="" width="96" '
            f'height="96" loading="lazy"></span>' if img else
            f'<span class="pt ini" aria-hidden="true">{initials(a["title"])}</span>')
    return f'''            <li class="th-person">
              <a href="{S.piece_url(a)}">
                {face}
                <span class="nm">{esc(a['title'])}</span>
                <span class="rl">{esc(a.get('place') or a['section'])}</span>
              </a>
            </li>'''


def youth_band(arts):
    """Four contributors answering one question. Titles alone left most of the
    row empty, so the home page introduces the people, as the section does."""
    voices = sorted([a for a in arts if a['section'] == 'Youth'],
                    key=lambda x: x['slug'])
    if not voices:
        return ''
    cards = '\n'.join(voice_card(a) for a in voices)
    return f'''      <!-- Youth Voices -->
      <section class="th-sec" style="padding-top:0">
        <h2 class="th-h2">Youth Voices</h2>
        <div class="th-div"><i></i><b></b><i></i></div>
        <p class="th-lede">Young Tibetans on what their community gives back to the countries that gave it refuge.</p>
        <ul class="th-people">
{cards}
        </ul>
        <div class="th-viewall"><a href="{S.page_for('Youth')}">All Youth Voices →</a></div>
      </section>

'''


def interview_band(arts):
    """The latest filmed conversation: its still on the left, and on the right
    the title, a trimmed description and a way straight into it."""
    filmed = [a for a in arts
              if a['section'] == 'Interviews' and V.has(a['slug'])]
    if not filmed:
        return ''
    a = max(filmed, key=lambda x: x['date'])
    url = S.piece_url(a)
    blurb = S.excerpt(a['slug'], 165)
    return f'''      <!-- Latest interview -->
      <section class="th-sec" style="padding-top:0">
        <h2 class="th-h2">In Conversation</h2>
        <div class="th-div"><i></i><b></b><i></i></div>
        <div class="th-watch">
{V.panel(a['slug'], cls='th-watch-vid', caption=False)}          <div class="b">
            {S.chip(a['section'], 'th-chip card-chip')}
            <h3><a href="{url}">{esc(a['title'])}</a></h3>
            <p>{esc(blurb)}</p>
            <a class="btn" href="{url}">Watch the interview</a>
          </div>
        </div>
      </section>

'''

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

{interview_band(arts)}{youth_band(arts)}'''

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
    print(f"  youth     {sum(1 for a in arts if a['section'] == 'Youth')} voices")


if __name__ == '__main__':
    main()
