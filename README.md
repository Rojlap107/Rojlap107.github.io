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
| `issues.html` | Magazine Issue — current issue, contents, past issues |
| `main-essays.html` and sections | Tibet Today · Tibet Beyond Borders · History · The Strategic Triangle · Global Perspectives · Youth · Tibet Monitor |
| `deyshal.html` and sub-sections | Archives · Data & Visuals · Must Reads, plus six awaiting content |
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

The article, section and Deyshal pages are generated from the WordPress export
(`~/Downloads/transhimalaya.WordPress.*.xml`), not hand-written:

```bash
python3 tools/build_articles.py --all    # every published article
python3 tools/build_categories.py        # the section pages
python3 tools/build_deyshal.py           # the Deyshal hub and sub-sections
```

`build_articles.py` also downloads and resizes the images each article needs.

## Conventions

- `.th-*` for site components, `.issue-*`, `.art-*`, `.cat-*`, `.dy-*`, `.pg-*` per page type
- No emoji — icons are inline SVG in the sprite at the top of each page
- Mobile submenu rules are declared **last** in `base.css`; at equal specificity a
  media query does not beat source order

## Still needed from FNVA

- **Issue PDFs** in `assets/pdf/` (`transhimalaya-vol14-no2.pdf` etc.) — the download
  buttons already point at these paths
- **Past-issue data** — the six back issues shown are placeholders
- **Razorpay key** and a server-side order/verification endpoint for the subscription buttons
- **A mail handler** for the contact form
- **Copy approval** — section descriptions, the Must Reads selection, and the About and
  Team pages were drafted from fnvaworld.org and need checking
- Content for Youth, Tibet Monitor and six Deyshal sub-sections
