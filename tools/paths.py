#!/usr/bin/env python3
"""The URL scheme — one source of truth for where every page lives.

A page has a *type* and a *slug*. The type decides its URL prefix, its
template and its page stylesheet; the slug is the last path segment. Every
page is written as `<dir>/index.html` so the served URL ends in a slash and
needs no extension — the same shape WordPress produces from
`/articles/%postname%/`, so the migration is a rename rather than a rewrite.

    type            URL                        file
    home            /                          index.html
    issue           /journal-editions/         journal-editions/index.html
    article         /articles/<slug>/          articles/<slug>/index.html
    section         /sections/<slug>/          sections/<slug>/index.html
    interview       /interviews/<slug>/        interviews/<slug>/index.html
    dreshey-hub     /dreshey/                  dreshey/index.html
    dreshey         /dreshey/<slug>/           dreshey/<slug>/index.html
    authors-index   /authors/                  authors/index.html
    author          /authors/<slug>/           authors/<slug>/index.html
    team-index      /team/                     team/index.html
    page            /<slug>/                   <slug>/index.html
"""

# The top-level navigation keys, as marked with data-nav="..." in
# templates/partials/header.html. A page names the one it sits under and the
# build gives that link the `active` class — WordPress's current-menu-item.
NAV_ABOUT = 'about'          # the About submenu: about, team, authors, career, contact
NAV_IN_FOCUS = 'in-focus'    # In Focus gathers History, Tibet Today, Tibet Beyond Borders

# section slug -> the nav key it belongs under; the rest are nav items themselves
SECTION_NAV = {
    'history': NAV_IN_FOCUS,
    'tibet-today': NAV_IN_FOCUS,
    'tibet-beyond-borders': NAV_IN_FOCUS,
}

# type -> (URL prefix, template, page stylesheet, nav key to mark active)
TYPES = {
    'home':          ('',                  'home.html',          'home.css',     None),
    'issue':         ('journal-editions',  'issue.html',         'issues.css',   'journal-editions'),
    'article':       ('articles',          'article.html',       'article.css',  None),
    'section':       ('sections',          'section.html',       'category.css', None),
    # An interview lives at /interviews/<slug>/, not under /articles/. Its
    # listing stays with every other section, at /sections/interviews/.
    'interview':     ('interviews',        'interview.html',     'article.css',  'interviews'),
    'dreshey-hub':   ('dreshey',           'dreshey-hub.html',   'dreshey.css',  'dreshey'),
    'dreshey':       ('dreshey',           'dreshey-sub.html',   'dreshey.css',  'dreshey'),
    'authors-index': ('authors',           'authors-index.html', 'authors.css',  NAV_ABOUT),
    'author':        ('authors',           'author.html',        'authors.css',  NAV_ABOUT),
    'team-index':    ('team',              'team-index.html',    'pages.css',    NAV_ABOUT),
    'page':          ('',                  'page.html',          'pages.css',    NAV_ABOUT),
}

# types whose URL is the prefix itself — the slug is not appended
INDEX_TYPES = {'home', 'issue', 'dreshey-hub', 'authors-index', 'team-index'}


def url(page_type, slug=''):
    """The site-absolute URL for a page, always with a trailing slash."""
    prefix = TYPES[page_type][0]
    if page_type == 'home':
        return '/'
    if page_type in INDEX_TYPES:
        return f'/{prefix}/'
    return f'/{prefix}/{slug}/' if prefix else f'/{slug}/'


def out_path(page_type, slug=''):
    """Where the built file goes, relative to the site root."""
    u = url(page_type, slug)
    return 'index.html' if u == '/' else u.strip('/') + '/index.html'


def template(page_type):
    return TYPES[page_type][1]


def stylesheet(page_type):
    return TYPES[page_type][2]


def nav_active(page_type, slug=''):
    """The data-nav key this page should light up, or None for no highlight.

    Article pages deliberately highlight nothing: an essay belongs to a
    section but is not itself a navigation destination.
    """
    if page_type == 'section':
        return SECTION_NAV.get(slug, slug)
    return TYPES[page_type][3]


def asset(path):
    """A site-absolute asset URL, whatever form the caller happens to hold.

    Generators draw image paths from two places — tools/articles.json, which
    stores them bare ("assets/img/x.jpg"), and the content fragments, where
    they are already absolute ("/assets/img/x.jpg"). Prepending a slash by
    hand produces "//assets/..." for the second kind, which the browser reads
    as a protocol-relative host. Always route through here instead.
    """
    return '/' + str(path).lstrip('/')
