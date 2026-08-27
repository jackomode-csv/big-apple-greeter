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
    if t == 'split':
        # Same indent, not indent+2: .split's inner column <div> is not
        # itself indented, so its children sit level with the split.
        ctx['left'] = stack(b.get('left', []), indent)
    elif t == 'wide':
        ctx['blocks'] = stack(b.get('blocks', []), indent + 2)
    out = render(template(t), ctx)
    if b.get('note'):
        out = banner(b['note'], indent) + out
    return out


def stack(blocks, indent=2):
    """One blank line between blocks, whatever each template ends with."""
    return '\n\n'.join(block(b, indent).rstrip('\n') for b in blocks) + '\n'


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
        if t not in seen:
            seen.append(t)
            css.append(t)
        for key in ('blocks', 'left'):
            if isinstance(b.get(key), list):
                css.extend(styles(b[key], seen))
    return css


def read_css(names):
    out = []
    for n in names:
        p = os.path.join(TPL, n + '.css')
        if os.path.isfile(p):
            out.append(io.open(p, encoding='utf-8').read().rstrip() + '\n\n')
    return ''.join(out)


def build(page):
    data = json.load(io.open(os.path.join(ROOT, 'content', page + '.json'), encoding='utf-8'))
    body = stack(data['blocks'])
    css = read_css(styles(data['blocks']))
    html = render(template('_page'), dict(data, body=body, css=css))
    out = os.path.join(ROOT, page + '.html')
    io.open(out, 'w', encoding='utf-8', newline='').write(html)
    return out, len(html)


if __name__ == '__main__':
    for page in (sys.argv[1:] or ['about-v2']):
        p, n = build(page)
        print('%-24s %6.1f KB' % (os.path.basename(p), n / 1024))
