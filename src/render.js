// Renders the reviews block. Used by the Worker (live Google data) and by
// scripts/build-fallback.mjs (the static copy baked into the HTML, shown if
// Google can't be reached or the API key isn't set yet).

export const REVIEW_LINK = "https://g.page/r/CRlPuRF2X2gtEBM/review";

const esc = (s) =>
  String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);

const stars = (n) => {
  const full = Math.round(Number(n) || 0);
  return `<span class="lhr-stars" role="img" aria-label="${full} out of 5 stars">${"★".repeat(full)}<span class="lhr-dim">${"★".repeat(5 - full)}</span></span>`;
};

const trim = (t, max = 320) => {
  t = String(t || "").replace(/\s+/g, " ").trim();
  if (t.length <= max) return t;
  return t.slice(0, t.lastIndexOf(" ", max)) + "…";
};

const initials = (name) =>
  String(name || "?").split(/\s+/).filter(Boolean).slice(0, 2).map((w) => w[0].toUpperCase()).join("");

const key = (n) => String(n || "").toLowerCase().replace(/[^a-z]/g, "");

/** Every 5-star review we know about: live Google ones first, then the
 *  built-in list (deduped by reviewer name). */
export function allFiveStar(live, builtIn) {
  const seen = new Set();
  return [...(live || []), ...(builtIn || [])].filter((r) => {
    if (Number(r.rating) !== 5 || !r.text) return false;
    const k = key(r.name);
    if (seen.has(k)) return false;
    seen.add(k);
    return true;
  });
}

const card = (r) => {
  const avatar = r.photo
    ? `<img class="lhr-avatar" src="${esc(r.photo)}" alt="" width="44" height="44" loading="lazy" referrerpolicy="no-referrer">`
    : `<span class="lhr-avatar lhr-initials" aria-hidden="true">${esc(initials(r.name))}</span>`;
  const name = r.authorUrl
    ? `<a href="${esc(r.authorUrl)}" target="_blank" rel="noopener nofollow">${esc(r.name)}</a>`
    : esc(r.name);
  return `<figure class="lhr-card">
    <div class="lhr-top">${stars(5)}<svg class="lhr-g" viewBox="0 0 24 24" aria-label="Google review" role="img"><path fill="#4285F4" d="M22.5 12.3c0-.8-.1-1.5-.2-2.2H12v4.2h5.9a5 5 0 0 1-2.2 3.3v2.7h3.5c2.1-1.9 3.3-4.7 3.3-8z"/><path fill="#34A853" d="M12 23c3 0 5.5-1 7.3-2.7l-3.5-2.7c-1 .7-2.3 1.1-3.8 1.1-2.9 0-5.4-2-6.3-4.7H2v2.8A11 11 0 0 0 12 23z"/><path fill="#FBBC05" d="M5.7 14a6.6 6.6 0 0 1 0-4.2V7H2a11 11 0 0 0 0 9.9L5.7 14z"/><path fill="#EA4335" d="M12 5.4c1.6 0 3.1.6 4.3 1.7l3.1-3.1A11 11 0 0 0 2 7l3.7 2.9C6.6 7.3 9.1 5.4 12 5.4z"/></svg></div>
    <blockquote>${esc(trim(r.text, 280))}</blockquote>
    <figcaption class="lhr-head">${avatar}<div><div class="lhr-name">${name}</div>${r.when ? `<div class="lhr-meta">${esc(r.when)}</div>` : ""}</div></figcaption>
  </figure>`;
};

/**
 * data: { rating?, count?, mapsUrl?, source: "google" | "static",
 *         reviews: [{ name, authorUrl?, photo?, rating, when?, text }] }
 * Renders every review given as an endlessly scrolling strip (pauses on
 * hover; becomes a swipeable row when the visitor prefers reduced motion).
 */
export function renderReviews(data) {
  const reviews = data.reviews || [];
  const live = data.source === "google";
  const cards = reviews.map(card).join("");
  // Short lists get repeated so the strip is always wider than the screen.
  const reps = Math.max(1, Math.ceil(6 / Math.max(reviews.length, 1)));
  const half = Array(reps).fill(cards).join("");
  const secs = Math.max(30, reviews.length * reps * 9);

  const summary = live && data.rating && data.count
    ? `<a class="lhr-summary" href="${esc(data.mapsUrl || REVIEW_LINK)}" target="_blank" rel="noopener">
        <span class="lhr-score">${Number(data.rating).toFixed(1)}</span>${stars(data.rating)}
        <span class="lhr-count">${Number(data.count)} Google reviews</span></a>`
    : `<a class="lhr-summary" href="${REVIEW_LINK}" target="_blank" rel="noopener">${stars(5)}<span class="lhr-count">5-star reviews on Google</span></a>`;

  return `<div class="lhr-wrap">
    ${summary}
    <div class="lhr-marquee" style="--dur:${secs}s" tabindex="0" aria-label="Customer reviews">
      <div class="lhr-track"><div class="lhr-set">${half}</div><div class="lhr-set" aria-hidden="true">${half}</div></div>
    </div>
    <div class="lhr-actions">
      <a class="lhr-btn" href="${REVIEW_LINK}" target="_blank" rel="noopener">Leave us a review</a>
      <a class="lhr-btn lhr-ghost" href="${esc(data.mapsUrl || REVIEW_LINK)}" target="_blank" rel="noopener">Read all reviews on Google</a>
    </div>
  </div>`;
}

/** Turn a Places API (New) place response into the data shape above. */
export function fromPlaces(place) {
  const reviews = (place.reviews || [])
    .filter((r) => (r.text?.text || r.originalText?.text))
    .map((r) => ({
      name: r.authorAttribution?.displayName || "Google user",
      authorUrl: r.authorAttribution?.uri,
      photo: r.authorAttribution?.photoUri,
      rating: r.rating,
      when: r.relativePublishTimeDescription,
      text: r.text?.text || r.originalText?.text,
    }));
  return {
    source: "google",
    rating: place.rating,
    count: place.userRatingCount,
    mapsUrl: place.googleMapsUri,
    reviews,
  };
}
