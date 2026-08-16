#!/usr/bin/env python3
"""Rebuild article pages from the finalised 1st-issue Word documents.

Each essay's .docx (under ~/Desktop/Tenzin Paljor/FNVA/1st Issue) is converted
with pandoc, its embedded figures extracted into assets/img/issue/<slug>/, and a
page emitted with article.tpl.html — matching the existing article design
(.art-fig figures, <h2> sub-heads, About-the-author bio). Slugs, titles,
authors, sections and the Must-Read / You-may-also-like rails come from
tools/articles.json so the contents page and author pages keep resolving.

    python3 tools/build_issue.py            # all mapped essays
    python3 tools/build_issue.py --only tibet-was-never-part-of-china

Run from the site root.
"""

import argparse, html, json, os, re, subprocess, sys

ISSUE = os.path.expanduser("~/Desktop/Tenzin Paljor/FNVA/1st Issue")
MEDIA_ROOT = "assets/img/issue"

# slug (as in articles.json) -> path of the finalised .docx, relative to ISSUE
DOCX = {
  'the-mcmahon-shatra-line':
    'S2_ HISTORY AND FOUNDATIONAL/Claude Arpi/CLAUDE ARPI.docx',
  'tibet-was-never-part-of-china':
    'S2_ HISTORY AND FOUNDATIONAL/Hon-shiang Lau/HON-SHINAG LAU.docx',
  'a-brief-overview-of-india-tibet-cultural-relations-and-its-legacies':
    'S2_ HISTORY AND FOUNDATIONAL/Jampa Samten/Jampa Samten_Finalised_11-06-2026.docx',
  'what-the-fire-knew':
    'S3_ INSIDE TIBET/Bhuchung D. Sonam/Bhuchung D. Sonam_14-05-2026 (4).docx',
  'chinas-colonial-polices-and-its-practice-in-tibet':
    'S3_ INSIDE TIBET/Dr. Gyal Lo/Gyal Lo_Finalised_13-06-2026.docx',
  'the-political-economy-of-tibet-under-the-peoples-republic-of-china':
    'S3_ INSIDE TIBET/Gabriel Lafitte/Gabriel Lafitte_19-05-2026_finalised.docx',
  'sacred-authority-state-power-and-indias-strategic-geometry-the-dalai-lama-institution-in-a-global-context':
    'S3_ INSIDE TIBET/Kate Saunders/Kate Saunders_Finalised_13-06-2026.docx',
  'the-plateaus-quiet-revolt-geography-identity-and-the-elusive-quest-to-close-tibet':
    'S3_ INSIDE TIBET/Sriparna Pathak/Sriparna Pathak (3).docx',
  'tibet-under-watch-chinas-digital-repression':
    'S3_ INSIDE TIBET/Tenzin Dalha/Tenzin Dalha (1).docx',
  'beyond-exile-governance-the-strategic-evolution-of-the-central-tibetan-administration':
    'S4_ TIBET IN EXILE/Bhuchung K. Tsering/Bhuchung Tsering_edited (2).docx',
  'tenshug-offering-by-civil-society-in-dharamshala-ritual-as-action-for-the-tibet-cause':
    'S4_ TIBET IN EXILE/Jyotsna Roy/Jyotsna Roy_19-05-2026_Finalised.doc',
  'the-dalai-lamas-reincarnation-future-dynamics-in-sino-tibetan-conflict-and-geo-political-consequences':
    'S4_ TIBET IN EXILE/Kelsang Gyaltsen/Kelsang Gyaltsen (1).docx',
  'the-middle-way-as-statecraft-tibetan-political-philosophy-in-an-age-of-power-asymmetry':
    'S4_ TIBET IN EXILE/Rinzin Namgyal/Rinzin Namgyal_18-05-2026_Finalised.docx',
  'the-role-of-monlam-in-preserving-tibetan-language-in-the-digital-space':
    'S4_ TIBET IN EXILE/Tenzin Thinley/Tenzin Thinley_11-06-2026_Finalised.docx',
  'how-should-india-prepare-and-respond-to-the-passing-away-of-the-14th-dalai-lama-a-strategic-appraisal-in-a-time-of-uncertainty':
    'S5_ STRATEGIC TRIANGLE- INDIA TIBET AND THE PRC/Amb. Anil Wadhwa/AMBASSADOR Anil Wadhwa (1).docx',
  'india-and-the-tibet-question-shelter-strategy-and-the-future-of-policy':
    'S5_ STRATEGIC TRIANGLE- INDIA TIBET AND THE PRC/Amb. Dilip Sinha/Ambassador Dilip Sinha (2).docx',
  'high-altitude-high-stakes-military-posture-and-escalation-dynamics-along-the-himalayan-frontier':
    'S5_ STRATEGIC TRIANGLE- INDIA TIBET AND THE PRC/Lt. General Vinod Bhatia/Gen Bhatia_finalised (1).docx',
  'chinas-politics-of-toponyms-in-tibet-and-beyond-strategic-concern-for-india':
    'S5_ STRATEGIC TRIANGLE- INDIA TIBET AND THE PRC/Tenzing Dhamdul/Tenzing Dhamdul_01-06-26_Finalised.docx',
  'nepals-strategic-reality-outlasts-its-political-upheaval':
    'S6_ REGIONAL AND INTERNATIONAL PERSPECTIVES/Biswas Baral/Biswas Baral (1).docx',
  'why-east-turkistan-xinjiang-matters-to-india':
    'S6_ REGIONAL AND INTERNATIONAL PERSPECTIVES/Dolkun Isa/Dolkun Isa.docx',
  'cultural-erasure-southern-mongolia-and-chinas-assimilation-strategy':
    'S6_ REGIONAL AND INTERNATIONAL PERSPECTIVES/Enghebatu Togochog/Enghebatu Togochog_finalised.docx',
  'xi-jinpings-ten-commandments-for-governing-tibet':
    'S6_ REGIONAL AND INTERNATIONAL PERSPECTIVES/Prof. Ming Xia/Prof.Ming Xia (2).docx',
  'living-between-giants-lessons-from-bhutans-strategic-experience':
    'S6_ REGIONAL AND INTERNATIONAL PERSPECTIVES/Tenzing Lamsang/Tenzing Lamsang (2).docx',
}


def esc(s):
    return html.escape(s, quote=False)


def text(x):
    return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', x or '')).strip()


MONTH = {'01': 'January', '02': 'February', '03': 'March', '04': 'April', '05': 'May',
         '06': 'June', '07': 'July', '08': 'August', '09': 'September',
         '10': 'October', '11': 'November', '12': 'December'}


def pretty(d):
    return f"{int(d[8:10])} {MONTH[d[5:7]]} {d[:4]}"


# ----------------------------------------------------------------- inline markdown

def inline(s):
    """Convert a run of pandoc-markdown inline text to safe HTML."""
    s = re.sub(r'\\([\\`*_{}\[\]()#+.!\'"-])', r'\1', s)   # drop backslash escapes
    # protect links first
    links = []
    def stash_link(m):
        links.append((m.group(1), m.group(2)))
        return f'\x00{len(links)-1}\x00'
    s = re.sub(r'\[([^\]]+)\]\((https?://[^)]+)\)', stash_link, s)
    s = re.sub(r'\[\]\{[^}]*\}', '', s)                   # empty pandoc spans
    s = re.sub(r'\[([^\]]*)\]\{[^}]*\}', r'\1', s)        # [text]{.underline} -> text
    s = s.replace('[]', '')
    s = s.replace('---', '—').replace('--', '–')          # em / en dashes
    s = esc(s)
    s = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', s)
    s = re.sub(r'(?<!\*)\*(?!\s)(.+?)(?<!\s)\*(?!\*)', r'<em>\1</em>', s)
    s = re.sub(r'\^([^^]+)\^', r'<sup>\1</sup>', s)         # superscripts
    def put_link(m):
        t, u = links[int(m.group(1))]
        return f'<a href="{esc(u)}" rel="noopener">{esc(t)}</a>'
    s = re.sub(r'\x00(\d+)\x00', put_link, s)
    return s


IMG_RE = re.compile(r'!\[[^\]]*\]\(([^)]+?)\)(\{[^}]*\})?')


def img_path(block):
    m = IMG_RE.search(block)
    return m.group(1) if m else None


def is_bold_head(b):
    b = b.strip()
    return (b.startswith('**') and b.endswith('**') and b.count('**') == 2
            and len(text(b)) < 90 and not b.endswith(':**') is None)


def build_body(md, slug):
    """Return (body_html, bio_text, first_landscape_image_or_None)."""
    # split off the author bio
    parts = re.split(r'(?im)^\s*\**\s*about the author\s*:?\s*\**\s*$', md, maxsplit=1)
    if len(parts) == 1:
        parts = re.split(r'(?i)\bAbout the Author\b\s*:?', md, maxsplit=1)
    body_md = parts[0]
    bio = text(inline(parts[1])) if len(parts) > 1 else ''
    bio = re.sub(r'!\[[^\]]*\]\([^)]*\)(\{[^}]*\})?', '', bio).strip()

    blocks = [b.strip() for b in re.split(r'\n\s*\n', body_md) if b.strip()]

    # drop a trailing lone image — the author headshot glued before the bio —
    # but keep a genuine final figure (one preceded by a Figure/caption/source line)
    def is_figpart(b):
        bt = b.strip()
        return bool(re.match(r'(?i)^figure\s+\d', bt)
                    or (bt.startswith('*') and bt.endswith('*'))
                    or re.match(r'(?i)^\**\s*source', bt))
    if blocks and IMG_RE.search(blocks[-1]) and not IMG_RE.sub('', blocks[-1]).strip():
        if len(blocks) < 2 or not is_figpart(blocks[-2]):
            blocks.pop()

    out, pending = [], []          # pending holds fignum/caption lines before an image
    first_img = [None]

    def flush_pending():
        for kind, val in pending:
            if kind == 'fignum':
                out.append(f'        <p><strong>{esc(val)}</strong></p>')
            elif kind == 'caption':
                out.append(f'        <p><em>{inline(val)}</em></p>')
            elif kind == 'source':
                out.append(f'        <p class="src">{inline(val)}</p>')
        pending.clear()

    def emit_figure(path, extra_source=None):
        cap_bits, fignum = [], None
        for kind, val in pending:
            if kind == 'fignum':
                fignum = val
            elif kind == 'caption':
                cap_bits.append(inline(val))
            elif kind == 'source':
                cap_bits.append(f'<span class="src">Source: {inline(val)}</span>')
        pending.clear()
        if extra_source:
            cap_bits.append(f'<span class="src">Source: {inline(extra_source)}</span>')
        label = f'<b>{esc(fignum)}</b> · ' if fignum else ''
        cap = ' — '.join(x for x in cap_bits if x)
        figcap = (f'\n          <figcaption>{label}{cap}</figcaption>'
                  if (label or cap) else '')
        out.append(f'        <figure class="art-fig">\n'
                   f'          <img src="{path}" alt="" loading="lazy">{figcap}\n'
                   f'        </figure>')

    for b in blocks:
        m = IMG_RE.search(b)
        if m:                       # an image block (maybe with a trailing source)
            local = m.group(1)
            trailing = IMG_RE.sub('', b).strip()
            src = None
            if re.match(r'(?i)\**\s*source', trailing):
                src = re.sub(r'(?i)^\**\s*source\s*:?\s*', '', trailing).strip(' *')
            if first_img[0] is None:
                first_img[0] = local
            emit_figure(local, src)
            continue
        bt = b.strip()
        if re.match(r'(?i)^figure\s+\d', bt) and len(bt) < 60:
            pending.append(('fignum', bt)); continue
        if re.match(r'(?i)^\**\s*source\b', bt):
            srctext = re.sub(r'(?i)^\**\s*source\s*:?\s*', '', bt).strip(' *')
            if out and out[-1].lstrip().startswith('<figure class="art-fig">'):
                span = f'<span class="src">Source: {inline(srctext)}</span>'
                if '<figcaption>' in out[-1]:
                    out[-1] = out[-1].replace('</figcaption>', f' — {span}</figcaption>')
                else:
                    out[-1] = out[-1].replace(
                        '        </figure>',
                        f'          <figcaption>{span}</figcaption>\n        </figure>')
            else:
                pending.append(('source', srctext))
            continue
        if bt.startswith('*') and bt.endswith('*') and bt.count('*') == 2 and len(bt) < 220:
            pending.append(('caption', bt.strip('*'))); continue
        # not a figure component -> flush any pending as plain paragraphs
        flush_pending()
        if bt.startswith('>'):
            q = inline(re.sub(r'^\s*>\s?', '', bt, flags=re.M))
            out.append(f'        <blockquote class="art-pull"><p>{q}</p></blockquote>')
        elif bt.startswith('**') and bt.endswith('**') and bt.count('**') == 2 and len(text(bt)) < 90:
            out.append(f'        <h2>{inline(bt.strip("*"))}</h2>')
        elif re.match(r'^#{1,6}\s', bt):
            out.append(f'        <h2>{inline(re.sub(r"^#{1,6}\\s+", "", bt))}</h2>')
        else:
            out.append(f'        <p>{inline(bt)}</p>')
    flush_pending()
    return '\n'.join(out), bio, first_img[0]


# ----------------------------------------------------------------- page assembly

def convert_docx(path, slug):
    media = os.path.join(MEDIA_ROOT, slug)
    os.makedirs(media, exist_ok=True)
    src = path
    if path.lower().endswith('.doc'):        # legacy binary .doc — macOS textutil reads it
        tmp = os.path.join(media, '_src.docx')
        subprocess.run(['textutil', '-convert', 'docx', path, '-output', tmp],
                       capture_output=True)
        if os.path.exists(tmp):
            src = tmp
    md = subprocess.run(['pandoc', src, '-t', 'markdown', '--wrap=none',
                         f'--extract-media={media}'],
                        capture_output=True, text=True).stdout
    # resize / strip any oversized extracted figures
    mdir = os.path.join(media, 'media')
    if os.path.isdir(mdir):
        for fn in os.listdir(mdir):
            fp = os.path.join(mdir, fn)
            subprocess.run(['magick', fp, '-resize', '1500x1500>', '-strip',
                            '-quality', '82', fp],
                           capture_output=True)
    return md


def standfirst(body_html):
    m = re.search(r'<p[^>]*>(.*?)</p>', body_html, re.S)
    if not m:
        return ''
    s = text(m.group(1))
    parts = re.split(r'(?<=[a-z)’"])\.\s+(?=[A-Z])', s)
    out = parts[0]
    if len(out) < 110 and len(parts) > 1:
        out += '. ' + parts[1]
    return out.rstrip('.') + '.'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--only')
    args = ap.parse_args()

    if not os.path.exists('index.html'):
        sys.exit('run from the site root')

    tpl = open('tools/article.tpl.html', encoding='utf-8').read()
    arts = {a['slug']: a for a in json.load(open('tools/articles.json'))}

    # author portraits + fallback bios (from the already-built author pages)
    author_img, author_bio = {}, {}
    from build_articles import author_slug
    for a in arts.values():
        aslug = author_slug(a['author'])
        p = f"assets/img/au-{aslug}.jpg"
        if os.path.exists(p):
            author_img[a['author']] = p
        apage = f"author-{aslug}.html"
        if os.path.exists(apage):
            m = re.search(r'<p class="bio">(.*?)</p>', open(apage, encoding='utf-8').read(), re.S)
            if m:
                author_bio[a['author']] = text(m.group(1))

    slugs = [args.only] if args.only else list(DOCX)
    for slug in slugs:
        if slug not in DOCX:
            print(f"  ! no docx mapped for {slug}"); continue
        post = arts[slug]
        docx = os.path.join(ISSUE, DOCX[slug])
        if not os.path.exists(docx):
            print(f"  ! missing {docx}"); continue

        md = convert_docx(docx, slug)
        body, bio, first_img = build_body(md, slug)
        if not bio:                      # docx had no "About the Author" — reuse author-page bio
            bio = author_bio.get(post['author'], '')
        lede = post.get('lede') or f'assets/img/hero-bg.jpg'

        others = [p for s, p in arts.items() if s != slug]
        mr = '\n'.join(
            f'            <li><a href="{p["slug"]}.html"><span class="t">{esc(p["title"])}</span>'
            f'<span class="m">{esc(p["author"])} · {esc(p["section"])}</span></a></li>'
            for p in others[:5])
        same = [p for p in others if p['section'] == post['section']]
        rel_posts = (same + [p for p in others if p not in same])[:3]
        rel = '\n'.join(f'''            <article class="th-card">
              <a class="ph" href="{p['slug']}.html" style="background-image:url({p.get('lede','assets/img/hero-bg.jpg')})"></a>
              <div class="b">
                <h3><a href="{p['slug']}.html">{esc(p['title'])}</a></h3>
                <div class="meta"><span><svg class="ic" aria-hidden="true"><use href="#ic-cal"/></svg> {pretty(p['date'])}</span><span>·</span><span>By {esc(p['author'])}</span></div>
              </div>
            </article>''' for p in rel_posts)

        av = author_img.get(post['author'], '')
        avatar = (f'<img class="av" src="{av}" alt="" width="44" height="44">' if av else '')
        author_pic = (f'<img src="{av}" alt="" width="96" height="96">' if av else '')
        words = len(text(body).split())

        page = (tpl
                .replace('{{TITLE}}', esc(post['title']))
                .replace('{{STANDFIRST}}', esc(standfirst(body)))
                .replace('{{SECTION}}', esc(post['section']))
                .replace('{{AUTHOR_HREF}}', 'author-' + author_slug(post['author']) + '.html')
                .replace('{{AUTHOR}}', esc(post['author']))
                .replace('{{DATE_ISO}}', post['date'])
                .replace('{{DATE}}', pretty(post['date']))
                .replace('{{MINS}}', str(max(2, round(words / 200))))
                .replace('{{LEDE}}', lede)
                .replace('{{AVATAR}}', avatar)
                .replace('{{AUTHOR_PIC}}', author_pic)
                .replace('{{BIO}}', esc(bio) or 'Contributor to TransHimalaya.')
                .replace('{{BODY}}', body)
                .replace('{{NOTES}}', '')
                .replace('{{MUSTREAD}}', mr)
                .replace('{{RELATED}}', rel))
        open(f'{slug}.html', 'w', encoding='utf-8').write(page)
        nfig = page.count('art-fig')
        print(f"  {slug[:44]:44} {words:5d}w  {nfig} fig  bio:{'y' if bio else '-'}")


if __name__ == '__main__':
    main()
