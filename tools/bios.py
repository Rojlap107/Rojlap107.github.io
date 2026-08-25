#!/usr/bin/env python3
"""One canonical bio per author, shared by the article pages and author pages.

Two generators find bios in different places — build_issue.py in the "About
the Author" note of each finalised .docx, build_authors.py in the WordPress
export and in its own supplied text — and the same person was ending up with a
fuller bio at the foot of their article than on their author page. Both now
merge into this store, keyed by author slug so a spelling variant does not
split one person in two, and both read the fullest text back out. Whichever
generator runs first, the two pages agree.

    import bios as B
    store = B.merge({slug: text}, store)   # longest text wins
    text  = B.best(slug, fallback, store)
    B.save(store)
"""

import html, json, os, re, unicodedata
import xml.etree.ElementTree as ET

PATH = 'tools/bios.json'

# what the article template prints when an author has no bio. It is scraped
# back off the author page, so without this it would enter the store as though
# it were real text and an author would look as if they had a bio.
PLACEHOLDER = 'Contributor to TransHimalaya.'


def load():
    return json.load(open(PATH, encoding='utf-8')) if os.path.exists(PATH) else {}


def save(store):
    json.dump(dict(sorted(store.items())), open(PATH, 'w'), indent=1, ensure_ascii=False)


def tidy(bio):
    """Trim the debris a source can leave on the front of a bio.

    Worth doing here rather than in each generator: comparing by length, a bio
    still wearing its markdown "**" is longer than the same bio without it, so
    the untidy copy would win.
    """
    b = re.sub(r'^(?:\*+|_+|:|\s)+', '', (bio or '').strip())
    b = re.sub(r'(?:\s*[#*_|]+)+$', '', b)          # a stray heading marker at the end
    return re.sub(r'[ \t\xa0]+', ' ', b).strip()


def merge(found, store=None):
    """Record what a generator has discovered, keeping the fullest text."""
    own = store is None
    store = load() if own else store
    for slug, bio in (found or {}).items():
        bio = tidy(bio)
        if bio == PLACEHOLDER:
            continue
        if slug and len(bio) > len(store.get(slug, '')):
            store[slug] = bio
    if own:
        save(store)
    return store


def best(slug, fallback='', store=None):
    """The fullest bio known for this author."""
    store = load() if store is None else store
    # tidy the fallback too, or an untidy copy can measure longer than the
    # tidied text already in the store and win the comparison
    have, fallback = store.get(slug, ''), tidy(fallback)
    return have if len(have) >= len(fallback) else fallback


# ---------------------------------------------------------------- sources

XML = os.path.expanduser('~/Downloads/transhimalaya.WordPress.2026-08-03.xml')
NS = {'wp': 'http://wordpress.org/export/1.2/',
      'dc': 'http://purl.org/dc/elements/1.1/',
      'content': 'http://purl.org/rss/1.0/modules/content/'}

# Bios for contributors the WordPress export does not carry, or carries only in
# brief. Kondapalli's is the detailed text from his own document with the centre
# and school restored into the opening sentence — the detailed version named
# only "Jawaharlal Nehru University". The centre is the Centre for East Asian
# Studies, as both that bio's own later sentence and About TH.docx have it.
SUPPLIED = {
    'Srikanth Kondapalli':
        'Srikanth Kondapalli is Professor in Chinese Studies at the Centre for '
        'East Asian Studies, School of International Studies, Jawaharlal Nehru '
        'University (JNU), New Delhi. He was former Dean of School of '
        'International Studies, JNU from 2022-24; Chairman of the Centre for '
        'East Asian Studies, SIS, JNU from 2008-10, 2012-20, and in 2022. He is '
        'Chair Professor under the Chair of Excellence of Ministry of Defence '
        'since August 2022. He is a distinguished fellow at several think-tanks '
        'including Vivekananda International Foundation and Institute for Peace '
        'and Conflict Studies. He has supervised more than 30 Ph.D. researchers '
        'at JNU and is also an academic advisor for Ph.D. researchers at Al '
        'Farabi Kazakh National University and Ablai Khan University at Almaty '
        'and Tamkhang University (Taipei). He is a Trustee with the Foundation '
        'for Non-violent Alternatives (FNVA) since 2021.',
}


def slug(name):
    """Author slug — the same rule as build_articles.author_slug."""
    n = ''.join(c for c in unicodedata.normalize('NFD', name or '')
                if not unicodedata.combining(c))
    return re.sub(r'-+', '-', re.sub(r'[^a-z0-9]+', '-', n.lower())).strip('-')


def from_export():
    """The "About the author" note at the end of each post in the WordPress
    export, keyed by author slug. Empty if the export is not on this machine."""
    if not os.path.exists(XML):
        return {}
    found = {}
    ch = ET.parse(XML).getroot().find('channel')
    for it in ch.findall('item'):
        if it.findtext('wp:post_type', default='', namespaces=NS) != 'post':
            continue
        if it.findtext('wp:status', default='', namespaces=NS) != 'publish':
            continue
        if not it.findtext('wp:post_date', default='', namespaces=NS).startswith('2026'):
            continue
        who = it.findtext('dc:creator', default='', namespaces=NS)
        raw = re.sub(r'<!--.*?-->', '',
                     it.findtext('content:encoded', default='', namespaces=NS) or '',
                     flags=re.S)
        m = re.search(r'ABOUT THE AUTHOR(.*)$', raw, re.S)
        if m and who:
            # unescape before collapsing: the export carries &nbsp; and &#8220;,
            # which would otherwise be escaped again and shown as literal text
            txt = html.unescape(re.sub(r'<[^>]+>', '', m.group(1)))
            txt = re.sub(r'\s+', ' ', txt).strip()
            bio = re.sub(r'^[:*\s]+', '', txt).strip()
            k = slug(who)
            if len(bio) > len(found.get(k, '')):
                found[k] = bio
    return found


def seed(store=None):
    """Every bio known before any page is rendered. Both generators call this
    first, so neither writes a page from an incomplete picture — which is how
    an author came to read differently on their article and on their own page.
    """
    store = load() if store is None else store
    store = merge(from_export(), store)
    store = merge({slug(n): b for n, b in SUPPLIED.items()}, store)
    return store
