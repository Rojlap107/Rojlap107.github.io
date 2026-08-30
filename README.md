# TransHimalaya

The website for **TransHimalaya** — a magazine of ideas, policy and perspectives on
Tibet, the Himalaya and Inner Asia, published by the Foundation for Non-violent
Alternatives (FNVA).

Built by Norzin Consultancy.

## Running it

```bash
python3 -m http.server 8748
```

Then open <http://localhost:8748>. URLs end in a slash (`/articles/foreword/`) and
the server resolves each to that directory's `index.html`.

## How the site is put together

Every page is **content** (unique to it) wrapped in **chrome** (shared by all of
them). Nothing repeats the masthead, the navigation or the footer.

```
content/          the unique part of each page, as an HTML fragment
  manifest.json   every page: type, slug, URL, title, description
templates/
  partials/       header.html · footer.html · head.html · sprite.svg · scripts.html
  base.html       the document shell those partials bracket
  fragments/      article.html — the shape of an article body
assets/css/       tokens · chrome · components · cursor, plus one per page type
tools/            the URL scheme, the renderer, and the content generators
```

To change the masthead, the navigation or the footer, edit **one file** —
`templates/partials/header.html` or `templates/partials/footer.html` — and rebuild:

```bash
python3 tools/rebuild.py
```

This structure maps onto a WordPress theme directly: `partials/header.html` is
`header.php`, `partials/footer.html` is `footer.php`, `base.html` is the shell
they bracket, and the per-type templates are `single.php` / `archive.php`.

## URLs

| type | URL | file |
|---|---|---|
| home | `/` | `index.html` |
| edition | `/journal-editions/` | `journal-editions/index.html` |
| article | `/articles/<slug>/` | `articles/<slug>/index.html` |
| section | `/sections/<slug>/` | `sections/<slug>/index.html` |
| Dreshey | `/dreshey/` and `/dreshey/<slug>/` | … |
| author | `/authors/` and `/authors/<slug>/` | … |
| team | `/team/` | `team/index.html` |
| page | `/about/` `/contact/` | … |

`tools/paths.py` is the single source of truth for this. The scheme matches
WordPress's `/articles/%postname%/`, so the migration is a rename, not a rewrite.

All links and assets are **site-absolute** (`/assets/…`, `/articles/…`) because a
page at `/articles/<slug>/` cannot resolve a relative path. `tools/check_links.py`
fails the build if a relative reference creeps back in.

## Rebuilding

```bash
python3 tools/rebuild.py              # reassemble pages from content/ + templates/
python3 tools/rebuild.py --check      # …and verify every internal link
python3 tools/rebuild.py --content    # regenerate the content first (needs the sources below)
python3 tools/build.py --only about   # one page
python3 tools/check_links.py          # link and asset check on its own
```

## Generators

The article, section, author, Dreshey and home-page content is generated,
not hand-written. Each writes into `content/`; `tools/build.py` then wraps every
fragment in the chrome.

```bash
python3 tools/build_issue.py          # article pages from the finalised .docx
python3 tools/build_issue.py --only <slug>
python3 tools/build_youth.py          # the Youth Voices page
python3 tools/build_authors.py        # author pages and the author index
python3 tools/build_categories.py     # section pages
python3 tools/build_deyshal.py        # the Dreshey hub and sub-sections
python3 tools/build_home.py           # the generated middle of the home page
python3 tools/build_sections_css.py   # section colours into components.css
```

Run them in that order — the section, author, Dreshey and home pages all
summarise the articles.

`/about/`, `/team/`, `/governing-council/` and `/contact/` are
hand-maintained: edit their fragments under `content/page/` (and
`content/team-index/`) directly.

`tools/build_articles.py` is the **superseded** WordPress-export path. It rebuilds
the same articles from the older WordPress text and rewrites
`tools/articles.json`; only run it deliberately.

### Sources that live outside this repository

- `build_issue.py`, `build_youth.py` → `~/Desktop/Tenzin Paljor/FNVA/1st Issue/**/*.docx`
- `build_authors.py`, `build_articles.py` → `~/Downloads/transhimalaya.WordPress.2026-08-03.xml`

Without those, `content/` as committed is the only copy — edit the fragments
directly rather than re-running a generator whose source you cannot see.

Requires `pandoc` and ImageMagick (`magick`) on PATH.

## Stylesheets

| file | what it holds |
|---|---|
| `tokens.css` | colour, type and imagery custom properties, and the reset |
| `chrome.css` | **the masthead, navigation and footer** — change the chrome here |
| `components.css` | section headings, cards, chips, icons, section colours |
| `cursor.css` | the bell (drilbu) pointer |
| `home` `issues` `article` `category` `dreshey` `authors` `pages` | one per page type |

Every page loads the first four, then its own. `templates/partials/head.html` is
where that list lives.

## Section colours

`tools/sections.py` is the single source of truth for each topic's colour, its
slug and the page that lists it. Every card, chip and filter pill takes its
colour from there, so one topic always reads the same. After changing a colour:

```bash
python3 tools/build_sections_css.py
```

## Opening card images

The Foreword and Editor's Note have only author portraits, so their home-page
cards use the portrait contained on a blurred fill of itself (never cropped to
16:10, which cuts faces off):

```bash
magick SRC -fuzz 12% -trim +repage /tmp/_src.png
magick /tmp/_src.png -resize 900x563^ -gravity center -extent 900x563 -blur 0x18 -modulate 96,70 /tmp/_bg.jpg
magick /tmp/_src.png -resize 470x520 /tmp/_fg.png
magick /tmp/_bg.jpg /tmp/_fg.png -gravity center -composite -strip -quality 84 OUT
```

## Conventions

- `.th-*` for site components, `.issue-*`, `.art-*`, `.cat-*`, `.dy-*`, `.pg-*` per page type
- No emoji — icons are inline SVG in `templates/partials/sprite.svg`
- Navigation items carry `data-nav="<key>"`; the build gives the current page's
  item the `active` class, so renaming a label cannot break the highlight
- Mobile submenu rules are declared **last** in `chrome.css`; at equal specificity a
  media query does not beat source order

## Still needed from FNVA

- **Inaugural issue PDF** at `assets/pdf/transhimalaya-issue-1-august-2026.pdf` — the
  download button already points at this path
- **Inaugural issue cover** — `assets/img/cover.jpg` is still the old placeholder
- **Razorpay key** and a server-side order/verification endpoint for the subscription buttons
- **A mail handler** for the contact form
- **Copy approval** — section descriptions, the Must Reads selection, and the About and
  Team pages were drafted from fnvaworld.org and need checking
- Content for Youth, Tibet Monitor and six Dreshey sub-sections
