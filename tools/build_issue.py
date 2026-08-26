#!/usr/bin/env python3
"""Rebuild article pages from the finalised 1st-issue Word documents.

Each essay's .docx (under ~/Desktop/Tenzin Paljor/FNVA/1st Issue) is converted
with pandoc, its embedded figures extracted into assets/img/issue/<slug>/, and a
fragment emitted with templates/fragments/article.html — matching the article design
(.art-fig figures, <h2> sub-heads, About-the-author bio). Slugs, titles,
authors, sections and the Must-Read / You-may-also-like rails come from
tools/articles.json so the contents page and author pages keep resolving.

    python3 tools/build_issue.py            # all mapped essays
    python3 tools/build_issue.py --only tibet-was-never-part-of-china

Writes content/article/<slug>.html; run tools/build.py afterwards to wrap
each fragment in the site chrome. Run from the site root.
"""

import argparse, difflib, html, json, os, re, subprocess, sys
import bios as B
import content as C
import paths as P
import sections as S

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


# new pieces not in the original WordPress export. `strip_lead` drops leading
# title/author/label lines; kind='interview' uses the Q&A formatter.
EXTRAS = [
  dict(slug='why-does-tibet-matter', title='Why Does Tibet Matter?',
       author='Srikanth Kondapalli', section='History', date='2026-08-01',
       docx='S2_ HISTORY AND FOUNDATIONAL/Srikanth Kondapalli/Kondapalli Final Why Tibet Matters.docx'),
  dict(slug='foreword', title='Foreword', author='Shyam Saran',
       section='Foreword', date='2026-08-01',
       docx=' S1_ Prologue/Foreword/Foreword for Ms. Rebon Banerjee Dhar - 16.7.2026.docx',
       strip_lead=[r'^foreword$']),
  dict(slug='editors-note', title='Editor’s Note', author='Srikanth Kondapalli',
       section='Editor’s Note', date='2026-08-01',
       docx=' S1_ Prologue/Editor_s Note/Editors note.docx',
       strip_lead=[r'^draft$', r'^editor.?s note$']),
  dict(slug='tibet-in-the-year-2048', title='Tibet in the Year 2048',
       author='Wangpo Tethong', section='Strategic Foresight', date='2026-08-01',
       docx=' S1_ Prologue/Wangpo Tethong/01-06-26_ Wangpo Tethong_Finalised (1).docx',
       strip_lead=[r'^tibet in the year 2048$', r'^wangpo tethong$']),
  dict(slug='the-way-forward-policy-recommendations',
       title='The Way Forward: Policy Recommendations', author='The Editors',
       section='Policy', date='2026-08-01',
       docx=' S1_ Prologue/Way Forward/POLICY RECCOMMENDATIONS.docx',
       strip_lead=[r'^policy recommendations']),
  dict(slug='interview-with-sikyong-penpa-tsering',
       title='Interview with Sikyong Penpa Tsering', author='Tenzing Dhamdul',
       section='Interviews', date='2026-08-01', kind='interview',
       docx='S7_ IN CONVERSATION WITH LEADERS/Interview for the print edition.docx'),
]


# per-article hero image override: promote a high-res in-article image to the
# front (and skip it in the body), with its caption/source.
HERO = {
  'living-between-giants-lessons-from-bhutans-strategic-experience': dict(
      img='assets/img/issue/living-between-giants-lessons-from-bhutans-strategic-experience/media/image2.jpeg',
      caption='His Majesty King Jigme Khesar Namgyel Wangchuck during the Global '
              'Peace Prayer Festival in November in Thimphu, Bhutan.',
      source='His Majesty The King’s Facebook Page'),
  # The caption below belongs to this image in the document. A promoted hero
  # drops its own label and caption from the body, so it has to be given here.
  'why-does-tibet-matter': dict(
      img='assets/img/issue/why-does-tibet-matter/media/image5.jpg',
      caption='The supine (lying down) Srinmo whose body spanned the entire '
              'Tibetan plateau, with strategic geomantic temples like the '
              'Jokhang Monastery to pin her down and tame the land for Buddhism.',
      source='Utsang Culture'),
}


def hero_bits(hero):
    """(skip_img, skip_texts, lede_cap) for a HERO entry, or (None, None, '')."""
    if not hero:
        return None, None, ''
    cap = (f'{esc(hero["caption"])} ' if hero.get('caption') else '')
    src = (f'<span class="src">Source: {esc(hero["source"])}</span>' if hero.get('source') else '')
    lede_cap = f'\n          <figcaption>{cap}{src}</figcaption>' if (cap or src) else ''
    texts = [t for t in (hero.get('caption'), hero.get('source')) if t]
    return hero['img'].rsplit('/', 1)[-1], texts, lede_cap


def esc(s):
    return html.escape(s, quote=False)


def text(x):
    return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', x or '')).strip()


def clean_bio(s):
    """Bio is a plain-text field (the template escapes it once), so strip tags,
    un-escape entities and drop stray leading backslashes."""
    return re.sub(r'^[\\\s]+', '', html.unescape(text(s))).strip()


MONTH = {'01': 'January', '02': 'February', '03': 'March', '04': 'April', '05': 'May',
         '06': 'June', '07': 'July', '08': 'August', '09': 'September',
         '10': 'October', '11': 'November', '12': 'December'}


def pretty(d):
    return f"{int(d[8:10])} {MONTH[d[5:7]]} {d[:4]}"


# ----------------------------------------------------------------- inline markdown

_FN = {}          # footnote label -> (display number, text), set per article
FN_MARK = re.compile(r'<sup class="fn"><a id="fnr-([^"]+)" href="#fn-([^"]+)">([^<]*)</a></sup>')


def inline(s):
    """Convert a run of pandoc-markdown inline text to safe HTML."""
    s = re.sub(r'\\([^\w\s])', r'\1', s)                   # drop backslash escapes (\$ \~ …)
    s = re.sub(r'HYPERLINK\s+"[^"]*"\s*', '', s)           # Word HYPERLINK field codes
    # <https://…> autolinks: drop the brackets now. Left in place, esc() turns
    # them into &lt;…&gt; and the bare-URL linkifier below swallows the '&gt'
    # into the href, which then 404s. The brackets carry no meaning anyway.
    s = re.sub(r'<\s*(https?://[^>\s]+?)\s*>', r'\1', s)
    # protect links first
    links = []
    def stash_link(m):
        links.append((m.group(1), m.group(2)))
        return f'\x00{len(links)-1}\x00'
    # pandoc underline/mark-wrapped links: [[text]{.underline}](url) -> link
    s = re.sub(r'\[?\[([^\]]+)\]\{\.[a-z]+\}\]\((https?://[^)]+)\)', stash_link, s)
    s = re.sub(r'\[([^\]]+)\]\((https?://[^)]+)\)', stash_link, s)

    def stash_bare_host(m):
        links.append((m.group(1), 'https://' + m.group(2)))
        return f'\x00{len(links)-1}\x00'
    # A target that lost its scheme — "[Citizen Lab](example.ca/path)" — matched
    # none of the link rules and fell through to the bracket cleanup, which left
    # the raw URL sitting in the middle of the sentence.
    s = re.sub(r'\[([^\]]+)\]\((?!https?://|#|mailto:|/)'
               r'([a-z0-9][a-z0-9.-]*\.[a-z]{2,}/[^)\s]*)\)',
               stash_bare_host, s, flags=re.I)
    s = re.sub(r'\[\]\{[^}]*\}', '', s)                   # empty pandoc spans
    s = re.sub(r'\[([^\]]*)\]\{[^}]*\}', r'\1', s)        # [text]{.underline} -> text
    s = s.replace('[]', '')
    s = s.replace('---', '—').replace('--', '–')          # em / en dashes
    s = esc(s)

    def fn_ref(m):                                        # footnote ref -> superscript link
        label = m.group(1)
        if label in _FN:
            return (f'<sup class="fn"><a id="fnr-{esc(label)}" '
                    f'href="#fn-{esc(label)}">{esc(_FN[label][0])}</a></sup>')
        return ''
    # handle footnote refs BEFORE superscripts, so the '^' inside [^n] is not
    # swept up by the ^…^ superscript rule (which would swallow whole sentences)
    s = re.sub(r'\[\^([^\]]+)\]', fn_ref, s)
    s = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', s)
    s = re.sub(r'(?<!\*)\*(?!\s)(.+?)(?<!\s)\*(?!\*)', r'<em>\1</em>', s)
    s = re.sub(r'\^([^^]+)\^', r'<sup>\1</sup>', s)         # superscripts (km^2^, 14^th^)
    def put_link(m):
        t, u = links[int(m.group(1))]
        return (f'<a href="{esc(u)}" target="_blank" rel="noopener">'
                f'{esc(t)}</a>')
    s = re.sub(r'\x00(\d+)\x00', put_link, s)
    # clean up any leftover pandoc attribute spans / brackets from nested links
    s = re.sub(r'\{\.[^}]*\}', '', s)                     # {.mark} {.underline}
    s = re.sub(r'\[(<a\b[^>]*>.*?</a>)\]', r'\1', s)      # [<a>…</a>] -> link
    # malformed citation scaffolding around bare URLs: '[[url … ]{.x}](url)'
    s = re.sub(r'\]\(https?://[^)]+\)', '', s)            # drop the duplicate href part
    s = re.sub(r'\[+(?=\s*https?://)', '', s)             # '[' before a URL
    s = re.sub(r'(?<=[a-zA-Z0-9/])\]+(?=[\s,.;)]|$)', '', s)   # ']' right after a URL
    s = re.sub(r'(?<![">])\b(https?://[^\s<>)\]]+[a-zA-Z0-9/])',
               r'<a href="\1" target="_blank" rel="noopener">\1</a>', s)
    s = re.sub(r'\[([^\[\]<>]{1,120})\]', r'\1', s)       # [orphan text] -> text
    return s


IMG_RE = re.compile(r'!\[[^\]]*\]\(([^)]+?)\)(\{[^}]*\})?')


def img_path(block):
    m = IMG_RE.search(block)
    return m.group(1) if m else None


def is_bold_head(b):
    b = b.strip()
    return (b.startswith('**') and b.endswith('**') and b.count('**') == 2
            and len(text(b)) < 90 and not b.endswith(':**') is None)



def split_footnotes(md):
    """Take the footnote definitions out of the markdown and return both.

    A definition can run past its first line: pandoc indents the rest under it,
    which is how a note holding a bare URL gets written. Matching only the first
    line lost that URL from the note and left it in the body as a stray
    paragraph -- and being the last block, it was then mistaken for the trailing
    paragraph the author bio is read from.
    """
    keep, defs, cur = [], [], None
    for line in md.split('\n'):
        m = re.match(r'^\[\^([^\]]+)\]:[ \t]*(.*)$', line)
        if m:
            cur = [m.group(1), m.group(2).strip()]
            defs.append(cur)
            continue
        if cur is not None:
            if not line.strip():
                continue                                  # blank line inside a note
            if re.match(r'^[ \t]{2,}', line):             # indented continuation
                cur[1] = f'{cur[1]} {line.strip()}'.strip()
                continue
            cur = None                                    # back to body text
        keep.append(line)
    return '\n'.join(keep), [(l, t) for l, t in defs]


def build_body(md, slug, strip_lead=None, title=None, author=None,
               skip_img=None, skip_texts=None):
    """Return (body_html, bio_text, first_image, notes_html)."""
    skip_norm = {re.sub(r'[^a-z0-9]', '', t.lower()) for t in (skip_texts or [])}
    global _FN
    _FN = {}
    md, defs = split_footnotes(md)
    for i, (label, txt) in enumerate(defs, 1):
        _FN[label] = (label.strip() if label.strip().isdigit() else str(i), txt.strip())

    # split off the author bio at the LAST "About the Author" marker (some docs
    # carry a spurious earlier one), and cut it before any references section
    marks = list(re.finditer(r'(?i)\bAbout the Author\b\s*:?', md))
    if marks:
        body_md, bio_md = md[:marks[-1].start()], md[marks[-1].end():]
    else:
        body_md, bio_md = md, ''
    bio_md = re.split(r'(?im)^\s*\**\s*(references|bibliography|works cited|notes)\b',
                      bio_md)[0]
    # Not every document heads its reference list. One rules a line of dashes
    # and starts numbering, which without this ends up appended to the bio.
    bio_md = re.split(r'(?m)^[ \t]*[-\u2013\u2014_]{4,}[ \t]*$', bio_md)[0]
    bio_md = re.split(r'(?m)^[ \t]*\d{1,2}[.:][ \t]+\S', bio_md)[0]
    # strip any headshot image markdown BEFORE inline() (which would mangle it)
    raw_bio = re.sub(r'!\[[^\]]*\]\([^)]*\)(\{[^}]*\})?', '', bio_md)
    bio = clean_bio(inline(raw_bio))

    blocks = [b.strip() for b in re.split(r'\n\s*\n', body_md) if b.strip()]
    # drop pandoc footnote definitions and any stray "About the Author" labels
    blocks = [b for b in blocks
              if not re.match(r'^\[\^[^\]]+\]:', b)
              and not re.match(r'(?i)^\**\s*about the author\s*:?\s*\**$', text(b))]

    def bare(b):
        """A block's words with markdown decoration removed, for matching."""
        t = re.sub(r'\{[^}]*\}', '', text(b))            # pandoc spans, {.underline}
        t = re.sub(r'^#{1,6}\s*', '', t.strip())          # heading markers
        return t.strip().strip('*_[]# ').strip()

    # Drop leading title / author / label lines; title and author come from the
    # metadata. Matching ignores markdown decoration, so a label written
    # "**DRAFT**" or "# Editor's Note" is recognised, and repeats until no
    # pattern matches so the order of the patterns does not matter.
    if strip_lead:
        dropping = True
        while dropping and blocks:
            dropping = False
            for pat in strip_lead:
                if blocks and re.match(pat, bare(blocks[0]), re.I):
                    blocks.pop(0); dropping = True; break

    def norm(s):
        s = re.sub(r'\{[^}]*\}', '', s)                    # pandoc spans, e.g. {.mark}
        s = re.sub(r'\[\^[^\]]*\]', '', text(s))
        return re.sub(r'[^a-z0-9]', '', s.lower())

    # Drop the leading title + byline. The byline is a line that is *only* the
    # author's name; drop everything up to and including it (the title may span
    # lines and may not match the metadata title verbatim).
    if author:
        an = norm(author)
        for i in range(min(3, len(blocks))):
            bn = norm(blocks[i])
            # The document's byline and the metadata name often differ a little
            # — "Tenzing"/"Tenzin" Lamsang, "Lt Gen … (Retd.)" against
            # "Lt General …" — so compare loosely. A byline is always short.
            if bn and len(bn) < 44 and (
                    bn == an or difflib.SequenceMatcher(None, bn, an).ratio() > 0.75):
                del blocks[:i + 1]; break
    # a leading title line with no byline after it (matches the metadata title)
    if title and blocks:
        b0, tn = norm(blocks[0]), norm(title)
        if b0 and (b0 == tn or (len(b0) > 12 and (b0 in tn or tn in b0))):
            blocks.pop(0)

    # a trailing self-description ("<Author> is/serves …") is the bio, not body
    if not bio and author and blocks:
        lt = text(blocks[-1])
        if re.match(rf'(?i)^{re.escape(author)}\b', lt) and \
           re.search(r'(?i)^\S+\s+\S+\s+(is|was|serves|served|currently)\b', lt):
            bio = clean_bio(inline(blocks.pop()))

    # A signed piece ends with the author's name over their affiliation, and
    # sometimes a bare "Date:". The byline carries the name and the bio carries
    # the affiliation, so the run is redundant. Only a short run of short lines
    # qualifies, so a closing paragraph is never mistaken for a signature.
    if author and len(blocks) > 3:
        an = norm(author)
        for i in range(max(0, len(blocks) - 8), len(blocks)):
            bn = norm(blocks[i])
            if bn and len(bn) < 44 and (
                    bn == an or difflib.SequenceMatcher(None, bn, an).ratio() > 0.75):
                if all(len(text(b)) < 100 for b in blocks[i:]):
                    del blocks[i:]
                break

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
    skip_src = [False]              # drop the source line after a skipped hero image

    def fold_fig(cap_html):
        """Attach a caption to the figure just emitted, so every image caption
        renders the same way (a styled <figcaption>) rather than as body text."""
        if out and out[-1].lstrip().startswith('<figure class="art-fig">'):
            if '<figcaption>' in out[-1]:
                out[-1] = out[-1].replace('</figcaption>', f' — {cap_html}</figcaption>')
            else:
                out[-1] = out[-1].replace(
                    '        </figure>',
                    f'          <figcaption>{cap_html}</figcaption>\n        </figure>')
            return True
        return False

    def caption_html(t):
        """Render a caption string that may carry a trailing 'Source: …'."""
        m = re.search(r'(?i)\bsource\s*:?\s*', t)
        if not m:
            return inline(t)
        desc, src = t[:m.start()].strip(' .—-'), t[m.end():].strip()
        span = f'<span class="src">Source: {inline(src)}</span>' if src else ''
        return f'{inline(desc)} {span}'.strip() if desc else span

    def flush_pending():
        for kind, val in pending:
            if kind == 'fignum':
                continue          # a label with no figure to sit in is noise
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
                   f'          <img src="{P.asset(path)}" alt="" loading="lazy">{figcap}\n'
                   f'        </figure>')

    for b in blocks:
        take_src = skip_src[0]; skip_src[0] = False
        if skip_norm and re.sub(r'[^a-z0-9]', '', text(b).lower()) in skip_norm:
            continue                 # a hero caption/source line, shown on the hero instead
        m = IMG_RE.search(b)
        if m:                       # an image block (maybe with glued caption/source/bio)
            local = m.group(1)
            trailing = IMG_RE.sub('', b).strip()
            if first_img[0] is None:
                first_img[0] = local
            # this image was promoted to the hero — drop it, its Figure label and source
            if skip_img and local.endswith(skip_img):
                pending.clear(); skip_src[0] = True
                continue
            # a long paragraph glued to an image is the author headshot + bio
            if trailing and len(text(trailing)) > 200 and not bio:
                bio = clean_bio(inline(trailing))
                continue                                   # drop the headshot itself
            if trailing and re.match(r'(?i)\**\s*source', trailing):
                emit_figure(local, re.sub(r'(?i)^\**\s*source\s*:?\s*', '', trailing).strip(' *'))
            else:
                emit_figure(local)
                if trailing:                               # a caption glued after the image
                    fold_fig(caption_html(trailing))
            continue
        bt = b.strip()
        if re.match(r'(?i)^figure\s+\d', bt) and len(bt) < 60:
            pending.append(('fignum', bt)); continue
        if re.match(r'(?i)^\**\s*source\b', bt):
            if take_src:
                continue             # the source line of the image promoted to the hero
            srctext = re.sub(r'(?i)^\**\s*source\s*:?\s*', '', bt).strip(' *')
            if not fold_fig(f'<span class="src">Source: {inline(srctext)}</span>'):
                pending.append(('source', srctext))
            continue
        if bt.startswith('*') and bt.endswith('*') and bt.count('*') == 2 and len(bt) < 220:
            # Captions appear on either side of their image depending on the
            # document. One that follows a figure belongs to it; one that comes
            # first waits for the image still to be emitted.
            if (out and out[-1].lstrip().startswith('<figure class="art-fig">')
                    and '<figcaption>' not in out[-1]):
                fold_fig(caption_html(bt.strip('*')))
            else:
                pending.append(('caption', bt.strip('*')))
            continue
        # Several documents write a figure as three lines — label, caption,
        # image — rather than italicising the caption. Without this, the plain
        # caption paragraph ends the figure block, stranding the label.
        if (pending and pending[-1][0] == 'fignum'
                and not any(k == 'caption' for k, _ in pending)
                and len(bt) < 320 and not re.match(r'^[>#|!\[]|^\*\*', bt)):
            pending.append(('caption', bt)); continue
        # not a figure component -> flush any pending as plain paragraphs
        flush_pending()
        prev_is_fig = out and out[-1].lstrip().startswith('<figure class="art-fig">')
        if bt.startswith('>'):
            q = inline(re.sub(r'^\s*>\s?', '', bt, flags=re.M))
            out.append(f'        <blockquote class="art-pull"><p>{q}</p></blockquote>')
        elif re.match(r'^\[[^\]]+\]\{\.underline\}$', bt) and len(text(bt)) < 90:
            out.append(f'        <h2>{inline(bt)}</h2>')      # underline-styled sub-head
        elif (bt.startswith('**') and bt.endswith('**') and bt.count('**') == 2
                and len(text(bt)) < 130 and not text(bt).rstrip().endswith('.')):
            out.append(f'        <h2>{inline(bt.strip("*"))}</h2>')
        elif re.match(r'^#{1,6}\s', bt):
            inner = re.sub(r'^#{1,6}\s+', '', bt)        # a genuine sub-head is short;
            if len(text(inner)) < 90:                    # long '#' lines are mis-styled body
                out.append(f'        <h2>{inline(inner)}</h2>')
            else:
                out.append(f'        <p>{inline(inner)}</p>')
        elif prev_is_fig and re.search(r'(?i)\bsource\s*:', bt) and len(text(bt)) < 240:
            fold_fig(caption_html(bt))                     # a caption that names its source
        else:
            out.append(f'        <p>{inline(bt)}</p>')
    flush_pending()
    body_html = '\n'.join(out)
    notes_html = ''

    # A note the text points at is a reference — a link, a book, a source. A
    # note with no marker is the author's own: in the documents these hang off
    # the title or the byline, so they lose their marker when those lines are
    # dropped, and numbering them alongside the references throws the sequence
    # out. They are listed separately and unnumbered; the references renumber
    # from 1 so a marker in the text and its entry always agree.
    if _FN:
        cited, seen = [], set()
        for m in FN_MARK.finditer(body_html + bio):
            if m.group(1) not in seen:
                seen.add(m.group(1)); cited.append(m.group(1))
        number = {l: str(i) for i, l in enumerate(cited, 1)}

        def renumber(m):
            l = m.group(1)
            return (f'<sup class="fn"><a id="fnr-{esc(l)}" href="#fn-{esc(l)}">'
                    f'{esc(number.get(l, m.group(3)))}</a></sup>')
        body_html = FN_MARK.sub(renumber, body_html)
        bio = FN_MARK.sub(renumber, bio)

        refs = '\n'.join(
            f'          <li id="fn-{esc(l)}">{inline(_FN[l][1])} '
            f'<a class="fn-back" href="#fnr-{esc(l)}" aria-label="Back to text">↩</a></li>'
            for l in cited)
        own = '\n'.join(
            f'          <li>{inline(t)}</li>'
            for l, (n, t) in sorted(_FN.items(),
                                    key=lambda kv: int(kv[1][0]) if kv[1][0].isdigit() else 999)
            if l not in number)
        if refs:
            notes_html += ('\n        <section class="art-notes">\n'
                           '          <h2>References</h2>\n'
                           f'          <ol>\n{refs}\n          </ol>\n        </section>\n')
        if own:
            notes_html += ('\n        <section class="art-notes art-ownnotes">\n'
                           '          <h2>Notes by the Author</h2>\n'
                           f'          <ul>\n{own}\n          </ul>\n        </section>\n')
    return body_html, bio, first_img[0], notes_html


# ----------------------------------------------------------------- page assembly

def convert_docx(path, slug):
    media = os.path.join(MEDIA_ROOT, slug)
    os.makedirs(media, exist_ok=True)
    src, tmp = path, None
    if path.lower().endswith('.doc'):        # legacy binary .doc — macOS textutil reads it
        # under /tmp, not under media/: anything left in assets/ is published
        tmp = f'/tmp/_th_{slug}.docx'
        subprocess.run(['textutil', '-convert', 'docx', path, '-output', tmp],
                       capture_output=True)
        if os.path.exists(tmp):
            src = tmp
    md = subprocess.run(['pandoc', src, '-t', 'markdown', '--wrap=none',
                         f'--extract-media={media}'],
                        capture_output=True, text=True).stdout
    if tmp and os.path.exists(tmp):
        os.remove(tmp)
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


def build_interview(md):
    """Interview formatter: the host's questions are bold lead-ins, the
    interviewee's answers are body paragraphs. Labels (Q n:, speaker names,
    Introduction/Concluding) and the title/section lines are dropped."""
    blocks = [b.strip() for b in re.split(r'\n\s*\n', md) if b.strip()]
    out, standf, want_summary = [], '', False

    def plain(b):
        return re.sub(r'\*', '', text(b)).strip()

    for b in blocks:
        raw = b.strip()
        pl = plain(raw)
        low = pl.lower()
        if want_summary:
            standf = pl; want_summary = False; continue
        if low in ('conversation with leaders', 'interview with sikyong penpa tsering',
                   'below is the interview'):
            continue
        if low.startswith('summary of the talk'):
            rest = re.sub(r'(?i)^summary of the talk[:\s]*', '', pl)
            if len(rest) > 40:
                standf = rest
            else:
                want_summary = True
            continue
        if re.match(r'(?i)^\*{3}.*\*{3}$', raw):          # ***Held at… / Host:…*** dateline
            out.append(f'        <p class="art-note"><em>{inline(raw.strip("*"))}</em></p>')
            continue
        if not pl or pl == '.':
            continue
        if re.match(r'(?i)^(sikyong|host)\s*:?$', pl):    # bare speaker label
            continue
        if re.match(r'(?i)^(introduction|concluding|q\s*\d+)\s*:?$', pl):   # label-only line
            continue
        is_bold = raw.startswith('**') and raw.rstrip().endswith('**') and raw.count('**') == 2
        is_ital = raw.startswith('*') and raw.endswith('*') and raw.count('*') == 2 and not is_bold
        inner = raw.strip('*') if (is_bold or is_ital) else raw
        inner = re.sub(r'(?i)^(introduction|concluding|q\s*\d+)\s*:?\s*', '', inner).strip()
        if not plain(inner):
            continue
        if is_bold:
            out.append(f'        <p class="art-q"><strong>{inline(inner)}</strong></p>')
        else:
            out.append(f'        <p>{inline(inner)}</p>')     # answer (de-italicised)
    return '\n'.join(out), standf


def render_page(meta, body, bio, tpl, arts, author_img, author_href, notes='', lede_cap=''):
    from build_articles import author_slug
    slug = meta['slug']
    lede = meta.get('lede') or 'assets/img/hero-bg.jpg'
    others = [p for s, p in arts.items() if s != slug]
    mr = '\n'.join(
        f'            <li><a href="{P.url("article", p["slug"])}"><span class="t">{esc(p["title"])}</span>'
        f'<span class="m">{esc(p["author"])} · {esc(p["section"])}</span></a></li>'
        for p in others[:5])
    same = [p for p in others if p['section'] == meta['section']]
    rel_posts = (same + [p for p in others if p not in same])[:3]
    rel = '\n'.join(f'''            <article class="th-card">
              <a class="ph" href="{P.url('article', p['slug'])}" style="background-image:url({P.asset(p.get('lede','assets/img/hero-bg.jpg'))})"></a>
              <div class="b">
                {S.chip(p['section'], 'th-chip card-chip')}
                <h3><a href="{P.url('article', p['slug'])}">{esc(p['title'])}</a></h3>
                <div class="meta"><span><svg class="ic" aria-hidden="true"><use href="#ic-cal"/></svg> {pretty(p['date'])}</span><span>·</span><span>By {esc(p['author'])}</span></div>
              </div>
            </article>''' for p in rel_posts)
    av = author_img.get(meta['author'], '')
    avatar = (f'<img class="av" src="{P.asset(av)}" alt="" width="44" height="44">' if av else '')
    author_pic = (f'<img src="{P.asset(av)}" alt="" width="96" height="96">' if av else '')
    words = len(text(body).split())
    sf = meta.get('standfirst') or standfirst(body)
    page = (tpl
            .replace('{{TITLE}}', esc(meta['title']))
            .replace('{{STANDFIRST}}', esc(sf))
            .replace('{{SECTION_CHIP}}', S.chip_link(meta['section'], 'th-chip'))
            .replace('{{SECTION}}', esc(meta['section']))
            .replace('{{AUTHOR_HREF}}', author_href)
            .replace('{{AUTHOR}}', esc(meta['author']))
            .replace('{{DATE_ISO}}', meta['date'])
            .replace('{{DATE}}', pretty(meta['date']))
            .replace('{{MINS}}', str(max(2, round(words / 200))))
            .replace('{{LEDE}}', P.asset(lede))
            .replace('{{AVATAR}}', avatar)
            .replace('{{AUTHOR_PIC}}', author_pic)
            .replace('{{BIO}}', esc(bio) or 'Contributor to TransHimalaya.')
            .replace('{{BODY}}', body)
            .replace('{{LEDE_CAP}}', lede_cap)
            .replace('{{NOTES}}', notes)
            .replace('{{MUSTREAD}}', mr)
            .replace('{{RELATED}}', rel))
    C.write('article', slug, esc(meta['title']), esc(sf), page,
            manifest=MANIFEST)
    return words, page.count('art-fig')


def resolve_href(author):
    """An author's own page if they have one, the author index if not."""
    from build_articles import author_slug
    aslug = author_slug(author)
    if os.path.exists(f'content/author/{aslug}.html'):
        return P.url('author', aslug)
    return P.url('authors-index')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--only')
    ap.add_argument('--extras', action='store_true', help='only the new (EXTRAS) pieces')
    args = ap.parse_args()

    if not os.path.exists('content/manifest.json'):
        sys.exit('run from the site root')

    tpl = open('templates/fragments/article.html', encoding='utf-8').read()
    arts = {a['slug']: a for a in json.load(open('tools/articles.json'))}
    global MANIFEST
    MANIFEST = C.load()

    from build_articles import author_slug
    # Bios come from the store, never from the author pages this run will
    # rewrite: scraping them fed a previous run's mistakes straight back in.
    BIOS = B.seed()
    author_img = {}
    for a in arts.values():
        p = f"assets/img/au-{author_slug(a['author'])}.jpg"
        if os.path.exists(p):
            author_img[a['author']] = p

    # Two passes. An author with two pieces, or one whose fullest bio lives in
    # another source, would otherwise get whichever text happened to be known
    # when their page was written. Everything is converted first, so the store
    # is complete before a single page is rendered.
    jobs = []
    if not args.extras:
        for slug in ([args.only] if args.only else list(DOCX)):
            if slug not in DOCX:
                print(f"  ! no docx mapped for {slug}"); continue
            post = arts[slug]
            docx = os.path.join(ISSUE, DOCX[slug])
            if not os.path.exists(docx):
                print(f"  ! missing {docx}"); continue
            md = convert_docx(docx, slug)
            hero = HERO.get(slug)
            skip_img, skip_texts, lede_cap = hero_bits(hero)
            body, bio, _, notes = build_body(md, slug, title=post['title'],
                                             author=post['author'],
                                             skip_img=skip_img, skip_texts=skip_texts)
            if hero:
                post = {**post, 'lede': hero['img']}
            jobs.append(dict(meta=post, body=body, bio=bio, notes=notes,
                             lede_cap=lede_cap, author=post['author'],
                             href=P.url('author', author_slug(post['author'])),
                             tag=''))

    for meta in EXTRAS:
        if args.only and meta['slug'] != args.only:
            continue
        docx = os.path.join(ISSUE, meta['docx'])
        if not os.path.exists(docx):
            print(f"  ! missing {docx}"); continue
        md = convert_docx(docx, meta['slug'])
        notes, lede_cap = '', ''
        hero = HERO.get(meta['slug'])
        if meta.get('kind') == 'interview':
            body, sf = build_interview(md)
            bio, meta = '', {**meta, 'standfirst': sf}
        else:
            skip_img, skip_texts, lede_cap = hero_bits(hero)
            body, bio, _, notes = build_body(md, meta['slug'], meta.get('strip_lead'),
                                             title=meta['title'], author=meta['author'],
                                             skip_img=skip_img, skip_texts=skip_texts)
        lede = hero['img'] if hero else arts.get(meta['slug'], {}).get('lede', 'assets/img/hero-bg.jpg')
        meta = {**meta, 'lede': lede}
        jobs.append(dict(meta=meta, body=body, bio=bio, notes=notes,
                         lede_cap=lede_cap, author=meta['author'],
                         href=resolve_href(meta['author']), tag='  [extra]'))

    for j in jobs:                                  # first pass: learn the bios
        B.merge({author_slug(j['author']): j['bio']}, BIOS)
    for j in jobs:                                  # second pass: write the pages
        bio = B.best(author_slug(j['author']), j['bio'], BIOS)
        w, nf = render_page(j['meta'], j['body'], bio, tpl, arts, author_img,
                            j['href'], j['notes'], j['lede_cap'])
        print(f"  {j['meta']['slug'][:44]:44} {w:5d}w  {nf} fig  "
              f"bio:{'y' if bio else '-'}{j['tag']}")

    B.save(BIOS)
    C.save(MANIFEST)


if __name__ == '__main__':
    main()
