#!/usr/bin/env python3
"""Build one article per Youth Voices contributor from the S8 documents.

Four young Tibetans answer the same question — how the Tibetan community in
their region has contributed to their host country. Three of the answers are
bundled in one document, Kunga Norbu's is in another. Each becomes its own
article, opening on its title with no photograph above it; the contributor's
portrait is their byline avatar and their card image on /sections/youth/.

    python3 tools/build_youth.py

Writes content/article/<slug>.html for each voice and refreshes their entries
in tools/articles.json. Run tools/build.py afterwards.
"""

import json, os, re, subprocess
import bios as B
import build_issue as bi
import content as C
import paths as P

ISSUE = os.path.expanduser("~/Desktop/Tenzin Paljor/FNVA/1st Issue")
S8 = os.path.join(ISSUE, "S8_ YOUTH VOICES")
MEDIA = "assets/img/issue/youth-voices"
DATE = '2026-08-01'

# the question every contributor was asked
PROMPT = ('How the Tibetan community in your region has contributed to '
          'your host country.')

# name, slug, host country, source portrait under S8 (None where we have none)
PEOPLE = [
    ('Tenzin Woesel',   'tenzin-woesel',   'India',  'tenzin woesel.jpeg'),
    ('Tenzin Yangchen', 'tenzin-yangchen', 'France', 'yangchen.jpeg'),
    ('Tenzin Yanki',    'tenzin-yanki',    'France', None),
    ('Kunga Norbu',     'kunga-norbu',     'India',  'kunga norbu.jpeg'),
]

BUNDLE = "Youth Voices_ 3 Different Tibetans.docx"
SOLO = "Kunga Youth voices.docx"


def md(path):
    return subprocess.run(['pandoc', path, '-t', 'markdown', '--wrap=none'],
                          capture_output=True, text=True).stdout


def paras(text_md):
    return [b.strip() for b in re.split(r'\n\s*\n', text_md) if b.strip()]


def portrait(src_name, slug):
    """A square portrait, used as the byline avatar and the card image."""
    if not src_name:
        return ''
    os.makedirs(MEDIA, exist_ok=True)
    out = f"{MEDIA}/{slug}.jpg"
    subprocess.run(['magick', os.path.join(S8, src_name), '-resize', '600x600^',
                    '-gravity', 'north', '-extent', '600x600', '-resize', '400x400',
                    '-strip', '-quality', '84', out], capture_output=True)
    return out if os.path.exists(out) else ''


def split_voice(blocks, name):
    """(body paragraphs, bio) for one contributor.

    The bio sits before the body for some contributors and after it for
    others, and the shared prompt, the host-country label, a trailing
    name-and-role sign-off and any 'Sources:' line are not part of either.
    """
    body, bio = [], ''
    for b in blocks:
        if bi.IMG_RE.search(b):
            continue
        pl = bi.text(b)
        if not pl:
            continue
        if re.match(r'(?i)^(host country|how the tibetan community)', pl):
            continue
        if re.match(r'(?i)^sources?\b', pl):
            continue
        # a self-description, wherever it falls, is the bio
        if re.match(rf'(?i)^{re.escape(name)}\b', pl) and re.search(r'\b(is|serves)\b', pl):
            bio = bio or pl
            continue
        if re.match(r"(?i)^(i am|i'm)\b", pl):
            bio = bio or pl
            continue
        # the sign-off: the name, or a short line naming their role
        if len(pl) < 60 and (name.split()[-1] in pl
                             or re.search(r'(?i)\b(secretary|coordinator|initiative)\b', pl)):
            continue
        body.append(f'        <p>{bi.inline(b.strip("*"))}</p>')
    return body, bio


def voices():
    """Every contributor's blocks, keyed by name."""
    bundle = paras(md(os.path.join(S8, BUNDLE)))
    names3 = [n for n, _, _, _ in PEOPLE if n != 'Kunga Norbu']
    at = {}
    for i, b in enumerate(bundle):
        pl = re.sub(r'\*', '', bi.text(b)).strip()   # names come italicised
        for n in names3:
            if pl.lower() == n.lower():
                at[n] = i
    out, order = {}, sorted(at, key=lambda n: at[n])
    for j, n in enumerate(order):
        end = at[order[j + 1]] if j + 1 < len(order) else len(bundle)
        out[n] = bundle[at[n] + 1:end]
    out['Kunga Norbu'] = paras(md(os.path.join(S8, SOLO)))
    return out


def main():
    if not os.path.exists('content/manifest.json'):
        raise SystemExit('run this from the site root')

    tpl = open('templates/fragments/article.html', encoding='utf-8').read()
    arts = json.load(open('tools/articles.json'))
    bi.MANIFEST = C.load()
    BIOS = B.seed()
    blocks = voices()

    slugs = {slug for _, slug, _, _ in PEOPLE}
    arts = [a for a in arts if a['slug'] not in slugs and a['slug'] != 'youth-voices']

    jobs = []
    for name, slug, place, src in PEOPLE:
        body, bio = split_voice(blocks.get(name, []), name)
        photo = portrait(src, slug)
        entry = {'slug': slug, 'title': name, 'author': name, 'date': DATE,
                 'section': 'Youth', 'lede': photo, 'place': place}
        arts.append(entry)
        jobs.append((entry, '\n'.join(body), bio, photo))
        print(f"  {name:16} {place:7} {'portrait' if photo else 'initials':9} "
              f"{len(body)} paras  bio:{'y' if bio else '-'}")

    arts.sort(key=lambda a: (a['date'], a['slug']), reverse=True)
    json.dump(arts, open('tools/articles.json', 'w'), indent=1, ensure_ascii=False)

    by_slug = {a['slug']: a for a in arts}
    for entry, body, bio, photo in jobs:
        B.merge({B.slug(entry['author']): bio}, BIOS)
        # `lede` empty: the piece opens on its title, with no photograph above.
        # The portrait still reaches the byline through author_img.
        meta = {**entry, 'lede': '', 'standfirst': PROMPT}
        bi.render_page(meta, body, B.best(B.slug(entry['author']), bio, BIOS),
                       tpl, by_slug, {entry['author']: photo} if photo else {},
                       # each contributor is an author of this issue, so
                       # build_authors always gives them a page to link to
                       P.url('author', B.slug(entry['author'])))

    # the combined page these were split out of
    C.prune('article', {a['slug'] for a in arts}, bi.MANIFEST)
    C.save(bi.MANIFEST)
    B.save(BIOS)
    print(f"  wrote {len(jobs)} youth articles")


if __name__ == '__main__':
    main()
