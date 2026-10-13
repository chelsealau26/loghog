// Rebuilds the built-in (fallback) reviews inside pages/index.html and
// pages/about-us.html. The live Worker replaces this content with Google
// reviews; visitors only see this copy if Google can't be reached.
//
// Run from the repo root:  node scripts/build-fallback.mjs

import { readFileSync, writeFileSync } from "node:fs";
import { renderReviews } from "../src/render.js";

const FALLBACK = {
  home: [
    { name: "Steve Greene", photo: "/assets/unnamed-0671640.png", rating: 5,
      text: "Fast, on time, trimmed seven trees on our property in Navarre! Dave was very professional, did a fantastic job and hauled away all the branches, and left the yard looking great!! Thank you so much! Highly recommended!" },
    { name: "Jayden McGoldrick", photo: "/assets/unnamed-1-0671733.png", rating: 5,
      text: "Solid work from LogHog. David and his crew are friendly and professional. They had a very large dying oak removed in a timely and safe manner. Would recommend them to anyone." },
    { name: "Dan Massingill", photo: "/assets/unnamed-2-0671795.png", rating: 5,
      text: "Great communication, speedy service! Had a fairly large stump left over from fallen oak tree. Log Hog had the stump cut up and grinded down flat in no time and the price was hundreds less than the competition!" },
  ],
  about: [
    { name: "Blair Ritchey", rating: 5,
      text: "I was impressed by how professional and hard-working Dave was. He knew exactly what needed to be done, went right up the tree and dropped the branches and tree right where he said he would. I would recommend him to anyone that needs tree work." },
    { name: "Travis Bradley", rating: 5,
      text: "Dave from Log Hog is fast and clean with his work!! I was beyond impressed with his work and always happy to support a fellow veteran and small business owner! 10/10 would RECOMMEND!" },
  ],
};

const STYLE = `<style id="lhr-style">
[data-lh-reviews]{padding:8px 16px 64px;font-family:'Open Sans',Arial,sans-serif;color:rgba(26,26,26,1)}
.lhr-wrap{max-width:1140px;margin:0 auto}
.lhr-wrap>*{width:100%;box-sizing:border-box}
.lhr-card,.lhr-card *{box-sizing:border-box}
.lhr-summary{display:flex;flex-wrap:wrap;align-items:center;justify-content:center;gap:10px;margin:0 auto 28px;text-decoration:none;color:inherit}
.lhr-score{font-size:34px;font-weight:700;line-height:1}
.lhr-summary .lhr-stars{font-size:24px}
.lhr-count{font-size:16px;color:rgba(205,90,40,1);text-decoration:underline;text-underline-offset:3px}
.lhr-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:20px}
.lhr-card{margin:0;background:#fff;border:1px solid rgba(23,17,14,.12);border-radius:10px;padding:22px;box-shadow:0 2px 10px rgba(23,17,14,.06);display:flex;flex-direction:column;gap:14px}
.lhr-head{display:flex;align-items:center;gap:12px}
.lhr-avatar{width:44px;height:44px;border-radius:50%;object-fit:cover;flex:0 0 44px}
.lhr-initials{display:flex;align-items:center;justify-content:center;background:rgba(85,62,54,1);color:#fff;font-weight:700;font-size:16px}
.lhr-name{font-weight:700;font-size:16px;line-height:1.2}
.lhr-name a{color:inherit;text-decoration:none}
.lhr-meta{font-size:13px;color:rgba(26,26,26,.6);display:flex;gap:8px;align-items:center;margin-top:3px}
.lhr-stars{color:#f5b301;letter-spacing:1px}
.lhr-dim{color:rgba(26,26,26,.18)}
.lhr-card blockquote{margin:0;font-size:15px;line-height:1.6;color:rgba(26,26,26,.85);border:0;padding:0}
.lhr-actions{display:flex;flex-wrap:wrap;gap:12px;justify-content:center;margin-top:32px}
.lhr-btn{display:inline-block;background:rgba(205,90,40,1);color:#fff!important;text-decoration:none;font-weight:700;letter-spacing:1px;font-size:15px;padding:15px 30px;border-radius:6px}
.lhr-btn:hover{background:rgba(244,106,45,1)}
.lhr-ghost{background:transparent;color:rgba(205,90,40,1)!important;border:2px solid rgba(205,90,40,1);padding:13px 28px}
.lhr-ghost:hover{background:rgba(205,90,40,.08)}
.lhr-attr{text-align:center;font-size:12px;color:rgba(26,26,26,.5);margin:18px 0 0}
</style>`;

// The original Simvoly testimonial blocks these sections replace.
const TARGETS = {
  "pages/index.html": { page: "home", container: "container-widget-1633014007450" },
  "pages/about-us.html": { page: "about", container: "container-widget-1730675677246" },
};

function outerDiv(html, id) {
  const at = html.indexOf(`id="${id}"`);
  if (at < 0) return null;
  const start = html.lastIndexOf("<div", at);
  const re = /<(\/?)div\b[^>]*>/g;
  re.lastIndex = start;
  let depth = 0, m;
  while ((m = re.exec(html))) {
    depth += m[1] ? -1 : 1;
    if (depth === 0) return [start, re.lastIndex];
  }
  throw new Error("unbalanced divs around " + id);
}

for (const [file, { page, container }] of Object.entries(TARGETS)) {
  let html = readFileSync(file, "utf8");
  const inner = renderReviews({ source: "static", reviews: FALLBACK[page] }, { limit: 4 });
  const section = `<section data-lh-reviews="${page}" aria-label="Customer reviews">${inner}</section>`;

  const existing = /<section data-lh-reviews="[^"]*"[^>]*>[\s\S]*?<\/section><!--\/lhr-->/;
  if (existing.test(html)) {
    html = html.replace(existing, section + "<!--/lhr-->");
  } else {
    const span = outerDiv(html, container);
    if (!span) throw new Error(`${file}: original testimonials block not found`);
    html = html.slice(0, span[0]) + section + "<!--/lhr-->" + html.slice(span[1]);
  }

  html = html.replace(/<style id="lhr-style">[\s\S]*?<\/style>\n?/, "");
  html = html.replace("</head>", STYLE + "\n</head>");
  writeFileSync(file, html);
  console.log("updated", file);
}
