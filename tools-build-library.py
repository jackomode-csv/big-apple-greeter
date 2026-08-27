# Build site.css and blocks.css by lifting rules out of the seven pages
# verbatim. Every declaration came from the pages as-is.
#
# Run this BEFORE migrating any page. It decides what is shared by comparing
# the seven inline stylesheets, so once a page has been migrated its rules are
# gone from the comparison and the result collapses.
import io, os, re, collections

SITE = r'C:\Users\Jack Murray\OneDrive\Documents\big-apple-greeter'
OUT = os.path.join(SITE, 'assets')
PAGES = ['index', 'about', 'visitors', 'volunteers', 'support',
         'register', 'volunteer-register']


def read(p):
    s = io.open(os.path.join(SITE, p + '.html'), encoding='utf-8').read()
    return ''.join(re.findall(r'<style[^>]*>(.*?)</style>', s, re.S))


def split(css):
    """Top-level chunks: one rule, or a whole @media block, in source order."""
    out, depth, buf = [], 0, ''
    for ch in css:
        buf += ch
        if ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0:
                out.append(buf.strip()); buf = ''
    return [c for c in out if c.strip()]


strip_comments = lambda s: re.sub(r'/\*.*?\*/', '', s, flags=re.S)
norm = lambda c: ' '.join(strip_comments(c).split())
sel_of = lambda c: norm(c).split('{')[0].strip()

raw = {p: split(read(p)) for p in PAGES}
normed = {p: [norm(c) for c in raw[p]] for p in PAGES}
count = collections.Counter()
for p in PAGES:
    for c in set(normed[p]):
        count[c] += 1

# ---------------------------------------------------------------- site.css --
universal, seen = [], set()
for i, c in enumerate(normed['index']):
    if count[c] == len(PAGES) and c not in seen and not c.startswith(':root'):
        universal.append(raw['index'][i])
        seen.add(c)

assert len(universal) > 30, (
    'only %d universal rules - has a page already been migrated? '
    'Restore the pages before rebuilding the library.' % len(universal))

# :root varies slightly per page: index omits --panel/--radius, register adds
# --green. Union them so one sheet serves every page and no page loses a token.
# Comments are stripped first, or a trailing /* note */ parses as a key.
tokens, notes = {}, {}
for p in PAGES:
    m = re.search(r':root\s*\{(.*?)\}', read(p), re.S)
    if not m:
        continue
    body = m.group(1)
    for decl in strip_comments(body).split(';'):
        if ':' in decl:
            k, v = decl.split(':', 1)
            if k.strip().startswith('--'):
                tokens.setdefault(k.strip(), v.strip())
    for k, note in re.findall(r'(--[\w-]+)\s*:[^;]*;\s*/\*(.*?)\*/', body, re.S):
        notes.setdefault(k, ' '.join(note.split()))

# .btn is the one near-miss, and it matters. Six pages write
# border-radius:var(--radius); index writes 2px, because index is the one page
# whose :root never declared --radius. So .btn fails the byte-identical test
# and would stay inline everywhere while .btn-outline moves into this file.
# Inline loads last, so .btn's red fill would then beat .btn-outline and every
# ghost button on the site would render solid. The var() form goes in here,
# and this file declares --radius, so it resolves wherever it is linked.
BTN = ('.btn{ display:inline-block; background:var(--red); color:#fff;'
       ' font-weight:600; font-size:.95rem; letter-spacing:.02em;'
       ' padding:14px 30px; border-radius:var(--radius); white-space:nowrap;'
       ' transition:background .2s ease; }')

HEADER = '''/* ==========================================================================
   Big Apple Greeter - site.css
   Shared foundation: tokens, reset, base type, header, footer, buttons.

   Every rule below was already present, byte for byte, on all seven pages,
   with one documented exception (.btn - see the note in the build script).
   Nothing has been renamed, so a page that links this file and drops its own
   copy of these rules renders exactly as it does today.

   Deliberately absent: a global type scale. The pages size headings per
   component and share only letter-spacing, so declaring h1/h2/h3 sizes here
   would change rendering rather than preserve it.
   ========================================================================== */

'''

site = [HEADER, ':root {\n']
for k, v in tokens.items():
    tail = ('   /* %s */' % notes[k]) if k in notes else ''
    site.append('  %-14s %s;%s\n' % (k + ':', v, tail))
site.append('}\n\n')
site.append('/* ---- reset, base, header, footer: identical on all seven pages ---- */\n\n')

placed = False
for c in universal:
    if not placed and sel_of(c).startswith('.btn'):
        site.append(BTN + '\n\n')
        placed = True
    site.append(c.strip() + '\n\n')
if not placed:
    site.append(BTN + '\n\n')

io.open(os.path.join(OUT, 'site.css'), 'w', encoding='utf-8', newline='').write(''.join(site))

# -------------------------------------------------------------- blocks.css --
FAMILIES = [
    ('Hero', 'index', ['hero', 'hero-overlay', 'hero-video', 'hero-media', 'hero-cta',
                       'hero-btn', 'hero-controls', 'btn-watch', 'scroll-cue', 'eyebrow'],
     'Four pages declared this identically (.hero, .sup-hero, .hub-hero, .fam-hero).'),
    ('Hero, photo variant', 'about', ['about-hero'],
     'The one hero that differs: a column layout, white type over a photo.'),
    ('Feature band', 'index', ['feature', 'feature-', 'media', 'media-'], ''),
    ('Clips + map', 'index', ['clips', 'clips-', 'clip-', 'map', 'map-', 'qr', 'qr-'], ''),
    ('News + reviews', 'index', ['quotes', 'qn-', 'rev-', 'news', 'news-'], ''),
    ('FAQ', 'visitors', ['faq', 'faqs', 'faq-'], ''),
    ('Tabs', 'visitors', ['tab', 'tabs', 'tabpanel'], ''),
    ('Invited band', 'volunteers', ['invited'], ''),
    ('CTA band', 'about', ['story-cta', 'reunion-cta', 'cta-row'],
     '.story-cta and .reunion-cta were byte-identical; declared once.'),
    ('Pull quote', 'support', ['story-quote'], ''),
    ('Tax band', 'support', ['tax-band'], ''),
    ('Photo banner', 'about', ['photo-banner'], ''),
    ('Page head', 'visitors', ['page-head', 'intro', 'lede'], ''),
    ('Content group', 'visitors', ['group', 'group-head', 'rows', 'wide', 'linkrow', 'more'],
     'The workhorse: 46 uses across four pages.'),
    ('Form kit', 'register', ['field', 'req', 'err', 'grid', 'chip', 'chips', 'g2', 'g3',
                              'panel', 'lbl', 'dot', 'station', 'bullet', 'sub', 'shell',
                              'spam', 'stepper', 'step', 'note'],
     'Shared by both registration pages.'),
]


def claims(sel, names):
    """A name ending in '-' is a prefix (clip- matches .clip-video); anything
    else must match a whole class, so .sub never swallows .subway."""
    for n in names:
        pat = r'[.#]' + re.escape(n) + ('' if n.endswith('-') else r'(?![\w-])')
        if re.search(pat, sel):
            return True
    return False


blocks = ['''/* ==========================================================================
   Big Apple Greeter - blocks.css
   The block library. Each rule set is lifted verbatim from the page that owns
   it, grouped by the class vocabulary the markup actually uses.

   Two consolidations, and only two:
     .hero / .sup-hero / .hub-hero / .fam-hero were byte-identical on four
       pages, so the hero is declared once.
     .story-cta / .reunion-cta were byte-identical, likewise.

   Nothing was renamed. Nine band classes are load-bearing for the site's
   JavaScript - the scroll-reveal groups and the reel play button select on
   them - so every original class name is kept exactly as it is today.
   ========================================================================== */

''']

used, stats = set(), []
for title, src, names, note in FAMILIES:
    hits = []
    for i, c in enumerate(raw[src]):
        s = sel_of(c)
        if s.startswith('@') or normed[src][i] in used:
            continue
        if claims(s, names):
            hits.append(c.strip())
            used.add(normed[src][i])
    if hits:
        blocks.append('/* ---- %s  (from %s.html) ---- */\n' % (title.upper(), src))
        if note:
            blocks.append('/* %s */\n' % note)
        blocks.append('\n' + '\n\n'.join(hits) + '\n\n')
        stats.append((title, len(hits)))

io.open(os.path.join(OUT, 'blocks.css'), 'w', encoding='utf-8', newline='').write(''.join(blocks))

print('site.css    %6.1f KB   %d universal rules (+ .btn), %d tokens'
      % (os.path.getsize(os.path.join(OUT, 'site.css')) / 1024, len(universal), len(tokens)))
print('blocks.css  %6.1f KB   %d rules across %d blocks'
      % (os.path.getsize(os.path.join(OUT, 'blocks.css')) / 1024, len(used), len(stats)))
for t, n in stats:
    print('   %-22s %3d' % (t, n))
