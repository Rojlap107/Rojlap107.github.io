#!/usr/bin/env python3
"""Rebuild the site.

Two workflows, because they have very different costs:

    python3 tools/rebuild.py            # reassemble pages from content/ + templates/
    python3 tools/rebuild.py --content  # regenerate the content first, then reassemble

The first is what you want after editing a partial, a stylesheet or a content
fragment: it is fast and needs nothing but this repository. The second re-runs
every content generator, which reads the Word documents and the WordPress
export from outside the repo (see README) and re-downloads images.

    python3 tools/rebuild.py --check    # reassemble, then verify every link

Run from the site root.
"""

import argparse, subprocess, sys

# in dependency order: articles first, because the section, author, Dreshey and
# home pages all summarise them
CONTENT_STEPS = [
    ('build_issue.py',        'article pages from the finalised documents'),
    ('build_youth.py',        'the Youth Voices page'),
    ('build_authors.py',      'author pages and the author index'),
    ('build_categories.py',   'section pages'),
    ('build_deyshal.py',      'the Dreshey hub and sub-sections'),
    ('build_home.py',         'the generated middle of the home page'),
    ('build_sections_css.py', 'section colours into components.css'),
]


def run(script, *args):
    print(f'\n== {script} {" ".join(args)}')
    r = subprocess.run([sys.executable, f'tools/{script}', *args])
    return r.returncode


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--content', action='store_true',
                    help='regenerate content from the source documents first')
    ap.add_argument('--check', action='store_true',
                    help='verify every internal link afterwards')
    args = ap.parse_args()

    failed = []
    if args.content:
        for script, what in CONTENT_STEPS:
            if run(script):
                failed.append(script)
                print(f'  ! {script} failed ({what}) — continuing')

    if run('build.py', '--clean'):
        failed.append('build.py')

    if args.check and run('check_links.py'):
        failed.append('check_links.py')

    print()
    if failed:
        print('  FAILED: ' + ', '.join(failed))
        return 1
    print('  rebuild complete')
    return 0


if __name__ == '__main__':
    sys.exit(main())
