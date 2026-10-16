// Prints the built-in reviews as JSON. Used by scripts/build_site.py.
import { FALLBACK_REVIEWS } from "../src/fallback-reviews.js";
process.stdout.write(JSON.stringify(FALLBACK_REVIEWS));
