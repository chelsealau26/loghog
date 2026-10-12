#!/usr/bin/env bash
# OptSpot site migration toolkit
# Usage:  bash migrate.sh <command>
# Run "bash migrate.sh help" for the list.

set -uo pipefail

DQ='"'
SQ="'"
ENVFILE=".migration-env"
DEADFILE="dead-urls.txt"

# Which Cloudflare product a new site deploys to when nobody says otherwise.
# Pages, because the account is at its Workers limit. Existing Worker sites
# keep working - run "bash migrate.sh config workers" for those.
DEFAULT_TARGET="pages"

# Simvoly serves from more than one root domain, and ASSETHOST only ever
# holds the one the homepage happened to use most. Confirmed by loading
# simvoly.com itself, which pulls from both:
#
#   content.app-sources.com        images and uploads
#   static.web-repository.com      platform.client.min.js, hit.js
#   content.web-repository.com     more uploads
#
# Both roots die when the client's account closes. Deriving the list from
# ASSETHOST alone let a live Simvoly dependency reach PASS - see the note
# in cmd_standalone.
SIMVOLY_ROOTS="app-sources.com,web-repository.com"

# ---------------------------------------------------------------- helpers ---

say()  { printf '%s\n' "$*"; }
head2() { printf '\n=== %s ===\n' "$*"; }
die()  { printf '\nSTOP: %s\n' "$*" >&2; exit 1; }

load_env() {
  [ -f "$ENVFILE" ] || die "$ENVFILE not found. Run: bash migrate.sh domain <clientdomain.com>"
  # shellcheck disable=SC1090
  source "$ENVFILE"
  [ -n "${SITE:-}" ]      || die "SITE is blank. Re-run the domain command."
  [ -n "${ASSETHOST:-}" ] || die "ASSETHOST is blank. Re-run the domain command."
}

save_env() {
  printf 'export SITE="%s"\nexport ASSETHOST="%s"\nexport TARGET="%s"\n' \
    "$SITE" "$ASSETHOST" "${TARGET:-$DEFAULT_TARGET}" > "$ENVFILE"
}

# Remember which Cloudflare product this site deploys to, without disturbing
# SITE or ASSETHOST. Does nothing if the domain command has not run yet.
save_target() {
  [ -f "$ENVFILE" ] || return 0
  # shellcheck disable=SC1090
  source "$ENVFILE"
  TARGET="$1"
  save_env
}

# What the saved target is, or the default if nothing is saved.
current_target() {
  if [ -f "$ENVFILE" ]; then
    # shellcheck disable=SC1090
    source "$ENVFILE"
  fi
  printf '%s' "${TARGET:-$DEFAULT_TARGET}"
}

# Accept the ways people actually type it.
normalize_target() {
  case "$(printf '%s' "${1:-}" | tr '[:upper:]' '[:lower:]')" in
    pages|page|cfpages|cloudflare-pages) printf 'pages' ;;
    worker|workers|cfworkers|cloudflare-workers) printf 'workers' ;;
    *) printf '' ;;
  esac
}

need_pages() {
  [ -d pages ] || die "No pages/ folder. Run: bash migrate.sh pages"
  local n
  n=$(find pages -name '*.html' | wc -l)
  [ "$n" -gt 0 ] || die "pages/ is empty. Run: bash migrate.sh pages"
}

# Turn a URL into the flat filename used everywhere in this toolkit.
url_to_name() {
  local path
  path=$(printf '%s' "$1" | sed -E 's|https?://[^/]+||; s|[?#].*$||; s|^/+||; s|/+$||')
  [ -z "$path" ] && path="index"
  printf '%s' "$path" | tr '/' '-'
}

# ---------------------------------------------------------------- domain ----

cmd_domain() {
  local site="${1:-}"
  [ -n "$site" ] || die "Give me the domain. Example: bash migrate.sh domain halowash.com"
  site=$(printf '%s' "$site" | sed -E 's|^https?://||; s|/.*$||')
  SITE="$site"

  head2 "Checking $SITE is reachable"
  local code
  code=$(curl -s -o /tmp/_home.html -L --compressed -w '%{http_code}' \
    -A "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36" \
    "https://$SITE/")
  say "HTTP $code"
  [ "$code" = "200" ] || die "Site did not return 200. Check the domain spelling and try again."
  grep -qi '<html' /tmp/_home.html || die "Response was not HTML. Check the domain."

  head2 "Finding the asset host"
  grep -ohE 'https?://[a-zA-Z0-9.-]+' /tmp/_home.html \
    | sed 's|https\?://||' \
    | grep -v "^$SITE$" \
    | grep -viE 'google|facebook|instagram|youtube|vimeo|twitter|linkedin|gstatic|schema\.org|w3\.org|gravatar|cloudflare' \
    | sort | uniq -c | sort -rn | head -8 > /tmp/_hosts.txt
  cat /tmp/_hosts.txt

  ASSETHOST=$(awk 'NR==1{print $2}' /tmp/_hosts.txt)
  if [ -z "${ASSETHOST:-}" ]; then
    die "Could not find an asset host. Set it by hand:
  bash migrate.sh sethost the-real-domain.com"
  fi

  save_env
  head2 "Saved"
  say "SITE:      $SITE"
  say "ASSETHOST: $ASSETHOST"
  say ""
  say "If ASSETHOST above is not the client's image CDN, pick the right one"
  say "from the list and run:  bash migrate.sh sethost <that-domain>"
  say ""
  say "You do not need to set a second host by hand. localize and standalone"
  say "already know every Simvoly root domain:"
  say "  $SIMVOLY_ROOTS"
}

cmd_sethost() {
  local host="${1:-}"
  [ -n "$host" ] || die "Give me the host. Example: bash migrate.sh sethost content.app-sources.com"
  [ -f "$ENVFILE" ] || die "Run the domain command first."
  # shellcheck disable=SC1090
  source "$ENVFILE"
  ASSETHOST=$(printf '%s' "$host" | sed -E 's|^https?://||; s|/.*$||')
  save_env
  say "SITE:      $SITE"
  say "ASSETHOST: $ASSETHOST"
}

cmd_check() {
  [ -f "$ENVFILE" ] || die "$ENVFILE not found. Run the domain command."
  # shellcheck disable=SC1090
  source "$ENVFILE"
  local bad=0
  [ -n "${SITE:-}" ]       || { say "BAD: SITE is blank"; bad=1; }
  [ -n "${ASSETHOST:-}" ]  || { say "BAD: ASSETHOST is blank"; bad=1; }
  [ "${ASSETHOST:-}" != "${SITE:-}" ] || { say "BAD: ASSETHOST matches SITE"; bad=1; }
  case "${ASSETHOST:-}" in *.*) ;; *) say "BAD: ASSETHOST is not a domain"; bad=1 ;; esac
  [ "$bad" -eq 0 ] || die "Re-run: bash migrate.sh domain <clientdomain.com>"
  say "OK  SITE: $SITE  |  ASSETHOST: $ASSETHOST  |  DEPLOY TO: ${TARGET:-$DEFAULT_TARGET}"
  say "    Simvoly roots watched: $SIMVOLY_ROOTS"
}

# ------------------------------------------------------------------ urls ----

cmd_urls() {
  load_env
  head2 "Reading the sitemap"
  : > /tmp/_urls.raw

  for sm in "sitemap.xml" "sitemap_index.xml" "sitemap-index.xml"; do
    curl -s -L --compressed "https://$SITE/$sm" -o /tmp/_sm.xml || true
    if grep -q '<loc>' /tmp/_sm.xml 2>/dev/null; then
      say "Found $sm"
      if grep -qi '<sitemapindex' /tmp/_sm.xml; then
        say "It is an index. Fetching the child sitemaps."
        grep -oE '<loc>[^<]+' /tmp/_sm.xml | sed 's/<loc>//' | while read -r child; do
          say "  $child"
          curl -s -L --compressed "$child" | grep -oE '<loc>[^<]+' | sed 's/<loc>//' >> /tmp/_urls.raw
          sleep 1
        done
      else
        grep -oE '<loc>[^<]+' /tmp/_sm.xml | sed 's/<loc>//' >> /tmp/_urls.raw
      fi
      break
    fi
  done

  sort -u /tmp/_urls.raw | grep -E "^https?://" > urls.txt || true
  local n
  n=$(wc -l < urls.txt)
  if [ "$n" -eq 0 ]; then
    rm -f urls.txt
    die "No sitemap found. Build urls.txt by hand:
  1. Open the live site and click through every nav menu, dropdown and footer link.
  2. In the Explorer panel, create a file called urls.txt
  3. Put one full URL per line, starting with https://
  4. Save, then run: bash migrate.sh pages"
  fi
  say ""
  say "Found $n pages:"
  cat urls.txt
}

# ----------------------------------------------------------------- pages ----

cmd_pages() {
  load_env
  [ -f urls.txt ] || die "No urls.txt. Run: bash migrate.sh urls"
  mkdir -p pages
  local total ok bad n name code
  total=$(grep -c . urls.txt)
  ok=0; bad=0; n=0
  head2 "Downloading $total pages (about 1 per second)"
  while read -r url || [ -n "$url" ]; do
    [ -z "$url" ] && continue
    n=$((n + 1))
    name=$(url_to_name "$url")
    code=$(curl -s -L --compressed -w '%{http_code}' \
      -A "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36" \
      "$url" -o "pages/$name.html")
    if [ "$code" = "200" ]; then
      printf '%4d/%d  OK   %s.html\n' "$n" "$total" "$name"; ok=$((ok + 1))
    else
      printf '%4d/%d  %s  FAILED  %s\n' "$n" "$total" "$code" "$url"; bad=$((bad + 1))
      rm -f "pages/$name.html"
    fi
    sleep 1
  done < urls.txt

  head2 "Result"
  say "Downloaded: $ok    Failed: $bad"

  head2 "Checking every file is real HTML"
  local notHtml=0
  for f in pages/*.html; do
    grep -qi '<html\|<!doctype' "$f" || { say "NOT HTML: $f"; notHtml=$((notHtml + 1)); }
  done
  [ "$notHtml" -eq 0 ] && say "All files are HTML."

  head2 "Smallest files (check these for error pages)"
  ls -lhS pages/ | tail -5

  [ "$bad" -eq 0 ] || say "
$bad pages failed. Fix the URLs in urls.txt and run this command again."
}

# ----------------------------------------------------------------- audit ----

cmd_audit() {
  load_env; need_pages
  mkdir -p audit
  local SKIP="$SITE|$ASSETHOST"

  grep -ohE "<iframe[^>]+src=[$DQ$SQ][^$DQ$SQ]+[$DQ$SQ]" pages/*.html | sort -u > audit/iframes.txt || true
  grep -ohE "<script[^>]+src=[$DQ$SQ]https?://[^$DQ$SQ]+[$DQ$SQ]" pages/*.html | sort -u | grep -vE "$SKIP" > audit/scripts.txt || true
  grep -ohE "<form[^>]*action=[$DQ$SQ][^$DQ$SQ]*[$DQ$SQ]" pages/*.html | sort -u > audit/forms.txt || true
  grep -ohE "href=[$DQ$SQ]https?://[^$DQ$SQ]+[$DQ$SQ]" pages/*.html | grep -vE "$SKIP" | sort -u > audit/external-links.txt || true
  grep -ohE 'GTM-[A-Z0-9]+|G-[A-Z0-9]+|UA-[0-9-]+|AW-[0-9]+' pages/*.html | sort -u > audit/tracking.txt || true

  for f in iframes scripts forms external-links tracking; do
    head2 "$f  ($(wc -l < "audit/$f.txt"))"
    cat "audit/$f.txt"
  done

  head2 "Next"
  say "Write a verdict for every interactive feature: survives / rebuild / drop."
  say "That list is your real scope of work."
  say ""
  say "This audit does not cover popups. Simvoly popups need a real browser"
  say "to find reliably. Run: bash migrate.sh popups"
}

# -------------------------------------------------------------- localize ----

cmd_localize() {
  load_env; need_pages
  cat > /tmp/_localize.py <<'LOCALIZEEOF'
"""Download every external asset a page needs and rewrite the references to local paths.

Run through migrate.sh, not directly.
"""
import os
import re
import sys
import json
import shutil
import hashlib
import posixpath
from urllib.parse import urljoin, urlsplit, unquote
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

SITE = os.environ.get("SITE", "")
ASSETHOST = os.environ.get("ASSETHOST", "")

# Every root domain Simvoly serves from, not just the one saved as ASSETHOST.
SIMVOLY_ROOTS = [
    r.strip().lower()
    for r in os.environ.get("SIMVOLY_ROOTS", "").split(",")
    if r.strip()
]

PAGES = "pages"
ORIGINAL = "pages-original"
# Captured popup markup gets the same treatment as a page: a pristine copy
# kept aside, assets downloaded, Simvoly URLs rewritten. That is what makes
# a popup liftable instead of rebuildable.
POPUPS = "popups"
POPUPS_ORIG = "popups-original"
ASSETDIR = os.path.join(PAGES, "assets")
PUBLIC_PREFIX = "/assets/"

# Remembers which URL became which filename, so running localize twice does not
# save a second hash-suffixed copy of every asset. Kept at the repo root on
# purpose - anything inside pages/ gets deployed to Cloudflare.
MANIFEST = ".asset-map.json"

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")

# Live services that must keep working from their own servers.
# These do not die when the Simvoly account closes.
KEEP_REMOTE = (
    "googletagmanager.com", "google-analytics.com", "analytics.google.com",
    "googleadservices.com", "googlesyndication.com", "doubleclick.net",
    "google.com/recaptcha", "recaptcha.net", "hcaptcha.com",
    "maps.googleapis.com", "maps.gstatic.com",
    "connect.facebook.net", "facebook.com", "facebook.net",
    "youtube.com", "youtu.be", "youtube-nocookie.com", "vimeo.com",
    "js.stripe.com", "checkout.stripe.com",
    "fonts.googleapis.com", "fonts.gstatic.com",
)

STATIC_EXT = {
    ".css", ".js", ".mjs",
    ".jpg", ".jpeg", ".png", ".gif", ".webp", ".avif", ".svg", ".ico", ".bmp",
    ".woff", ".woff2", ".ttf", ".eot", ".otf",
    ".mp4", ".webm", ".ogg", ".mp3", ".wav",
}

URL_RE = re.compile(r"""(?:https?:)?//[^\s"'()<>\\]+""")
CSS_URL_RE = re.compile(r"""url\(\s*(['"]?)([^'")]+)\1\s*\)""", re.I)
CSS_IMPORT_RE = re.compile(r"""@import\s+(?:url\(\s*)?(['"])([^'"]+)\1""", re.I)

downloaded = {}   # absolute url -> local filename
failed = {}       # absolute url -> reason
used_names = set()


def norm(url):
    """Make a protocol-relative URL absolute."""
    if url.startswith("//"):
        return "https:" + url
    return url


def key_of(url):
    """One key per resource, so http:// and https:// do not download twice."""
    return norm(url).split("://", 1)[-1]


def host_of(url):
    return urlsplit(norm(url)).netloc.lower()


def root_of(host):
    """app-sources.com out of content.app-sources.com."""
    parts = host.split(".")
    return ".".join(parts[-2:]) if len(parts) >= 2 else host


def is_simvoly_host(host):
    """Does this host die when the client's Simvoly account closes?

    ASSETHOST is whichever host the homepage referenced most, so it names
    one Simvoly domain and misses the others. SIMVOLY_ROOTS carries the
    full list.
    """
    host = (host or "").lower()
    if not host:
        return False
    if ASSETHOST:
        ah = ASSETHOST.lower()
        ah_root = root_of(ah)
        if host == ah or (ah_root and (host == ah_root or host.endswith("." + ah_root))):
            return True
    return any(host == r or host.endswith("." + r) for r in SIMVOLY_ROOTS)


def keep_remote(url):
    low = norm(url).lower()
    return any(k in low for k in KEEP_REMOTE)


def ext_of(url):
    path = urlsplit(norm(url)).path
    return posixpath.splitext(path)[1].lower()


def wanted(url):
    """Should this URL become a local file?"""
    if keep_remote(url):
        return False
    host = host_of(url)
    if not host:
        return False
    split = urlsplit(norm(url))
    if split.path in ("", "/") and not split.query:
        return False  # a bare host is a preconnect hint, not a file
    if SITE and host in (SITE, "www." + SITE):
        return False
    # Anything on a Simvoly host comes local, extension or not. Their upload
    # URLs often have no file extension, which the STATIC_EXT check below
    # would skip - and a skipped Simvoly file is a site that breaks at
    # cancellation.
    if is_simvoly_host(host):
        return True
    return ext_of(url) in STATIC_EXT


def local_name(url):
    """A stable, unique, safe filename for this URL."""
    if key_of(url) in downloaded:
        return downloaded[key_of(url)]
    split = urlsplit(norm(url))
    base = posixpath.basename(unquote(split.path)) or "file"
    base = re.sub(r"[^A-Za-z0-9._-]", "_", base)
    stem, ext = posixpath.splitext(base)
    if not ext:
        ext = ".bin"
    stem = stem[:60] or "file"
    name = stem + ext
    if name in used_names:
        digest = hashlib.sha1(url.encode()).hexdigest()[:8]
        name = f"{stem}-{digest}{ext}"
    used_names.add(name)
    return name


def fetch_once(url):
    req = Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    with urlopen(req, timeout=30) as resp:
        return resp.read()


def fetch(url):
    """Try the URL as given. If https fails, fall back to http, and vice versa."""
    url = norm(url)
    try:
        return fetch_once(url)
    except Exception:
        if url.startswith("https://"):
            return fetch_once("http://" + url[8:])
        if url.startswith("http://"):
            return fetch_once("https://" + url[7:])
        raise


def download(url, depth=0):
    """Download one URL, recursing into CSS. Returns the local filename or None."""
    url = norm(url)
    key = key_of(url)
    if key in downloaded:
        return downloaded[key]
    if key in failed:
        return None

    name = local_name(url)
    dest = os.path.join(ASSETDIR, name)

    if os.path.exists(dest) and os.path.getsize(dest) > 0:
        downloaded[key] = name
    else:
        try:
            data = fetch(url)
        except (URLError, HTTPError, OSError, ValueError) as exc:
            failed[key] = str(exc)
            used_names.discard(name)
            print(f"   FAILED  {url}\n           {exc}")
            return None
        if not data:
            failed[key] = "empty response"
            print(f"   EMPTY   {url}")
            return None
        with open(dest, "wb") as fh:
            fh.write(data)
        downloaded[key] = name
        print(f"   saved   {name}")

    if ext_of(url) == ".css" and depth < 4:
        rewrite_css(dest, url, depth)

    return name


def rewrite_css(path, css_url, depth):
    """Pull in whatever a stylesheet references, and point it at the local copy."""
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as fh:
            text = fh.read()
    except OSError:
        return

    targets = []
    for match in CSS_URL_RE.finditer(text):
        targets.append(match.group(2))
    for match in CSS_IMPORT_RE.finditer(text):
        targets.append(match.group(2))

    replacements = {}
    for raw in targets:
        raw = raw.strip()
        if not raw or raw.startswith(("data:", "#")):
            continue
        absolute = urljoin(norm(css_url), raw)
        if not wanted(absolute):
            continue
        name = download(absolute, depth + 1)
        if name:
            replacements[raw] = name

    if not replacements:
        return

    def sub_url(match):
        quote, target = match.group(1), match.group(2).strip()
        if target in replacements:
            return f"url({quote}{replacements[target]}{quote})"
        return match.group(0)

    def sub_import(match):
        quote, target = match.group(1), match.group(2).strip()
        if target in replacements:
            return f"@import {quote}{replacements[target]}{quote}"
        return match.group(0)

    text = CSS_URL_RE.sub(sub_url, text)
    text = CSS_IMPORT_RE.sub(sub_import, text)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


def load_manifest():
    """Re-use the filenames a previous run already picked."""
    if not os.path.exists(MANIFEST):
        return
    try:
        with open(MANIFEST, "r", encoding="utf-8") as fh:
            saved = json.load(fh)
    except (OSError, ValueError):
        print(f"   {MANIFEST} is unreadable, ignoring it")
        return
    kept = 0
    for key, name in saved.items():
        # Only trust the entry if the file is still on disk.
        if os.path.exists(os.path.join(ASSETDIR, name)):
            downloaded[key] = name
            used_names.add(name)
            kept += 1
    print(f"Reusing {kept} filename(s) from {MANIFEST}")


def save_manifest():
    try:
        with open(MANIFEST, "w", encoding="utf-8") as fh:
            json.dump(downloaded, fh, indent=2, sort_keys=True)
    except OSError as exc:
        print(f"   could not write {MANIFEST}: {exc}")


def restore_originals():
    """Keep one pristine copy of what Simvoly served, and work from it."""
    os.makedirs(ORIGINAL, exist_ok=True)
    existing = [f for f in os.listdir(ORIGINAL) if f.endswith(".html")]
    if not existing:
        count = 0
        for f in sorted(os.listdir(PAGES)):
            if f.endswith(".html"):
                shutil.copy2(os.path.join(PAGES, f), os.path.join(ORIGINAL, f))
                count += 1
        print(f"Saved {count} untouched pages to {ORIGINAL}/")
    else:
        count = 0
        for f in sorted(os.listdir(ORIGINAL)):
            if f.endswith(".html"):
                shutil.copy2(os.path.join(ORIGINAL, f), os.path.join(PAGES, f))
                count += 1
        print(f"Restored {count} pages from {ORIGINAL}/ so this run starts clean")

    # Popups come from popups-original/, which the popups command wrote and
    # nothing else touches. Rebuilding popups/ from it every run is what
    # stops a second localize double-rewriting the markup.
    if os.path.isdir(POPUPS_ORIG):
        os.makedirs(POPUPS, exist_ok=True)
        count = 0
        for f in sorted(os.listdir(POPUPS_ORIG)):
            if f.endswith(".html"):
                shutil.copy2(os.path.join(POPUPS_ORIG, f),
                             os.path.join(POPUPS, f))
                count += 1
        if count:
            print(f"Restored {count} captured popup(s) from {POPUPS_ORIG}/")


def main():
    if not os.path.isdir(PAGES):
        sys.exit("STOP: no pages/ folder.")
    os.makedirs(ASSETDIR, exist_ok=True)

    if SIMVOLY_ROOTS:
        print("Simvoly roots treated as must-localize: " + ", ".join(SIMVOLY_ROOTS))

    load_manifest()

    restore_originals()

    html_files = [os.path.join(PAGES, f)
                  for f in sorted(os.listdir(PAGES)) if f.endswith(".html")]
    if os.path.isdir(POPUPS):
        html_files += [os.path.join(POPUPS, f)
                       for f in sorted(os.listdir(POPUPS)) if f.endswith(".html")]

    print("\n=== Collecting asset URLs from every page and popup ===")
    all_urls = set()
    for f in html_files:
        with open(f, "r", encoding="utf-8", errors="ignore") as fh:
            text = fh.read()
        for match in URL_RE.findall(text):
            candidate = match.rstrip(".,;")
            if wanted(candidate):
                all_urls.add(norm(candidate))

    by_kind = {}
    for u in all_urls:
        by_kind.setdefault(ext_of(u) or "(no extension)", 0)
        by_kind[ext_of(u) or "(no extension)"] += 1
    for kind in sorted(by_kind):
        print(f"   {by_kind[kind]:5d}  {kind}")
    print(f"   {len(all_urls):5d}  total")

    if not all_urls:
        print("\nNothing external to download. Either the pages are already local,")
        print("or ASSETHOST is wrong. Check with: bash migrate.sh check")
        return

    print(f"\n=== Downloading {len(all_urls)} assets ===")
    # Stylesheets first, so their own references get queued early.
    ordered = sorted(all_urls, key=lambda u: (ext_of(u) != ".css", u))
    for u in ordered:
        download(u)

    save_manifest()

    print(f"\n=== Rewriting {len(html_files)} files to use the local copies ===")
    total_swaps = 0
    for path in html_files:
        f = os.path.relpath(path)
        with open(path, "r", encoding="utf-8", errors="ignore") as fh:
            text = fh.read()
        swaps = 0
        for key, name in downloaded.items():
            for variant in ("https://" + key, "http://" + key, "//" + key):
                if variant in text:
                    text = text.replace(variant, PUBLIC_PREFIX + name)
                    swaps += 1
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)
        total_swaps += swaps
        print(f"   {f}: {swaps} references rewritten")

    print("\n=== Summary ===")
    print(f"Assets downloaded: {len(downloaded)}")
    print(f"Assets failed:     {len(failed)}")
    print(f"Reference swaps:   {total_swaps}")
    if failed:
        print("\nThese did not download. Check them by hand before cancelling Simvoly:")
        for key, reason in list(failed.items())[:20]:
            print(f"   {key}\n      {reason}")


if __name__ == "__main__":
    main()
LOCALIZEEOF
  head2 "Cutting the cord to $ASSETHOST"
  SITE="$SITE" ASSETHOST="$ASSETHOST" SIMVOLY_ROOTS="$SIMVOLY_ROOTS" python3 /tmp/_localize.py
  if [ -f "$DEADFILE" ]; then
    say ""
    cmd_deadurls
  fi
  # Popups go back in here, at the end, for the same reason dead-urls does:
  # localize rebuilds pages/ from pages-original/ every run, so anything
  # spliced in earlier would be wiped. Done here, it survives every re-run.
  if [ -f popup-rules.json ] && [ -d popups ]; then
    say ""
    cmd_injectpopups
  fi
  say ""
  say "Now run:  bash migrate.sh standalone"
}

# ----------------------------------------------------------- placeholder ----
# A stand-in for images Simvoly has already deleted. Deliberately ugly: a grey
# box with a border reads as "missing image", where a white box reads as a
# layout bug and gets ignored.
#
# Written with nothing but the standard library, because a Codespace may not
# have Pillow or ImageMagick and this must not be the step that needs an install.

cmd_placeholder() {
  mkdir -p pages/assets
  cat > /tmp/_placeholder.py <<'PLACEEOF'
"""Write a 600x350 grey placeholder PNG using only the standard library.

Run through migrate.sh, not directly.
"""
import os
import zlib
import struct

W, H = 600, 350
DEST = os.path.join("pages", "assets", "placeholder.png")

FILL = (221, 221, 221)
BORDER = (136, 136, 136)
BORDER_PX = 4
# A diagonal cross, so the box cannot be mistaken for a real flat-colour image.
CROSS = (170, 170, 170)


def build_rows():
    rows = []
    for y in range(H):
        row = bytearray()
        row.append(0)  # PNG filter type 0 for this scanline
        for x in range(W):
            on_border = (
                x < BORDER_PX or x >= W - BORDER_PX
                or y < BORDER_PX or y >= H - BORDER_PX
            )
            if on_border:
                r, g, b = BORDER
            elif abs(y * W - x * H) < (W * 2) or abs(y * W - (W - x) * H) < (W * 2):
                r, g, b = CROSS
            else:
                r, g, b = FILL
            row.extend((r, g, b))
        rows.append(bytes(row))
    return b"".join(rows)


def chunk(tag, data):
    out = struct.pack(">I", len(data)) + tag + data
    return out + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)


def main():
    os.makedirs(os.path.dirname(DEST), exist_ok=True)
    header = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)  # 8-bit truecolour
    png = (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", header)
        + chunk(b"IDAT", zlib.compress(build_rows(), 9))
        + chunk(b"IEND", b"")
    )
    with open(DEST, "wb") as fh:
        fh.write(png)
    print(f"Wrote {DEST}  ({W}x{H}, {len(png)} bytes)")


if __name__ == "__main__":
    main()
PLACEEOF
  head2 "Building the placeholder image"
  python3 /tmp/_placeholder.py
  say ""
  say "Point dead references at it in $DEADFILE, one rule per line:"
  say ""
  say "  https://content.app-sources.com/s/.../gone.png  /assets/placeholder.png"
  say ""
  say "Then run:  bash migrate.sh patch"
}

# -------------------------------------------------------------- deadurls ----
# Some references are not downloadable files: base paths, directory URLs and
# config values that name the asset host but never point at a real file.
# localize cannot fix those - there is nothing to download. List them in
# dead-urls.txt and this command swaps them out by hand.
#
# "bash migrate.sh patch" is the same command. The runbook says patch.

cmd_deadurls() {
  [ -f "$DEADFILE" ] || die "No $DEADFILE. Create it with one rule per line:

  https://content.app-sources.com/uploads/    /assets/

Old value first, new value second, separated by spaces.
Lines starting with # are ignored."
  [ -d pages ] || die "No pages/ folder."
  cat > /tmp/_dead.py <<'DEADEOF'
"""Apply the find-and-replace rules in dead-urls.txt to the built pages.

Run through migrate.sh, not directly.
"""
import os
import sys

DEADFILE = "dead-urls.txt"
PAGES = "pages"
ASSETDIR = os.path.join(PAGES, "assets")

rules = []
with open(DEADFILE, encoding="utf-8") as fh:
    for lineno, line in enumerate(fh, 1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        # Be forgiving about lines pasted straight out of this command's own
        # report, which look like:   12  https://old/thing  ->  /new/thing
        if len(parts) > 2 and parts[0].isdigit():
            parts = parts[1:]
        parts = [p for p in parts if p not in ("->", "=>", "→")]
        if len(parts) != 2:
            print(f"   line {lineno}: needs exactly two values, skipped -> {line}")
            continue
        rules.append((parts[0], parts[1]))

if not rules:
    sys.exit(f"STOP: no usable rules in {DEADFILE}")


def variants(old):
    """The same URL can sit in the HTML three ways. Match all of them.

    standalone prints every reference as https://, because it normalises
    before reporting. The raw file may hold //host/path or http://host/path,
    so a rule written as https:// would quietly match nothing.
    """
    for prefix in ("https://", "http://", "//"):
        if old.startswith(prefix):
            rest = old[len(prefix):]
            return ["https://" + rest, "http://" + rest, "//" + rest]
    return [old]


# Expand each rule, then go longest first. That matters: //host/x is a
# substring of https://host/x, so the scheme-ful forms must be replaced
# first or https:// would be left as a broken https:/ stub.
expanded = []
for old, new in rules:
    for form in variants(old):
        expanded.append((form, new))
seen = set()
rules = []
for old, new in expanded:
    if old not in seen:
        seen.add(old)
        rules.append((old, new))
rules.sort(key=lambda r: -len(r[0]))

targets = []
for f in sorted(os.listdir(PAGES)):
    if f.endswith(".html"):
        targets.append(os.path.join(PAGES, f))
if os.path.isdir(ASSETDIR):
    for f in sorted(os.listdir(ASSETDIR)):
        if f.endswith((".css", ".js")):
            targets.append(os.path.join(ASSETDIR, f))

counts = {old: 0 for old, _ in rules}
changed = 0
for path in targets:
    with open(path, "r", encoding="utf-8", errors="ignore") as fh:
        text = fh.read()
    before = text
    for old, new in rules:
        n = text.count(old)
        if n:
            text = text.replace(old, new)
            counts[old] += n
    if text != before:
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)
        changed += 1

print(f"Scanned {len(targets)} file(s), changed {changed}\n")
hits = 0
for old, new in rules:
    if counts[old]:
        hits += counts[old]
        print(f"   {counts[old]:5d}  {old}  ->  {new}")

if hits == 0:
    print("   nothing matched\n")
    print("Every rule missed. The text in dead-urls.txt has to appear in the")
    print("file exactly. Find the real form with:")
    print("   grep -o '[^\"']*app-sources[^\"']*' pages/index.html")
    print("then copy what it prints into dead-urls.txt.")
DEADEOF
  head2 "Applying $DEADFILE"
  python3 /tmp/_dead.py
}

cmd_standalone() {
  load_env
  [ -d pages ] || die "No pages/ folder."
  cat > /tmp/_standalone.py <<'STANDALONEEOF'
"""Prove the site no longer needs Simvoly.

Run through migrate.sh, not directly.
"""
import os
import re
import sys
from urllib.parse import urlsplit
from collections import Counter

SITE = os.environ.get("SITE", "").lower()
ASSETHOST = os.environ.get("ASSETHOST", "").lower()

# Every root domain Simvoly serves from. Without this, a file on a Simvoly
# host that is not ASSETHOST was either called a harmless third-party
# service (if it had no file extension) or reported as somebody else's
# server that "will not die with the Simvoly account" - which was wrong,
# and is exactly the reference that breaks the site at cancellation.
SIMVOLY_ROOTS = [
    r.strip().lower()
    for r in os.environ.get("SIMVOLY_ROOTS", "").split(",")
    if r.strip()
]

PAGES = "pages"
ASSETDIR = os.path.join(PAGES, "assets")
POPUPDIR = "popups"

KEEP_REMOTE = (
    "googletagmanager.com", "google-analytics.com", "analytics.google.com",
    "googleadservices.com", "googlesyndication.com", "doubleclick.net",
    "google.com/recaptcha", "recaptcha.net", "hcaptcha.com",
    "maps.googleapis.com", "maps.gstatic.com",
    "connect.facebook.net", "facebook.com", "facebook.net",
    "youtube.com", "youtu.be", "youtube-nocookie.com", "vimeo.com",
    "js.stripe.com", "checkout.stripe.com",
    "fonts.googleapis.com", "fonts.gstatic.com",
    "calendar.google.com", "docs.google.com", "forms.gle", "google.com/maps",
    "instagram.com", "cdninstagram.com", "twitter.com", "x.com", "linkedin.com",
    "yelp.com", "tripadvisor.com", "apple.com", "app-store", "play.google.com",
)

STATIC_EXT = {
    ".css", ".js", ".mjs",
    ".jpg", ".jpeg", ".png", ".gif", ".webp", ".avif", ".svg", ".ico", ".bmp",
    ".woff", ".woff2", ".ttf", ".eot", ".otf",
    ".mp4", ".webm", ".ogg", ".mp3", ".wav",
}


def is_static(url):
    import posixpath
    path = urlsplit(url if "//" not in url[:2] else "https:" + url).path
    return posixpath.splitext(path)[1].lower() in STATIC_EXT

# Only these attributes make the browser actually go fetch something.
FETCHING = re.compile(
    r"""(?<![-\w])(?:src|href|srcset|poster|data-src|data-bg|content)\s*=\s*(['"])(.*?)\1""",
    re.I | re.S,
)
CSS_URL = re.compile(r"""url\(\s*['"]?([^'")]+)""", re.I)
CSS_IMPORT = re.compile(r"""@import\s+(?:url\(\s*)?['"]([^'"]+)""", re.I)


def external(url):
    url = url.strip()
    if not url.lower().startswith(("http://", "https://", "//")):
        return None
    if url.startswith("//"):
        url = "https:" + url
    host = urlsplit(url).netloc.lower()
    if not host:
        return None
    if host in (SITE, "www." + SITE):
        return None
    return host, url


def bare_host(url):
    """https://host/ with nothing after it - a preconnect or config value, not a file."""
    split = urlsplit(url if not url.startswith("//") else "https:" + url)
    return split.path in ("", "/") and not split.query


def keep(url):
    return any(k in url.lower() for k in KEEP_REMOTE)


def scan_html(path):
    hits = []
    with open(path, "r", encoding="utf-8", errors="ignore") as fh:
        text = fh.read()
    for match in FETCHING.finditer(text):
        raw = match.group(2)
        for piece in re.split(r"[,\s]+", raw):
            piece = piece.strip()
            if not piece or piece.startswith("data:"):
                continue
            got = external(piece)
            if got:
                hits.append(got)
    for match in CSS_URL.finditer(text):
        got = external(match.group(1))
        if got:
            hits.append(got)
    return hits


def scan_css(path):
    hits = []
    with open(path, "r", encoding="utf-8", errors="ignore") as fh:
        text = fh.read()
    for pattern in (CSS_URL, CSS_IMPORT):
        for match in pattern.finditer(text):
            got = external(match.group(1))
            if got:
                hits.append(got)
    return hits


def root_of(host):
    """app-sources.com out of content.app-sources.com."""
    parts = host.split(".")
    return ".".join(parts[-2:]) if len(parts) >= 2 else host


ASSETROOT = root_of(ASSETHOST) if ASSETHOST else ""


def is_simvoly(host):
    """Simvoly serves from more than one host, on more than one domain.

    content.app-sources.com holds images. service-api.app-sources.com runs
    live features. static.web-repository.com serves the builder's own
    JavaScript. All of them die when the account closes, so all of them
    count - not just the one saved as ASSETHOST.
    """
    host = (host or "").lower()
    if not host:
        return False
    if ASSETHOST and host == ASSETHOST:
        return True
    if ASSETROOT and (host == ASSETROOT or host.endswith("." + ASSETROOT)):
        return True
    return any(host == r or host.endswith("." + r) for r in SIMVOLY_ROOTS)


def main():
    if not os.path.isdir(PAGES):
        sys.exit("STOP: no pages/ folder.")

    blocking = Counter()    # on Simvoly - the site dies without it
    orphan = Counter()      # static file on some other host - should be local
    services = Counter()    # live third-party services - fine to keep
    hints = Counter()       # preconnect / dns-prefetch - nothing is fetched
    where = {}
    urls_by_host = {}

    targets = []
    for f in sorted(os.listdir(PAGES)):
        if f.endswith(".html"):
            targets.append((os.path.join(PAGES, f), scan_html))
    if os.path.isdir(ASSETDIR):
        for f in sorted(os.listdir(ASSETDIR)):
            if f.endswith(".css"):
                targets.append((os.path.join(ASSETDIR, f), scan_css))
    # Captured popups count too. Their markup never goes through localize,
    # so a popup image can still point at Simvoly long after the pages pass.
    popups_scanned = 0
    if os.path.isdir(POPUPDIR):
        for f in sorted(os.listdir(POPUPDIR)):
            if f.endswith(".html"):
                targets.append((os.path.join(POPUPDIR, f), scan_html))
                popups_scanned += 1

    for path, scanner in targets:
        for host, url in scanner(path):
            name = os.path.basename(path)
            if bare_host(url):
                hints[host] += 1
            elif is_simvoly(host):
                blocking[host] += 1
                where.setdefault(host, set()).add(name)
                urls_by_host.setdefault(host, Counter())[url] += 1
            elif keep(url):
                services[host] += 1
            elif is_static(url):
                orphan[host] += 1
                where.setdefault(host, set()).add(name)
                urls_by_host.setdefault(host, Counter())[url] += 1
            else:
                services[host] += 1

    print(f"Scanned {len(targets)} files", end="")
    if popups_scanned:
        print(f" (including {popups_scanned} captured popup(s))")
    else:
        print("")
    if SIMVOLY_ROOTS:
        print("Simvoly roots watched: " + ", ".join(SIMVOLY_ROOTS))
    if not os.path.isdir(POPUPDIR):
        print("No popups/ folder - run 'bash migrate.sh popups' before trusting a PASS.")
    print("")

    if services:
        print("Live third-party services (fine - these keep working):")
        for host, n in services.most_common():
            print(f"   {n:5d}  {host}")
        print("   Confirm each of these still works on the new site. They are")
        print("   embeds and tags, not files that disappear.\n")

    if hints:
        print("Connection hints only (preconnect, dns-prefetch, config attributes):")
        for host, n in hints.most_common():
            print(f"   {n:5d}  {host}")
        print("   These name a host but never fetch a file, so nothing breaks when")
        print("   that host goes away. Tidy them up if you like - see the runbook.\n")

    problems = 0

    if blocking:
        print("=" * 62)
        print("FAIL - still loading from Simvoly")
        print("=" * 62)
        for host, n in blocking.most_common():
            print(f"\n   {n} reference(s) to {host}")
            files = sorted(where[host])
            shown = ", ".join(files[:6])
            more = f" (+{len(files) - 6} more)" if len(files) > 6 else ""
            print(f"      in: {shown}{more}")
            distinct = urls_by_host.get(host, Counter())
            print(f"      {len(distinct)} distinct file(s):")
            for u, c in distinct.most_common(12):
                print(f"        {c:3d}x  {u}")
            if len(distinct) > 12:
                print(f"        ... and {len(distinct) - 12} more")
        others = [h for h in blocking if h != ASSETHOST]
        if others:
            verb = "is" if len(others) == 1 else "are"
            print(f"\n   Note: {', '.join(sorted(others))} {verb} Simvoly too,")
            print(f"   even though not saved as ASSETHOST ({ASSETHOST}).")
            print("   A URL with no file extension is usually a live feature, not")
            print("   an image. Those cannot be downloaded - decide whether to")
            print("   rebuild or drop it.")
        problems += 1

    if orphan:
        print("\n" + "=" * 62)
        print("WARNING - static files loading from other outside hosts")
        print("=" * 62)
        for host, n in orphan.most_common():
            print(f"\n   {n} file(s) from {host}")
            files = sorted(where[host])
            shown = ", ".join(files[:6])
            more = f" (+{len(files) - 6} more)" if len(files) > 6 else ""
            print(f"      in: {shown}{more}")
        print("\n   As far as this check knows these are not Simvoly's, so they")
        print("   should survive the cancellation. They are still somebody")
        print("   else's server - self-host them if you can. If you recognise")
        print("   one as Simvoly infrastructure, add its root domain to")
        print("   SIMVOLY_ROOTS at the top of migrate.sh and run this again.")
        problems += 1

    if not problems:
        print("=" * 62)
        print("PASS - nothing on this site depends on Simvoly.")
        print("Every page, style and script is served from your own files.")
        print("=" * 62)
        return 0

    print("\nRun this to try again:  bash migrate.sh localize")
    print("Anything still listed after that has to be handled by hand.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
STANDALONEEOF
  head2 "Can this site stand without Simvoly?"
  SITE="$SITE" ASSETHOST="$ASSETHOST" SIMVOLY_ROOTS="$SIMVOLY_ROOTS" python3 /tmp/_standalone.py
}

cmd_verifyassets() {
  local dir="pages/assets"
  [ -d "$dir" ] || die "No $dir folder. Run: bash migrate.sh localize"
  head2 "Checking every downloaded file is real"
  say "Files: $(find "$dir" -type f | wc -l)"
  du -sh "$dir"
  : > /tmp/_bad.txt
  local t
  for f in "$dir"/*; do
    [ -f "$f" ] || continue
    case "$f" in *.svg|*.css|*.js|*.mjs|*.json) continue ;; esac
    t=$(file --mime-type -b "$f")
    case "$t" in
      image/*|video/*|audio/*|font/*|application/pdf) ;;
      application/font*|application/x-font*) ;;
      application/vnd.ms-fontobject|application/vnd.ms-opentype) ;;
      *opentype*|*truetype*|*sfnt*|*woff*) ;;
      *) printf '%s  (%s)\n' "$f" "$t" >> /tmp/_bad.txt ;;
    esac
  done
  if [ -s /tmp/_bad.txt ]; then
    say ""
    say "These are not real media files - almost always an error page saved"
    say "under an image name. Review, then delete the bad ones by hand:"
    cat /tmp/_bad.txt
  else
    say "All media files are real."
  fi
  say ""
  say "SVG, CSS and JS are skipped on purpose. The 'file' command does not"
  say "report SVGs as image data, and a naive check deletes the client's logos."
  say "Fonts pass too. 'file' reports .otf as application/vnd.ms-opentype,"
  say "which is a real font, not an error page."

  head2 "Looking for duplicate copies of the same file"
  find "$dir" -type f -exec md5sum {} + 2>/dev/null | sort > /tmp/_sums.txt
  awk '{print $1}' /tmp/_sums.txt | uniq -d > /tmp/_dupehashes.txt
  if [ -s /tmp/_dupehashes.txt ]; then
    say "Same bytes saved under more than one name:"
    while read -r h; do
      say ""
      grep "^$h " /tmp/_sums.txt | awk '{print "   " $2}'
    done < /tmp/_dupehashes.txt
    say ""
    say "This happens when localize is run twice. Use the unreferenced check"
    say "below to see which copy nothing points at, then delete that one."
  else
    say "No duplicates."
  fi

  head2 "Files nothing on the site points at"
  local n name unused=0
  for f in "$dir"/*; do
    [ -f "$f" ] || continue
    name=$(basename "$f")
    if ! grep -rqlF "$name" pages popups --include='*.html' --include='*.css' --include='*.js' 2>/dev/null; then
      say "   $name"
      unused=$((unused + 1))
    fi
  done
  if [ "$unused" -eq 0 ]; then
    say "None. Every file is referenced."
  else
    say ""
    say "$unused file(s) are dead weight. Safe to delete, but eyeball the list first."
    say "placeholder.png shows up here until dead-urls.txt points at it."
  fi
}

# ------------------------------------------------------------------ pdfs ----

cmd_pdfs() {
  load_env; need_pages
  grep -ohE "https?://[^[:space:]${DQ}${SQ})<>]+\.pdf" pages/*.html | sed 's/?.*$//' | sort -u > pdf-urls.txt || true
  local total
  total=$(wc -l < pdf-urls.txt)
  head2 "Found $total PDFs"
  if [ "$total" -eq 0 ]; then
    rm -f pdf-urls.txt
    say "This site has no PDFs. Nothing to do. Move on."
    return 0
  fi
  mkdir -p pdfs
  local n=0 name
  while read -r url; do
    [ -z "$url" ] && continue
    n=$((n + 1))
    name=$(basename "$url")
    printf '%4d/%d  %s\n' "$n" "$total" "$name"
    curl -s -L --compressed "$url" -o "pdfs/$name"
    sleep 1
  done < pdf-urls.txt

  head2 "Verifying"
  say "Downloaded: $(find pdfs -type f | wc -l) files"
  local bad=0
  for f in pdfs/*; do
    [ -f "$f" ] || continue
    file --mime-type -b "$f" | grep -q 'application/pdf' || { say "NOT A PDF: $f"; bad=$((bad + 1)); }
  done
  [ "$bad" -eq 0 ] && say "All files are real PDFs."
}

# ---------------------------------------------------------------- popups ----
# Opens each page in a real browser and sorts what it finds into three piles:
#
#   PLATFORM   Simvoly's own cookie banner, cart preview, analytics panel.
#              On every site, never the client's. Ignored.
#   TEMPLATE   popup markup nobody wired up. Nothing in the page points at
#              it, so it cannot fire. Ignored.
#   ACTIVE     something references it - a button, a trigger attribute, a
#              line of config. These are the ones that matter.
#
# Only ACTIVE popups are saved, and they are saved as Simvoly's own markup,
# byte for byte. They are not rebuilt later - localize rewrites their asset
# URLs like any page, and injectpopups splices them back into the site. The
# only thing replaced is the few lines that decide when a popup opens.

cmd_popups() {
  load_env
  [ -f urls.txt ] || die "No urls.txt. Run: bash migrate.sh urls"
  if ! python3 -c "import playwright" 2>/dev/null; then
    die "This command needs Playwright. Install it once per Codespace:

  pip install playwright --break-system-packages
  python3 -m playwright install chromium --with-deps

Then run this command again. Takes a few minutes the first time."
  fi
  mkdir -p popups-original
  cat > /tmp/_popups.py <<'POPEOF'
"""Find the client's real popups on a live Simvoly site and save their markup.

Run through migrate.sh, not directly.
"""
import os
import re
import sys
import json
import time

from playwright.sync_api import sync_playwright

OUT = "popups-original"
RULES = "popup-rules.json"
WAIT_MS = 4000          # let Simvoly's JS finish building the page
SETTLE_MS = 1200

SCAN_JS = r"""
() => {
  const NAME_RE = /popup|modal|lightbox|dialog|flyout/i;
  const PLATFORM_RE = /cookies?-popup|cookie-consent|analyticsSettings|cart-preview|gdpr|consent-(banner|manager)/i;
  const GENERIC = new Set(["popup","modal","overlay","dialog","none","active",
    "open","hidden","show","hide","is-open","at-center","container","wrapper",
    "inner","popup-wrapper","popup-overlay","popup-container","popup-content"]);

  const classOf = (el) => {
    const c = el.className;
    const s = (c && c.baseVal !== undefined) ? c.baseVal : c;
    return (s || "").toString().trim();
  };

  // Simvoly's furniture is identified by the whole block, not just its
  // outermost div - the cookie banner's wrapper is a bare .popup-overlay
  // and the telltale class sits on a child.
  const isPlatform = (el) => {
    if (PLATFORM_RE.test(classOf(el) + " " + (el.id || ""))) return true;
    for (const d of el.querySelectorAll("*")) {
      if (PLATFORM_RE.test(classOf(d) + " " + (d.id || ""))) return true;
    }
    for (let n = el.parentElement; n && n !== document.body; n = n.parentElement) {
      if (PLATFORM_RE.test(classOf(n) + " " + (n.id || ""))) return true;
    }
    return false;
  };

  // What else in the document points at this popup? Done against the DOM,
  // not by string-searching the HTML - the browser rewrites attribute order
  // and whitespace, so a text match silently misses.
  const referencedBy = (el) => {
    const tokens = [];
    if (el.id) tokens.push(el.id);
    for (const c of classOf(el).split(/\s+/)) {
      if (c && c.length >= 4 && !GENERIC.has(c.toLowerCase())) tokens.push(c);
    }
    if (!tokens.length) return [];

    const hits = [];
    for (const other of document.querySelectorAll("*")) {
      if (other === el || el.contains(other) || other.contains(el)) continue;
      for (const a of other.attributes) {
        for (const t of tokens) {
          if (a.value && a.value.includes(t)) {
            hits.push({
              kind: "attribute",
              where: other.tagName.toLowerCase() + (other.id ? "#" + other.id : ""),
              detail: a.name + '="' + a.value.slice(0, 70) + '"',
              selector: other.id ? "#" + other.id
                        : other.tagName.toLowerCase() + "[" + a.name + "='" + a.value + "']",
            });
          }
        }
      }
    }
    for (const s of document.querySelectorAll("script:not([src])")) {
      if (el.contains(s)) continue;
      const txt = s.textContent || "";
      for (const t of tokens) {
        const i = txt.indexOf(t);
        if (i >= 0) {
          hits.push({
            kind: "inline script",
            where: "<script>",
            detail: txt.slice(Math.max(0, i - 60), i + 90).replace(/\s+/g, " "),
            selector: "",
          });
        }
      }
    }
    return hits.slice(0, 8);
  };

  const found = [];
  for (const el of document.querySelectorAll("body *")) {
    if (!el.children.length) continue;
    const cs = getComputedStyle(el);
    const named = NAME_RE.test(classOf(el) + " " + (el.id || ""));
    const layered = (cs.position === "fixed" || cs.position === "absolute")
                    && (parseInt(cs.zIndex, 10) || 0) >= 100;
    const hidden = cs.display === "none" || cs.visibility === "hidden"
                   || parseFloat(cs.opacity) === 0;
    if (!(named || (layered && hidden))) continue;
    const words = (el.textContent || "").replace(/\s+/g, " ").trim();
    if (words.length < 10 && !el.querySelector("a[href], button, input")) continue;
    found.push({ el, hidden });
  }
  const tops = found.filter(
    (c) => !found.some((o) => o.el !== c.el && o.el.contains(c.el))
  );

  return tops.map((c) => {
    const el = c.el;
    const attrs = {};
    for (const a of el.attributes) attrs[a.name] = a.value;
    const hits = referencedBy(el);
    const triggerAttrs = {};
    for (const k in attrs) {
      if (/^data-/i.test(k) && /delay|trigger|exit|scroll|show|auto|seconds|frequency|popup/i.test(k)) {
        triggerAttrs[k] = attrs[k];
      }
    }
    return {
      id: el.id || "",
      classes: classOf(el),
      hiddenAtLoad: c.hidden,
      isPlatform: isPlatform(el),
      refs: hits,
      triggerAttrs: triggerAttrs,
      headings: [...el.querySelectorAll("h1,h2,h3,h4,h5,h6")]
        .map((h) => (h.textContent || "").replace(/\s+/g, " ").trim())
        .filter(Boolean),
      text: (el.textContent || "").replace(/\s+/g, " ").trim().slice(0, 300),
      links: [...el.querySelectorAll("a[href]")]
        .map((a) => ({ text: (a.textContent || "").trim().slice(0, 40), href: a.href }))
        .filter((l) => !l.href.startsWith("javascript:")),
      fields: [...el.querySelectorAll("input,select,textarea")]
        .filter((f) => (f.type || "").toLowerCase() !== "hidden")
        .map((f) => (f.name || f.placeholder || f.type || "?")),
      formActions: [...el.querySelectorAll("form")]
        .map((f) => f.getAttribute("action") || "(same page)"),
      images: [...new Set([...el.querySelectorAll("img")].map((i) => i.src).filter(Boolean))],
      html: el.outerHTML,
    };
  });
}
"""


def safe(name):
    return re.sub(r"[^A-Za-z0-9._-]", "-", name)[:70]


def url_to_name(url):
    path = re.sub(r"^https?://[^/]+", "", url)
    path = re.sub(r"[?#].*$", "", path).strip("/")
    return safe(path or "index")


def page_path(url):
    path = re.sub(r"^https?://[^/]+", "", url)
    path = re.sub(r"[?#].*$", "", path)
    return path or "/"


def main():
    urls = [l.strip() for l in open("urls.txt", encoding="utf-8") if l.strip()]
    if not urls:
        sys.exit("STOP: urls.txt is empty.")

    os.makedirs(OUT, exist_ok=True)
    active, templates, platform = [], 0, 0

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        for n, url in enumerate(urls, 1):
            page = browser.new_page(viewport={"width": 1440, "height": 900})
            print(f"{n:4d}/{len(urls)}  {url}")
            try:
                page.goto(url, wait_until="networkidle", timeout=60000)
            except Exception as exc:
                print(f"          could not load: {exc}")
                page.close()
                continue

            page.wait_for_timeout(WAIT_MS)
            try:                         # trip exit-intent popups
                page.mouse.move(700, 400)
                page.mouse.move(700, 0)
                page.wait_for_timeout(SETTLE_MS)
            except Exception:
                pass

            try:
                found = page.evaluate(SCAN_JS)
            except Exception as exc:
                print(f"          scan failed: {exc}")
                page.close()
                continue

            name = url_to_name(url)
            seq = 0
            for p in found:
                if p["isPlatform"]:
                    platform += 1
                    continue
                if not p["refs"]:
                    templates += 1
                    label = p["id"] or p["classes"][:40]
                    print(f"          TEMPLATE  {label}  (nothing references it)")
                    continue

                seq += 1
                pid = p["id"] or f"{name}-popup{seq}"
                stem = safe(pid)
                with open(os.path.join(OUT, stem + ".html"), "w",
                          encoding="utf-8") as fh:
                    fh.write(p["html"])
                shot = ""
                try:
                    page.evaluate(
                        """(id) => { const el = document.getElementById(id);
                             if (!el) return; el.classList.remove('none');
                             el.style.setProperty('display','block','important');
                             el.style.setProperty('visibility','visible','important');
                             el.style.setProperty('opacity','1','important');
                             el.style.setProperty('z-index','2147483647','important');
                             el.scrollIntoView({block:'center'}); }""", p["id"])
                    page.wait_for_timeout(400)
                    shot = stem + ".png"
                    page.screenshot(path=os.path.join(OUT, shot))
                except Exception:
                    shot = ""

                head = p["headings"][0] if p["headings"] else p["text"][:60]
                print(f"          ACTIVE    {stem}  \"{head[:50]}\"")
                for r in p["refs"][:3]:
                    print(f"                      [{r['kind']}] {r['detail'][:90]}")
                if p["triggerAttrs"]:
                    for k, v in p["triggerAttrs"].items():
                        print(f"                      {k}={v}")
                if p["fields"]:
                    print(f"                      form fields: "
                          f"{', '.join(p['fields'][:6])}")
                for a in p["formActions"]:
                    print(f"                      form posts to: {a}")

                click_sel = ""
                for r in p["refs"]:
                    if r["kind"] == "attribute" and r["selector"]:
                        click_sel = r["selector"]
                        break

                active.append({
                    "id": pid,
                    "file": stem + ".html",
                    "screenshot": shot,
                    "foundOn": page_path(url),
                    "heading": head,
                    "trigger": "TBD",
                    "delaySeconds": None,
                    "scrollPercent": None,
                    "clickSelector": click_sel,
                    "pages": [page_path(url)],
                    "frequency": "TBD",
                    "device": "TBD",
                    "formTarget": "TBD" if (p["fields"] or p["formActions"]) else None,
                    "notes": "",
                })
            page.close()
            time.sleep(1)
        browser.close()

    # Same popup on many pages is one popup. Merge by id and collect the paths.
    merged = {}
    for a in active:
        if a["id"] in merged:
            for pth in a["pages"]:
                if pth not in merged[a["id"]]["pages"]:
                    merged[a["id"]]["pages"].append(pth)
        else:
            merged[a["id"]] = a
    rules = list(merged.values())

    print("\n=== Summary ===")
    print(f"Pages checked:            {len(urls)}")
    print(f"ACTIVE popups:            {len(rules)}")
    print(f"Templates ignored:        {templates}")
    print(f"Simvoly dialogs ignored:  {platform}")

    if not rules:
        print("\nNo active client popups found.")
        print("If the Simvoly dashboard says otherwise, the popup fires on a")
        print("trigger this scan does not reach - a long delay, deep scroll, or")
        print("a click. Add it to popup-rules.json by hand and save its markup")
        print(f"into {OUT}/ yourself. See Step 8A.")
        return

    if os.path.exists(RULES):
        print(f"\n{RULES} already exists - leaving it alone.")
        print("Delete it and re-run if you want a fresh scaffold.")
    else:
        with open(RULES, "w", encoding="utf-8") as fh:
            json.dump(rules, fh, indent=2)
        print(f"\nWrote {RULES} with {len(rules)} entry(ies).")

    print("\nEvery TBD in that file is a setting only the Simvoly dashboard")
    print("knows. Fill them in before anyone cancels the account:")
    print("   trigger        load | delay | scroll | exit | click")
    print("   delaySeconds   the real number, not 'a few'")
    print("   pages          every page it shows on")
    print("   frequency      always | once-per-session | once-per-N-days | once-ever")
    print("   device         all | desktop | mobile")
    print("   formTarget     where submissions should go now")
    print("\nThen run:  bash migrate.sh localize")


if __name__ == "__main__":
    main()
POPEOF
  head2 "Finding the client's real popups on $SITE"
  say "This opens a real browser, so it is slower than the other commands."
  say ""
  python3 /tmp/_popups.py
}

# ------------------------------------------------------------ injectpopups ---
# Puts the popups back into the site. Runs at the end of localize, so the
# markup it splices in has already had its Simvoly URLs rewritten to local
# ones, and so a re-run of localize never loses the work.
#
# Each block is wrapped in a marker comment, which makes this safe to run
# as many times as you like - an existing block is replaced, not duplicated.

cmd_injectpopups() {
  [ -d pages ] || die "No pages/ folder."
  [ -f popup-rules.json ] || die "No popup-rules.json. Run: bash migrate.sh popups"
  [ -d popups ] || die "No popups/ folder. Run: bash migrate.sh localize"
  write_popup_lift_js
  cat > /tmp/_inject.py <<'INJECTEOF'
"""Splice the captured popup markup and its trigger config back into the pages.

Run through migrate.sh, not directly.
"""
import os
import re
import sys
import json

PAGES = "pages"
POPUPS = "popups"
RULES = "popup-rules.json"
START = "<!-- OPTSPOT-POPUPS -->"
END = "<!-- /OPTSPOT-POPUPS -->"
BLOCK_RE = re.compile(re.escape(START) + r".*?" + re.escape(END), re.S)


def page_file(path):
    """The runbook's flat filename for a site path."""
    slug = path.strip("/").replace("/", "-")
    return "index.html" if not slug else slug + ".html"


def main():
    with open(RULES, encoding="utf-8") as fh:
        rules = json.load(fh)
    if not rules:
        sys.exit("STOP: popup-rules.json is empty.")

    tbd = sum(1 for r in rules
              for v in r.values() if isinstance(v, str) and v == "TBD")
    if tbd:
        print(f"WARNING: {tbd} field(s) in {RULES} are still TBD.")
        print("         A popup with a guessed trigger is worse than no popup.")
        print("         Filling them in is Step 8A.\n")

    # Which popups belong on which page file.
    by_page = {}
    for r in rules:
        for path in (r.get("pages") or [r.get("foundOn", "/")]):
            by_page.setdefault(page_file(path), []).append(r)

    touched = 0
    missing_markup = []
    missing_pages = []

    for fname, popups in sorted(by_page.items()):
        target = os.path.join(PAGES, fname)
        if not os.path.exists(target):
            missing_pages.append(fname)
            continue

        chunks = []
        for r in popups:
            src = os.path.join(POPUPS, r.get("file") or (r["id"] + ".html"))
            if not os.path.exists(src):
                missing_markup.append(src)
                continue
            with open(src, encoding="utf-8", errors="ignore") as fh:
                chunks.append(fh.read().strip())

        if not chunks:
            continue

        cfg = []
        for r in popups:
            entry = {"id": r["id"], "trigger": r.get("trigger") or "delay"}
            for key in ("delaySeconds", "scrollPercent", "clickSelector",
                        "pages", "frequency", "device"):
                if r.get(key) not in (None, "", []):
                    entry[key] = r[key]
            cfg.append(entry)

        block = "\n".join([
            START,
            "\n".join(chunks),
            '<script>window.OP_LIFT = ' + json.dumps(cfg) + ';</script>',
            '<script src="/assets/popup-lift.js"></script>',
            END,
        ])

        with open(target, "r", encoding="utf-8", errors="ignore") as fh:
            html = fh.read()

        if BLOCK_RE.search(html):
            html = BLOCK_RE.sub(lambda _m: block, html)   # lambda: no \g escapes
            how = "replaced"
        elif "</body>" in html:
            html = html.replace("</body>", block + "\n</body>", 1)
            how = "inserted"
        else:
            html = html + "\n" + block
            how = "appended (no </body> found)"

        with open(target, "w", encoding="utf-8") as fh:
            fh.write(html)
        touched += 1
        names = ", ".join(r["id"] for r in popups)
        print(f"   {how:10s} {fname}  <- {names}")

    print(f"\nPages updated: {touched}")
    if missing_markup:
        print("\nNo saved markup for these - re-run 'bash migrate.sh popups':")
        for m in sorted(set(missing_markup)):
            print(f"   {m}")
    if missing_pages:
        print("\npopup-rules.json names pages that were never downloaded:")
        for m in sorted(set(missing_pages)):
            print(f"   {m}")
        print("   Fix the 'pages' list, or re-run Step 7 for those URLs.")


if __name__ == "__main__":
    main()
INJECTEOF
  head2 "Putting the popups back into the pages"
  python3 /tmp/_inject.py
}

# The only part of a popup that is rebuilt. Everything else - markup, copy,
# images, layout, styling - is Simvoly's own, carried across untouched. This
# replaces the handful of lines that decided when a popup opened.
write_popup_lift_js() {
  mkdir -p pages/assets
  cat > pages/assets/popup-lift.js <<'LIFTEOF'
/* popup-lift.js - runs Simvoly's own popup markup without Simvoly.
 * Written by migrate.sh. Do not edit here; edit the toolkit.
 *
 * The markup and the site stylesheet do the work. This only decides when a
 * popup opens, reading window.OP_LIFT, which injectpopups writes from
 * popup-rules.json.
 *
 * Simvoly marks a hidden popup with the class "none" on .popup-wrapper, and
 * usually an inline display:none too. Both are handled, with a direct
 * display fallback in case a site does neither.
 */
(function () {
  "use strict";
  var cfg = window.OP_LIFT || [];
  if (!cfg.length) return;
  var path = location.pathname.replace(/index\.html$/, "") || "/";

  function store(k) { try { return localStorage.getItem(k); } catch (e) { return null; } }
  function remember(k) { try { localStorage.setItem(k, String(Date.now())); } catch (e) {} }

  function allowed(p) {
    var freq = p.frequency || "always";
    if (freq === "always" || freq === "TBD") return true;
    if (freq === "once-per-session") {
      try { return !sessionStorage.getItem("op_s_" + p.id); } catch (e) { return true; }
    }
    var last = store("op_popup_" + p.id);
    if (!last) return true;
    if (freq === "once-ever") return false;
    var days = parseInt(String(freq).replace(/\D/g, ""), 10) || 7;
    return (Date.now() - Number(last)) > days * 86400000;
  }

  function deviceOk(p) {
    if (!p.device || p.device === "all" || p.device === "TBD") return true;
    var mobile = window.matchMedia("(max-width: 768px)").matches;
    return p.device === "mobile" ? mobile : !mobile;
  }

  function pageOk(p) {
    if (!p.pages || !p.pages.length) return true;
    return p.pages.some(function (x) {
      return x === path || x + "/" === path || x === path + "/";
    });
  }

  function show(p) {
    var el = document.getElementById(p.id);
    if (!el || el.getAttribute("data-op-open") === "1") return;
    el.classList.remove("none");
    if (el.style && el.style.display === "none") el.style.display = "";
    if (getComputedStyle(el).display === "none") el.style.display = "block";
    el.setAttribute("data-op-open", "1");
    remember("op_popup_" + p.id);
    try { sessionStorage.setItem("op_s_" + p.id, "1"); } catch (e) {}
    var f = el.querySelector("input, button, a[href]");
    if (f) { try { f.focus(); } catch (e) {} }
  }

  function hide(el) {
    if (!el) return;
    el.classList.add("none");
    el.style.display = "none";
    el.removeAttribute("data-op-open");
  }

  document.addEventListener("click", function (e) {
    var closer = e.target.closest(
      ".custom-popup-close-btn, .popup-close, [data-popup-close], .close-btn");
    if (closer) {
      var owner = closer.closest('[data-op-open="1"]');
      if (owner) { e.preventDefault(); hide(owner); return; }
    }
    if (e.target.getAttribute && e.target.getAttribute("data-op-open") === "1") {
      hide(e.target);
    }
  });

  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") {
      [].slice.call(document.querySelectorAll('[data-op-open="1"]')).forEach(hide);
    }
  });

  cfg.forEach(function (p) {
    if (!p.id || !deviceOk(p) || !pageOk(p) || !allowed(p)) return;
    var t = p.trigger || "delay";

    if (t === "load") {
      show(p);
    } else if (t === "scroll") {
      var fired = false;
      window.addEventListener("scroll", function () {
        if (fired) return;
        var doc = document.body.scrollHeight - window.innerHeight;
        var pct = doc > 0 ? (window.scrollY / doc) * 100 : 100;
        if (pct >= (p.scrollPercent || 50)) { fired = true; show(p); }
      }, { passive: true });
    } else if (t === "exit") {
      document.addEventListener("mouseout", function (e) {
        if (!e.relatedTarget && e.clientY < 10) show(p);
      });
    } else if (t === "click") {
      var sel = p.clickSelector || "[data-popup-target='" + p.id + "']";
      document.addEventListener("click", function (e) {
        if (e.target.closest(sel)) { e.preventDefault(); show(p); }
      });
    } else {
      // "delay", and anything still TBD, so a half-filled rules file still
      // shows the popup rather than silently dropping it.
      setTimeout(function () { show(p); }, (p.delaySeconds || 5) * 1000);
    }
  });
})();
LIFTEOF
  say "   wrote pages/assets/popup-lift.js"
}

cmd_popuplift() {
  write_popup_lift_js
  say ""
  say "That is the only rebuilt part of a popup. Markup, copy, images and"
  say "styling all come across as Simvoly wrote them."
  say "It is written automatically by localize - you rarely run this by hand."
}

# ------------------------------------------------------------------ copy ----

cmd_copy() {
  need_pages
  mkdir -p copy
  cat > /tmp/_extract.py <<'PYEOF'
import html, re, sys

raw = open(sys.argv[1], encoding='utf-8', errors='ignore').read()
raw = re.sub(r'<!--.*?-->', '', raw, flags=re.S)
raw = re.sub(r'<(script|style|noscript|template|svg)\b[^>]*>.*?</\1>', '', raw, flags=re.S | re.I)
text = html.unescape(re.sub(r'<[^>]+>', '\n', raw))

seen, out = set(), []
for line in (l.strip() for l in text.split('\n')):
    if line and line not in seen:
        seen.add(line)
        out.append(line)

print('\n'.join(out))
PYEOF

  head2 "Extracting readable copy"
  local name n=0
  for f in pages/*.html; do
    name=$(basename "$f" .html)
    python3 /tmp/_extract.py "$f" > "copy/$name.txt"
    n=$((n + 1))
  done
  say "Wrote $n files to copy/"

  head2 "Pages that extracted almost nothing"
  local thin=0
  for f in copy/*.txt; do
    if [ "$(wc -l < "$f")" -lt 10 ]; then say "  $f  ($(wc -l < "$f") lines)"; thin=$((thin + 1)); fi
  done
  if [ "$thin" -eq 0 ]; then
    say "None. Every page has real content."
  else
    say ""
    say "$thin page(s) are very short. Thank-you and checkout pages really are short."
    say "Anything else was probably rendered by JavaScript - copy it by hand from the live site."
  fi
}

# ------------------------------------------------------------------- seo ----

cmd_seo() {
  [ -f urls.txt ] || die "No urls.txt. Run: bash migrate.sh urls"
  need_pages
  cat > /tmp/_seo.py <<'PYEOF'
import os, re, csv

rows = []
for url in open("urls.txt", encoding="utf-8"):
    url = url.strip()
    if not url:
        continue

    path = re.sub(r'^https?://[^/]+', '', url)
    path = re.sub(r'[?#].*$', '', path) or "/"

    slug = path.strip("/").replace("/", "-") or "index"
    candidates = [
        f"pages/{slug}.html",
        f"pages/{os.path.basename(url.rstrip('/')) or 'index'}.html",
        "pages/index.html" if path == "/" else "",
    ]
    f = next((c for c in candidates if c and os.path.exists(c)), None)

    title = desc = ""
    if f:
        doc = open(f, encoding="utf-8", errors="ignore").read()
        m = re.search(r'<title[^>]*>(.*?)</title>', doc, re.I | re.S)
        if m:
            title = " ".join(re.sub(r'<[^>]+>', '', m.group(1)).split())
        for tag in re.findall(r'<meta\b[^>]*>', doc, re.I):
            if re.search(r'name\s*=\s*["\']?description["\']?', tag, re.I):
                m = re.search(r'content\s*=\s*["\']([^"\']*)["\']', tag, re.I)
                if m:
                    desc = " ".join(m.group(1).split())
                break

    rows.append({
        "old_path": path,
        "new_path": path,
        "changed": "no",
        "title": title,
        "description": desc,
        "source_file": f if f else "MISSING",
    })

with open("redirect-map.csv", "w", newline="", encoding="utf-8") as out:
    w = csv.DictWriter(out, fieldnames=["old_path", "new_path", "changed", "title", "description", "source_file"])
    w.writeheader()
    w.writerows(rows)

missing = [r for r in rows if r["source_file"] == "MISSING"]
notitle = [r for r in rows if not r["title"]]
nodesc = [r for r in rows if not r["description"]]

print(f"Wrote redirect-map.csv with {len(rows)} rows")
print(f"Missing page files: {len(missing)}")
for r in missing:
    print("   MISSING:", r["old_path"])
print(f"Pages with no <title>: {len(notitle)}")
for r in notitle:
    print("   NO TITLE:", r["old_path"])
print(f"Pages with no meta description: {len(nodesc)}")
PYEOF
  head2 "Building redirect-map.csv"
  python3 /tmp/_seo.py
  say ""
  say "Next: open redirect-map.csv in the Explorer panel."
  say "Change new_path only for pages whose slug is changing, and set changed to yes."
  say "Save the file, then run: bash migrate.sh redirects"
}

cmd_redirects() {
  [ -f redirect-map.csv ] || die "No redirect-map.csv. Run: bash migrate.sh seo"
  cat > /tmp/_red.py <<'PYEOF'
import csv, os

lines = []
for r in csv.DictReader(open("redirect-map.csv", encoding="utf-8")):
    old = (r.get("old_path") or "").strip()
    new = (r.get("new_path") or "").strip()
    if old and new and old != new:
        lines.append(f"{old} {new} 301")

os.makedirs("pages", exist_ok=True)
with open("pages/_redirects", "w", encoding="utf-8") as out:
    out.write("\n".join(lines) + ("\n" if lines else ""))

print(f"Wrote pages/_redirects with {len(lines)} rules")
for l in lines:
    print("   " + l)
if not lines:
    print("Zero rules is the good outcome - every slug stayed the same.")
PYEOF
  head2 "Building pages/_redirects"
  python3 /tmp/_red.py
}

# -------------------------------------------------------------- homepage ----

cmd_homepage() {
  load_env
  need_pages
  head2 "Making sure the homepage is pages/index.html"
  if [ -f pages/index.html ]; then
    say "pages/index.html already exists. Nothing to do."
    return 0
  fi
  for candidate in "pages/$SITE.html" "pages/www.$SITE.html" "pages/home.html"; do
    if [ -f "$candidate" ]; then
      mv "$candidate" pages/index.html
      say "Renamed $candidate  ->  pages/index.html"
      return 0
    fi
  done
  say "Could not find the homepage automatically. Here is what is in pages/:"
  ls pages/
  die "Rename the homepage by hand:  mv pages/THEFILE.html pages/index.html"
}

# ---------------------------------------------------------------- config ----

cmd_config() {
  local asked target raw name
  asked="${1:-}"

  if [ -n "$asked" ]; then
    target=$(normalize_target "$asked")
    [ -n "$target" ] || die "I do not know the target '$asked'.

  bash migrate.sh config pages      Cloudflare Pages   (use this for new sites)
  bash migrate.sh config workers    Cloudflare Workers (existing Worker sites only)"
  else
    target=$(current_target)
    say "No target given, using '$target'."
    say "Be explicit next time:  bash migrate.sh config pages"
    say ""
  fi

  raw=$(basename "$(pwd)")
  # Cloudflare requires the project name to be lowercase letters, digits and
  # dashes only. Repo folders are often title case, which fails the deploy.
  # Same rule for both products.
  name=$(printf '%s' "$raw" \
    | tr '[:upper:]' '[:lower:]' \
    | sed -E 's/[^a-z0-9-]+/-/g; s/-+/-/g; s/^-+//; s/-+$//' \
    | cut -c1-54)
  [ -n "$name" ] || die "Could not build a valid name from the folder '$raw'.
Rename the folder, or set name by hand in wrangler.toml."
  case "$name" in
    [a-z0-9]*[a-z0-9]|[a-z0-9]) ;;
    *) die "'$name' is not a valid Cloudflare project name. Rename the folder." ;;
  esac
  [ "$name" = "$raw" ] || say "Folder is '$raw', using project name '$name'"

  local want_lines want_key
  if [ "$target" = "pages" ]; then
    # Pages reads this at build time. pages_build_output_dir is what tells
    # Cloudflare to publish pages/ and not the whole repo - the single most
    # common way a Pages deploy goes wrong.
    {
      printf 'name = "%s"\n' "$name"
      printf 'pages_build_output_dir = "./pages"\n'
      printf 'compatibility_date = "%s"\n' "$(date +%Y-%m-%d)"
    } > wrangler.toml
    want_lines=3
    want_key="pages_build_output_dir"
  else
    {
      printf 'name = "%s"\n' "$name"
      printf 'compatibility_date = "%s"\n' "$(date +%Y-%m-%d)"
      printf 'preview_urls = true\n'
      printf '\n'
      printf '[assets]\n'
      printf 'directory = "./pages"\n'
    } > wrangler.toml
    want_lines=5
    want_key="\[assets\]"
  fi

  head2 "wrangler.toml  (target: $target)"
  cat wrangler.toml

  local lines
  lines=$(grep -c . wrangler.toml)
  [ "$lines" -eq "$want_lines" ] || die \
    "wrangler.toml looks wrong. Expected $want_lines non-blank lines, got $lines."
  grep -qE "$want_key" wrangler.toml || die \
    "wrangler.toml is missing its $target settings. Run this command again."

  save_target "$target"

  say ""
  if [ "$target" = "pages" ]; then
    say "Looks right. 3 lines, publishing ./pages"
    say ""
    say "Because this file exists, it is the source of truth. Cloudflare will"
    say "show the build fields in the dashboard but will not let you edit them."
    say "That is on purpose - it stops anyone publishing the repo root by"
    say "accident, which puts pages-original/ online and 404s the homepage."
  else
    say "Looks right. 5 lines, with an [assets] block pointing at ./pages"
  fi
  say "Project name is '$name' - this must match the Cloudflare project name."
}

# ---------------------------------------------------------------- status ----

cmd_status() {
  head2 "Migration status"
  [ -f "$ENVFILE" ] && { source "$ENVFILE"; say "SITE          $SITE"; say "ASSETHOST     $ASSETHOST"; } || say "SITE          (not set - run the domain command)"
  say "urls.txt      $( [ -f urls.txt ] && wc -l < urls.txt || echo 'missing' ) pages listed"
  say "pages/        $( [ -d pages ] && find pages -name '*.html' | wc -l || echo 0 ) html files"
  say "pages/assets/ $( [ -d pages/assets ] && find pages/assets -type f | wc -l || echo 0 ) files"
  say "pdfs/         $( [ -d pdfs ] && find pdfs -type f | wc -l || echo 0 ) files"
  say "popups/       $( [ -d popups-original ] && find popups-original -name '*.html' | wc -l || echo 0 ) active popup(s) captured"
  say "popup rules   $(popup_rules_state)"
  say "popups in situ $(popup_inject_state)"
  say "copy/         $( [ -d copy ] && find copy -name '*.txt' | wc -l || echo 0 ) files"
  say "audit/        $( [ -d audit ] && find audit -name '*.txt' | wc -l || echo 0 ) files"
  say "redirect map  $( [ -f redirect-map.csv ] && echo 'built' || echo 'missing' )"
  say "_redirects    $( [ -f pages/_redirects ] && echo 'built' || echo 'missing' )"
  say "homepage      $( [ -f pages/index.html ] && echo 'pages/index.html OK' || echo 'NOT RENAMED - run: bash migrate.sh homepage' )"

  local target
  target="${TARGET:-$DEFAULT_TARGET}"
  say "deploy target $target"
  say "wrangler.toml $(config_state "$target")"
}

# Captured popup content is only half the job. The trigger and frequency
# rules live in the Simvoly dashboard and have to be written down by hand
# before the account closes, so this is called out separately.
popup_rules_state() {
  local captured=0
  [ -d popups ] && captured=$(find popups -name '*.html' | wc -l | tr -d ' ')
  if [ ! -f popup-rules.json ]; then
    if [ "$captured" -gt 0 ]; then
      printf 'MISSING - %s popup(s) captured but no rules recorded (Step 8A)' "$captured"
    else
      printf 'none yet'
    fi
    return
  fi
  # grep -o so several TBDs on one line all count, and so a no-match run
  # still ends in wc printing a clean 0 rather than grep's exit status.
  local tbd
  tbd=$(grep -o 'TBD' popup-rules.json 2>/dev/null | wc -l | tr -d ' ')
  [ -n "$tbd" ] || tbd=0
  if [ "$tbd" -gt 0 ]; then
    printf 'INCOMPLETE - %s field(s) still TBD in popup-rules.json' "$tbd"
  else
    printf 'popup-rules.json OK'
  fi
}

# Have the captured popups actually been put back into the pages yet?
popup_inject_state() {
  if [ ! -d popups-original ] || [ -z "$(find popups-original -name '*.html' 2>/dev/null)" ]; then
    printf 'n/a - no popups on this site'
    return
  fi
  local n
  n=$(grep -rl 'OPTSPOT-POPUPS' pages --include='*.html' 2>/dev/null | wc -l | tr -d ' ')
  [ -n "$n" ] || n=0
  if [ "$n" -eq 0 ]; then
    printf 'NOT INJECTED - run: bash migrate.sh localize'
  else
    printf 'on %s page(s)' "$n"
  fi
}

# Is wrangler.toml the right shape for the target we are deploying to?
config_state() {
  local target="$1"
  if [ ! -f wrangler.toml ]; then
    printf 'missing - run: bash migrate.sh config %s' "$target"
    return
  fi
  if [ "$target" = "pages" ]; then
    if grep -q 'pages_build_output_dir' wrangler.toml; then
      printf 'OK for Pages'
    elif grep -q '^\[assets\]' wrangler.toml; then
      printf 'WRONG - this is a Workers config. Run: bash migrate.sh config pages'
    else
      printf 'WRONG SHAPE - run: bash migrate.sh config pages'
    fi
  else
    if grep -q '^\[assets\]' wrangler.toml; then
      printf 'OK for Workers'
    elif grep -q 'pages_build_output_dir' wrangler.toml; then
      printf 'WRONG - this is a Pages config. Run: bash migrate.sh config workers'
    else
      printf 'WRONG SHAPE - run: bash migrate.sh config workers'
    fi
  fi
}

# ------------------------------------------------------------------ help ----

cmd_help() {
  cat <<'HELPEOF'
OptSpot migration toolkit

  bash migrate.sh domain <clientdomain.com>   Step 5  - set the domain, find the asset host
  bash migrate.sh sethost <cdn-domain.com>    Step 5  - override the asset host by hand
  bash migrate.sh check                       Step 5  - confirm both values are still set
  bash migrate.sh urls                        Step 6  - build urls.txt from the sitemap
  bash migrate.sh pages                       Step 7  - download every page
  bash migrate.sh audit                       Step 8  - what survives the migration
  bash migrate.sh popups                      Step 8A - find the real popups, with a real browser
  bash migrate.sh localize                    Step 9  - download every asset, cut the cord
  bash migrate.sh placeholder                 Step 9  - build the missing-image stand-in
  bash migrate.sh patch                       Step 9  - swap out URLs localize cannot download
  bash migrate.sh deadurls                    Step 9  - same as patch
  bash migrate.sh injectpopups                Step 9  - put the popups back (localize does this for you)
  bash migrate.sh popuplift                   Step 9  - rewrite pages/assets/popup-lift.js
  bash migrate.sh standalone                  Step 9  - prove nothing needs Simvoly
  bash migrate.sh verifyassets                Step 9  - confirm downloads are real files
  bash migrate.sh pdfs                        Step 10 - download every PDF
  bash migrate.sh copy                        Step 11 - extract readable text
  bash migrate.sh seo                         Step 12 - build redirect-map.csv
  bash migrate.sh redirects                   Step 12 - build pages/_redirects
  bash migrate.sh homepage                    Step 14 - rename the homepage to index.html
  bash migrate.sh config pages                Step 16 - write wrangler.toml for Cloudflare Pages
  bash migrate.sh config workers              Step 16 - write wrangler.toml for Cloudflare Workers
  bash migrate.sh status                      Any time - what is done so far

Popups are lifted, not rebuilt. Run popups BEFORE localize - it reads the
live site, so it only works while Simvoly is still serving. It keeps Simvoly's
own markup, skips the cookie banner and any unused template popup, and writes
popup-rules.json. localize then rewrites the popup assets and splices the
markup back into the pages.

The one thing no scan can reach is WHEN a popup fires. Trigger, delay, page
rules, frequency and device live only in the Simvoly dashboard. Fill in every
TBD in popup-rules.json by hand, or they are gone at cancellation.

New sites go to Pages. The account is at its Workers limit, so "config pages"
is the one you want. Sites already running as Workers stay on Workers - use
"config workers" when you are updating one of those.
HELPEOF
}

# ------------------------------------------------------------------ main ----

case "${1:-help}" in
  domain)    shift; cmd_domain "$@" ;;
  sethost)   shift; cmd_sethost "$@" ;;
  check)     cmd_check ;;
  urls)      cmd_urls ;;
  pages)     cmd_pages ;;
  audit)     cmd_audit ;;
  localize)  cmd_localize ;;
  placeholder) cmd_placeholder ;;
  deadurls|patch) cmd_deadurls ;;
  standalone) cmd_standalone ;;
  verifyassets) cmd_verifyassets ;;
  pdfs)      cmd_pdfs ;;
  popups)    cmd_popups ;;
  injectpopups) cmd_injectpopups ;;
  popuplift) cmd_popuplift ;;
  copy)      cmd_copy ;;
  seo)       cmd_seo ;;
  redirects) cmd_redirects ;;
  homepage)  cmd_homepage ;;
  config)    shift; cmd_config "$@" ;;
  status)    cmd_status ;;
  help|*)    cmd_help ;;
esac