#!/usr/bin/env python
"""Render a page from content/<page>.json and the templates in blocks/.

    python tools-render.py about-v2

The page is data: an ordered list of block instances, each naming a template
and carrying the text, images and links that go in it. This script turns that
list back into HTML. Nothing here knows anything about the About page
specifically, so the same renderer serves every page that gets converted.

Template syntax is mustache-shaped and deliberately tiny:

    {{key}}            insert the value
    {{a.b}}            dotted lookup
    {{#key}}...{{/key}} list  -> repeat once per item, item fields in scope
                        truthy -> render once
                        absent or empty -> skip
    {{^key}}...{{/key}} render only when key is absent or empty

Values are inserted raw, not escaped. The JSON holds authored HTML fragments,
because the copy on this site uses <b> for emphasis and named entities such as
&rsquo; throughout, and escaping would mangle both. That is a real trade: an
editor writing into these fields is writing HTML, so the admin layer will need
to sanitise on save rather than on render.
"""
import io, json, os, re, sys

ROOT = os.path.dirname(os.path.abspath(__file__))
TPL = os.path.join(ROOT, 'blocks')
_cache = {}


def template(name):
    if name not in _cache:
        p = os.path.join(TPL, name + '.html')
        if not os.path.isfile(p):
            raise SystemExit('no template for block type %r (blocks/%s.html)' % (name, name))
        _cache[name] = io.open(p, encoding='utf-8').read()
    return _cache[name]


def lookup(ctx, key):
    cur = ctx
    for part in key.split('.'):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            return None
    return cur


SECTION = re.compile(r'\{\{([#^])([\w.]+)\}\}(.*?)\{\{/\2\}\}', re.S)
VALUE = re.compile(r'\{\{\{?([\w.]+)\}\}\}?')


def render(tpl, ctx):
    def section(m):
        kind, key, inner = m.group(1), m.group(2), m.group(3)
        val = lookup(ctx, key)
        empty = val is None or val is False or val == '' or val == [] or val == {}
        if kind == '^':
            return render(inner, ctx) if empty else ''
        if empty:
            return ''
        if isinstance(val, list):
            out = []
            for item in val:
                sub = dict(ctx)
                sub.update(item) if isinstance(item, dict) else sub.update({'.': item})
                out.append(render(inner, sub))
            return ''.join(out)
        if isinstance(val, dict):
            sub = dict(ctx)
            sub.update(val)
            return render(inner, sub)
        # A truthy scalar renders the section once and is available by its key.
        return render(inner, ctx)

    prev = None
    while prev != tpl:
        prev = tpl
        tpl = SECTION.sub(section, tpl)

    def value(m):
        v = lookup(ctx, m.group(1))
        return '' if v is None or v is True or v is False else str(v)

    return VALUE.sub(value, tpl)


def banner(note, indent):
    """The signpost comments the hand-written pages carry. Kept because they
    make the generated file readable, and because the same string is what an
    editor would show as the block's name in a sidebar."""
    return '%s<!-- ============ %s ============ -->\n' % (' ' * indent, note)


def block(b, indent=2):
    """Render one block. Containers recurse, so nesting depth is not fixed."""
    t = b['type']
    ctx = dict(b)
    if t == 'sections-with-photo':
        # The sections inside render through the ordinary group template, so
        # a section beside a photo and a section on its own are the same
        # thing described the same way. Same indent, not indent+2: the inner
        # column <div> is not itself indented.
        ctx['sections'] = stack(b.get('sections', []), indent)
    out = render(template(t), ctx)
    if b.get('note'):
        out = banner(b['note'], indent) + out
    return out


# Blocks that span the full window. Everything else is page content and sits
# in the centred column, so the renderer wraps runs of them rather than making
# anyone put a container block in the content file.
FULL_BLEED = {'header', 'hero-photo', 'fam-hero', 'cta', 'reunion-cta', 'invited', 'footer'}


def stack(blocks, indent=2, wrap=False):
    """One blank line between blocks, whatever each template ends with.

    With wrap=True, consecutive content blocks are collected into the .wide
    container. That container holds no content of its own, so it does not
    belong in the content file: an editor should be arranging sections, not
    thinking about which div they live in.
    """
    if not wrap:
        return '\n\n'.join(block(b, indent).rstrip('\n') for b in blocks) + '\n'

    out, run = [], []

    def flush():
        if run:
            inner = '\n\n'.join(block(b, indent + 2).rstrip('\n') for b in run) + '\n'
            out.append(render(template('_wide'), {'blocks': inner}).rstrip('\n'))
            del run[:]

    for b in blocks:
        if b['type'] in FULL_BLEED:
            flush()
            out.append(block(b, indent).rstrip('\n'))
        else:
            run.append(b)
    flush()
    return '\n\n'.join(out) + '\n'


def styles(blocks, seen=None):
    """CSS for the blocks this page uses, and nothing else.

    _base.css first, then one file per block type in the order the blocks
    appear. A block with no .css file simply contributes nothing, which is
    how chrome-only blocks behave.
    """
    if seen is None:
        seen = []
        css = ['_base']
    else:
        css = []
    for b in blocks:
        t = b['type']
        for dep in DEPENDS.get(t, []):
            if dep not in seen:
                seen.append(dep)
                css.append(dep)
        if t not in seen:
            seen.append(t)
            css.append(t)
        if isinstance(b.get('sections'), list):
            css.extend(styles(b['sections'], seen))
    return css


def read_css(names):
    out = []
    for n in names:
        p = os.path.join(TPL, n + '.css')
        if os.path.isfile(p):
            out.append(io.open(p, encoding='utf-8').read().rstrip() + '\n\n')
    return ''.join(out)


# A block that reuses another block's classes rather than restating them.
# link-group and split-group are groups with a different row shape or an extra
# wrapper; both lean on .group, .group-head and .rows from group.css, so a page
# that uses one without a plain group still needs those rules.
DEPENDS = {
    'link-group': ['group'],
    'split-group': ['group'],
}


def read_js(names):
    """Behavioural blocks carry their script beside their markup.

    Emitted in the same order as the CSS, once per block type, after the
    scripts every page shares. A block with no .js file contributes nothing,
    which is how content blocks behave."""
    out = []
    for n in names:
        p = os.path.join(TPL, n + '.js')
        if os.path.isfile(p):
            out.append('<script>\n' + io.open(p, encoding='utf-8').read().rstrip() + '\n</script>\n')
    return ''.join(out)


# Only the video leaves the repo. assets/*.mp4 is gitignored and lives on R2;
# the 35 images under assets/ are committed and stay where they are. So the
# rewrite is deliberately narrow: it moves .mp4 references and nothing else.
VIDEO_SRC = re.compile(r'(["\'(])assets/([\w.\-]+\.mp4)')


def rebase(html, base):
    """Point every assets/*.mp4 reference at `base` instead.

    Left empty the page keeps its relative paths, which is what you want
    locally: the masters are still in assets/ and the page opens from disk
    with the reels playing. Set it for a deploy and the same content file
    renders against the bucket, so the URL lives in one place rather than
    being pasted through the markup."""
    if not base:
        return html
    if not base.endswith('/'):
        base += '/'
    return VIDEO_SRC.sub(lambda m: m.group(1) + base + m.group(2), html)


def asset_base(data):
    """--base wins, then BAG_ASSET_BASE, then the content file, then local."""
    for i, a in enumerate(sys.argv):
        if a == '--base' and i + 1 < len(sys.argv):
            return sys.argv[i + 1]
        if a.startswith('--base='):
            return a.split('=', 1)[1]
    return os.environ.get('BAG_ASSET_BASE') or data.get('asset_base') or ''


def build(page):
    data = json.load(io.open(os.path.join(ROOT, 'content', page + '.json'), encoding='utf-8'))
    body = stack(data['blocks'], wrap=True)
    # Sorted, not page order: reordering content must never be able to change
    # which rule wins. _base stays first; the rest are alphabetical so the
    # cascade is a property of the library, not of how a page is arranged.
    used = styles(data['blocks'])
    css = read_css(['_base'] + sorted(t for t in used if t != '_base'))
    # Scripts follow page order, not alphabetical: CSS is sorted so the cascade
    # cannot depend on how a page is arranged, but a script's effect does not
    # cascade, and reading them in the order the blocks appear is kinder.
    scripts = read_js([t for t in used if t != '_base'])
    html = render(template('_page'), dict(data, body=body, css=css, scripts=scripts))
    html = rebase(html, asset_base(data))
    out = os.path.join(ROOT, page + '.html')
    io.open(out, 'w', encoding='utf-8', newline='').write(html)
    return out, len(html)


if __name__ == '__main__':
    # page names are the bare arguments; --base and its value are not pages
    skip = False
    clean = []
    for a in sys.argv[1:]:
        if skip:
            skip = False
            continue
        if a == '--base':
            skip = True
            continue
        if a.startswith('--'):
            continue
        clean.append(a)
    for page in (clean or ['about-v2']):
        p, n = build(page)
        print('%-24s %6.1f KB' % (os.path.basename(p), n / 1024))
