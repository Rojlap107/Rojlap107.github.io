#!/usr/bin/env python3
"""Assemble the Youth Voices page from the S8 documents.

Three reflections come bundled in one file, Kunga Norbu's in another. Each
becomes a titled section (with a portrait where we have one) on a single
youth-voices.html page; the contents page links to the anchors.

    python3 tools/build_youth.py
"""

import os, re, subprocess, json
import build_issue as bi

ISSUE = os.path.expanduser("~/Desktop/Tenzin Paljor/FNVA/1st Issue")
S8 = os.path.join(ISSUE, "S8_ YOUTH VOICES")
MEDIA = "assets/img/issue/youth-voices"

# name -> (anchor slug, source photo under S8 or None)
PEOPLE = [
    ('Tenzin Woesel',   'tenzin-woesel',   'tenzin woesel.jpeg'),
    ('Tenzin Yangchen', 'tenzin-yangchen', 'yangchen.jpeg'),
    ('Tenzin Yanki',    'tenzin-yanki',    None),
    ('Kunga Norbu',     'kunga-norbu',     'kunga norbu.jpeg'),
]


def md(path):
    return subprocess.run(['pandoc', path, '-t', 'markdown', '--wrap=none'],
                          capture_output=True, text=True).stdout


def paras(text_md):
    return [b.strip() for b in re.split(r'\n\s*\n', text_md) if b.strip()]


def portrait(src_name, slug):
    if not src_name:
        return None
    os.makedirs(MEDIA, exist_ok=True)
    out = f"{MEDIA}/{slug}.jpg"
    subprocess.run(['magick', os.path.join(S8, src_name), '-resize', '400x400^',
                    '-gravity', 'north', '-extent', '400x400', '-resize', '300x300',
                    '-strip', '-quality', '82', out], capture_output=True)
    return out if os.path.exists(out) else None


def clean_paras(blocks, name):
    """Body paragraphs and the trailing bio sentence, dropping images/labels."""
    body, bio = [], ''
    for b in blocks:
        if bi.IMG_RE.search(b):
            continue
        pl = bi.text(b)
        if not pl:
            continue
        # a trailing self-description is the bio
        if re.match(rf'(?i)^{re.escape(name)}\b', pl) and (' is ' in pl or ' serves ' in pl):
            bio = pl; continue
        if pl.lower().startswith('i am ') or pl.lower().startswith("i'm "):
            bio = pl; continue
        # drop the shared prompt / host-country / sources / role footer lines
        if re.match(r'(?i)^(host country|how the tibetan community|sources?\b)', pl):
            continue
        if len(pl) < 40 and (name.split()[-1] in pl or 'Secretary' in pl or 'Coordinator' in pl or 'Initiative' in pl):
            continue
        body.append(f'        <p>{bi.inline(b.strip("*"))}</p>')
    return body, bio


def section(name, slug, photo, body, bio):
    fig = (f'        <figure class="art-fig art-portrait">\n'
           f'          <img src="{photo}" alt="{bi.esc(name)}" loading="lazy">\n'
           f'        </figure>\n' if photo else '')
    biohtml = (f'        <p class="art-note"><em>{bi.inline(bio)}</em></p>\n' if bio else '')
    return (f'        <h2 id="{slug}">{bi.esc(name)}</h2>\n'
            f'{fig}' + '\n'.join(body) + '\n' + biohtml)


def main():
    three = paras(md(os.path.join(S8, "Youth Voices_ 3 Different Tibetans.docx")))
    kunga = paras(md(os.path.join(S8, "Kunga Youth voices.docx")))

    # split the bundled file on the italic name headers
    names3 = ['Tenzin Woesel', 'Tenzin Yangchen', 'Tenzin Yanki']
    idx = {}
    for i, b in enumerate(three):
        pl = re.sub(r'\*', '', bi.text(b)).strip()      # names come wrapped in *italics*
        for n in names3:
            if pl.lower() == n.lower():
                idx[n] = i
    pieces = {}
    order = sorted(idx, key=lambda n: idx[n])
    for j, n in enumerate(order):
        start = idx[n] + 1
        end = idx[order[j + 1]] if j + 1 < len(order) else len(three)
        pieces[n] = three[start:end]
    # Kunga: everything up to the trailing name/role footer
    pieces['Kunga Norbu'] = kunga

    body_parts = ['        <p>Four young Tibetans reflect on exile, identity and what '
                  'their community gives back to the places that gave it refuge.</p>']
    for name, slug, ph in PEOPLE:
        blk = pieces.get(name, [])
        body, bio = clean_paras(blk, name)
        photo = portrait(ph, slug)
        body_parts.append(section(name, slug, photo, body, bio))
        print(f"  {name:16} {'photo' if photo else 'no-photo':8} {len(body)} paras  bio:{'y' if bio else '-'}")
    body = '\n'.join(body_parts)

    tpl = open('tools/article.tpl.html', encoding='utf-8').read()
    arts = {a['slug']: a for a in json.load(open('tools/articles.json'))}
    meta = {'slug': 'youth-voices', 'title': 'Youth Voices', 'author': 'Youth Voices',
            'section': 'Youth', 'date': '2026-08-01',
            'lede': arts.get('youth-voices', {}).get('lede', 'assets/img/hero-bg.jpg')}
    bio = ('Reflections from young Tibetans on exile, identity and their '
           'contribution to their host communities.')
    bi.render_page(meta, body, bio, tpl, arts, {}, 'authors.html')
    print("  wrote youth-voices.html")


if __name__ == '__main__':
    main()
