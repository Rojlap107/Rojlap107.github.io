#!/usr/bin/env python3
"""Generate a profile page for each patron and trustee of FNVA.

Unlike the author pages, these people do not appear in the WordPress export —
they write no articles — so their details live here. The pages reuse the same
profile shell (and authors.css) as the author pages, with the group name
(Patron / Trustee) as the kicker in place of "Author" and no article list.

    python3 tools/build_team.py

Run from the site root. Bios are drafts drawn from public roles and should be
checked with FNVA before publication.
"""

import html, os, re, sys, unicodedata

# name, group, role (one line under the name), bio
PEOPLE = [
    dict(
        name='B. P. Singh',
        group='Patron',
        role='Former Home Secretary, Government of India',
        bio='B. P. Singh served as Home Secretary to the Government of India, '
            'part of a long career in public administration. He is a patron of '
            'the Foundation for Non-violent Alternatives.',
    ),
    dict(
        name='Ven. Samdhong Lobsang Tenzin Rinpoche',
        group='Patron',
        role='Former Kalon Tripa, Central Tibetan Administration',
        bio='A Tibetan Buddhist monk, scholar and statesman, Samdhong Rinpoche '
            'was the first directly elected Kalon Tripa — the political head of '
            'the Central Tibetan Administration — serving from 2001 to 2011. A '
            'lifelong exponent of Gandhian non-violence and Buddhist philosophy, '
            'he has taught and written widely on both.',
    ),
    dict(
        name='Amb. Shyam Saran',
        group='Trustee',
        role='Former Foreign Secretary, Government of India',
        bio='A career diplomat, Shyam Saran served as Foreign Secretary of India '
            'from 2004 to 2006, and subsequently as the Prime Minister’s Special '
            'Envoy on the civil nuclear agreement and on climate change. He has '
            'since chaired and advised a number of institutions on foreign affairs '
            'and strategic questions.',
    ),
    dict(
        name='Prof. Srikanth Kondapalli',
        group='Trustee',
        role='Professor of Chinese Studies, Jawaharlal Nehru University',
        bio='One of India’s foremost analysts of China, Srikanth Kondapalli is '
            'Professor in Chinese Studies at the School of International Studies, '
            'Jawaharlal Nehru University, where he has also served as Dean. His '
            'research spans Chinese foreign and security policy, the People’s '
            'Liberation Army, and China’s relations with South Asia.',
    ),
]

HONORIFICS = ('lt general', 'lt gen', 'general', 'prof.', 'prof', 'dr.', 'dr',
              'amb.', 'amb', 'ven.', 'ven', 'mr.', 'ms.')


def esc(s):
    return html.escape(s, quote=False)


def slugify(name):
    n = ''.join(c for c in unicodedata.normalize('NFD', name) if not unicodedata.combining(c))
    return re.sub(r'-+', '-', re.sub(r'[^a-z0-9]+', '-', n.lower())).strip('-')


def initials(name):
    low = name.lower()
    for h in HONORIFICS:
        if low.startswith(h + ' '):
            name = name[len(h) + 1:]
            break
    parts = name.split()
    return (parts[0][0] + parts[-1][0]).upper()


def main():
    if not os.path.exists('index.html'):
        sys.exit('run this from the site root')

    idx = open('index.html', encoding='utf-8').read()
    sprite = re.search(r'  <svg width="0" height="0".*?</svg>\n', idx, re.S).group(0)
    header = re.search(r'      <!-- Header -->.*?</nav>\n', idx, re.S).group(0)
    tail = re.search(r'      <!-- Subscription · Razorpay -->.*?</footer>\n', idx, re.S).group(0)

    for p in PEOPLE:
        slug = slugify(p['name'])
        photo = f'assets/img/member-{slug}.jpg'
        portrait = (f'<img class="portrait" src="{photo}" alt="" width="180" height="180">'
                    if os.path.exists(photo) else
                    f'<span class="portrait is-initials" aria-hidden="true">{esc(initials(p["name"]))}</span>')

        body = f'''      <section class="au-profile">
        <p class="crumb"><a href="team.html">Team</a></p>
        <div class="au-hero">
          {portrait}
          <div>
            <p class="k">{esc(p['group'])}</p>
            <h1>{esc(p['name'])}</h1>
            <p class="rl">{esc(p['role'])}</p>
            <p class="bio">{esc(p['bio'])}</p>
          </div>
        </div>
      </section>
'''
        s = ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
             '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
             f'<title>{esc(p["name"])} — TransHimalaya</title>\n'
             f'<meta name="description" content="{esc(p["name"])} — {esc(p["role"])}.">\n'
             '<link rel="icon" href="assets/img/logo-mark.png">\n'
             '<link rel="stylesheet" href="assets/css/base.css">\n'
             '<link rel="stylesheet" href="assets/css/authors.css">\n</head>\n'
             f'<body>\n<div class="th-site">\n{sprite}{header}\n{body}\n{tail}</div>\n'
             '<script src="assets/js/site.js"></script>\n</body>\n</html>\n')
        open(f'member-{slug}.html', 'w', encoding='utf-8').write(s)
        o, c = s.count('<div'), s.count('</div>')
        print(f"  member-{slug:38} {p['group']:8}  {'OK' if o == c else f'MISMATCH {o}/{c}'}")


if __name__ == '__main__':
    main()
