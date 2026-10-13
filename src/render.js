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

/**
 * data: { rating?, count?, mapsUrl?, source: "google" | "static",
 *         reviews: [{ name, authorUrl?, photo?, rating, when?, text }] }
 */
export function renderReviews(data, { limit = 4 } = {}) {
  const reviews = (data.reviews || []).slice(0, limit);
  const live = data.source === "google";

  const summary =
    live && data.rating && data.count
      ? `<a class="lhr-summary" href="${esc(data.mapsUrl || REVIEW_LINK)}" target="_blank" rel="noopener">
          <span class="lhr-score">${Number(data.rating).toFixed(1)}</span>${stars(data.rating)}
          <span class="lhr-count">${Number(data.count)} Google reviews</span></a>`
      : "";

  const cards = reviews
    .map((r) => {
      const avatar = r.photo
        ? `<img class="lhr-avatar" src="${esc(r.photo)}" alt="" width="44" height="44" loading="lazy" referrerpolicy="no-referrer">`
        : `<span class="lhr-avatar lhr-initials" aria-hidden="true">${esc(initials(r.name))}</span>`;
      const name = r.authorUrl
        ? `<a href="${esc(r.authorUrl)}" target="_blank" rel="noopener nofollow">${esc(r.name)}</a>`
        : esc(r.name);
      return `<figure class="lhr-card">
        <div class="lhr-head">${avatar}<div><div class="lhr-name">${name}</div>
          <div class="lhr-meta">${stars(r.rating)}${r.when ? ` <span>${esc(r.when)}</span>` : ""}</div></div></div>
        <blockquote>${esc(trim(r.text))}</blockquote>
      </figure>`;
    })
    .join("");

  return `<div class="lhr-wrap">
    ${summary}
    <div class="lhr-grid">${cards}</div>
    <div class="lhr-actions">
      <a class="lhr-btn" href="${REVIEW_LINK}" target="_blank" rel="noopener">LEAVE US A REVIEW</a>
      ${live ? `<a class="lhr-btn lhr-ghost" href="${esc(data.mapsUrl || REVIEW_LINK)}" target="_blank" rel="noopener">READ ALL REVIEWS ON GOOGLE</a>` : ""}
    </div>
    ${live ? `<p class="lhr-attr">Reviews from Google Maps</p>` : ""}
  </div>`;
}

/** Turn a Places API (New) place response into the data shape above. */
export function fromPlaces(place) {
  const reviews = (place.reviews || [])
    .filter((r) => (r.rating || 0) >= 4 && (r.text?.text || r.originalText?.text))
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
