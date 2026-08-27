# Migrate one page onto site.css + blocks.css.
#
# The page keeps its own <style> for anything genuinely page-specific. Rules
# that already exist byte-for-byte in the shared files are deleted from it, and
# the two files are linked ahead of it, so the order stays shared-first,
# page-specific-after, exactly as the page reads today.
#
# The way this goes wrong is order. A rule that moves into a shared file moves
# EARLIER. If something that stays inline used to be beaten by it, that flips.
# Two vetoes below catch it.
import io, os, re, sys

SITE = r'C:\Users\Jack Murray\OneDrive\Documents\big-apple-greeter'
PAGE = sys.argv[1] if len(sys.argv) > 1 else 'support'


def split(css):
    out, depth, buf = [], 0, ''
    for ch in css:
        buf += ch
        if ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0:
                out.append(buf); buf = ''
    return [c for c in out if c.strip()]


strip_c = lambda s: re.sub(r'/\*.*?\*/', '', s, flags=re.S)
norm = lambda c: ' '.join(strip_c(c).split())
sel_of = lambda c: norm(c).split('{')[0].strip()


def sel_set(chunk):
    s = sel_of(chunk)
    if s.startswith('@'):
        return set()
    return {' '.join(p.split()) for p in s.split(',') if p.strip()}


def props(chunk):
    b = norm(chunk)
    if '{' not in b:
        return set()
    b = b[b.find('{') + 1:b.rfind('}')]
    return {d.split(':')[0].strip() for d in b.split(';') if ':' in d}


shared = set()
for f in ('site.css', 'blocks.css'):
    for c in split(io.open(os.path.join(SITE, 'assets', f), encoding='utf-8').read()):
        shared.add(norm(c))

P = os.path.join(SITE, PAGE + '.html')
html = io.open(P, encoding='utf-8').read()
if 'assets/site.css' in html:
    sys.exit('%s.html is already migrated.' % PAGE)

m = re.search(r'(<style[^>]*>)(.*?)(</style>)', html, re.S)
chunks = split(m.group(2))
movable = [i for i, c in enumerate(chunks) if norm(c) in shared]

# Veto pass. A candidate is held back if any rule that STAYS inline sits
# earlier in the page and either declares the same selector, or declares a
# property this rule also sets. The second case is the one that bites:
# .btn and .btn-outline are different selectors that both set background on
# an element carrying class="btn btn-outline", so extracting one without the
# other reverses which declaration wins.
stay = [i for i in range(len(chunks)) if i not in set(movable)]
vetoed = []
for i in list(movable):
    mine, myprops = sel_set(chunks[i]), props(chunks[i])
    if not mine:
        continue
    for j in stay:
        if j >= i:
            continue
        if (sel_set(chunks[j]) & mine) or (props(chunks[j]) & myprops):
            vetoed.append((sel_of(chunks[i]), sel_of(chunks[j])))
            movable.remove(i)
            break

keep = [c for i, c in enumerate(chunks) if i not in set(movable)]
new_css = ''.join(keep)

LINKS = ("<!-- Shared foundation and block library. Linked ahead of this page's own\n"
         "     <style>, so page-specific rules still win, exactly as before. -->\n"
         '<link rel="stylesheet" href="assets/site.css">\n'
         '<link rel="stylesheet" href="assets/blocks.css">\n')

io.open(P, 'w', encoding='utf-8', newline='').write(
    html[:m.start()] + LINKS + m.group(1) + new_css + m.group(3) + html[m.end():])

print('%s.html' % PAGE)
print('  rules          %d -> %d   (%d moved out)' % (len(chunks), len(keep), len(movable)))
print('  inline CSS  %.1f KB -> %.1f KB' % (len(m.group(2)) / 1024, len(new_css) / 1024))
if vetoed:
    print('  held back to protect the cascade:')
    for a, b in vetoed:
        print('     %-34s  (page rule %s comes first)' % (a[:34], b[:28]))
else:
    print('  no cascade conflicts found')
