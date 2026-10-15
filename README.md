Site migration toolkit
Moves a client site off Simvoly and onto GitHub + Cloudflare.

This repo is a template. Create each client's repo from it with the green Use this template button, so migrate.sh is already there when you open a Codespace.

The full step-by-step process is in Trainual: Website Migration: Simvoly → GitHub → Cloudflare. Follow that. This README is a quick reference, not the process.

The one rule
Never paste more than one line into the terminal. Multi-line pastes get mangled — the shell swallows the lines that follow and reports success while doing nothing.

Commands
Run everything from the repo root.

bash migrate.sh help
Command	What it does
domain <clientdomain.com>	Set the client domain, find the image CDN
sethost <cdn-domain.com>	Override the CDN by hand
check	Confirm both values are still set
urls	Build urls.txt from the sitemap
pages	Download every page
audit	What survives the migration — iframes, scripts, forms, tracking
localize	Download every asset and repoint the pages at local copies
standalone	The gate. Proves nothing still loads from Simvoly
verifyassets	Confirm downloads are real files, not error pages
pdfs	Download every PDF
copy	Extract readable text from each page
seo	Build redirect-map.csv
redirects	Build pages/_redirects from that CSV
homepage	Make sure the homepage is pages/index.html
config	Write wrangler.toml
status	What is done so far
Lost your place? Run bash migrate.sh status.

What ends up in here
Folder	What it is
pages/	The site Cloudflare serves. This is the deploy directory.
pages/assets/	Every image, stylesheet, script and font, self-hosted
pages-original/	Untouched copies of what Simvoly served. Never edit these.
copy/	Plain-text copy from each page, for rebuilding
audit/	What survives vs what needs rebuilding
pdfs/	Downloaded PDFs, if the site had any
redirect-map.csv	Old path → new path, plus titles and meta descriptions
.migration-env	The client domain and CDN host
🛑 Before anyone cancels Simvoly
bash migrate.sh standalone
Must say PASS. Until it does, the site still loads styling, scripts or images from Simvoly and will break the moment that account closes. There is no recovery — the CDN goes with the account.

Updating this toolkit
Commit the fix to migrate.sh here. Every client repo created from the template after that picks it up. Repos already created keep the version they started with, which is what you want — a migration in progress should not change underneath the person running it.

When you change the toolkit, check that the "You should see" samples in the Trainual course still match what the script prints.
## Live Google reviews (Log Hog)
The homepage and About page show live reviews from the Google Business Profile.
`src/index.js` (Cloudflare Worker) fetches them from the Google Places API, caches them
for 12 hours, and drops them into the `[data-lh-reviews]` sections. If Google can't be
reached or no key is set, the built-in reviews baked into the HTML are shown instead.

One-time setup:
1. Google Cloud console → enable **Places API (New)** → create an API key restricted to that API.
2. `npx wrangler secret put GOOGLE_PLACES_API_KEY` (or Cloudflare dashboard → loghog → Settings → Variables and Secrets).
3. Optional: put the Place ID in `GOOGLE_PLACE_ID` in wrangler.toml (otherwise it's looked up by name).

Change the built-in reviews: edit `scripts/build-fallback.mjs`, then run `node scripts/build-fallback.mjs`.

## Log Hog site (2026 redesign)
The site in `pages/` is generated. Don't edit the HTML by hand:
- Content, services, FAQs, service areas: `scripts/build_site.py`
- Styles: `src/site/site.css`
- Built-in fallback reviews: `src/fallback-reviews.js`

Rebuild with `python3 scripts/build_site.py`, then commit. Pushing to `main` deploys automatically.
