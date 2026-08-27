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
| `group` | the workhorse. Heading, optional date stamp or link, then either a prose paragraph or a definition list. Optionally two-column |
| `sections-with-photo` | a run of sections with a photo beside them. The sections inside are ordinary `group`s |
| `photo-banner` | full-width image with a caption |
| `cta` | closing call to action with buttons |

**There are no layout containers in the content model.** A page is a flat list
of things a person can name. The centred column that holds the middle of a page
is applied by the renderer: block types listed in `FULL_BLEED` span the window,
and any run of the rest is wrapped in `.wide`. Nobody editing the site has to
know that div exists.

`sections-with-photo` is the one block that holds others, and it holds them
because that is what it *is* — two sections and the photo that sits beside them.
The sections inside render through the ordinary `group` template, so a section
beside a photo and a section on its own are described the same way.

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
| volunteers | header, footer, group, sections-with-photo, cta | fam-hero, invited |
| support | header, footer, group, cta | sup-hero, story-quote, tax-band |
| visitors | header, footer, group | hub-hero, tabs, faq |
| index | header, footer | hero (video), feature, clips, quotes |
| register, volunteer-register | header, footer | form-shell |

Roughly eleven more block types covers the site.

`reunion-cta` on the volunteers page is byte-identical to `story-cta`, so it is
the same block under a second name.

---

## How someone edits the site

Three levels, in increasing order of effort.

### 1. Edit the JSON (works today, no infrastructure)

Open `content/about-v2.json`, change the text, run:

```
python tools-render.py about-v2
```

Reordering the page is moving an entry in the `blocks` list. Adding a board
member is appending to `rows.items`. Changing a headline is changing a string.
No HTML involved.

This is a developer workflow, not a client one, but it is the thing everything
else is built on: the CMS below writes this same file.

### 2. Sveltia CMS at /admin (the realistic client answer)

`admin/config.yml` is written and ready. Sveltia gives a login screen, a form
per block, and drag handles to reorder blocks. Clicking Publish commits the
JSON back to GitHub; the workflow in `.github/workflows/build.yml` re-renders
and deploys.

The reason this fits so neatly is a coincidence worth stating: Sveltia's
variable-type list widget stores which block an item is in a key called `type`,
and lists its options under `types`. That is the exact shape
`content/about-v2.json` already has. The content model was not designed for the
CMS; it is just what a block model looks like from both ends.

Sveltia rather than Decap because Decap is barely maintained now. The config
format is the same, so switching later costs nothing.

**Still needed before this works:**

- Somewhere to host the site. It is not hosted anywhere at the moment.
- An OAuth relay so the browser can log in to GitHub. `sveltia-cms-auth` as a
  Cloudflare Worker, free, about ten minutes.
- The video moved to R2. `assets/*.mp4` is gitignored, so any deploy today
  ships a site with 13 dead reels.

Every block type on the About page has an entry in `admin/config.yml`, so
nothing on that page is uneditable.

**What this gives them:** reorder blocks, edit any text, swap images, add and
remove sections, add rows to a list.

**What it does not give them:** free-form drag-anywhere layout. They cannot
drag a text box to arbitrary coordinates the way Squarespace allows. That is a
feature. It is what stops the site being wrecked by accident, and it is why the
pages will still look designed in two years.

### 3. In-page visual editing

A `?edit=1` mode on the real page: click text to edit it where it sits, drag
block handles to reorder, an add-block panel down one side. Saves back through
the same JSON.

This is buildable now specifically because the block model exists - the editor
manipulates the block list and re-renders with a JavaScript port of the same
forty-line template function. It is still a page builder, though, and page
builders are weeks of work rather than days. Worth doing only if level 2 turns
out not to be enough.

---

## The constraint

JavaScript. Per page: index 18.9 KB, register 21.3 KB, volunteer-register
11.2 KB, visitors 5.6 KB, support 4.7 KB, volunteers 4.2 KB, about 1.7 KB.
It selects on specific classes — `.rev-carousel`, `.tabs`, `.stepper`,
`.map-col`, `.field[data-required]`.

That splits the blocks in two:

- **Content blocks** — `group`, `sections-with-photo`, `photo-banner`, `cta`,
  `hero-photo`.
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
