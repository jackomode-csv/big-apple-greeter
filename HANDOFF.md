# Big Apple Greeter Rebuild — Change Log (July 21–23, 2026)

## Site-wide

- **Nav logo behavior**: the animated logo video now plays one full cycle on page load, parks on its last frame, and replays only while the mouse is over the nav bar (finishing its cycle when you leave). Reduced-motion users get the static SVG. Applied to all six pages.
- **Nav simplified**: removed every dropdown submenu (Visitors, Volunteers, About Us, Support Us) since each section is a single page now.
- **Font preview switcher**: a fixed pill on every page lets the client toggle the whole site between Libre Franklin, Inclusive Sans (loaded from Google Fonts), and Arial. Only the base font swaps; all sizing/spacing stays identical. Choice persists across pages via localStorage. Because Inclusive Sans tops out at weight 700, headings in that mode get a half-pixel text stroke to match the other fonts' 800 weight. On the two form pages the pill sits higher so it doesn't cover the test-ride chip.
- **Original-site photos purged**: every photo carried over from the real bigapplegreeter.org was removed unless replaced with our own version. Photo backgrounds (DeKalb Ave on the homepage reviews section and Support hero; High Line on the volunteers "You're invited" band) became flat dark-red gradients. Files remain in /assets, just unreferenced.

## Homepage (index.html)

- **Hero reel replaced** with `logo_reel_2.mp4` (20s, 1080p); poster regenerated from its first frame.
- **Feature loop ("Big Apple Greeter, New York Icon")**: added Bronx and Staten Island clips to the landmark rotation (now Astor Place → Unisphere → Apple of Liberty → Bronx → Staten). Both new clips were center/right-crop converted from 16:9 to the frame's 4:3 so nothing letterboxes and the apple stays in frame. Playback was rebuilt as a double-buffered two-player system: the next clip preloads invisibly and crossfades in, eliminating the poster flash between clips; fixed follow-on bugs (hidden player autoplaying and skipping clips) by stripping poster/autoplay after first play and only letting the visible player advance the reel.
- **"Meet the Greeters" carousel section removed entirely** (markup, CSS, scripts ~8.4 KB).
- **Reviews section rebuilt as News + Reviews**, split left/right:
  - Left: "In the News" feed of real outside press only — Bronx Times (Apr 2025), NYC Tourism + Conventions, amNewYork (Chinatown tourism), CityPASS. (Searched for the New Yorker piece; couldn't verify a link so it was left out pending a URL.)
  - Right: current TripAdvisor pull quotes — headline "The cream of the crop." (Jon L, July 2026) plus 8 quotes in a two-column grid, each with a gold five-star row (all are genuine 5-bubble reviews). "Read More" button now links to the actual TripAdvisor page.
- **"We'll take you there"**: after the photo purge, the carousel holds only the two QR slides (opens in wide QR mode); the map shows the One Centre Street apple pin.

## About page (about.html)

- **New hero**: the "photobomb" composite (greeters in Dumbo with the giant apple) replaced the old photo-collage background. Iterated the overlay: lightened, then reshaped so the scrim is darkest at the edges and nearly clear over the subjects; headline moved to the top (sky) — stats initially at the bottom, later removed entirely once they appeared on the Yankee scoreboards image.
- **Mission**: converted the four-row list back into one flowing paragraph, with the key phrases bolded (enhance NYC's worldwide image, enrich the New York experience, friendlier/stronger/prouder New York).
- **Layout**: Mission and Story share one left column with Lynn's photo in a sticky right column spanning both.
- **Lynn Brooks photo**: replaced with the 35th-anniversary memorial frame version; renders without the site's default shadow (the artwork has its own), enlarged via a wider photo column plus a 116% desktop bleed; caption removed.
- **Yankee Stadium photo**: moved from the side column to a full-width banner under the Story; crop fixed to 16:9 anchored top so the jumbotron stays visible. The blurry 800px original was AI-upscaled 4x (Real-ESRGAN, NMKD-Superscale model chosen after comparing three models), then superseded by the custom composite with Big Apple Greeter stats on the scoreboards (delivered as an optimized 1800px JPG). Fixed the sticky Lynn frame colliding with the banner (removed negative margin, added bottom buffer).

## Volunteers page (volunteers.html)

- **Hero is now a reel**: `volunteer.mp4` (with audio) replaced the static artwork. No autoplay — click-to-play in the visitors-page style: the pitch overlay is the paused state, "Meet the Family" is the play button (outlined, play triangle), corner sound/pause controls, frame 1 as poster.
- **Frame-timed text**: "You're already one of us." became real HTML (was baked into the artwork), positioned to match the visitors poster title (left edge 7%, top 39% of the frame). During playback the tagline + buttons hide immediately and return when the video ends; the title stays until frame 28, fades out, and returns at frame 325 (29.97 fps). Video later updated to a newer cut (14.35s) with poster regenerated.
- **"Pull Up a Chair" now stays on-site**: links to the new volunteer application instead of bigapplegreeters.net.

## New page: volunteer-register.html

- Full port of the visitor form's subway treatment: 5-stop stepper (Contact → Background → Reference → Interests → Finish) with the apple riding the line, enamel station signs, chip buttons, "Stand clear of the closing doors" validation, review summary, and the tiled success wall ("Welcome To The Family").
- Fields mirror the real volunteer application: contact + address + phones, work status, experience and motivation essays, reference contact, 24 interest checkboxes.
- `FORM_ENDPOINT` config constant (preview mode logs the JSON payload); test-ride chip fills sample data.

## Support page (support.html)

- **Hero stats removed** (150,000+ / $0 / 100% / 501(c)(3)).
- **New closing feature**: the Lester Barnett story (the couple toasting across New York) sits at the bottom as a centered quote section, "Why We Greet · Lester Barnett", with the final line ("That's why I'm a Greeter…") set large and bold.

## Tooling installed along the way

- **Real-ESRGAN AI upscaler** permanently installed at `~/.claude/tools/real-esrgan/` with four models (NMKD-Superscale and Nomos8kSC for photos; x4plus; anime for flat art).
- **`upscale-image` skill** registered at `~/.claude/skills/` so any future session can upscale images on request with the right model and workflow.
