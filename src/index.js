// Serves the static site from ./pages and, on pages that have a reviews
// section, swaps in live reviews from Google (Places API).
//
// Setup (one time):
//   npx wrangler secret put GOOGLE_PLACES_API_KEY
//   Optional: set GOOGLE_PLACE_ID in wrangler.toml [vars]. If it's not set,
//   the Worker looks the business up by name and caches the result.
//
// Google is called at most about twice a day per Cloudflare data center
// (results are cached for 12 hours), which stays inside Google's free monthly
// allowance for this kind of request.

import { renderReviews, fromPlaces } from "./render.js";

const CACHE_KEY = "https://loghog.internal/google-reviews-v1";
const CACHE_SECONDS = 12 * 60 * 60;
const FAIL_KEY = "https://loghog.internal/google-reviews-failed-v2";
const SEARCH_QUERY = "Log Hog Tree Service";
const PHONE_DIGITS = "8504264220";
const PAGE_LIMITS = { home: 4, about: 3 };

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);

    if (url.pathname === "/api/reviews") {
      const data = await getReviews(env, ctx).catch((e) => ({ error: String(e.message || e) }));
      return Response.json(data, { headers: { "cache-control": "public, max-age=3600" } });
    }

    const res = await env.ASSETS.fetch(request);
    const type = res.headers.get("content-type") || "";
    if (request.method !== "GET" || !res.ok || !type.includes("text/html")) return res;

    let data;
    try {
      data = await getReviews(env, ctx);
    } catch (e) {
      console.log("reviews unavailable, serving built-in copy:", e.message || e);
      return res;
    }
    if (!data?.reviews?.length) return res;

    return new HTMLRewriter()
      .on("[data-lh-reviews]", {
        element(el) {
          const page = el.getAttribute("data-lh-reviews");
          el.setInnerContent(renderReviews(data, { limit: PAGE_LIMITS[page] || 4 }), { html: true });
          el.setAttribute("data-source", "google");
        },
      })
      .transform(res);
  },
};

async function getReviews(env, ctx) {
  if (!env.GOOGLE_PLACES_API_KEY) throw new Error("GOOGLE_PLACES_API_KEY not set");

  const cache = caches.default;
  const hit = await cache.match(CACHE_KEY);
  if (hit) return hit.json();

  const base = env.PLACES_ENDPOINT || "https://places.googleapis.com/v1";
  const headers = { "X-Goog-Api-Key": env.GOOGLE_PLACES_API_KEY };

  // A recent failure is remembered for 30 minutes so a problem can't turn
  // every page view into a paid Google request.
  const failed = await cache.match(FAIL_KEY);
  if (failed) throw new Error("recent failure: " + (await failed.text()));

  try {
    const placeId = env.GOOGLE_PLACE_ID || (await findPlaceId(base, headers));
    const r = await fetch(`${base}/places/${encodeURIComponent(placeId)}`, {
      headers: { ...headers, "X-Goog-FieldMask": "id,rating,userRatingCount,googleMapsUri,reviews" },
    });
    if (!r.ok) throw new Error(`place details failed: ${r.status} ${(await r.text()).slice(0, 300)}`);
    const data = { ...fromPlaces(await r.json()), placeId };
    ctx.waitUntil(put(cache, CACHE_KEY, JSON.stringify(data), CACHE_SECONDS));
    return data;
  } catch (e) {
    ctx.waitUntil(put(cache, FAIL_KEY, String(e.message || e), 30 * 60));
    throw e;
  }
}

// Find the business on Google: match the phone number first, then the name.
async function findPlaceId(base, headers) {
  const r = await fetch(`${base}/places:searchText`, {
    method: "POST",
    headers: {
      ...headers,
      "Content-Type": "application/json",
      "X-Goog-FieldMask": "places.id,places.displayName,places.nationalPhoneNumber,places.internationalPhoneNumber",
    },
    body: JSON.stringify({
      textQuery: SEARCH_QUERY,
      pageSize: 10,
      // Log Hog has no public address (service-area business); Google leaves
      // those out of search results unless asked.
      includePureServiceAreaBusinesses: true,
    }),
  });
  if (!r.ok) throw new Error(`place search failed: ${r.status} ${(await r.text()).slice(0, 300)}`);
  const places = (await r.json()).places || [];
  const digits = (s) => String(s || "").replace(/\D/g, "").slice(-10);
  const found =
    places.find((p) => [p.nationalPhoneNumber, p.internationalPhoneNumber].some((n) => digits(n) === PHONE_DIGITS)) ||
    places.find((p) => /log\s*hog/i.test(p.displayName?.text || ""));
  if (!found) {
    const seen = places.map((p) => `${p.displayName?.text} ${p.nationalPhoneNumber || ""}`).join("; ");
    throw new Error(`business not found by search (saw: ${seen || "nothing"})`);
  }
  return found.id;
}

function put(cache, key, body, seconds) {
  return cache.put(key, new Response(body, { headers: { "cache-control": `public, max-age=${seconds}` } }));
}
