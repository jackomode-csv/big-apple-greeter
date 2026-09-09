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
blocks/<type>.js        that block's behaviour, for the blocks that have any
tools-render.py         turns the JSON back into HTML
```

`blocks/<type>.js` is optional and most blocks have none. Where it exists the
renderer emits it, wrapped in one `<script>`, after the scripts every page
shares — so a behavioural block travels complete, markup, styling and player
together. `fam-hero` is the first block to use it.

Two blocks reuse another's classes rather than restating them: `link-group` and
`split-group` are groups with a different row shape or an extra wrapper, and
both lean on `.group`, `.group-head` and `.rows`. `DEPENDS` in the renderer
records that, so a page using one without a plain `group` still gets those
rules.

Video is not served from the repo. `assets/*.mp4` and the delivery encodes in
`assets/_web/` are gitignored, and the renderer rewrites `assets/<clip>.mp4`
to point at the R2 bucket when an asset base is set:

```
python tools-render.py volunteers-v2                     # assets/volunteer.mp4
python tools-render.py --base https://<host> volunteers-v2
```

`--base` wins, then `BAG_ASSET_BASE`, then `asset_base` in the content file,
then relative paths. The rewrite is narrow on purpose: it moves `.mp4` and
nothing else, because the images under `assets/` are committed and stay put.

Set `asset_base` in the content file rather than as a CI variable. The deploy
workflow fails when rendered output disagrees with committed HTML, so what is
committed and what is deployed have to render the same way.

The scroll-fade selectors are page data (`hero_reveal`, `block_reveal`) rather
than constants in `_page.html`, because they name each page's own hero parts:
About cascades `.page-head` items, volunteers cascades `.hero-title` and the
pitch.

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

Extracted from `volunteers.html`, verbatim:

| block | what it is |
|---|---|
| `fam-hero` | full-screen video hero: pitch overlay, corner play/mute controls. The first behavioural block — its player travels with it in `blocks/fam-hero.js` |
| `split-group` | a `group` whose rows sit in the `.split` grid |
| `link-group` | a `group` whose rows are whole-row links: heading, date stamp, blurb, "Read →" |
| `invited` | full-bleed statement band on a dark gradient |
| `reunion-cta` | closing call to action: one button and a contact line |

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

### A landmine in `_base.css`

`blocks/_base.css` is not a CSS file. Lines 4-7 are the tail of an HTML
comment, a `<link>` and a `<style>` opening tag:

```
, so
     page-specific rules still win, exactly as before. -->
<link rel="stylesheet" href="assets/site.css">
<style>
```

The extraction sliced `about.html` at the wrong boundary. It works, and the
output is genuinely correct, because `_page.html` opens `<!--` on line 12,
`_base.css` closes it and opens `<style>`, and line 13 closes `</style>`. But
the head is assembled by a CSS file smuggling HTML through the renderer, and
the `/* _base.css */` header the extractor prepended is sitting inside that
HTML comment rather than inside the stylesheet.

Repairing it means moving the comment, link and `<style>` into `_page.html` and
making `_base.css` pure CSS — a small change, but one that moves the
`/* _base.css */` header from an ignored HTML comment into `<style>`, where the
DOM check compares it. Do it on its own, against its own before-and-after, not
folded into a page conversion.

---

## Status

Converted: **about** (as `about-v2.html`) and **volunteers** (as
`volunteers-v2.html`). Both originals are untouched.

Still hand-written: index, visitors, support, register, volunteer-register.

What the remaining pages would need, given the blocks that already exist:

| page | already covered | still to build |
|---|---|---|
| support | header, footer, group, cta | sup-hero, story-quote, tax-band |
| visitors | header, footer, group, link-group | hub-hero, tabs, faq |
| index | header, footer | hero (video), feature, clips, quotes |
| register, volunteer-register | header, footer | form-shell |

Roughly nine more block types covers the site.

**Correction.** An earlier version of this document said `reunion-cta` was
"byte-identical to `story-cta`, so it is the same block under a second name."
It is not. The two share three rules — the container, its `h2` and its `p` —
and diverge after that: `story-cta` has `.cta-row`, `.btn` and `.btn-outline`;
`reunion-cta` has none of those and adds three `.contact` rules. The markup
differs to match. Folding them together would have shipped `.reunion-cta` rules
to the About page, which is the contamination `blocks/<type>.css` exists to
prevent, so they are two blocks.

The same document undercounted what volunteers needed: not two new blocks but
five, plus a way for a block to carry its own script.

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

### volunteers

Same two checks, same result.

**DOM equivalence.** 459 nodes each, identical. `<style>` and `<script>` text
is compared separately, because extraction deliberately reorders the CSS and
re-comments it.

| width | volunteers.html vs volunteers-v2.html | control |
|---|---|---|
| 390 | 0 px | 0 px |
| 768 | 0 px | 0 px |
| 1440 | 0 px | 0 px |
| 1920 | 0 px | 0 px |

Screenshots are taken with `reduced_motion: reduce`, which pins `.reveal` at
opacity 1. Without it the scroll fade can be caught mid-transition and the
comparison becomes a coin flip — a different nondeterminism from the logo one
below, and one that affects the whole page rather than a 32x18 box.

**Three CSS differences, none of which render.** Worth stating because a clean
pixel diff cannot see a `:hover` rule or an unexercised media query.

- `@media (max-width:560px) .page-head{padding:56px 24px 0}` is **dropped**.
  `.page-head` belongs to `hero-photo`, About's hero; volunteers uses
  `fam-hero` and has no such element. The rule was dead in the original.
- `.group` **gains** `scroll-margin-top:110px`, from the shared `group.css`.
  This is the one real conflict between the two pages' group rules. It changes
  no layout, but it does change where `#how` and `#family` land when followed —
  110px lower, clearing the sticky header. On a page whose own hero links to
  `#how`, that is a fix, but it is a behaviour change and not a silent one.
- Nine `group.css` rules arrive **unused**: `.mission-copy`, `.rows.two-col`,
  `.group-head .asof`, `.rows .role` and their companions. They are About-page
  group variants. Block-level CSS granularity means a page that uses `group`
  gets every variant of `group`; splitting them further would mean splitting
  the block. None of the nine match anything in volunteers' markup.

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
