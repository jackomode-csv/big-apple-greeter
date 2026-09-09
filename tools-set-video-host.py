#!/usr/bin/env python
"""Point the hand-written pages' video at a host, or back at the repo.

    python tools-set-video-host.py https://<host>/<prefix>
    python tools-set-video-host.py --local

The block-rendered pages get this from `asset_base` in their content file and
are not touched here. The other seven pages are hand-written and self-contained
by design, so their video URLs live in the markup. This rewrites them in place
and is idempotent: run it again with a different host and it moves them again,
which is what you want the day the bucket gets a custom domain.

Only <clip>.mp4 moves. Posters, images and stylesheets are committed to the
repo and stay relative.
"""
import io, os, re, sys

ROOT = os.path.dirname(os.path.abspath(__file__))
PAGES = ['index.html', 'about.html', 'visitors.html', 'volunteers.html',
         'support.html', 'register.html', 'volunteer-register.html']

# matches both forms, so the rewrite is reversible and repeatable:
#   "assets/hero.mp4"   and   "https://any-host/any/prefix/hero.mp4"
REF = re.compile(r'(["\'(])(?:assets/|https?://[^"\'()]*?/)([\w.\-]+\.mp4)')


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    arg = sys.argv[1]
    local = arg == '--local'
    base = '' if local else arg.rstrip('/') + '/'
    if not local and not arg.startswith('http'):
        sys.exit('give a full https:// base, or --local')

    total = 0
    for name in PAGES:
        p = os.path.join(ROOT, name)
        if not os.path.isfile(p):
            continue
        s = io.open(p, encoding='utf-8').read()
        new, n = REF.subn(lambda m: m.group(1) + (base or 'assets/') + m.group(2), s)
        if n and new != s:
            io.open(p, 'w', encoding='utf-8', newline='').write(new)
        total += n
        print('  %-26s %2d ref%s' % (name, n, '' if n == 1 else 's'))
    print('\n%d video references now point at %s'
          % (total, 'assets/ in the repo' if local else base))


if __name__ == '__main__':
    main()
