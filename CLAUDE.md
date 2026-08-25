# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A static site for **TransHimalaya**, a journal published by the Foundation for Non-violent
Alternatives (FNVA). No framework, no bundler, no package.json — 87 hand-shaped HTML files at
the repo root, plus `assets/` and a set of Python generators in `tools/`. Built by Norzin
Consultancy.

## Commands

```bash
python3 -m http.server 8748          # serve locally → http://localhost:8748
```

Generators — **always run from the site root**, never from `tools/`:

```bash
python3 tools/build_issue.py                 # the 23 first-issue article pages, from .docx
python3 tools/build_issue.py --only <slug>   # one article
python3 tools/build_issue.py --extras        # only the EXTRAS pieces (foreword, interview, …)
python3 tools/build_youth.py                 # youth-voices.html
python3 tools/build_categories.py            # section pages (in-focus, history, interviews, …)
python3 tools/build_deyshal.py               # dreshey.html hub + 9 sub-sections
python3 tools/build_authors.py               # author-<slug>.html + authors.html
python3 tools/build_team.py                  # member-<slug>.html (patrons, trustees)
python3 tools/build_home.py                  # the generated middle of index.html
python3 tools/build_sections_css.py          # section colours into base.css
```

There are no tests and no linter. The generators self-check by counting `<div>` vs `</div>` and
printing `OK` or `MISMATCH n/m` per page — treat a MISMATCH as a build failure.

Requires `pandoc` and ImageMagick (`magick`) on PATH.

## Architecture

### index.html is the chrome template

`build_authors.py`, `build_categories.py`, `build_deyshal.py` and `build_team.py` each read
`index.html` and regex out three regions to wrap their pages in:

- sprite — `<svg width="0" height="0">…</svg>`
- header + nav — `<!-- Header -->` … `</nav>`
- footer — `<!-- Newsletter -->` … `</footer>`

So the HTML comment markers in `index.html` (`<!-- Header -->`, `<!-- Opening -->`,
`<!-- Featured stories -->`, `<!-- About + Photo essay band -->`, `<!-- Newsletter -->`,
`<!-- Footer -->`) are load-bearing. Removing or renaming one breaks a generator, usually with
an `AttributeError` on `.group(0)`.

`build_home.py` writes *into* `index.html`, replacing everything from `<!-- Opening -->` to
`<!-- About + Photo essay band -->`. The hero, the About/Photo band, the newsletter and the
footer in `index.html` are hand-maintained; the middle is not — edits there are lost on the
next `build_home.py`.

Article pages come from `tools/article.tpl.html`, which carries its **own** copy of the nav.
A site-wide nav change therefore means: edit `index.html`, edit `article.tpl.html`, then
re-run the generators.

### tools/articles.json is the article index

`build_issue.py` reads it (slug, title, author, date, section, lede) and every other generator
depends on it for contents lists, section pages, author pages, must-read and
"you may also like" rails. It is currently **written only by `build_articles.py`**.

`build_articles.py` is the older WordPress-export path (reads a WXR file from `~/Downloads`)
and has been superseded by `build_issue.py` for the first issue's essays. Running it will
overwrite the docx-built article pages and rewrite `articles.json`. Don't run it unless that
is specifically what you want.

### tools/sections.py is the single source of truth for section identity

Colour, ordering, slug, and which page a section chip links to all live in `COLOURS` / `PAGES`
there. Chips carry a class (`cat-<slug>`), never an inline colour; the classes are emitted into
`base.css` between the `/* >>> section-colours … */` and `/* <<< section-colours */` markers.
After changing a colour, run `python3 tools/build_sections_css.py` — it replaces that block
idempotently.

`sections.py` also holds `excerpt()`, which scrapes each article page's `<p class="art-standfirst">`
for card summaries. Cards therefore depend on the article pages already existing: build
articles before section/home pages.

### Sources live outside the repo

The generators read from absolute paths under `$HOME` that are not committed:

- `build_issue.py`, `build_youth.py` → `~/Desktop/Tenzin Paljor/FNVA/1st Issue/**/*.docx`
  (the `DOCX` dict in `build_issue.py` maps slug → document path)
- `build_articles.py`, `build_authors.py` → `~/Downloads/transhimalaya.WordPress.2026-08-03.xml`

Without those, the generated pages already in git are the only artefact. Prefer editing HTML
directly over re-running a generator whose source you can't see.

`build_team.py` is the exception — patron and trustee data is inline in the script, because
they write no articles and so appear in no export.

### Ordering

`build_issue.py` (or `build_articles.py`) → `build_authors.py` → `build_categories.py` /
`build_deyshal.py` / `build_home.py`.

## Conventions

- CSS: `base.css` (shared chrome) plus exactly one stylesheet per page type —
  `home`, `issues`, `article`, `category`, `dreshey`, `authors`, `pages`. Every page loads
  `base.css` first.
- Class prefixes: `.th-*` for shared components; `.issue-*`, `.art-*`, `.cat-*`, `.dy-*`,
  `.pg-*` per page type.
- No emoji. Icons are inline SVG `<symbol>`s in the sprite at the top of each page, referenced
  with `<use href="#ic-…">`.
- Mobile submenu rules are declared **last** in `base.css` on purpose — at equal specificity a
  media query does not beat source order. Don't move them.
- British spellings in prose and in code comments ("colour", "centred").
- Section names use a typographic apostrophe where the copy does (`Editor’s Note`) — keys in
  `sections.py` must match exactly.
- Author slugs keep honorifics and fold accents (`Lt General Vinod Bhatia` →
  `lt-general-vinod-bhatia`). `build_articles.author_slug` is the shared implementation;
  `build_issue.py` imports it rather than reimplementing.

## Outstanding, per README

Issue PDF at `assets/pdf/transhimalaya-issue-1-august-2026.pdf`, the real cover for
`assets/img/cover.jpg`, a Razorpay key and server-side verification for the subscription
buttons, a mail handler for the contact form, and FNVA approval of the drafted copy (section
standfirsts, Must Reads selection, About/Team bios). Youth, Tibet Monitor and six Dreshey
sub-sections still render an honest empty state rather than fake content — keep it that way
until real material arrives.
