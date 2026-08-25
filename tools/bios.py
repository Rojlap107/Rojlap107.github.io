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

import json, os

PATH = 'tools/bios.json'

# what the article template prints when an author has no bio. It is scraped
# back off the author page, so without this it would enter the store as though
# it were real text and an author would look as if they had a bio.
PLACEHOLDER = 'Contributor to TransHimalaya.'


def load():
    return json.load(open(PATH, encoding='utf-8')) if os.path.exists(PATH) else {}


def save(store):
    json.dump(dict(sorted(store.items())), open(PATH, 'w'), indent=1, ensure_ascii=False)


def merge(found, store=None):
    """Record what a generator has discovered, keeping the fullest text."""
    own = store is None
    store = load() if own else store
    for slug, bio in (found or {}).items():
        bio = (bio or '').strip()
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
    have, fallback = store.get(slug, ''), (fallback or '').strip()
    return have if len(have) >= len(fallback) else fallback
