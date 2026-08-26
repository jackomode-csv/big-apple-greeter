# Big Apple Greeter — Site Guide for Claude

This is a hand-built static website for Big Apple Greeter, a New York City
nonprofit. The person asking for changes is usually the CLIENT, who is not
technical. Built by Jack Murray, who handles anything structural.

## How to behave with the client

- Speak plain English. No code talk, no file paths, no jargon in replies.
- Before saving anything, summarize what will change in one or two sentences
  and ask them to confirm.
- After every confirmed change, commit it with a short message describing the
  change in plain words (e.g. "Updated board member list").
- To publish: `git push` (once a remote is configured). If push fails or no
  remote exists, tell them the change is saved locally and Jack can publish it.
- If something looks broken after a change, revert to the last commit rather
  than attempting creative repairs.
- If a request requires changing layout, scripts, or video behavior, make the
  change carefully but tell them Jack should review it.

## What the client will usually edit (safe zones)

- **index.html** — "In the News" feed items (source, headline link, blurb);
  TripAdvisor pull quotes in the quote grid (quote, name, place, date);
  the headline quote and attribution above them.
- **about.html** — Mission paragraph; Story timeline rows; Board Leadership
  and Directors lists (name, role, affiliation); IGA section text.
- **support.html** — Why Give / Ways to Give / Monthly Giving rows; contact
  names, emails, phone numbers; the Lester Barnett quote section.
- **volunteers.html** — "How We Do Things" rows; Extended Family blog links;
  closing CTA text.
- **visitors.html** — FAQ entries and NYC tips.
- **register.html / volunteer-register.html** — form field labels, options,
  step copy. The `FORM_ENDPOINT` constant is where submissions POST; empty
  string = preview mode.

## Do not break (ask Jack territory)

- Hero reel mechanics on index, visitors, volunteers, support (click-to-play,
  overlay = paused state, corner controls). Support's reel stops at exactly
  15s via a rAF check. Volunteers' title fades at frames 28/325 (29.97 fps).
- The double-buffered feature loop on index (two stacked <video> elements;
  poster/autoplay are stripped after first play — this prevents flashing).
- The nav logo plays once, parks on last frame, replays on nav hover.
- The subway-themed multi-step forms (stepper, validation, review, success).
- The Leaflet map wiring (slide index ↔ CLIPS array ↔ map pins).
- The site font is Inclusive Sans on all seven pages. The old three-way preview
  switcher was removed once Jack called the decision final. Headings carry a
  half-pixel text stroke because Inclusive Sans stops at weight 700, so do not
  drop that rule. Libre Franklin still loads for one thing only: the static SVG
  wordmark that reduced-motion users see in place of the logo video.

## Conventions

- Colors come from CSS variables at the top of each page's <style>:
  `--red:#de5447` (primary), `--red-bright:#c23a2d` (hover/accents).
  Change colors by changing the variables, not individual rules.
- Every page is self-contained (own <style> and <script>). A site-wide change
  must be applied to all seven pages: index, about, visitors, volunteers,
  support, register, volunteer-register.
- Copy style: no em dashes in site copy — rewrite with sentences, commas, or
  colons. Curly quotes as HTML entities (&ldquo; &rsquo; etc.).
- Videos live in /assets. Posters are frame 1 of their video, extracted with
  ffmpeg (`-frames:v 1 -q:v 2`). If a video is replaced, regenerate its poster.
- Photos must never be original bigapplegreeter.org assets; only client-made
  composites (see HANDOFF.md for history).

## Reference docs

- HANDOFF.md — full change history of the rebuild (what exists and why).
- CLIENT-SETUP.md — the client's getting-started sheet.
