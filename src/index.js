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
const SEARCH_QUERY = "Log Hog Tree Service Pensacola FL";
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

  let placeId = env.GOOGLE_PLACE_ID;
  if (!placeId) {
    const r = await fetch(`${base}/places:searchText`, {
      method: "POST",
      headers: { ...headers, "Content-Type": "application/json", "X-Goog-FieldMask": "places.id,places.displayName" },
      body: JSON.stringify({ textQuery: SEARCH_QUERY, pageSize: 1 }),
    });
    if (!r.ok) throw new Error(`place search failed: ${r.status} ${await r.text()}`);
    const found = (await r.json()).places?.[0];
    if (!found || !/log\s*hog/i.test(found.displayName?.text || "")) throw new Error("business not found by search");
    placeId = found.id;
  }

  const r = await fetch(`${base}/places/${encodeURIComponent(placeId)}`, {
    headers: { ...headers, "X-Goog-FieldMask": "id,rating,userRatingCount,googleMapsUri,reviews" },
  });
  if (!r.ok) throw new Error(`place details failed: ${r.status} ${await r.text()}`);
  const data = { ...fromPlaces(await r.json()), placeId };

  ctx.waitUntil(
    cache.put(CACHE_KEY, new Response(JSON.stringify(data), {
      headers: { "content-type": "application/json", "cache-control": `public, max-age=${CACHE_SECONDS}` },
    })),
  );
  return data;
}
