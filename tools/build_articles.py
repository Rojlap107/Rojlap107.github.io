#!/usr/bin/env python3
"""Generate article pages for TransHimalaya from the WordPress export.

SUPERSEDED by tools/build_issue.py, which builds the same articles from the
finalised Word documents. Running this overwrites those pages with the older
WordPress text and rewrites tools/articles.json — only run it deliberately.

Reads the WXR file, converts each chosen post into an article page using the
site's own markup, and downloads the images it needs into assets/img/.

    python3 tools/build_articles.py            # the articles shown on the home page
    python3 tools/build_articles.py --all      # every published 2026 article

Writes content/article/<slug>.html; run tools/build.py afterwards.
Run from the site root.
"""

import argparse, html, json, os, re, subprocess, sys, unicodedata, urllib.request
import xml.etree.ElementTree as ET

import content as C
import paths as P
import sections as S

XML = os.path.expanduser("~/Downloads/transhimalaya.WordPress.2026-08-03.xml")
NS = {'wp': 'http://wordpress.org/export/1.2/',
      'dc': 'http://purl.org/dc/elements/1.1/',
      'content': 'http://purl.org/rss/1.0/modules/content/'}
IMG_DIR = "assets/img"

# Section shown on the article; the parent "In Focus" only applies when a
# post carries no more specific category.
SECTION = {
    'The Strategic Triangle: India Tibet and the PRC': 'The Strategic Triangle',
    'Regional and Global Perspectives': 'Global Perspectives',
    'Tibet Today': 'Tibet Today',
    'Tibet Beyond Borders': 'Tibet Beyond Borders',
    'History': 'History',
    'In Focus': 'In Focus',
}

# Articles carried on the home page, in the order they appear there.
HOMEPAGE = [
    'cultural-erasure', 'xi-jinpings-ten-commandments', 'why-east-turkistan',
    'living-between-giants', 'india-and-the-tibet-question',
    'tibet-under-watch', 'the-role-of-monlam',
    'chinas-politics-of-toponyms',
]


def text(x):
    return re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', '', x or ''))).strip()


def esc(s):
    return html.escape(s, quote=False)


def author_slug(name):
    """Author-page slug — must match tools/build_authors.py (accent-folded,
    honorifics kept, e.g. 'Lt General Vinod Bhatia' -> lt-general-vinod-bhatia)."""
    n = ''.join(c for c in unicodedata.normalize('NFD', name) if not unicodedata.combining(c))
    return re.sub(r'-+', '-', re.sub(r'[^a-z0-9]+', '-', n.lower())).strip('-')


def slugify(s):
    s = re.sub(r'[^a-z0-9]+', '-', text(s).lower()).strip('-')
    return re.sub(r'-+', '-', s)[:60]


# ---------------------------------------------------------------- images

def fetch(url, out, width, square=False):
    """Download once and resize. Returns the local path, or '' on failure."""
    path = os.path.join(IMG_DIR, out)
    if os.path.exists(path):
        return path
    tmp = "/tmp/_th_dl"
    try:
        # the host rejects the default urllib agent
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122 Safari/537.36'})
        with urllib.request.urlopen(req, timeout=30) as r, open(tmp, 'wb') as fh:
            fh.write(r.read())
    except Exception as e:
        print(f"    ! could not fetch {url.rsplit('/', 1)[-1]}: {e}")
        return ""
    cmd = ["magick", tmp]
    if square:
        cmd += ["-resize", f"{width}x{width}^", "-gravity", "center",
                "-extent", f"{width}x{width}"]
    else:
        cmd += ["-resize", f"{width}x>"]
    cmd += ["-quality", "80", path]
    if subprocess.run(cmd, capture_output=True).returncode != 0:
        print(f"    ! could not convert {out}")
        return ""
    return path


# ---------------------------------------------------------------- body

def fix_links(x):
    """Repair links that lost their scheme in the source (e.g. 'itizenlab.ca/...').

    A few hrefs in the export are missing their leading 'https://c' or similar.
    Anything that is not already absolute, a fragment, or a mail/phone link but
    does look like a bare domain gets https:// put back on the front.
    """
    def repair(m):
        href = m.group(1)
        if re.match(r'^(https?:|mailto:|tel:|#|/)', href):
            return m.group(0)
        if re.match(r'^[\w.-]+\.[a-z]{2,}(/|$|\?|#)', href, re.I):
            known = {'itizenlab.ca': 'citizenlab.ca'}
            host = href.split('/')[0]
            href = href.replace(host, known.get(host, host), 1)
            return 'href="https://%s"' % href
        return m.group(0)
    return re.sub(r'href="([^"]*)"', repair, x)


def split_notes(raw):
    """Separate the article body from its trailing references.

    Some articles label the list 'FOOTNOTES:'; others simply end with a run of
    '[n] ...' entries. Both are handled, so no references are silently lost.
    """
    body = re.split(r'ABOUT THE AUTHOR', re.sub(r'<!--.*?-->', '', raw, flags=re.S))[0]
    if 'FOOTNOTES:' in body:
        head, tail = body.split('FOOTNOTES:', 1)
        return head, tail
    # walk the trailing blocks back while they look like references
    blocks = list(re.finditer(r'<(p|div|li)\b[^>]*>.*?</\1>', body, re.S))
    start = None
    for m in reversed(blocks):
        if re.match(r'^\s*\[\d+\]', text(m.group(0))):
            start = m.start()
        elif start is not None:
            break
    if start is None:
        return body, ''
    return body[:start], body[start:]


def convert_body(raw, img_map):
    """Turn the WordPress body into the site's article markup."""
    body, _ = split_notes(raw)

    def tidy(x):
        x = re.sub(r'\s+', ' ', x).strip()
        for a in ('class', 'style', 'id', 'width', 'height', 'loading', 'srcset', 'sizes'):
            x = re.sub(r'\s%s="[^"]*"' % a, '', x)
        return x

    out, fignum = [], 0
    for m in re.finditer(r'<(p|figure|ol|ul|h2|h3)\b[^>]*>.*?</\1>', body, re.S):
        tag, chunk = m.group(1), m.group(0)

        if tag == 'figure':
            if '<table' in chunk:
                tbl = re.sub(r'\s(class|style|id)="[^"]*"', '', chunk)
                tbl = re.sub(r'</?figure[^>]*>', '', tbl).strip()
                cap = ''
                fc = re.search(r'<figcaption[^>]*>(.*?)</figcaption>', tbl, re.S)
                if fc:
                    cap = f'\n          <figcaption>{esc(text(fc.group(1)))}</figcaption>'
                    tbl = re.sub(r'<figcaption[^>]*>.*?</figcaption>', '', tbl, flags=re.S)
                out.append('        <figure class="art-table">\n'
                           f'          <div class="scroll">{tidy(tbl)}</div>{cap}\n'
                           '        </figure>')
                continue
            if 'pullquote' in chunk or '<blockquote' in chunk:
                t = tidy(re.sub(r'</?(figure|blockquote|p|cite)[^>]*>', '', chunk))
                if t:
                    out.append(f'        <blockquote class="art-pull"><p>{t}</p></blockquote>')
                continue
            src = re.search(r'src="([^"]+)"', chunk)
            if not src:
                continue
            local = img_map.get(src.group(1).rsplit('/', 1)[-1])
            if not local:
                continue
            fignum += 1
            cap = text(re.search(r'<figcaption[^>]*>(.*?)</figcaption>', chunk, re.S).group(1)) \
                if '<figcaption' in chunk else ''
            cap_html = (f'\n          <figcaption>Figure {fignum} · {esc(cap)}</figcaption>'
                        if cap else
                        f'\n          <figcaption>Figure {fignum}</figcaption>')
            out.append('        <figure class="art-fig">\n'
                       f'          <img src="{local}" alt="" loading="lazy">{cap_html}\n'
                       '        </figure>')
            continue

        inner = tidy(re.sub(r'^<%s[^>]*>|</%s>$' % (tag, tag), '', chunk.strip()))
        if not re.sub(r'<[^>]+>', '', inner).strip():
            continue
        if tag in ('ol', 'ul'):
            lis = [tidy(x) for x in re.findall(r'<li[^>]*>(.*?)</li>', chunk, re.S)]
            out.append(f'        <{tag}>\n' +
                       '\n'.join(f'          <li>{l}</li>' for l in lis) +
                       f'\n        </{tag}>')
        elif tag in ('h2', 'h3'):
            out.append(f'        <h2>{esc(text(inner))}</h2>')
        else:
            out.append(f'        <p>{inner}</p>')
    return fix_links('\n'.join(out))


def convert_footnotes(raw):
    _, tail = split_notes(raw)
    if not tail.strip():
        return ''
    tail = tail.split('<hr')[0]
    tail = re.sub(r'<(?!/?(a|em|i|strong)\b)[^>]+>', '', tail)
    tail = re.sub(r'\s+', ' ', html.unescape(tail))
    items = re.findall(r'\[(\d+)\]\s*(.*?)(?=\s*\[\d+\]|$)', tail)
    rows = [f'          <li id="fn{n}">{t.strip()}</li>' for n, t in items if t.strip()]
    return fix_links('\n'.join(rows))


def standfirst(body):
    """Opening sentence or two, used as the article's stand-first."""
    first = re.search(r'<p[^>]*>(.*?)</p>', re.sub(r'<!--.*?-->', '', body, flags=re.S), re.S)
    if not first:
        return ''
    s = text(first.group(1))
    parts = re.split(r'(?<=[a-z)’"])\.\s+(?=[A-Z])', s)
    out = parts[0]
    if len(out) < 110 and len(parts) > 1:
        out += '. ' + parts[1]
    return out.rstrip('.') + '.'


# ---------------------------------------------------------------- read the export

def load(only=None):
    ch = ET.parse(XML).getroot().find('channel')
    atts = {}
    for it in ch.findall('item'):
        if it.findtext('wp:post_type', default='', namespaces=NS) == 'attachment':
            atts[it.findtext('wp:post_id', default='', namespaces=NS)] = \
                it.findtext('wp:attachment_url', default='', namespaces=NS)

    posts = []
    for it in ch.findall('item'):
        if it.findtext('wp:post_type', default='', namespaces=NS) != 'post':
            continue
        if it.findtext('wp:status', default='', namespaces=NS) != 'publish':
            continue
        date = it.findtext('wp:post_date', default='', namespaces=NS)[:10]
        if not date.startswith('2026'):
            continue
        title = text(it.findtext('title'))
        if title == 'Hello world!':
            continue
        slug = it.findtext('wp:post_name', default='', namespaces=NS) or slugify(title)
        if only and not any(slug.startswith(k) for k in only):
            continue
        meta = {m.findtext('wp:meta_key', default='', namespaces=NS):
                m.findtext('wp:meta_value', default='', namespaces=NS)
                for m in it.findall('wp:postmeta', NS)}
        raw = it.findtext('content:encoded', default='', namespaces=NS) or ''
        cats = [c.text for c in it.findall('category') if c.get('domain') == 'category']
        section = next((SECTION[c] for c in cats if c in SECTION and c != 'In Focus'),
                       next((SECTION[c] for c in cats if c in SECTION), 'Essays'))
        bio = re.search(r'ABOUT THE AUTHOR(.*)$', raw, re.S)
        posts.append({
            'slug': slug, 'title': title, 'author': it.findtext('dc:creator', default='', namespaces=NS),
            'date': date, 'section': section, 'raw': raw,
            'featured': atts.get(meta.get('_thumbnail_id', ''), ''),
            'bio': re.sub(r'^[:\s]+', '', text(bio.group(1))) if bio else '',
            'words': len(text(raw).split()),
        })
    posts.sort(key=lambda p: p['date'], reverse=True)
    return posts


# ---------------------------------------------------------------- page

MONTH = {'01': 'January', '02': 'February', '03': 'March', '04': 'April', '05': 'May',
         '06': 'June', '07': 'July', '08': 'August', '09': 'September',
         '10': 'October', '11': 'November', '12': 'December'}


def pretty(d):
    return f"{int(d[8:10])} {MONTH[d[5:7]]} {d[:4]}"


def build(post, posts, tpl, author_img):
    img_map = {}
    # featured
    feat = ''
    if post['featured']:
        feat = fetch(post['featured'], f"ar-{post['slug'][:36]}-lede.jpg", 1600)
    # inline pictures, skipping the author portrait that sits in the author box
    body_only = re.split(r'ABOUT THE AUTHOR', post['raw'])[0]
    for i, url in enumerate(re.findall(r'<img[^>]*src="([^"]+)"', body_only), 1):
        name = url.rsplit('/', 1)[-1]
        local = fetch(url, f"ar-{post['slug'][:36]}-{i}.jpg", 1000)
        if local:
            img_map[name] = local

    body = convert_body(post['raw'], img_map)
    notes = convert_footnotes(post['raw'])
    notes_html = ('' if not notes else
                  '\n        <section class="art-notes">\n          <h2>Footnotes</h2>\n'
                  f'          <ol>\n{notes}\n          </ol>\n        </section>\n')

    # must-reads: the most recent other articles
    others = [p for p in posts if p['slug'] != post['slug']]
    mr = '\n'.join(
        f'            <li><a href="{S.piece_url(p)}"><span class="t">{esc(p["title"])}</span>'
        f'<span class="m">{S.by_line(p, esc(p["section"]))}</span></a></li>'
        for p in others[:5])

    # related: same section first, then anything else
    same = [p for p in others if p['section'] == post['section']]
    rel_posts = (same + [p for p in others if p not in same])[:3]
    rel = '\n'.join(f'''            <article class="th-card">
              <a class="ph" href="{S.piece_url(p)}" style="background-image:url({P.asset(S.card_image(p))})"></a>
              <div class="b">
                <h3><a href="{S.piece_url(p)}">{esc(p['title'])}</a></h3>
                <div class="meta"><span><svg class="ic" aria-hidden="true"><use href="#ic-cal"/></svg> {pretty(p['date'])}</span>{S.by_meta(p)}</div>
              </div>
            </article>''' for p in rel_posts)

    av = author_img.get(post['author'], '')
    avatar = (f'<img class="av" src="{P.asset(av)}" alt="" width="44" height="44">' if av else '')
    author_pic = (f'<img src="{P.asset(av)}" alt="" width="96" height="96">' if av else '')

    return (tpl
            .replace('{{TITLE}}', esc(post['title']))
            .replace('{{STANDFIRST}}', esc(standfirst(post['raw'])))
            .replace('{{SECTION}}', esc(post['section']))
            .replace('{{AUTHOR_HREF}}', P.url('author', author_slug(post['author'])))
            .replace('{{AUTHOR}}', esc(post['author']))
            .replace('{{DATE_ISO}}', post['date'])
            .replace('{{DATE}}', pretty(post['date']))
            .replace('{{MINS}}', str(max(2, round(post['words'] / 200))))
            .replace('{{LEDE}}', P.asset(feat or f'{IMG_DIR}/hero-bg.jpg'))
            .replace('{{AVATAR}}', avatar)
            .replace('{{AUTHOR_PIC}}', author_pic)
            .replace('{{BIO}}', esc(post['bio']) or 'Contributor to TransHimalaya.')
            .replace('{{BODY}}', body)
            .replace('{{NOTES}}', notes_html)
            .replace('{{MUSTREAD}}', mr)
            .replace('{{RELATED}}', rel))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--all', action='store_true', help='build every 2026 article')
    args = ap.parse_args()

    if not os.path.exists('content/manifest.json'):
        sys.exit('run this from the site root')
    tpl = open('templates/fragments/article.html', encoding='utf-8').read()
    manifest = C.load()

    posts = load(None if args.all else HOMEPAGE)
    print(f"building {len(posts)} articles")

    authors = json.load(open('/tmp/authors.json')) if os.path.exists('/tmp/authors.json') else {}
    author_img = {a: v['img'] for a, v in authors.items() if v.get('img')}

    # every post needs its lede resolved before related-cards can reference it
    for p in posts:
        p['lede'] = (fetch(p['featured'], f"ar-{p['slug'][:36]}-lede.jpg", 1600)
                     if p['featured'] else f'{IMG_DIR}/hero-bg.jpg')

    for p in posts:
        page = build(p, posts, tpl, author_img)
        C.write('article', p['slug'], esc(p['title']), esc(standfirst(p['raw'])),
                page, manifest=manifest)
        print(f"  {p['slug'][:44]:46} {p['words']:5d}w")
    C.save(manifest)

    json.dump([{k: p[k] for k in ('slug', 'title', 'author', 'date', 'section', 'lede')}
               for p in posts], open('tools/articles.json', 'w'), indent=1)
    print("wrote tools/articles.json")


if __name__ == '__main__':
    main()
