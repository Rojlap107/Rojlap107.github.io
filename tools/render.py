#!/usr/bin/env python3
"""A very small template renderer — enough for a static site, no dependencies.

Two forms:

    {{> name}}      include templates/partials/name.{html,svg}
    {{VAR}}         substitute a value; unknown names become empty

Includes are expanded before substitution and may nest, so a partial can
itself pull in another partial.

The templates map onto a WordPress theme one-to-one: partials/header.html is
header.php, partials/footer.html is footer.php, base.html is the document
shell those two bracket, and a per-type template (article.html, section.html)
is single.php / archive.php.
"""

import os
import re

TPL_DIR = 'templates'
PARTIAL_DIR = os.path.join(TPL_DIR, 'partials')
RE_INCLUDE = re.compile(r'\{\{>\s*([a-z0-9_-]+)\s*\}\}')
RE_VAR = re.compile(r'\{\{([A-Z][A-Z0-9_]*)\}\}')

_cache = {}


def partial(name):
    if name not in _cache:
        for ext in ('html', 'svg'):
            p = os.path.join(PARTIAL_DIR, f'{name}.{ext}')
            if os.path.exists(p):
                _cache[name] = open(p, encoding='utf-8').read()
                break
        else:
            raise FileNotFoundError(f'no partial named {name}')
    return _cache[name]


def template(name):
    p = os.path.join(TPL_DIR, name)
    return open(p, encoding='utf-8').read() if os.path.exists(p) else None


def expand(text, depth=0):
    """Resolve {{> partial}} includes, innermost last."""
    if depth > 8:
        raise RecursionError('partial includes nested too deeply')
    if not RE_INCLUDE.search(text):
        return text
    return expand(RE_INCLUDE.sub(lambda m: partial(m.group(1)), text), depth + 1)


def render(tpl_text, values):
    return RE_VAR.sub(lambda m: str(values.get(m.group(1), '')), expand(tpl_text))


def mark_active(html, nav_key):
    """Give the nav link carrying data-nav="<key>" the active class — the
    equivalent of WordPress's current-menu-item.

    Matching on data-nav rather than on href means renaming a menu label or
    moving a section's URL cannot silently stop the highlight from working.
    """
    if not nav_key:
        return html
    needle = f'<a data-nav="{nav_key}"'
    if needle not in html:
        raise KeyError(f'no nav item with data-nav="{nav_key}" in the header partial')
    return html.replace(needle, f'<a class="active" data-nav="{nav_key}"', 1)
