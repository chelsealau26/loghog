"""Adds/refreshes the "Areas we serve" section on the homepage and the
areaServed list in each page's structured data.

Keep AREAS in sync with the service areas on the Google Business Profile.
Run from the repo root:  python3 scripts/service-areas.py
"""
import json
import re
from pathlib import Path

AREAS = [
    "Pensacola", "West Pensacola", "Pensacola Beach", "Gulf Breeze", "Perdido Key",
    "Warrington", "Myrtle Grove", "Bellview", "Brent", "Ensley", "Ferry Pass",
    "Gonzalez", "Cantonment", "Muscogee", "McDavid", "Goulding", "Seminole",
    "Pace", "Milton", "Lillian, AL",
]


def full(name):
    return name if "," in name else f"{name}, FL"


STYLE = """<style id="lha-style">
.lha{padding:56px 16px;background:rgba(23,17,14,1);color:#fff;font-family:'Open Sans',Arial,sans-serif;text-align:center}
.lha-wrap{max-width:1000px;margin:0 auto}
.lha-wrap>*{width:100%;box-sizing:border-box}
.lha-wrap>.lha-cta{width:auto}
.lha .lha-eyebrow{color:rgba(244,106,45,1)!important;font-size:14px;font-weight:700;letter-spacing:2px;margin:0 0 8px}
.lha h2{color:#fff;font-size:34px;line-height:1.2;font-weight:700;margin:0 0 12px}
.lha p{color:rgba(255,255,255,.8);font-size:16px;line-height:1.6;margin:0 auto 26px;max-width:640px}
.lha ul{list-style:none;margin:0 0 30px;padding:0;display:flex;flex-wrap:wrap;justify-content:center;gap:10px}
.lha li{border:1px solid rgba(255,255,255,.25);border-radius:999px;padding:8px 16px;font-size:15px;color:#fff}
.lha-cta{display:inline-block;background:rgba(205,90,40,1);color:#fff!important;text-decoration:none;font-weight:700;letter-spacing:1px;font-size:15px;padding:15px 30px;border-radius:6px}
.lha-cta:hover{background:rgba(244,106,45,1)}
@media(max-width:600px){.lha h2{font-size:26px}.lha li{font-size:14px;padding:7px 13px}}
</style>"""

SECTION = (
    '<section class="lha" aria-labelledby="lha-title"><div class="lha-wrap">'
    '<p class="lha-eyebrow">AREAS WE SERVE</p>'
    '<h2 id="lha-title">Tree Service in Pensacola &amp; Surrounding Areas</h2>'
    "<p>Tree removal, trimming, storm cleanup and stump grinding across Escambia and Santa Rosa counties "
    "and nearby Alabama. Not sure if we cover your street? Just ask.</p>"
    "<ul>" + "".join(f"<li>{a}</li>" for a in AREAS) + "</ul>"
    '<a class="lha-cta" href="/contact">GET YOUR FREE QUOTE</a>'
    "</div></section><!--/lha-->"
)

pages = Path("pages")

# Homepage section, placed right after the reviews
f = pages / "index.html"
s = f.read_text()
s = re.sub(r'<section class="lha".*?<!--/lha-->', "", s, flags=re.S)
s = re.sub(r'<style id="lha-style">.*?</style>\n?', "", s, flags=re.S)
assert s.count("<!--/lhr-->") == 1
s = s.replace("<!--/lhr-->", "<!--/lhr-->" + SECTION, 1)
s = s.replace("</head>", STYLE + "\n</head>", 1)
f.write_text(s)

# Structured data on every page
area_served = [{"@type": "AdministrativeArea", "name": "Escambia County, FL"},
               {"@type": "AdministrativeArea", "name": "Santa Rosa County, FL"}]
area_served += [{"@type": "City", "name": full(a)} for a in AREAS]
for name in ["index.html", "about-us.html", "contact.html"]:
    f = pages / name
    s = f.read_text()
    m = re.search(r'(<script type="application/ld\+json" id="lh-schema">)(.*?)(</script>)', s, re.S)
    data = json.loads(m.group(2))
    data["areaServed"] = area_served
    s = s[: m.start(2)] + json.dumps(data, ensure_ascii=False) + s[m.end(2):]
    f.write_text(s)
    print("updated", name)
