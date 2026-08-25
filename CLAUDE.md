# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A static site for **TransHimalaya**, a journal published by the Foundation for Non-violent
Alternatives (FNVA). No framework, no bundler, no package.json — Python generators in `tools/`
assemble ~90 pages from content fragments and shared templates. Built by Norzin Consultancy.
It is intended to become a WordPress theme, and the structure is shaped for that.

## Commands

```bash
python3 -m http.server 8748           # serve locally → http://localhost:8748

python3 tools/rebuild.py              # reassemble pages from content/ + templates/
python3 tools/rebuild.py --check      # …and verify every internal link
python3 tools/rebuild.py --content    # regenerate content from the source docs first
python3 tools/build.py --only <slug>  # one page (accepts a slug or a type)
python3 tools/build.py --clean        # delete built directories first
python3 tools/check_links.py          # link/asset check; fails on relative references
```

There are no tests and no linter. The checks that exist:

- `tools/build.py` counts `<div>` vs `</div>` per page and reports `MISMATCH n/m`.
- `tools/check_links.py` resolves every internal reference. Treat a non-zero exit as a
  build failure. The issue PDF is a known, allowed absence (see README).

Requires `pandoc` and ImageMagick (`magick`) on PATH.

## Architecture

### Content and chrome are separate

Every page is a content fragment wrapped in shared chrome. No page file contains a masthead,
a navigation bar or a footer of its own.

```
content/<type>/<slug>.html    the unique part of one page — no <html>, no chrome
content/manifest.json         every page: type, slug, url, out, head_title, description
templates/partials/           header.html · footer.html · head.html · sprite.svg · scripts.html
templates/base.html           the document shell the partials bracket
templates/fragments/article.html   the shape of an article body, with {{PLACEHOLDERS}}
```

To change the chrome site-wide, edit one partial and run `tools/rebuild.py`. This is the
point of the structure — do not reintroduce per-page copies of the header or footer.

`tools/render.py` is a ~60-line renderer: `{{> partial}}` includes and `{{VAR}}`
substitution, nothing else. `tools/build.py` walks the manifest and writes the pages.

The mapping to a WordPress theme is deliberate: `partials/header.html` → `header.php`,
`partials/footer.html` → `footer.php`, `base.html` → the shell they bracket, and a
per-type template → `single.php` / `archive.php`. `build.py` will use
`templates/<type>.html` if it exists and fall back to `base.html`, which is the
extension point for genuinely different page shapes.

### tools/paths.py owns the URL scheme

Type + slug → URL and output path. Every page is written as `<dir>/index.html` so URLs end
in a slash and carry no extension, matching `/articles/%postname%/` in WordPress.

```
home /  ·  issue /journal-editions/  ·  article /articles/<slug>/
section /sections/<slug>/  ·  dreshey-hub /dreshey/  ·  dreshey /dreshey/<slug>/
authors-index /authors/  ·  author /authors/<slug>/
team-index /team/  ·  member /team/<slug>/  ·  page /<slug>/
```

**All links and assets must be site-absolute.** A page at `/articles/<slug>/` cannot resolve
a relative path — `assets/img/x.jpg` there means `/articles/<slug>/assets/img/x.jpg`.
Use `paths.asset(p)` rather than prepending a slash by hand: image paths arrive both bare
(from `tools/articles.json`) and already-absolute (from content fragments), and
hand-prefixing the second kind produces `//assets/...`, which the browser reads as a
protocol-relative host. `check_links.py` catches both mistakes.

### Generators produce content, never pages

Each generator writes `content/<type>/<slug>.html` and registers the page via
`tools/content.py` (`C.write(...)`, then `C.save(manifest)`). None of them emits `<html>`
or scrapes chrome out of another page — that is how it used to work and it is why the
navigation had to be edited in ten places.

Dependency order, as encoded in `tools/rebuild.py`:

```
build_issue → build_youth → build_authors → build_team
            → build_categories → build_deyshal → build_home → build_sections_css
```

Articles come first because the section, author, Dreshey and home pages all summarise them.
`sections.excerpt()` reads `content/article/<slug>.html`, so the article fragments must
exist before anything that renders a card.

`tools/build_articles.py` is the **superseded** WordPress-export path. It rebuilds the same
articles from older text and rewrites `tools/articles.json`. Don't run it incidentally.

### tools/sections.py owns section identity

Colour, slug, and the page that lists each section. Chips carry a class (`cat-<slug>`),
never an inline colour; the classes are generated into `components.css` between the
`/* >>> section-colours … */` markers by `build_sections_css.py`, which replaces that block
idempotently.

### Sources live outside the repo

- `build_issue.py`, `build_youth.py` → `~/Desktop/Tenzin Paljor/FNVA/1st Issue/**/*.docx`
- `build_authors.py`, `build_articles.py` → `~/Downloads/transhimalaya.WordPress.2026-08-03.xml`

Without them, `content/` as committed is the only copy. Prefer editing a fragment directly
over re-running a generator whose source you cannot see. `build_team.py` is the exception —
patron and trustee data is inline in the script.

## Stylesheets

`tokens.css` (custom properties + reset) → `chrome.css` (**masthead, nav, footer**) →
`components.css` (headings, cards, chips, icons, section colours) → `cursor.css`, then one
per page type (`home` `issues` `article` `category` `dreshey` `authors` `pages`). The load
order lives in `templates/partials/head.html`.

There is no `base.css` any more; it was split into the four files above. If you need to know
which file a rule belongs in, `chrome.css` is only ever the header and footer.

## Conventions

- Class prefixes: `.th-*` shared; `.issue-*`, `.art-*`, `.cat-*`, `.dy-*`, `.pg-*` per page type.
- No emoji. Icons are `<symbol>`s in `templates/partials/sprite.svg`, used via `<use href="#ic-…">`.
- Nav items carry `data-nav="<key>"`; `paths.nav_active()` names the key for a page and
  `render.mark_active()` applies the `active` class. Match on `data-nav`, not on href.
  Article pages deliberately highlight nothing.
- Mobile submenu rules are declared **last** in `chrome.css` on purpose — at equal
  specificity a media query does not beat source order. Don't move them.
- British spellings in prose and comments ("colour", "centred").
- Section names use a typographic apostrophe where the copy does (`Editor’s Note`); keys in
  `sections.py` must match exactly.
- Author slugs keep honorifics and fold accents (`Lt General Vinod Bhatia` →
  `lt-general-vinod-bhatia`). `build_articles.author_slug` is the shared implementation.

## Outstanding, per README

Issue PDF at `assets/pdf/transhimalaya-issue-1-august-2026.pdf`, the real cover for
`assets/img/cover.jpg`, a Razorpay key and server-side verification for the subscription
buttons, a mail handler for the contact form, and FNVA approval of the drafted copy.
Youth, Tibet Monitor and six Dreshey sub-sections render an honest empty state rather than
fake content — keep it that way until real material arrives.
