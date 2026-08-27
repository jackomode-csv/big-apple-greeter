# The block system

The site is being converted from seven hand-written HTML files into pages that
are **data plus templates**. This document describes how that works and how far
it has got.

Nothing in here changes what a visitor sees. The first page converted,
`about-v2.html`, produces a DOM identical to the hand-written `about.html`,
node for node.

---

## The three pieces

```
content/<page>.json     the page as data: an ordered list of blocks
blocks/<type>.html      one template per block type
blocks/<type>.css       that block's styles, so it travels self-contained
tools-render.py         turns the JSON back into HTML
```

Run it:

```
python tools-render.py about-v2
```

That reads `content/about-v2.json`, renders each block through its template,
concatenates the CSS for the block types the page actually uses, and writes
`about-v2.html`.

### The page as data

A page is a list. Each entry names a block type and carries the text, images
and links that go in it:

```json
{
  "type": "cta",
  "note": "CLOSING CTA",
  "heading": "Thirty-five years in, the door&rsquo;s still open.",
  "body": "Visit with a New Yorker who loves this city, or become the New Yorker someone remembers forever.",
  "buttons": [
    { "href": "register.html", "label": "Request a Greeter" },
    { "href": "volunteers.html", "label": "Become a Greeter", "outline": true }
  ]
}
```

Reordering the page means reordering that list. Editing the copy means editing
those strings. Neither requires touching HTML, which is the whole point.

`note` doubles as the block's label: it is emitted as the signpost comment in
the generated HTML, and it is what an editing UI would show in a sidebar.

### The templates

Mustache-shaped and deliberately small. Four constructs, no more:

| | |
|---|---|
| `{{key}}` | insert the value |
| `{{a.b}}` | dotted lookup |
| `{{#key}}…{{/key}}` | list → repeat per item; truthy → render once; absent → skip |
| `{{^key}}…{{/key}}` | render only when absent or empty |

Values are inserted **raw, not escaped**. The copy on this site uses `<b>` for
emphasis and named entities such as `&rsquo;` throughout, and escaping would
mangle both. That is a real trade-off: anything written into these fields is
HTML, so an editing layer has to sanitise on save rather than on render.

### The blocks so far

Extracted from `about.html`, verbatim:

| block | what it is |
|---|---|
| `header` | site chrome. The nav is a loop, so adding a page is one line of JSON |
| `footer` | site chrome. The three link columns are a loop |
| `hero-photo` | full-height hero, white type over a photo |
| `split` | two columns: content on the left, a photo column on the right |
| `group` | the workhorse. Heading, optional date stamp or link, then either a prose paragraph or a definition list. Optionally two-column |
| `photo-banner` | full-width image with a caption |
| `cta` | closing call to action with buttons |
| `wide` | the max-width container that holds the middle of a page |

`split` and `wide` are containers: they hold other blocks and nest to any depth.

---

## Why this is separate from `assets/blocks.css`

`assets/blocks.css` is the union of all seven pages' block rules. It cannot be
linked by any single page, because attaching it imports styling that page never
had — measured at 24,603 differing pixels on `support.html`.

`blocks/<type>.css` is the fix. Each block owns its rules, the renderer emits
only the ones a page uses, and a page that has no `.photo-banner` never
receives `.photo-banner` styling.

`assets/site.css` is unaffected and still linked by all seven pages. It holds
the tokens, reset, header, footer and buttons that genuinely are universal.

---

## Status

Converted: **about** (as `about-v2.html`; the original `about.html` is
untouched).

Still hand-written: index, visitors, volunteers, support, register,
volunteer-register.

What the remaining pages would need, given the blocks that already exist:

| page | already covered | still to build |
|---|---|---|
| volunteers | header, footer, group, split, wide, cta | fam-hero, invited |
| support | header, footer, group, cta, wide | sup-hero, story-quote, tax-band |
| visitors | header, footer, group, wide | hub-hero, tabs, faq |
| index | header, footer | hero (video), feature, clips, quotes |
| register, volunteer-register | header, footer | form-shell |

Roughly eleven more block types covers the site.

`reunion-cta` on the volunteers page is byte-identical to `story-cta`, so it is
the same block under a second name.

---

## The constraint

JavaScript. Per page: index 18.9 KB, register 21.3 KB, volunteer-register
11.2 KB, visitors 5.6 KB, support 4.7 KB, volunteers 4.2 KB, about 1.7 KB.
It selects on specific classes — `.rev-carousel`, `.tabs`, `.stepper`,
`.map-col`, `.field[data-required]`.

That splits the blocks in two:

- **Content blocks** — `group`, `split`, `photo-banner`, `cta`, `hero-photo`.
  Reorder, duplicate, delete and retype freely.
- **Behavioural blocks** — the hero reel, the review carousel, the map, the
  tabs, the FAQ, the two form shells. Their script has to travel with them, and
  they cannot be recombined arbitrarily.

The two registration forms are realistically one large custom block each rather
than a stack of editable ones. They should stay hand-maintained.

Separately, and worth knowing: **the pages are invisible without JavaScript.**
`.reveal` starts at `opacity: 0` and the only rule that forces it visible sits
inside a `prefers-reduced-motion` query. Nothing about the block system changes
that, but it is a real accessibility and SEO problem that predates it.

---

## How this was verified

Two independent checks, because the risky part of a rewrite like this is what
you did not think to look at.

**DOM equivalence.** Both files parsed to a flat list of tags, attributes, text
and entities, then compared. 629 nodes each, identical. Comments and whitespace
are excluded, because neither renders.

**Pixel diff.** Both pages screenshotted headless at 390, 768, 1440 and 1920.
The harness proves itself first by shooting the *unchanged* page twice; a run
where the control is not clean tells you nothing about the change.

Result, with the header strip excluded for the reason given below:

| width | about.html vs about-v2.html |
|---|---|
| 390 | 0 px |
| 768 | 0 px |
| 1440 | 0 px |
| 1920 | 0 px |

Not "0 px after thresholding" — the difference image has no bounding box at
all, meaning no pixel anywhere outside the header differs by even one level.

The generated file differs from the hand-written one in exactly two
non-rendering ways: one blank line after `<body>`, and four `<li>` lines
re-indented from ten spaces to eight. The original was inconsistent there — the
History group used ten, every other group used eight. The renderer normalises.

**A note on the 67-pixel logo artifact.** Earlier in this project a 67-pixel
difference in the header logo was recorded on two pages and attributed to the
extra stylesheet request. That was wrong.

Measured properly: `about.html` shot against *itself*, five pairs at each of
the four widths.

| width | pairs of identical file | non-zero |
|---|---|---|
| 390 | 0 0 0 0 0 | 0 of 5 |
| 768 | 67 0 0 67 0 | 2 of 5 |
| 1440 | 0 67 67 0 0 | 2 of 5 |
| 1920 | 0 0 0 0 0 | 0 of 5 |

Four of twenty pairs of the *same unchanged file* differ, always by exactly
67 pixels, always in a 32x18 box on the header logo, max channel delta 16 of
255. It is nondeterministic rasterisation, not a consequence of any change.

Two consequences. Diffs inside the top 100px are noise until proven otherwise,
so the header strip is masked. And a single clean run proves nothing either
way at 768 or 1440 - the control has to be run alongside.
