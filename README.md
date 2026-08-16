# TransHimalaya

The website for **TransHimalaya** — a magazine of ideas, policy and perspectives on
Tibet, the Himalaya and Inner Asia, published by the Foundation for Non-violent
Alternatives (FNVA).

Built by Norzin Consultancy.

## Running it

```bash
python3 -m http.server 8748
```

Then open <http://localhost:8748>.

## Pages

| | |
|---|---|
| `index.html` | Home |
| `journal-issue.html` | Journal Issue — the inaugural issue and its full contents |
| `main-essays.html` and sections | Tibet Today · Tibet Beyond Borders · History · The Strategic Triangle · Global Perspectives · Youth · Tibet Monitor |
| `dreshey.html` and sub-sections | Archives · Data & Visuals · Must Reads, plus six awaiting content |
| `about.html` · `team.html` · `career.html` · `contact.html` · `authors.html` | About |
| 23 article pages | one per published article, at its own slug |

## Structure

```
assets/css/   base.css (shared chrome) + one stylesheet per page type
assets/js/    site.js — bell cursor, hamburger, submenus, sharing
assets/img/   logo, covers, article photography, author portraits
assets/pdf/   issue PDFs (to be supplied)
tools/        generators — see below
```

Every page loads `base.css` plus its own stylesheet.

## Generators

The article, section and Dreshey pages are generated from the WordPress export
(`~/Downloads/transhimalaya.WordPress.*.xml`), not hand-written:

```bash
python3 tools/build_articles.py --all    # every published article
python3 tools/build_categories.py        # the section pages
python3 tools/build_deyshal.py           # the Dreshey hub and sub-sections
python3 tools/build_team.py              # patron and trustee profile pages
```

`build_articles.py` also downloads and resizes the images each article needs.

`build_team.py` holds its own data — patrons and trustees write no articles, so
they are not in the WordPress export. Their bios are drafts drawn from public
roles and need checking with FNVA. Author profiles are generated separately by
`build_authors.py`; the research-team members on `team.html` link to those.

## Conventions

- `.th-*` for site components, `.issue-*`, `.art-*`, `.cat-*`, `.dy-*`, `.pg-*` per page type
- No emoji — icons are inline SVG in the sprite at the top of each page
- Mobile submenu rules are declared **last** in `base.css`; at equal specificity a
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
