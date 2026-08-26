#!/usr/bin/env python3
"""The content store — where generators put what they produce.

A generator's job is now only the part of a page that is unique to it. It
writes a body fragment into content/<type>/<slug>.html and registers the
page's metadata in content/manifest.json; `tools/build.py` later wraps every
fragment in the shared chrome. No generator emits <html>, a masthead, a
navigation bar or a footer any more — those live once, in
templates/partials/.
"""

import json, os
import paths as P

MANIFEST = 'content/manifest.json'

# page types that are alternative filings of the same thing
FAMILIES = [{'article', 'interview'}]
SUFFIX = ' — TransHimalaya'


def load():
    return json.load(open(MANIFEST, encoding='utf-8')) if os.path.exists(MANIFEST) else []


def save(manifest):
    manifest.sort(key=lambda e: (e['type'], e['slug']))
    json.dump(manifest, open(MANIFEST, 'w'), indent=1, ensure_ascii=False)


def write(page_type, slug, title, description, body,
          head_title=None, manifest=None):
    """Write one page's content and register it. Returns the manifest entry.

    Pass `manifest` to batch many writes and save() once at the end; omit it
    and the manifest is read and written per call.
    """
    own = manifest is None
    manifest = load() if own else manifest

    name = slug or page_type
    rel = f'{page_type}/{name}.html'
    os.makedirs(f'content/{page_type}', exist_ok=True)
    open(f'content/{rel}', 'w', encoding='utf-8').write(body)

    entry = {
        'type': page_type,
        'slug': slug,
        'url': P.url(page_type, slug),
        'out': P.out_path(page_type, slug),
        'head_title': head_title or (title + SUFFIX),
        'description': description,
        'content': rel,
        'legacy': f'{slug or page_type}.html',
    }
    for i, e in enumerate(manifest):
        if e['type'] == page_type and e['slug'] == slug:
            entry['legacy'] = e.get('legacy', entry['legacy'])
            manifest[i] = entry
            break
    else:
        manifest.append(entry)

    # A piece can be filed as an article or as an interview but never both, so
    # writing one retires the other — that is how the Sikyong interview left
    # /articles/. Types outside a family share slugs quite legitimately: a
    # contributor has an author page and, if they wrote one, a piece at the
    # same slug, and those must not delete each other.
    for family in FAMILIES:
        if page_type not in family:
            continue
        for e in [x for x in manifest if x['slug'] == slug
                  and x['type'] in family and x['type'] != page_type]:
            manifest.remove(e)
            _discard(e)
            print(f"    - moved {e['url']} -> {entry['url']}")
    if own:
        save(manifest)
    return entry


def _discard(entry):
    """Delete a retired page's fragment and its built output."""
    import shutil
    for p in (f"content/{entry['content']}", os.path.dirname(entry['out'])):
        if os.path.isdir(p):
            shutil.rmtree(p, ignore_errors=True)
        elif os.path.exists(p):
            os.remove(p)


def prune(page_type, keep_slugs, manifest):
    """Drop registered pages of a type that the generator no longer produces,
    and delete their fragments and built output."""
    import shutil
    gone = [e for e in manifest
            if e['type'] == page_type and e['slug'] not in keep_slugs]
    for e in gone:
        manifest.remove(e)
        for p in (f"content/{e['content']}", os.path.dirname(e['out'])):
            shutil.rmtree(p, ignore_errors=True) if os.path.isdir(p) else (
                os.remove(p) if os.path.exists(p) else None)
        print(f"    - dropped {e['url']}")
    return manifest
