// Prints the built-in reviews block as HTML. Used by scripts/build_site.py.
// Usage: node scripts/render-reviews.mjs <limit>
import { renderReviews } from "../src/render.js";
import { FALLBACK_REVIEWS } from "../src/fallback-reviews.js";

const limit = Number(process.argv[2] || 3);
process.stdout.write(renderReviews({ source: "static", reviews: FALLBACK_REVIEWS }, { limit }));
