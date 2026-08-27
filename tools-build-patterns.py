# blocks.html - the pattern library.
# Every block is the real markup, lifted from the page that owns it, rendered
# against site.css + blocks.css so you can see the library actually working
# before any page is migrated onto it.
import io, os, re

SITE = r'C:\Users\Jack Murray\OneDrive\Documents\big-apple-greeter'


def page(p):
    return io.open(os.path.join(SITE, p + '.html'), encoding='utf-8').read()


def element(html, needle, tag='section', nth=0):
    """Return the balanced element whose opening tag contains `needle`.
    nth picks which occurrence, since a page may hold several."""
    i = -1
    for _ in range(nth + 1):
        i = html.find(needle, i + 1)
        if i == -1:
            return None
    start = html.rfind('<' + tag, 0, i)
    if start == -1:
        return None
    o = re.compile(r'<' + tag + r'\b', re.I)
    c = re.compile(r'</' + tag + r'>', re.I)
    depth, k = 0, start
    while k < len(html):
        mo, mc = o.search(html, k), c.search(html, k)
        if not mc:
            return None
        if mo and mo.start() < mc.start():
            depth += 1; k = mo.end()
        else:
            depth -= 1; k = mc.end()
            if depth == 0:
                return html[start:k]
    return None


BLOCKS = [
    ('Hero', 'index', 'class="hero"', 'section',
     'Four pages share this exactly. The reel, the overlay copy, the two buttons and the scroll cue.', 0),
    ('Hero, photo variant', 'about', 'class="about-hero"', 'section',
     'The only hero that differs: a column layout with white type over a photo.', 0),
    ('Feature band', 'index', 'id="feature"', 'section',
     'Media on one side, copy on the other. The landmark reel cross-fades here.', 0),
    ('News + reviews', 'index', 'class="quotes"', 'section',
     'Press feed on the left, review pull-quotes on the right.', 0),
    ('Content group', 'visitors', 'class="group"', 'div',
     'The workhorse. A heading and a list of rows. 46 uses across four pages.', 1),
    ('FAQ', 'visitors', 'class="faq"', 'div',
     'Native details/summary, so it works with no JavaScript at all.', 0),
    ('Invited band', 'volunteers', 'class="invited"', 'section', '', 0),
    ('Pull quote', 'support', 'class="story-quote"', 'section', '', 0),
    ('Tax band', 'support', 'class="tax-band"', 'section', '', 0),
    ('Photo banner', 'about', 'class="photo-banner"', 'figure', '', 0),
    ('CTA band', 'about', 'class="story-cta"', 'section',
     'Identical to .reunion-cta on the volunteers page; one block, two names kept.', 0),
    ('Form panel', 'register', 'class="panel"', 'section',
     'One step of the registration form. The kit is shared by both register pages.', 0),
]

HEAD = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="robots" content="noindex, nofollow">
<title>Block library | Big Apple Greeter</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inclusive+Sans:ital,wght@0,300..700;1,300..700&display=swap" rel="stylesheet">

<!-- The whole point: these two files, and nothing else. -->
<link rel="stylesheet" href="assets/site.css">
<link rel="stylesheet" href="assets/blocks.css">

<style>
  /* Chrome for this page only. Nothing here ships. */
  .pl-head { padding: 64px 24px 40px; max-width: 1120px; margin: 0 auto; }
  .pl-head h1 { font-size: 2.4rem; font-weight: 700; margin-bottom: .6rem; }
  .pl-head p { color: var(--ink-soft); max-width: 62ch; margin-bottom: .8rem; }
  .pl-note { background: var(--panel); border-left: 3px solid var(--red);
             padding: 16px 20px; margin-top: 24px; font-size: .92rem;
             color: var(--ink-soft); max-width: 70ch; }
  .pl-label { position: sticky; top: 84px; z-index: 900;
              background: var(--ink); color: #fff; padding: 10px 24px;
              font-size: .72rem; font-weight: 600; letter-spacing: .16em;
              text-transform: uppercase; }
  .pl-label span { color: var(--muted); text-transform: none; letter-spacing: 0;
                   font-weight: 400; margin-left: 12px; }
  .pl-block { border-bottom: 1px solid var(--line); }
  .pl-missing { padding: 40px 24px; color: var(--muted); font-style: italic; }

  /* The site fades content in on scroll: .reveal starts at opacity 0 and the
     script adds .in. No script here, so without this every block would be
     blank. Forced visible for the library only. */
  .reveal, .reveal * { opacity: 1 !important; transition: none !important; }

  /* Blocks are a full viewport tall by design, which makes twelve of them
     impossible to survey. Compact caps each one so you can scan the set;
     True size shows them as a visitor gets them. */
  .pl-bar { position: sticky; top: 0; z-index: 950; display: flex; gap: 18px;
            align-items: center; background: #fff; border-bottom: 1px solid var(--line);
            padding: 12px 24px; font-size: .8rem; }
  .pl-bar button { font: inherit; font-weight: 600; cursor: pointer; padding: 8px 16px;
                   border: 1px solid var(--line); border-radius: 999px; background: #fff;
                   color: var(--ink); }
  .pl-bar button.on { background: var(--red); border-color: var(--red); color: #fff; }
  .pl-bar nav { display: flex; gap: 2px; flex-wrap: wrap; margin-left: auto; }
  .pl-bar nav a { padding: 6px 9px; border-radius: 4px; color: var(--ink-soft); font-size: .72rem; }
  .pl-bar nav a:hover { background: var(--panel); color: var(--red); }
  /* A fixed cap, not a vh one: the blocks are viewport-tall by design, so a
     vh cap would just reproduce the problem it is meant to solve. */
  body.compact .pl-block { max-height: 520px; overflow: hidden; position: relative; }
  body.compact .pl-block::after { content: ""; position: absolute; left: 0; right: 0;
    bottom: 0; height: 90px; background: linear-gradient(to bottom, transparent, #fff); }
  body.compact .pl-label { top: 49px; }
</style>
</head>
<body>

<div class="pl-bar">
  <button id="fit" class="on" type="button">Compact</button>
  <button id="real" type="button">True size</button>
  <nav id="jump"></nav>
</div>

<div class="pl-head">
  <h1>Block library</h1>
  <p>Every block below is the real markup, lifted from the page that owns it and
     rendered against <code>assets/site.css</code> and <code>assets/blocks.css</code>.
     No page has been migrated. This is what the library looks like on its own.</p>
  <div class="pl-note">
    <strong>What is not here:</strong> JavaScript. The reels, the cross-fade, the
    interactive map, the form stepper and the scroll-reveal all sit still on this
    page, because none of their scripts are loaded. Blocks that depend on script
    show their resting state, which is the state a visitor sees before anything runs.
  </div>
</div>
"""

parts = [HEAD]
found, missing = 0, []
for title, src, needle, tag, note, nth in BLOCKS:
    html = element(page(src), needle, tag, nth)
    parts.append('<div class="pl-label">%s <span>%s.html%s</span></div>\n'
                 % (title, src, ('  &mdash;  ' + note) if note else ''))
    if html:
        parts.append('<div class="pl-block">\n%s\n</div>\n\n' % html)
        found += 1
    else:
        parts.append('<div class="pl-missing">not located in %s.html</div>\n\n' % src)
        missing.append(title)

TOGGLE = """
<script>
  // Compact by default: twelve full-height blocks are otherwise unscannable.
  document.body.classList.add('compact');
  var fit = document.getElementById('fit'), real = document.getElementById('real');
  fit.onclick  = function () { document.body.classList.add('compact');
                               fit.classList.add('on'); real.classList.remove('on'); };
  real.onclick = function () { document.body.classList.remove('compact');
                               real.classList.add('on'); fit.classList.remove('on'); };
  // Jump links built from the labels, so they cannot drift out of sync.
  var jump = document.getElementById('jump');
  document.querySelectorAll('.pl-label').forEach(function (el, i) {
    el.id = 'b' + i;
    var a = document.createElement('a');
    a.href = '#b' + i;
    a.textContent = el.firstChild.textContent.trim();
    jump.appendChild(a);
  });
</script>
</body>
</html>
"""
parts.append(TOGGLE)
io.open(os.path.join(SITE, 'blocks.html'), 'w', encoding='utf-8', newline='').write(''.join(parts))
print('blocks.html  %.1f KB   %d of %d blocks rendered'
      % (os.path.getsize(os.path.join(SITE, 'blocks.html')) / 1024, found, len(BLOCKS)))
if missing:
    print('  not located:', ', '.join(missing))
