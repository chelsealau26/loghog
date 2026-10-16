"""Builds the Log Hog Tree Service website into ./pages.

Edit the content below, then run from the repo root:
    python3 scripts/build_site.py

Pages are plain HTML (fast, no frameworks). Live Google reviews are added by
the Cloudflare Worker (src/index.js) into the [data-lh-reviews] sections.
"""
import json
import re
import shutil
import subprocess
from datetime import date
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "pages"
SITE = "https://loghogtreeservice.com"
TODAY = date.today().isoformat()

BIZ = {
    "name": "Log Hog Tree Service",
    "phone_display": "(850) 426-4220",
    "phone_e164": "+18504264220",
    "hours": "Mon–Sat, 8am–5pm",
    "maps": "https://maps.google.com/?cid=3271970089992802073",
    "review": "https://g.page/r/CRlPuRF2X2gtEBM/review",
    "facebook": "https://www.facebook.com/profile.php?id=100085501815881",
    "instagram": "https://www.instagram.com/log_hog_tree_debris/",
}
SMS_BASE = "sms:+18504264220?&body="
SMS = SMS_BASE + "Hi%20Log%20Hog%21%20I%27d%20like%20a%20free%20quote.%20My%20address%20is%3A%20"
TEL = "tel:+18504264220"

# Keep in sync with the Google Business Profile service areas.
AREAS = [
    "Pensacola", "West Pensacola", "Pensacola Beach", "Gulf Breeze", "Perdido Key",
    "Warrington", "Myrtle Grove", "Bellview", "Brent", "Ensley", "Ferry Pass",
    "Gonzalez", "Cantonment", "Muscogee", "McDavid", "Goulding",
    "Pace", "Milton", "Lillian, AL", "Seminole, AL",
]

ICON = {
    "phone": '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M6.6 10.8a15.1 15.1 0 0 0 6.6 6.6l2.2-2.2c.3-.3.7-.4 1-.2 1.1.4 2.3.6 3.6.6.6 0 1 .4 1 1V20c0 .6-.4 1-1 1A17 17 0 0 1 3 4c0-.6.4-1 1-1h3.5c.6 0 1 .4 1 1 0 1.3.2 2.5.6 3.6.1.3 0 .7-.2 1z"/></svg>',
    "text": '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M4 3h16a2 2 0 0 1 2 2v11a2 2 0 0 1-2 2H8l-4.6 3.7A.9.9 0 0 1 2 21V5c0-1.1.9-2 2-2zm3.5 6.5a1.5 1.5 0 1 0 0 3 1.5 1.5 0 0 0 0-3zm4.5 0a1.5 1.5 0 1 0 0 3 1.5 1.5 0 0 0 0-3zm4.5 0a1.5 1.5 0 1 0 0 3 1.5 1.5 0 0 0 0-3z"/></svg>',
    "shield": '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M12 2 4 5v6c0 5 3.4 9.7 8 11 4.6-1.3 8-6 8-11V5l-8-3zm-1.2 14.2-3.5-3.5 1.4-1.4 2.1 2.1 4.6-4.6 1.4 1.4-6 6z"/></svg>',
    "flag": '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M5 2h2v20H5V2zm3 1h11l-2.5 4.5L19 12H8V3z"/></svg>',
    "star": '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="m12 2 2.9 6.6 7.1.6-5.4 4.7 1.6 7L12 17.3 5.8 21l1.6-7L2 9.2l7.1-.6L12 2z"/></svg>',
    "menu": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M3 6h18M3 12h18M3 18h18" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"/></svg>',
    "camera": '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M9 3 7.2 5H4a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2h-3.2L15 3H9zm3 5a5 5 0 1 1 0 10 5 5 0 0 1 0-10zm0 2a3 3 0 1 0 0 6 3 3 0 0 0 0-6z"/></svg>',
    "chat": '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M12 2C6.5 2 2 6 2 10.9c0 2.6 1.3 5 3.4 6.6L4.6 22l4.6-2.6c.9.2 1.8.3 2.8.3 5.5 0 10-4 10-8.8S17.5 2 12 2zm-1 13-4-4 1.4-1.4 2.6 2.6 5.6-5.6L18 8l-7 7z"/></svg>',
    "home": '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M12 3 2 11.5l1.3 1.5L5 11.6V21h5v-6h4v6h5v-9.4l1.7 1.4 1.3-1.5L12 3z"/></svg>',
    "pin": '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M12 2a7 7 0 0 0-7 7c0 5.2 7 13 7 13s7-7.8 7-13a7 7 0 0 0-7-7zm0 9.5A2.5 2.5 0 1 1 12 6.5a2.5 2.5 0 0 1 0 5z"/></svg>',
    "facebook": '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M24 12a12 12 0 1 0-13.9 11.9v-8.4h-3V12h3V9.4c0-3 1.8-4.7 4.5-4.7 1.3 0 2.7.2 2.7.2v3h-1.5c-1.5 0-2 .9-2 1.9V12h3.4l-.5 3.5h-2.9v8.4A12 12 0 0 0 24 12z"/></svg>',
    "instagram": '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M12 2.2c3.2 0 3.6 0 4.8.1 3.3.1 4.8 1.7 4.9 4.9.1 1.3.1 1.6.1 4.8s0 3.6-.1 4.8c-.1 3.2-1.7 4.8-4.9 4.9-1.3.1-1.6.1-4.8.1s-3.6 0-4.8-.1c-3.3-.1-4.8-1.7-4.9-4.9C2.2 15.6 2.2 15.2 2.2 12s0-3.6.1-4.8C2.4 3.9 3.9 2.4 7.2 2.3 8.4 2.2 8.8 2.2 12 2.2zM12 0C8.7 0 8.3 0 7.1.1 2.7.3.3 2.7.1 7.1 0 8.3 0 8.7 0 12s0 3.7.1 4.9c.2 4.4 2.6 6.8 7 7 1.2.1 1.6.1 4.9.1s3.7 0 4.9-.1c4.4-.2 6.8-2.6 7-7 .1-1.2.1-1.6.1-4.9s0-3.7-.1-4.9c-.2-4.4-2.6-6.8-7-7C15.7 0 15.3 0 12 0zm0 5.8a6.2 6.2 0 1 0 0 12.4 6.2 6.2 0 0 0 0-12.4zM12 16a4 4 0 1 1 0-8 4 4 0 0 1 0 8zm6.4-11.8a1.4 1.4 0 1 0 0 2.9 1.4 1.4 0 0 0 0-2.9z"/></svg>',
    "clock": '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20zm1 10.4 3.6 2.1-1 1.7L11 13V6h2z"/></svg>',
    "play": '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M7 4v16l13-8z"/></svg>',
}


def img(name, alt, sizes, widths, *, cls="", eager=False, w=None, h=None):
    srcset = ", ".join(f"/img/{name}-{x}.webp {x}w" for x in widths)
    attrs = f' class="{cls}"' if cls else ""
    load = ' fetchpriority="high"' if eager else ' loading="lazy" decoding="async"'
    dims = f' width="{w}" height="{h}"' if w and h else ""
    return (f'<img src="/img/{name}-{widths[0]}.webp" srcset="{srcset}" sizes="{sizes}" '
            f'alt="{escape(alt)}"{dims}{attrs}{load}>')


# ---------------------------------------------------------------- services
SERVICES = [
    {
        "slug": "tree-removal",
        "name": "Tree removal",
        "title": "Tree Removal in Pensacola, FL",
        "short": "Dead, leaning or unwanted trees taken down safely, with the mess hauled away.",
        "lede": "Dead, leaning, storm-damaged or just in the way: we take trees down piece by piece, drop them where they need to go, and haul it all away.",
        "photo": ("pine-removal-climb", "Log Hog climbing a tall pine to take it down in sections", [480, 900]),
        "body": """
<h2>When a tree needs to come down</h2>
<p>Most removals we do around Pensacola fall into a few groups:</p>
<ul>
<li><strong>Dead or dying trees.</strong> Pines hit by beetles, oaks rotting at the base, anything with large dead limbs. Dead wood gets brittle fast in our heat and humidity.</li>
<li><strong>Trees leaning toward something.</strong> A house, a fence, a driveway or power lines. A new lean after a storm is worth a look right away.</li>
<li><strong>Trees that have outgrown the spot.</strong> Roots lifting a slab, branches rubbing the roof, or a tree that blocks the view or the sun for a garden.</li>
<li><strong>Clearing for a project.</strong> A pool, an addition, a shed or a new fence line.</li>
</ul>
<h2>How we take a tree down</h2>
<p>Very few yards in Pensacola have room to drop a whole tree at once, so we usually climb it and take it down in sections, lowering limbs and trunk pieces with ropes so nothing lands on the house, the fence or the flower beds. As one customer put it, Dave “dropped the branches and tree right where he said he would.”</p>
<p>Once the tree is down, we cut up the wood, haul off the branches and debris, and rake up so the yard is clean when we leave.</p>
<h2>What's included</h2>
<ul class="checks">
<li>A free quote, with no obligation</li>
<li>Careful sectional takedown near homes, fences and lines</li>
<li>Cleanup and hauling of branches and debris</li>
<li>Stump grinding available in the same visit if you want the stump gone too</li>
<li>Licensed and insured work</li>
</ul>
<h2>Getting a quote</h2>
<p>Text a photo of the whole tree and your address to <a href="{SMS}">(850) 426-4220</a>. A second photo of the base and of anything it's close to (house, fence, wires) shows us exactly which tree you mean. Sometimes that's enough for a price. Most of the time we'll stop by to look at it in person, then text or call you back with a free quote.</p>
""",
        "faq": [
            ("Do I need a permit to remove a tree in Pensacola?", "Some trees do, depending on where you live and the type and size of the tree. Rules differ between the City of Pensacola, Escambia County and Santa Rosa County. Ask us when you send your photos and we'll tell you what we know, but check with your city or county before work starts."),
            ("Will you remove the stump too?", "Yes, if you want it gone. We can grind the stump below ground level in the same visit. Just mention it when you ask for your quote."),
            ("Can you take down a tree near my house or power lines?", "Trees near houses and fences are routine: we take them down in sections and lower the pieces. If a tree is touching or tangled in power lines, the utility may need to make it safe first. Send a photo and we'll tell you."),
        ],
    },
    {
        "slug": "tree-trimming",
        "name": "Tree trimming & pruning",
        "title": "Tree Trimming & Pruning in Pensacola, FL",
        "short": "Dead wood out, roof and power-line clearance, and a healthier, better-looking canopy.",
        "lede": "Regular trimming keeps your trees healthy, keeps branches off the roof, and takes out the dead wood before a storm does it for you.",
        "photo": ("tree-trimming-climb", "Log Hog climbing a backyard tree to trim it", [480, 900]),
        "body": """
<h2>Why trim your trees</h2>
<ul>
<li><strong>Storm prep.</strong> Dead and weak limbs are the first things to come down in a summer thunderstorm or a hurricane. Taking them out ahead of time is cheaper than cleaning them off your roof.</li>
<li><strong>Clearance.</strong> Branches rubbing the roof, hanging over the driveway or growing into lines.</li>
<li><strong>Tree health.</strong> Removing dead, diseased and crossing branches lets light and air through the canopy.</li>
<li><strong>Looks.</strong> A trimmed live oak or magnolia makes the whole yard look cared for.</li>
</ul>
<h2>How we trim</h2>
<p>We climb the tree and make clean cuts at the right spots, so the tree can seal over the wounds and keep its natural shape. We don't “top” trees: cutting the top off a tree leaves weak regrowth and usually shortens its life.</p>
<p>When we're done, we haul away the branches and clean up the yard.</p>
<h2>What's included</h2>
<ul class="checks">
<li>Dead wood removal and thinning</li>
<li>Roof, driveway and house clearance</li>
<li>Shaping for live oaks, magnolias, crepe myrtles and more</li>
<li>Bushes and shrubs trimmed while we're there</li>
<li>Cleanup and hauling of everything we cut</li>
</ul>
<p>Have several trees? Send photos of each one. One customer in Navarre had seven trees trimmed in a single visit.</p>
""",
        "faq": [
            ("When is the best time to trim trees in Pensacola?", "Most trees can be trimmed any time of year here. Many people schedule it in late winter or spring, before hurricane season starts in June. Dead or hanging limbs should come down as soon as you notice them."),
            ("How often should trees be trimmed?", "Every few years is typical for most yard trees. Fast growers, and trees close to the house, may need it more often."),
            ("Do you top trees?", "No. Topping leaves weak, fast regrowth that breaks easily and stresses the tree. We thin and reduce the canopy with proper cuts instead."),
        ],
    },
    {
        "slug": "stump-grinding",
        "name": "Stump grinding",
        "title": "Stump Grinding in Pensacola, FL",
        "short": "Stumps ground down below ground level so you can mow, plant or build over the spot.",
        "lede": "That old stump is a trip hazard, a mower-blade killer and a home for termites. We grind it down below ground level so the spot can go back to lawn.",
        "photo": ("stump-ready-to-grind", "A freshly cut stump ready for grinding", [480, 900]),
        "body": """
<h2>Why grind a stump</h2>
<ul>
<li>Stumps get in the way of mowing and landscaping, and they're easy to trip over.</li>
<li>Rotting stumps attract termites and other wood-boring insects.</li>
<li>Some trees keep sending up sprouts from the stump and roots.</li>
<li>You want to plant, lay sod or build where the tree used to be.</li>
</ul>
<h2>How it works</h2>
<p>A stump grinder chews the stump and the top of the main roots into wood chips, down below the surface. What's left is a patch of chips and soil you can fill with topsoil and seed or sod.</p>
<p>Already have a stump from an old removal or a tree that fell in a storm? We grind stumps on their own too. One customer had a large stump from a fallen oak “cut up and grinded down flat in no time.”</p>
<h2>What's included</h2>
<ul class="checks">
<li>Grinding below ground level</li>
<li>Surface roots near the stump ground down as well</li>
<li>Chips left as mulch or cleaned up, your choice (ask when you get your quote)</li>
<li>Several stumps? Send them all and we'll quote them together</li>
</ul>
<h2>Getting a quote</h2>
<p>Text a photo of each stump with something for scale (a shoe or a tape measure works) and your address. Let us know if there's a gate and how wide it is.</p>
""",
        "faq": [
            ("How deep do you grind?", "Below ground level, deep enough for grass or new plantings. If you plan to build or pour concrete over the spot, tell us and we'll talk about it."),
            ("What happens to the roots?", "The stump and the top of the main roots get ground up. The rest of the roots stay in the ground and break down naturally over time."),
            ("Can you get a grinder through my gate?", "Usually, yes. Measure your gate opening and send it with your photos so we can plan for it."),
        ],
    },
    {
        "slug": "storm-cleanup",
        "name": "Storm cleanup",
        "title": "Storm Cleanup & Fallen Tree Removal in Pensacola, FL",
        "short": "Fallen trees, hanging limbs and storm debris cleared after hurricanes and summer storms.",
        "lede": "After a hurricane or a summer thunderstorm, we clear fallen trees, take down hanging limbs and haul off the debris, so you can get back to normal.",
        "photo": ("storm-damaged-oak", "A large oak limb that split and fell beside a house after a storm", [480, 900]),
        "body": """
<h2>What we handle after a storm</h2>
<ul>
<li>Trees down across yards, driveways and fences</li>
<li>Limbs hanging in the canopy that could still fall</li>
<li>Split, cracked or newly leaning trees that need to come down</li>
<li>Branches and debris piled across the yard</li>
<li>Stumps left behind by uprooted trees</li>
</ul>
<h2>Stay safe first</h2>
<ul>
<li>Stay away from any tree or limb touching a power line, and call FPL or your electric co-op.</li>
<li>Don't stand under hanging or cracked limbs. They can fall without warning.</li>
<li>If a tree is on your house, take photos for your insurance company before anything is moved.</li>
</ul>
<h2>How to get on the schedule</h2>
<p>Text photos of the damage and your address to <a href="{SMS}">(850) 426-4220</a>. Photos show us what we're dealing with and help us plan the visit, which matters when everyone's phone is ringing after a storm. We'll come take a look, then text or call you back with a free quote.</p>
<p>Want to avoid the storm damage in the first place? <a href="/services/tree-trimming">Trimming out dead and weak limbs</a> before hurricane season is the best prevention.</p>
""",
        "faq": [
            ("Do you work with insurance claims?", "We can give you a written quote and photos of the job for your insurance company. Coverage is between you and your insurer, so check your policy."),
            ("Can you remove a tree that fell on my house?", "Send photos first. If it's on the roof, we'll tell you what it takes to get it off safely. Don't try to cut it yourself."),
            ("How soon can you come after a storm?", "It depends on how many calls come in. Texting photos is the fastest way to get a quote and a spot on the schedule."),
        ],
    },
    {
        "slug": "palm-tree-trimming",
        "name": "Palm & bush trimming",
        "title": "Palm Tree & Bush Trimming in Pensacola, FL",
        "short": "Dead fronds and seed pods cut back, bushes and shrubs shaped.",
        "lede": "Brown fronds and seed pods make a palm look tired. We trim palms back to healthy green and shape your bushes and shrubs while we're there.",
        "photo": ("before-after-palm-trim", "A palm tree before and after trimming", [480, 900]),
        "body": """
<h2>Palm trimming</h2>
<p>We cut off dead and dying fronds, seed pods and flower stalks, which keeps palms looking clean and stops heavy fronds from dropping on cars, roofs and people. We leave the healthy green fronds alone: over-trimming (the “hurricane cut”) weakens palms.</p>
<h2>Palm skinning, only if you want it</h2>
<p>Skinning removes the old frond bases (the “boots”) for a smooth trunk. We don't skin palms as part of a normal trim. If you're interested, just ask and we'll talk it through with you before any work starts.</p>
<h2>Bushes and shrubs</h2>
<p>We shape overgrown hedges, bushes and shrubs and cut back anything crowding the house, walkways or windows.</p>
<h2>What's included</h2>
<ul class="checks">
<li>Dead frond, seed pod and flower stalk removal</li>
<li>Trunk skinning only if we've agreed on it ahead of time</li>
<li>Hedge, bush and shrub shaping</li>
<li>Cleanup and hauling of everything we cut</li>
</ul>
""",
        "faq": [
            ("How often should palms be trimmed?", "Most palms look best with a trim once or twice a year. Trimming out seed pods before they drop saves a lot of mess."),
            ("Is it bad to cut off green fronds?", "Yes. Palms feed through their green fronds, so we leave them on. We only remove dead, dying and hanging fronds unless they're in the way."),
            ("Do you trim tall palms?", "Yes. Send a photo and let us know roughly how tall it is."),
            ("Do you skin palm trunks?", "Only if you ask for it and we agree on it ahead of time. It's not part of a normal palm trim."),
        ],
    },
    {
        "slug": "debris-hauling",
        "name": "Debris hauling",
        "title": "Brush & Debris Hauling in Pensacola, FL",
        "short": "Branches, brush piles and yard debris loaded up and hauled away.",
        "lede": "Got a brush pile from a weekend of yard work, or limbs from the last storm? We load it up and haul it away.",
        "photo": ("debris-trailer", "Log Hog dump trailer loaded with branches and palm fronds", [480, 900]),
        "body": """
<h2>What we haul</h2>
<ul>
<li>Branches and limbs, whole or cut up</li>
<li>Brush piles and yard waste</li>
<li>Logs and trunk sections</li>
<li>Storm debris</li>
<li>Palm fronds</li>
</ul>
<p>Cleanup is always included with our <a href="/services/tree-removal">tree removal</a>, <a href="/services/tree-trimming">trimming</a> and <a href="/services/palm-tree-trimming">palm</a> work. This service is for debris you already have on the ground.</p>
<h2>Getting a quote</h2>
<p>Text a photo of the pile and your address. A rough idea of the size (or something in the photo for scale) helps us quote it accurately.</p>
""",
        "faq": [
            ("Do you haul anything besides yard debris?", "We focus on trees, branches and yard debris. Ask about anything else when you text us."),
            ("Do I need to cut the branches up first?", "No. We can load them as they are."),
        ],
    },
]


# ---------------------------------------------------------------- shared parts
def schema_business():
    return {
        "@context": "https://schema.org",
        "@type": ["LocalBusiness", "HomeAndConstructionBusiness"],
        "@id": f"{SITE}/#business",
        "name": BIZ["name"],
        "url": f"{SITE}/",
        "logo": f"{SITE}/img/logo-192.png",
        "image": [f"{SITE}/img/og-image.jpg", f"{SITE}/img/dave-climbing-oak-880.webp"],
        "telephone": BIZ["phone_e164"],
        "description": "Christian and veteran-owned, licensed and insured tree service in Pensacola, FL: tree removal, trimming and pruning, storm cleanup, palm and bush trimming, stump grinding, and debris hauling.",
        "founder": {"@type": "Person", "name": "Dave Lau"},
        "address": {"@type": "PostalAddress", "addressLocality": "Pensacola", "addressRegion": "FL", "addressCountry": "US"},
        "areaServed": [{"@type": "AdministrativeArea", "name": "Escambia County, FL"},
                       {"@type": "AdministrativeArea", "name": "Santa Rosa County, FL"}]
                      + [{"@type": "City", "name": a if "," in a else f"{a}, FL"} for a in AREAS],
        "openingHoursSpecification": [{
            "@type": "OpeningHoursSpecification",
            "dayOfWeek": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"],
            "opens": "08:00", "closes": "17:00"}],
        "hasMap": BIZ["maps"],
        "sameAs": [BIZ["facebook"], BIZ["instagram"], BIZ["maps"]],
        "hasOfferCatalog": {"@type": "OfferCatalog", "name": "Tree services", "itemListElement": [
            {"@type": "Offer", "itemOffered": {"@type": "Service", "name": s["name"].capitalize(),
                                               "url": f"{SITE}/services/{s['slug']}"}} for s in SERVICES]},
    }


def schema_breadcrumbs(trail):
    return {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": i + 1, "name": n, "item": f"{SITE}{u}"} for i, (n, u) in enumerate(trail)]}


def schema_faq(faq):
    return {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faq]}


def crumbs_html(trail):
    items = "".join(
        f'<li><a href="{u}">{escape(n)}</a></li>' if i < len(trail) - 1 else f'<li aria-current="page">{escape(n)}</li>'
        for i, (n, u) in enumerate(trail))
    return f'<nav class="crumbs" aria-label="Breadcrumb"><ol>{items}</ol></nav>'


NAV = [("Services", "/#services"), ("About us", "/about-us"), ("Service areas", "/service-areas"), ("Contact", "/contact")]
ARROW = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>'


def header(current):
    links = "".join(
        f'<a href="{u}"{" aria-current=page" if u == current else ""}>{n}</a>' for n, u in NAV)
    return f"""<a class="skip" href="#main">Skip to content</a>
<div class="topbar"><div class="wrap"><span>Veteran-owned · Licensed &amp; insured</span><div class="tb-right"><a href="{TEL}">Call or text <strong>{BIZ["phone_display"]}</strong></a><span class="tb-social"><a class="soc fb" href="{BIZ["facebook"]}" rel="noopener" aria-label="Log Hog on Facebook">{ICON["facebook"]}</a><a class="soc ig" href="{BIZ["instagram"]}" rel="noopener" aria-label="Log Hog on Instagram">{ICON["instagram"]}</a></span></div></div></div>
<header class="site-header"><div class="wrap">
<a class="brand" href="/"><img src="/img/logo-192.webp" width="84" height="84" alt="Log Hog Tree Service, home"></a>
<nav class="nav" id="nav" aria-label="Main">{links}</nav>
<a class="head-call" href="{TEL}">{BIZ["phone_display"]}</a>
<a class="btn btn-primary" href="{SMS}">Text for a free quote</a>
<button class="menu-btn" aria-controls="nav" aria-expanded="false" aria-label="Menu">{ICON["menu"]}</button>
</div></header>"""


def footer():
    svc = "".join(f'<li><a href="/services/{s["slug"]}">{escape(s["name"].capitalize())}</a></li>' for s in SERVICES)
    return f"""<footer class="site-footer"><div class="wrap">
<div class="foot-brand"><a class="foot-logo" href="/" aria-label="Log Hog Tree Service, home"><img src="/img/logo-192.webp" width="112" height="112" alt="Log Hog Tree Service logo" loading="lazy"></a>
<p>Veteran-owned tree care for Pensacola and our neighbors nearby, one yard at a time.</p></div>
<div><h2>Services</h2><ul>{svc}</ul></div>
<div><h2>Log Hog</h2><ul><li><a href="/about-us">About us</a></li><li><a href="/service-areas">Where we work</a></li><li><a href="/contact">Get a free quote</a></li><li><a href="{BIZ["review"]}" rel="noopener">Leave us a review</a></li></ul></div>
<div><h2>Say hello</h2><ul>
<li><a href="{TEL}">{BIZ["phone_display"]}</a>, call or text</li>
<li>{BIZ["hours"]}</li>
<li class="foot-social"><a class="soc-btn fb" href="{BIZ["facebook"]}" rel="noopener">{ICON["facebook"]}Facebook</a><a class="soc-btn ig" href="{BIZ["instagram"]}" rel="noopener">{ICON["instagram"]}Instagram</a></li>
</ul></div>
<p class="foot-legal">© {date.today().year} Log Hog Tree Service, Pensacola, Florida. Licensed and insured.</p>
</div></footer>
<dialog class="vbox" aria-label="Time-lapse video"><button type="button" class="vbox-x" aria-label="Close">&times;</button><video controls playsinline preload="none"></video></dialog>
{STORM_POPUP}
<div class="mobile-bar"><a class="btn btn-quiet" href="{TEL}">{ICON["phone"]}Call</a><a class="btn btn-primary" href="{SMS}">{ICON["text"]}Text a photo</a></div>
<script>
(function(){{var m=document.querySelector('.masthead');if(document.body.classList.contains('home')&&m){{var on=function(){{m.classList.toggle('stuck',window.scrollY>140)}};window.addEventListener('scroll',on,{{passive:true}});on()}}
var b=document.querySelector('.menu-btn'),n=document.getElementById('nav');if(b)b.addEventListener('click',function(){{var o=n.classList.toggle('open');b.setAttribute('aria-expanded',o)}});
document.querySelectorAll('.ba-range').forEach(function(r){{var f=r.parentNode;var set=function(){{f.style.setProperty('--pos',r.value+'%')}};r.addEventListener('input',set);set()}});
var pk=document.querySelector('[data-picker]');if(pk){{var base='{SMS_BASE}';var chips=pk.querySelectorAll('.chip');var note=pk.querySelector('.picker-note');
var upd=function(){{var sel=[].map.call(pk.querySelectorAll('.chip[aria-pressed=true]'),function(c){{return c.dataset.pick}});
var lst=sel.length>1?sel.slice(0,-1).join(', ')+' and '+sel[sel.length-1]:sel[0];var msg=sel.length?"Hi Log Hog! I'd like a free quote for "+lst+'. My address is: ':"Hi Log Hog! I'd like a free quote. My address is: ";
document.querySelectorAll('a[href^="sms:"]:not([data-fixed])').forEach(function(a){{a.href=base+encodeURIComponent(msg)}});var pv=pk.querySelector('[data-preview]');if(pv){{pv.textContent=msg;pv.classList.remove('pop');void pv.offsetWidth;pv.classList.add('pop')}}
note.textContent=sel.length?'Got it: '+lst+'. Tap Text us a photo and add your picture.':"Tap what you need and we'll start the text for you. Just add a photo."}};
chips.forEach(function(c){{c.addEventListener('click',function(){{c.setAttribute('aria-pressed',c.getAttribute('aria-pressed')!=='true');upd()}})}});if(pk.querySelector('.chip[aria-pressed=true]'))upd()}}
var rv=document.querySelectorAll('[data-reveal]');if('IntersectionObserver' in window){{var io=new IntersectionObserver(function(es){{es.forEach(function(e){{if(e.isIntersecting){{e.target.classList.add('in');io.unobserve(e.target)}}}})}},{{threshold:.3}});rv.forEach(function(el){{io.observe(el)}})}}else rv.forEach(function(el){{el.classList.add('in')}});
document.querySelectorAll('.areas-sec').forEach(function(sec){{var hi=function(k,on){{sec.querySelectorAll('[data-area="'+k+'"]').forEach(function(el){{el.classList.toggle('on',on)}})}};
sec.querySelectorAll('[data-area]').forEach(function(el){{var k=el.dataset.area;['mouseenter','focus'].forEach(function(ev){{el.addEventListener(ev,function(){{hi(k,true)}})}});['mouseleave','blur'].forEach(function(ev){{el.addEventListener(ev,function(){{hi(k,false)}})}});
el.addEventListener('click',function(){{sec.querySelectorAll('.on').forEach(function(o){{o.classList.remove('on')}});hi(k,true)}})}})}});
var vb=document.querySelector('.vbox');if(vb){{var vv=vb.querySelector('video');var shut=function(){{vv.pause();vv.removeAttribute('src');vv.load();if(vb.open)vb.close()}};
document.querySelectorAll('[data-video]').forEach(function(t){{t.addEventListener('click',function(){{vv.src=t.dataset.video;var im=t.querySelector('img');if(im)vv.poster=im.currentSrc||im.src;else vv.removeAttribute('poster');vb.showModal();var p=vv.play();if(p&&p.catch)p.catch(function(){{}})}})}});
vb.querySelector('.vbox-x').addEventListener('click',shut);vb.addEventListener('click',function(e){{if(e.target===vb)shut()}});vb.addEventListener('close',function(){{vv.pause()}})}}
var sd=document.querySelector('dialog.storm');if(sd){{var K='lh-storm-dismissed',now=Date.now(),seen=0;try{{seen=+localStorage.getItem(K)||0}}catch(e){{}}
if(now<Date.parse(sd.dataset.until)&&now-seen>3*864e5&&sd.showModal){{setTimeout(function(){{if(!document.querySelector('dialog[open]'))sd.showModal()}},1800)}}
var sclose=function(){{try{{localStorage.setItem(K,String(Date.now()))}}catch(e){{}}if(sd.open)sd.close()}};
sd.querySelector('.storm-x').addEventListener('click',sclose);sd.addEventListener('click',function(e){{if(e.target===sd)sclose()}});sd.addEventListener('cancel',function(){{try{{localStorage.setItem(K,String(Date.now()))}}catch(e){{}}}});
sd.querySelectorAll('a').forEach(function(a){{a.addEventListener('click',function(){{try{{localStorage.setItem(K,String(Date.now()))}}catch(e){{}}}})}})}}
document.querySelectorAll('[data-yt]').forEach(function(v){{v.addEventListener('click',function(){{v.innerHTML='<iframe src="https://www.youtube-nocookie.com/embed/'+v.dataset.yt+'?autoplay=1" title="'+v.getAttribute('aria-label')+'" allow="autoplay; encrypted-media; picture-in-picture" allowfullscreen></iframe>'}},{{once:true}})}})}})();
</script>"""


FONTS = "https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700;800&display=swap"


def page(path, title, description, body, *, current=None, extra_schema=(), og_image="/img/og-image.jpg", body_class=""):
    canonical = f"{SITE}{path}"
    schemas = [schema_business(), *extra_schema]
    ld = "\n".join(f'<script type="application/ld+json">{json.dumps(s, ensure_ascii=False)}</script>' for s in schemas)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape(title)}</title>
<meta name="description" content="{escape(description)}">
<link rel="canonical" href="{canonical}">
<meta name="theme-color" content="#2a1e19">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Log Hog Tree Service">
<meta property="og:title" content="{escape(title)}">
<meta property="og:description" content="{escape(description)}">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="{SITE}{og_image}">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="/favicon.ico" sizes="any">
<link rel="icon" href="/favicon.png" type="image/png">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="{FONTS}">
<link rel="stylesheet" href="/site.css?v={CSS_VERSION}">
{ld}
</head>
<body class="{body_class}">
<div class="masthead">{header(current)}</div>
<main id="main">
{body}
</main>
{footer()}
</body>
</html>
"""


RATING_FALLBACK = f'<a href="{BIZ["maps"]}" rel="noopener">Read what our neighbors say on Google</a>'


def rating_line():
    return f'<p class="rating-line"><span class="stars" aria-hidden="true">★★★★★</span><span data-lh-rating>{RATING_FALLBACK}</span></p>'


def reviews_block(page_key, limit, heading="What your <em>neighbors</em> are saying",
                  intro="Real reviews from homeowners around Pensacola.", stone=True):
    return f"""<section class="section{' stone' if stone else ''}" id="reviews"><div class="wrap">
<div class="section-head"><h2>{heading}</h2><p class="lede">{intro}</p></div>
<div data-lh-reviews="{page_key}">{FALLBACK[limit]}</div>
</div></section>"""


def band(heading="Got a tree on <em>your mind?</em>",
         text="Don't wait for the next storm to make the decision for you. Snap a photo, send it over, and we'll get back to you with a free quote."):
    return f"""<section class="band2" data-reveal>
<div class="band2-bg" aria-hidden="true"><img src="/img/hero-climb-wide-960.webp" srcset="/img/hero-climb-wide-960.webp 960w, /img/hero-climb-wide-1536.webp 1536w" sizes="100vw" alt="" loading="lazy" decoding="async"></div>
<div class="wrap band2-inner">
<h2>{heading}</h2>
<p>{text}</p>
<div class="btns"><a class="btn btn-primary btn-glow" href="{SMS}">{ICON["text"]}Text us a photo</a><a class="btn btn-quiet" href="{TEL}">{ICON["phone"]}Call {BIZ["phone_display"]}</a></div>
<ul class="band2-trust"><li>{ICON["shield"]}Licensed &amp; insured</li><li>{ICON["flag"]}Veteran-owned</li><li>{ICON["star"]}{BIZ["hours"]}</li></ul>
</div>
</section>"""


AREA_LL = {
    "Pensacola": (30.421, -87.217), "West Pensacola": (30.427, -87.279), "Pensacola Beach": (30.333, -87.142),
    "Gulf Breeze": (30.357, -87.164), "Perdido Key": (30.293, -87.464), "Warrington": (30.384, -87.275),
    "Myrtle Grove": (30.421, -87.307), "Bellview": (30.462, -87.315), "Brent": (30.469, -87.236),
    "Ensley": (30.519, -87.273), "Ferry Pass": (30.510, -87.212), "Gonzalez": (30.582, -87.292),
    "Cantonment": (30.608, -87.340), "Muscogee": (30.790, -87.390), "McDavid": (30.862, -87.320),
    "Goulding": (30.443, -87.223), "Pace": (30.599, -87.161), "Milton": (30.632, -87.040),
    "Lillian, AL": (30.411, -87.437), "Seminole, AL": (30.507, -87.468),
}


MAP_C = (330, 340)
MAP_PX = 9.5  # pixels per mile


def _xy(name):
    lat, lon = AREA_LL[name]
    return MAP_C[0] + (lon + 87.217) * 59.6 * MAP_PX, MAP_C[1] - (lat - 30.421) * 69.0 * MAP_PX


def area_slug(a):
    return re.sub(r"[^a-z]+", "-", a.lower()).strip("-")


def area_chips():
    return '<ul class="area-chips">' + "".join(
        f'<li><button type="button" data-area="{area_slug(a)}">{ICON["pin"]}{escape(a)}</button></li>' for a in AREAS) + "</ul>"


MAP_LABELS = {"Pensacola", "Milton", "Perdido Key", "Gulf Breeze", "Cantonment", "McDavid", "Lillian, AL", "Pace"}


def area_map():
    cx, cy = MAP_C
    rings = "".join(f'<circle cx="{cx}" cy="{cy}" r="{m*MAP_PX:.0f}" class="ring"/>' for m in (5, 10, 15, 20, 25, 30))
    miles = "".join(f'<text x="{cx - m*MAP_PX*0.707 - 4:.0f}" y="{cy + m*MAP_PX*0.707 + 14:.0f}" text-anchor="end" class="mi">{m} mi</text>' for m in (10, 20, 30))
    dots = []
    for i, a in enumerate(AREAS):
        x, y = _xy(a)
        cls = "dot" + (" home" if a == "Pensacola" else "") + (" lbl" if a in MAP_LABELS else "")
        lab = escape(a.replace(", AL", ""))
        left = x < cx - 20
        dots.append(f'<g class="{cls}" data-area="{area_slug(a)}" style="--i:{i}" transform="translate({x:.0f} {y:.0f})"><circle r="{10 if a == "Pensacola" else 6.5}"/><text x="{-13 if left else 13}" y="5" text-anchor="{"end" if left else "start"}">{lab}</text></g>')
    return f"""<figure class="area-map" data-reveal aria-hidden="true"><svg viewBox="0 0 660 680">
<defs><radialGradient id="glow"><stop offset="0" stop-color="#ba5a34" stop-opacity=".38"/><stop offset="1" stop-color="#ba5a34" stop-opacity="0"/></radialGradient>
<clipPath id="lens"><circle cx="{cx}" cy="{cy}" r="318"/></clipPath></defs>
<g clip-path="url(#lens)">
<circle cx="{cx}" cy="{cy}" r="318" class="lens-bg"/>
<circle cx="{cx}" cy="{cy}" r="300" fill="url(#glow)"/>
<path class="gulf" d="M0 432 C90 424 150 430 210 424 S300 410 360 400 S470 392 520 386 S610 380 660 372 V680 H0Z"/>
<path class="bay" d="M250 380 C290 372 320 360 352 362 S390 350 420 356 C410 372 380 378 352 380 S290 390 250 380Z"/>
<text x="{cx}" y="560" text-anchor="middle" class="water">GULF OF MEXICO</text>
{rings}{miles}
<path class="line" d="M215 30 L218 140 L211 260 L216 404"/>
<text x="205" y="70" class="st" text-anchor="end">AL</text><text x="226" y="70" class="st">FL</text>
</g>
<circle cx="{cx}" cy="{cy}" r="318" class="lens-edge"/>
{"".join(dots)}
</svg></figure>"""


def areas_list():
    return '<ul class="areas">' + "".join(f"<li>{escape(a)}</li>" for a in AREAS) + "</ul>"


TOWN_SMS = SMS_BASE + __import__("urllib.parse").parse.quote("Hi Log Hog! I don't see my town on your list of service areas, but I'd like a free quote here. My address is: ")


STORM_SMS = SMS_BASE + __import__("urllib.parse").parse.quote("Hi Log Hog! I have tree damage from Hurricane Isaias. My address is: ")
STORM_UNTIL = "2026-11-01T00:00:00-05:00"  # popup stops showing at midnight Nov 1 (Central)

STORM_POPUP = f"""<dialog class="storm" aria-labelledby="storm-h" data-until="{STORM_UNTIL}">
<button type="button" class="storm-x" aria-label="Close">&times;</button>
<div class="storm-img">{img("storm-damaged-oak", "", "(max-width: 600px) 100vw, 260px", [480], w=480, h=360)}<span class="storm-tag">Hurricane Isaias</span></div>
<div class="storm-body">
<p class="storm-k">Storm cleanup</p>
<h2 id="storm-h">Trees down from <em>Isaias?</em></h2>
<p>We're helping neighbors around Pensacola with fallen trees, hanging limbs and storm debris. Text us a photo and your address and we'll get you on the list.</p>
<div class="btns"><a class="btn btn-primary" href="{STORM_SMS}" data-fixed>{ICON["text"]}Text us a photo</a><a class="btn btn-quiet" href="{TEL}">{ICON["phone"]}Call {BIZ["phone_display"]}</a></div>
<p class="storm-safe">If a tree is on a power line, stay clear and call your power company first.</p>
</div>
</dialog>"""


def faq_cta(q, a):
    ql, al = q.lower(), a.lower()
    text_btn = f'<a class="btn btn-primary btn-sm" href="{SMS}">{ICON["text"]}Text us a photo</a>'
    call_btn = f'<a class="btn btn-quiet btn-sm" href="{TEL}">{ICON["phone"]}Call {BIZ["phone_display"]}</a>'
    if "areas" in ql or "serve" in ql:
        return (f'<a class="btn btn-primary btn-sm" href="/service-areas">See every town we serve</a>'
                f'<a class="btn btn-quiet btn-sm" href="{TOWN_SMS}" data-fixed>{ICON["text"]}Not listed? Text us</a>')
    if "hours" in ql:
        return call_btn + f'<a class="btn btn-quiet btn-sm" href="{SMS}">{ICON["text"]}Text us anytime</a>'
    if "licensed" in ql:
        return f'<a class="btn btn-quiet btn-sm" href="#reviews">{ICON["star"]}See what neighbors say</a>'
    if any(k in ql + " " + al for k in ("quote", "photo", "send", "text us", "ask about", "let us know", "tell us")):
        return text_btn + call_btn
    return ""


def faq_html(faq):
    items = []
    for q, a in faq:
        cta = faq_cta(q, a)
        cta = f'<div class="faq-cta">{cta}</div>' if cta else ""
        items.append(f"<details><summary>{escape(q)}</summary><div class=\"faq-a\"><p>{escape(a)}</p>{cta}</div></details>")
    return '<div class="faq">' + "".join(items) + "</div>"


def cta_pair(primary="Text us a photo"):
    return f'<div class="btns"><a class="btn btn-primary" href="{SMS}">{ICON["text"]}{primary}</a><a class="btn btn-quiet" href="{TEL}">{ICON["phone"]}<span>Call<span class="num"> {BIZ["phone_display"]}</span></span></a></div>'


PLAN = f"""<ol class="plan">
<li><span class="plan-ico">{ICON["camera"]}</span><h3>Snap a photo</h3><p>Take a picture of the tree, stump or mess. Add your address and text it to {BIZ["phone_display"]}.</p></li>
<li><span class="plan-ico">{ICON["pin"]}</span><h3>We take a look</h3><p>Sometimes the photo is all we need. Most of the time it shows us which trees you mean, and we stop by to see them in person.</p></li>
<li><span class="plan-ico">{ICON["chat"]}</span><h3>Get a fair price</h3><p>We text or call you back with a free quote. No pressure and no obligation.</p></li>
<li><span class="plan-ico">{ICON["home"]}</span><h3>Enjoy your yard</h3><p>We show up when we say we will, do the job safely, and clean up like we were never there.</p></li>
</ol>"""

CREDS = f"""<div class="creds">
<div><span class="ti">{ICON["flag"]}</span><strong>22 years</strong><span>U.S. Navy, retired Chief</span></div>
<div><span class="ti">{ICON["shield"]}</span><strong>Licensed</strong><span>and fully insured</span></div>
<div><span class="ti">{ICON["star"]}</span><strong data-lh-score>5-star</strong><span data-lh-count>reviews from neighbors on Google</span></div>
</div>"""

PHONE_CHATS = {
    None: ("storm", "Hi! Can you take a look at this oak? It split in the storm. We're off Scenic Hwy.",
           "Thanks for the photo! We can cut that up and haul it all off. We'll swing by to take a look and get you a free quote."),
    "storm-cleanup": ("storm", "Hi! Can you take a look at this oak? It split in the storm. We're off Scenic Hwy.",
                      "Thanks for the photo! We can cut that up and haul it all off. We'll swing by to take a look and get you a free quote."),
    "tree-removal": ("removal", "Hi! Can you take down the tall tree on the left? It's getting too close to the house.",
                     "Thanks for the photo! We can take that down in sections and haul it all off. We'll swing by to take a look and get you a free quote."),
    "tree-trimming": ("trimming", "Hi! These oaks are hanging low over the yard. Can you trim them up?",
                      "Thanks for the photo! We can lift and thin those and clean everything up. We'll swing by to take a look and get you a free quote."),
    "stump-grinding": ("stump", "Hi! How much to grind this stump? It's in the backyard and the gate is about 4 ft wide.",
                       "Thanks for the photo and the gate size! We'll swing by to take a look and get you a free quote."),
    "palm-tree-trimming": ("palm", "Hi! Can you trim the dead fronds and seed pods off this palm?",
                           "Thanks for the photo! We can clean that up and haul off the fronds. We'll swing by to take a look and get you a free quote."),
    "debris-hauling": ("debris", "Hi! A tree came down in our yard. Can you cut it up and haul it all away?",
                       "Thanks for the photo! We can cut that up, load it and haul it off. We'll swing by to take a look and get you a free quote."),
}


def phone(slug=None):
    pic, me, them = PHONE_CHATS.get(slug, PHONE_CHATS[None])
    return f"""<div class="phone" aria-hidden="true"><div class="phone-screen">
<div class="phone-top"><img src="/img/logo-96.webp" alt="" width="34" height="34"><span><strong>Log Hog Tree Service</strong><small>(850) 426-4220</small></span></div>
<div class="msgs">
<div class="msg me photo"><img src="/img/phone-{pic}-480.webp" alt="" width="480" height="360" loading="lazy"></div>
<div class="msg me">{escape(me)}</div>
<div class="msg them">{escape(them)}</div>
<div class="msg me">Perfect, thank you!</div>
<div class="typing"><i></i><i></i><i></i></div>
</div></div></div>"""


PHONE = phone()


PICKS = ["Tree removal", "Trimming", "Stump grinding", "Storm cleanup", "Debris hauling", "Palms & bushes"]


def ticker():
    items = [("shield", "Licensed &amp; insured"), ("flag", "Veteran-owned"), ("star", "5-star rated on Google"),
             ("text", "Free quotes by text"), ("home", "We clean up every job"), ("pin", "Pensacola &amp; nearby")]
    row = "".join(f'<li>{ICON[i]}{t}</li>' for i, t in items)
    return f"""<section class="ticker" aria-label="Licensed and insured, veteran-owned, 5-star rated, free quotes by text">
<div class="ticker-track" aria-hidden="true"><ul>{row}</ul><ul>{row}</ul></div></section>"""


def quote_section(pre=None, slug=None):
    return f"""<section class="section dark quote-sec"><div class="wrap">
<div class="quote-grid">
<div>
<div class="section-head"><h2>Getting a quote is <em>easy</em></h2><p class="lede">No forms and no phone tag. It all starts with a photo.</p></div>
{PLAN}
</div>
<div class="phone-wrap" data-reveal>{phone(slug)}<p class="phone-cap">It really is this simple.</p></div>
</div>
{quote_picker(pre)}
</div></section>"""


PICK_ICONS = {
    "Tree removal": '<path d="M12 2 6 10h3l-4 6h5v6h4v-6h5l-4-6h3z"/>',
    "Trimming": '<path d="M6 3a3 3 0 1 0 2.2 5l2.4 2.4L4 17l1.4 1.4L12 12l6.6 6.6L20 17 8.2 5.2A3 3 0 0 0 6 3zm0 2a1 1 0 1 1 0 2 1 1 0 0 1 0-2zm9.4 2.2L13.4 9.2l1.4 1.4 5.6-5.6L19 3.6z"/>',
    "Stump grinding": '<path d="M12 4C7 4 3 5.8 3 8v8c0 2.2 4 4 9 4s9-1.8 9-4V8c0-2.2-4-4-9-4zm0 2c4.4 0 7 1.4 7 2s-2.6 2-7 2-7-1.4-7-2 2.6-2 7-2zm0 1.2c-2 0-3.4.4-3.4.8s1.4.8 3.4.8 3.4-.4 3.4-.8-1.4-.8-3.4-.8z"/>',
    "Storm cleanup": '<path d="M7 11a5 5 0 0 1 9.6-1.9A4 4 0 1 1 17 17H7a3 3 0 0 1 0-6zm6 7-2 4h2l-1 3 4-5h-2l1-2z"/>',
    "Debris hauling": '<path d="M2 6h12v9H2zm13 3h4l3 3v3h-7zM5.5 16a2 2 0 1 1 0 4 2 2 0 0 1 0-4zm12 0a2 2 0 1 1 0 4 2 2 0 0 1 0-4z"/>',
    "Palms & bushes": '<path d="M12 9c-1.5-3-5-4-8-3 2 .3 4 1.5 5 3-2-.5-5 0-7 2 2.5-.8 5-.6 7 .3L8 22h3l1.2-10.5C14 10.6 17 10.4 20 11c-2-2-5-2.5-7-2 1-1.5 3-2.7 5-3-3-1-6.5 0-6 3z"/>',
}


PICK_MSG = {"Trimming": "tree trimming", "Palms & bushes": "palm and bush trimming"}
SLUG_PICK = {"tree-removal": "Tree removal", "tree-trimming": "Trimming", "stump-grinding": "Stump grinding",
             "storm-cleanup": "Storm cleanup", "palm-tree-trimming": "Palms & bushes", "debris-hauling": "Debris hauling"}


def quote_picker(pre=None):
    chips = "".join(
        f'<button type="button" class="chip" aria-pressed="{"true" if p == pre else "false"}" data-pick="{escape(PICK_MSG.get(p, p.lower()))}">'
        f'<svg viewBox="0 0 24 24" aria-hidden="true"><g fill="currentColor">{PICK_ICONS[p]}</g></svg><span>{escape(p)}</span><i aria-hidden="true"></i></button>'
        for p in PICKS)
    return f"""<div class="picker" data-picker>
<div class="picker-left">
<p class="picker-step">Build your text</p>
<p class="picker-q" id="picker-q">What do you need help with?</p>
<div class="chips" role="group" aria-labelledby="picker-q">{chips}</div>
</div>
<div class="picker-right">
<p class="picker-step">Your message</p>
<div class="picker-preview"><span class="pp-to">To: Log Hog Tree Service</span><p class="pp-bubble" data-preview>Hi Log Hog! I'd like a free quote. My address is: </p><span class="pp-photo">{ICON["camera"]}Add your photo</span></div>
{cta_pair()}
<p class="picker-note" aria-live="polite">Tap what you need and we'll start the text for you. Just add a photo.</p>
</div>
</div>"""


SLIDERS = [
    ("ba-fallen", "A fallen tree across a front yard", "The same yard, cleared and cleaned up", "Fallen tree, cleared and hauled off", 880, 440),
    ("ba-oaks", "Oak trees with low, heavy limbs", "The same oaks trimmed and lifted", "Oaks trimmed and lifted", 544, 725),
]


def ba_slider(key, alt_before, alt_after, cap, w, h):
    src = lambda side: f'/img/{key}-{side}-600.webp'
    srcset = lambda side: f'/img/{key}-{side}-600.webp 600w, /img/{key}-{side}-1000.webp 1000w'
    return f"""<figure class="ba" style="--ar:{w}/{h}">
<div class="ba-frame" style="--pos:50%">
<img class="ba-after" src="{src('after')}" srcset="{srcset('after')}" sizes="(max-width: 860px) 100vw, 700px" alt="{escape(alt_after)}" width="{w}" height="{h}" loading="lazy" decoding="async">
<img class="ba-before" src="{src('before')}" srcset="{srcset('before')}" sizes="(max-width: 860px) 100vw, 700px" alt="{escape(alt_before)}" width="{w}" height="{h}" loading="lazy" decoding="async">
<span class="ba-tag ba-tag-b" aria-hidden="true">Before</span><span class="ba-tag ba-tag-a" aria-hidden="true">After</span>
<span class="ba-handle" aria-hidden="true"><span></span></span>
<input class="ba-range" type="range" min="0" max="100" value="50" aria-label="Drag to compare before and after: {escape(cap)}">
</div>
<figcaption>{escape(cap)}</figcaption>
</figure>"""


def our_work(ids):
    items = "".join(ba_slider(*x) for x in SLIDERS)
    return f"""<section class="section watch our-work" id="watch"><div class="wrap">
<div class="section-head"><h2>Our <em>work</em></h2><p class="lede">Drag the sliders to see the before and after, or tap a time-lapse to watch a job from start to finish.</p></div>
<div class="bas">{items}</div>
<h3 class="ow-sub">{ICON["play"]}Time-lapses from real jobs</h3>
{timelapse_grid(ids)}
<p class="tls-more"><a class="text-link" href="/about-us#watch">See more of our work</a></p>
</div></section>"""


def work_gallery():
    items = "".join(ba_slider(*x) for x in SLIDERS)
    return f"""<section class="section"><div class="wrap">
<div class="section-head"><h2>See the <em>difference</em></h2><p class="lede">Drag the slider on real jobs we've done around Pensacola. There's more on <a href="{BIZ["facebook"]}" rel="noopener">our Facebook page</a>.</p></div>
<div class="bas">{items}</div>
</div></section>"""


# ---------------------------------------------------------------- pages
HOME_FAQ = [
    ("How do I get a quote?", "Text a photo of the tree or job and your address to (850) 426-4220, or give us a call. Sometimes we can quote right from the photo. Most of the time, the photo shows us which trees you mean, and we stop by to look at them in person before we text or call you back with a price. Quotes are free and there's no obligation."),
    ("Are you licensed and insured?", "Yes. Log Hog Tree Service is licensed and insured."),
    ("Do you clean up after the job?", "Always. We haul away the branches and debris and rake up, so your yard is clean when we leave."),
    ("Can you grind the stump when you remove a tree?", "Yes. Stump grinding can be added to any tree removal. Just mention it when you ask for your quote."),
    ("What are your hours?", "Monday through Saturday, 8am to 5pm."),
    ("What areas do you serve?", "Pensacola and our neighbors nearby, including Gulf Breeze, Pensacola Beach, Perdido Key, Cantonment, Pace, Milton, and Lillian and Seminole, AL. See the full list on our service areas page."),
]


CARD_IMG = {'tree-removal': ('card-lift', [480, 800]), 'tree-trimming': ('card-trimming', [480, 800]), 'stump-grinding': ('stump-ready-to-grind', [480, 900]), 'storm-cleanup': ('storm-damaged-oak', [480, 900]), 'palm-tree-trimming': ('trimmed-palms-front-yard', [480, 900]), 'debris-hauling': ('debris-trailer', [480, 900])}


def home():
    cards = "".join(
        f'''<a class="card-link" href="/services/{s["slug"]}"><span class="card">{img(CARD_IMG[s["slug"]][0], "", "(max-width: 700px) 100vw, 380px", CARD_IMG[s["slug"]][1])}
<span class="card-body"><span class="card-title">{escape(s["name"])}</span><span class="card-text">{escape(s["short"])}</span></span></span>
<span class="card-go" aria-hidden="true">{ARROW}</span></a>'''
        for s in SERVICES)
    body = f"""
<section class="hero2">
<div class="hero2-stage" aria-hidden="true">
<picture class="hero2-bg">
<source media="(max-width: 760px)" srcset="/img/hero2-mobile-600.webp 600w, /img/hero2-mobile-900.webp 900w" sizes="100vw">
<img src="/img/hero2-bg-1400.webp" srcset="/img/hero2-bg-1400.webp 1400w, /img/hero2-bg-2136.webp 2136w" sizes="100vw" alt="" width="2136" height="900" fetchpriority="high">
</picture>
<div class="hero2-shade"></div>
</div>
<div class="hero2-stage hero2-front" aria-hidden="true">
<picture class="hero2-cut">
<source media="(max-width: 760px)" srcset="data:image/gif;base64,R0lGODlhAQABAAAAACH5BAEKAAEALAAAAAABAAEAAAICTAEAOw==">
<img src="/img/hero2-cut-1400.webp" srcset="/img/hero2-cut-1400.webp 1400w, /img/hero2-cut-2136.webp 2136w" sizes="100vw" alt="" width="2136" height="900">
</picture>
</div>
<div class="wrap hero2-inner">
<p class="hero2-big" aria-hidden="true"><span><span>Tree work</span></span><span><span>done right,</span></span></p>
<div class="hero2-copy">
<h1><span class="sr-only">Tree work done right, </span><em>by neighbors you can trust</em></h1>
<p class="lede">We handle the tree work around Pensacola, so you don't have to. Text us a photo for a free quote.</p>
{cta_pair()}
{rating_line()}
</div>
</div>
</section>

{ticker()}

<section class="section pains-sec"><div class="wrap pains">
<div class="pains-intro">
<h2 class="hd">Sound <em>familiar?</em></h2>
<p class="statement">The big limb hanging over the roof. The pine that leans a little more after every storm. The stump you've been mowing around for three years.</p>
<p class="muted">We get it, and you shouldn't have to climb a ladder with a chainsaw to deal with it.</p>
<a class="btn btn-primary" href="{SMS}">{ICON["text"]}Text us a photo of yours</a>
</div>
<div class="pain-list">
<a class="pain" href="/services/storm-cleanup">{img("storm-damaged-oak", "A large oak limb that split and fell beside a house", "160px", [480])}
<span class="pain-body"><span class="pain-title">Hurricane season worries</span><span class="pain-text">Every time a storm rolls in off the Gulf, you're watching that one tree out the window.</span><span class="pain-go">How we help with storm cleanup {ARROW}</span></span></a>
<a class="pain" href="/services/tree-removal">{img("climbing-backyard-tree", "A Log Hog climber high in a tall tree above a backyard fence", "160px", [480])}
<span class="pain-body"><span class="pain-title">Too big to do yourself</span><span class="pain-text">Big trees near houses, fences and power lines are dangerous work. It's not a weekend project.</span><span class="pain-go">How we take trees down safely {ARROW}</span></span></a>
<a class="pain" href="/about-us">{img("debris-trailer", "The Log Hog trailer loaded with branches after a job", "160px", [480])}
<span class="pain-body"><span class="pain-title">Finding someone you trust</span><span class="pain-text">You want someone licensed, insured, careful and fair on price, who won't leave a mess behind.</span><span class="pain-go">Meet Log Hog {ARROW}</span></span></a>
</div>
</div>
<div class="wrap"><div class="stakes">
<p class="stakes-k">{ICON["clock"]}Waiting usually costs more</p>
<ul>
<li>A limb through the roof costs a lot more than a trim.</li>
<li>After a big storm, every crew in town is booked for weeks.</li>
<li>Dead and leaning trees only get weaker, and harder to take down safely.</li>
</ul>
</div></div>
</section>

<section class="section stone meet"><div class="wrap meet-grid">
<div class="meet-photos" data-reveal>
<div class="meet-main">{img("dave-lau-founder", "Dave Lau, owner of Log Hog Tree Service, smiling in a customer's yard with his climbing gear", "(max-width: 900px) 100vw, 560px", [640, 1100], w=640, h=800)}</div>
<div class="meet-inset">{img("lift-portrait", "Log Hog's lift raised into a big live oak", "260px", [480, 810], w=480, h=640)}</div>
<div class="meet-badge"><svg viewBox="0 0 120 120"><defs><path id="mbc" d="M60 60m-46 0a46 46 0 1 1 92 0a46 46 0 1 1-92 0"/></defs><text><textPath href="#mbc">VETERAN-OWNED · LICENSED &amp; INSURED · </textPath></text></svg><span>{ICON["flag"]}</span></div>
</div>
<div class="meet-copy">
<h2 class="hd">Meet <em>Log Hog</em></h2>
<p>We're a small, local crew, and we take every job personally. Log Hog is owned by Dave Lau, who grew up in Mobile and served 22 years in the U.S. Navy, retiring as a Chief. He spent that career working on aircraft, where you do the job carefully and get it right the first time. That's how our whole crew works.</p>
<p>We show up when we say we will, treat your home like it belongs to family, and leave the yard cleaner than we found it. If there's a tree that's been worrying you, send us a picture. You'll get a straight answer and a fair price.</p>
<blockquote class="pull"><span class="qm" aria-hidden="true">“</span>There's nothing better than raking up the last of the branches and watching a customer step outside and smile at their yard.<cite>Dave Lau, owner</cite></blockquote>
{CREDS}
<a class="text-link" href="/about-us">More about us</a>
</div>
</div></section>

{reviews_block("home", 3, stone=False)}

{quote_section()}

<section class="section" id="services"><div class="wrap">
<div class="section-head"><h2>How we can <em>help</em></h2><p class="lede">Every job ends with cleanup. We haul it all off so you don't have to.</p></div>
<div class="cards">{cards}</div>
</div></section>

{LIFT_BLOCK}

{our_work(["1074760131659950", "1659355478552803", "1529463255849855"])}


<section class="section"><div class="wrap success">
{img("oaks-trimmed-front-yard", "Big oak trees freshly trimmed over a green front lawn and brick home", "(max-width: 900px) 100vw, 480px", [480, 900], w=480, h=640)}
<div>
<h2 class="hd">Picture your yard <em>next weekend</em></h2>
<ul class="checks">
<li>No more watching that dead limb every time the wind picks up</li>
<li>A smooth lawn where that old stump used to be</li>
<li>Trees that look healthy and cared for</li>
<li>No brush pile left behind. We haul it all away.</li>
</ul>
{cta_pair("Get my free quote")}
</div>
</div></section>


<section class="section dark areas-sec" id="areas"><div class="wrap areas-grid">
<div>
<div class="section-head"><h2>Proud to serve <em>our neighbors</em></h2><p class="lede">Pensacola, Escambia and Santa Rosa counties, and nearby Alabama.</p></div>
{area_chips()}
<div class="areas-cta"><a class="btn btn-primary" href="{TOWN_SMS}" data-fixed>{ICON["text"]}Don't see your town? Text us</a><a class="text-link" href="/service-areas">More about where we work</a></div>
</div>
{area_map()}
</div></section>

<section class="section"><div class="wrap narrow">
<div class="section-head"><h2>Questions folks <em>ask us</em></h2></div>
{faq_html(HOME_FAQ)}
</div></section>

{band()}
"""
    return page("/", "Tree Removal & Trimming in Pensacola, FL | Log Hog Tree Service",
                "Veteran-owned tree service in Pensacola, FL. Tree removal, trimming, stump grinding, storm cleanup and palm trimming. Licensed & insured. Text a photo to (850) 426-4220 for a free quote.",
                body, current="/", extra_schema=[schema_faq(HOME_FAQ)], body_class="home")


def inner_hero(trail, h1, lede, *, ctas=True, rating=True, photo=None, side=""):
    if photo:
        side = f'<div class="ph-photo">{img(photo[0], photo[1], "(max-width: 900px) 100vw, 520px", photo[2], eager=True)}</div>'
    return f"""<section class="page-hero{' split' if side else ''}"><div class="wrap">
<div class="ph-copy">
<h1>{escape(h1)}</h1>
<p class="lede">{escape(lede)}</p>
{cta_pair() if ctas else ""}
<ul class="badges"><li>{ICON["shield"]}Licensed &amp; insured</li><li>{ICON["flag"]}Veteran-owned</li><li>{ICON["text"]}Free quotes by text</li></ul>
{rating_line() if rating else ""}
</div>
{side}
</div></section>"""


def service_blocks(body):
    out = []
    for ch in re.split(r"(?=<h2>)", body.strip()):
        m = re.match(r"<h2>(.*?)</h2>(.*)", ch.strip(), re.S)
        if not m:
            continue
        h, rest = m.group(1), m.group(2).strip()
        rest = rest.replace("{SMS}", SMS)
        hl = h.lower()
        if hl.startswith("getting a quote") or hl.startswith("how to get on the schedule"):
            out.append(f"""<div class="sb sb-cta"><span class="ti">{ICON["camera"]}</span><div><h2>{h}</h2>{rest}{cta_pair()}</div></div>""")
        elif 'class="checks"' in rest:
            out.append(f'<div class="sb sb-incl"><h2>{h}</h2>{rest}</div>')
        elif "<ul>" in rest:
            intro, _, tail = rest.partition("<ul>")
            items, _, after = tail.partition("</ul>")
            lis = re.findall(r"<li>(.*?)</li>", items, re.S)
            cards = []
            for li in lis:
                mm = re.match(r"<strong>(.*?)</strong>\s*(.*)", li, re.S)
                cards.append(f'<li><strong>{mm.group(1)}</strong><span>{mm.group(2)}</span></li>' if mm else f"<li><span>{li}</span></li>")
            out.append(f'<div class="sb"><h2>{h}</h2>{intro}<ul class="sb-cards">{"".join(cards)}</ul>{after}</div>')
        else:
            out.append(f'<div class="sb sb-text"><h2>{h}</h2><div>{rest}</div></div>')
    return "\n".join(out)


def aside(photo=None, links_title=None, links=""):
    pic = img(*photo) if photo else ""
    more = f'<div class="aside-links"><h3>{links_title}</h3><ul>{links}</ul></div>' if links_title else ""
    return f"""<aside class="aside">{pic}
<div class="aside-box quote-card"><span class="ti">{ICON["text"]}</span><h2>Text us a photo</h2>
<p>Send a picture and your address. We'll take a look and get back to you with a fair, free quote.</p>
<a class="btn btn-primary" href="{SMS}">{ICON["text"]}Text a photo</a>
<a class="btn btn-quiet" href="{TEL}">{ICON["phone"]}{BIZ["phone_display"]}</a>
<p style="margin:12px 0 0">{BIZ["hours"]}. Licensed and insured.</p></div>
{more}</aside>"""


def service_page(s):
    trail = [("Home", "/"), ("Services", "/#services"), (s["name"].capitalize(), f"/services/{s['slug']}")]
    others = "".join(f'<li><a href="/services/{o["slug"]}">{escape(o["name"].capitalize())}</a></li>'
                     for o in SERVICES if o is not s)
    p_name, p_alt, p_w = s["photo"]
    body = f"""
{inner_hero(trail, s["title"], s["lede"], photo=(p_name, p_alt, p_w))}

<section class="section svc-sec"><div class="wrap with-aside">
<div class="svc-body">{service_blocks(s["body"])}</div>
{aside(None, "Other ways we can help", others)}
</div></section>

{watch_section([SVC_VIDEO[s["slug"]]], "Here's a real job from start to finish. Tap to watch.") if s["slug"] in SVC_VIDEO else ""}

{quote_section(SLUG_PICK[s["slug"]], s["slug"])}

{reviews_block("service", 3)}

<section class="section"><div class="wrap narrow">
<div class="section-head"><h2>Questions about <em>{escape(s["name"].lower())}</em></h2></div>
{faq_html(s["faq"])}
</div></section>

<section class="section dark areas-sec"><div class="wrap areas-grid">
<div>
<div class="section-head"><h2>{escape(s["name"].capitalize())} around <em>Pensacola</em></h2><p class="lede">We're proud to work in these communities.</p></div>
{area_chips()}
<div class="areas-cta"><a class="btn btn-primary" href="{TOWN_SMS}" data-fixed>{ICON["text"]}Don't see your town? Text us</a></div>
</div>
{area_map()}
</div></section>

{band()}
"""
    service_schema = {
        "@context": "https://schema.org", "@type": "Service",
        "name": s["name"].capitalize(), "serviceType": s["name"].capitalize(),
        "description": s["lede"], "url": f"{SITE}/services/{s['slug']}",
        "provider": {"@id": f"{SITE}/#business"},
        "areaServed": [{"@type": "City", "name": a if "," in a else f"{a}, FL"} for a in AREAS],
    }
    desc = f"{s['lede'].split('.')[0]}. Veteran-owned, licensed & insured. Text a photo to (850) 426-4220 for a free quote."
    if len(desc) > 165:
        desc = f"{s['title'].replace(' in Pensacola, FL', '')} in Pensacola, FL by Log Hog Tree Service. Veteran-owned, licensed & insured. Text a photo to (850) 426-4220 for a free quote."
    return page(f"/services/{s['slug']}", f"{s['title']} | Log Hog Tree Service", desc, body,
                extra_schema=[service_schema, schema_breadcrumbs(trail), schema_faq(s["faq"])])


TIMELAPSES = [
    ("1074760131659950", "Getting a big tree away from the house", "0:29"),
    ("1659355478552803", "An oak that kept dropping deadwood on a pole barn", "0:33"),
    ("1473657861010235", "Five trees in less than an hour", "0:28"),
    ("1277852727578886", "Taking down a sycamore on a beautiful day", "0:21"),
    ("1344567180867580", "Fewer leaves on the roof", "0:29"),
    ("1529463255849855", "Clearance and peace of mind", "0:31"),
]


TL_CAP = {vid: (cap, t) for vid, cap, t in TIMELAPSES}
SVC_VIDEO = {"tree-removal": "1074760131659950", "tree-trimming": "1659355478552803",
             "storm-cleanup": "1529463255849855", "debris-hauling": "1473657861010235"}


def video_card(vid, big=False):
    cap, t = TL_CAP[vid]
    return f'''<button type="button" class="tl{' tl-big' if big else ''}" data-video="/vid/tl-{vid}.mp4" aria-label="Play time-lapse: {escape(cap)}">
<span class="tl-media"><img src="/img/poster-{vid}-960.webp" alt="" width="960" height="540" loading="lazy"><span class="tl-play">{ICON["play"]}</span><span class="tl-time">{t}</span></span>
<span class="tl-cap">{escape(cap)}</span></button>'''


def timelapse_grid(ids=None):
    ids = ids or [v for v, _, _ in TIMELAPSES]
    return '<div class="tls">' + "".join(video_card(v) for v in ids) + "</div>"


def watch_section(ids, lede="Real time-lapses from real jobs around Pensacola. Tap one to watch.", more=True):
    link = '<p class="tls-more"><a class="text-link" href="/about-us#watch">See more of our work</a></p>' if more else ""
    return f"""<section class="section watch" id="watch"><div class="wrap">
<div class="section-head"><h2>Watch us <em>work</em></h2><p class="lede">{lede}</p></div>
{timelapse_grid(ids)}
{link}
</div></section>"""


LIFT_BLOCK = f"""<section class="section stone lift-sec"><div class="wrap lift-grid">
<div class="lift-photos" data-reveal>
<div class="lp-a">{img("lift-porch", "Log Hog's lift reaching over a home to trim a big oak", "(max-width: 900px) 100vw, 600px", [640, 1200], w=640, h=360)}</div>
<div class="lp-b">{img("dave-climbing-oak", "A Log Hog climber roped into an oak", "260px", [480], w=480, h=640)}</div>
</div>
<div>
<h2 class="hd">We climb <em>and</em> we lift</h2>
<p>Some trees are best climbed. Others are faster and safer from the bucket of our lift. We bring both, so we can use the right tool for your tree, your yard and your budget.</p>
<ul class="lift-list">
<li><strong>Climbing</strong><span>For tight backyards, trees over roofs and spots the lift can't reach.</span></li>
<li><strong>Our lift</strong><span>For big canopies and tall trees where a bucket gets us there quicker.</span></li>
</ul>
<button type="button" class="text-link lift-watch" data-video="/vid/tl-1074760131659950.mp4">{ICON["play"]}Watch the lift in action</button>
</div>
</div></section>"""


def about():
    trail = [("Home", "/"), ("About us", "/about-us")]
    body = f"""
{inner_hero(trail, "About Log Hog Tree Service", "A local, veteran-owned tree service in Pensacola. Owner Dave Lau and our crew take care of your trees like they were our own.", rating=False, photo=("pine-takedown-sections", "A Log Hog climber taking a tall pine down in sections", [480, 900]))}

<section class="section stone meet"><div class="wrap meet-grid">
<div class="meet-photos" data-reveal>
<div class="meet-main">{img("dave-lau-founder", "Dave Lau, owner of Log Hog Tree Service", "(max-width: 900px) 100vw, 560px", [640, 1100], w=640, h=800)}</div>
<div class="meet-inset">{img("dave-in-tree-selfie", "Dave up in a tree with his helmet and climbing gear", "220px", [640], w=640, h=480)}</div>
<div class="meet-badge"><svg viewBox="0 0 120 120"><defs><path id="mbc2" d="M60 60m-46 0a46 46 0 1 1 92 0a46 46 0 1 1-92 0"/></defs><text><textPath href="#mbc2">RETIRED NAVY CHIEF · 22 YEARS · </textPath></text></svg><span>{ICON["flag"]}</span></div>
</div>
<div class="meet-copy">
<h2 class="hd">Led by a retired <em>Navy Chief</em></h2>
<p>Log Hog is owned by Dave Lau, who was born and raised in Mobile, Alabama, and served 22 years in the U.S. Navy, retiring as a Navy Chief. He spent his career as an aviation mechanic, where precision, safety and hard work aren't optional. That same mindset runs through every job our crew does.</p>
<p>Tree care isn't just a job for us. We love making trees look their best, and we really enjoy seeing customers happy with their yards when we're done.</p>
<p>Faith is a big part of who Dave is, and it shapes how we do business: with honesty, integrity and respect for you and your home. When you hire Log Hog, you're getting a crew that cares about your property like it was our own.</p>
{CREDS}
{cta_pair()}
</div>
</div></section>

<section class="section watch" id="watch"><div class="wrap">
<div class="section-head"><h2>Watch us <em>work</em></h2><p class="lede">A few of our favorite time-lapses. Tap one to watch.</p></div>
{timelapse_grid()}
<p class="tls-more"><a class="text-link" href="{BIZ["facebook"]}" rel="noopener">See more on Facebook</a></p>
</div></section>

{reviews_block("about", 3, "What folks say about <em>working with us</em>", "Straight from our Google reviews.")}

{quote_section()}

{band("Ready to get your <em>yard back?</em>", "Text us a photo of the job and your address. You'll get a fair, free quote, with no pressure.")}
"""
    return page("/about-us", "About Log Hog | Veteran-Owned Tree Service in Pensacola, FL",
                "Log Hog Tree Service is a local, veteran-owned tree company in Pensacola, FL, owned by retired Navy Chief Dave Lau. Licensed and insured tree removal, trimming and stump grinding.",
                body, current="/about-us", extra_schema=[schema_breadcrumbs(trail)])


def contact():
    trail = [("Home", "/"), ("Contact", "/contact")]
    body = f"""
{inner_hero(trail, "Let's take a look at your tree", "The quickest way to a quote is a text with a photo. No forms, and no waiting around for a callback.", side='<div class="ph-phone">' + PHONE + '</div>')}

<section class="section"><div class="wrap">
<div class="ways">
<div class="way main"><span class="ti">{ICON["text"]}</span><h2>Text us a photo</h2><p>Send a picture or two of the tree or job, plus your address, to {BIZ["phone_display"]}. Sometimes that's enough for a price. Usually we'll stop by to see the trees in person, then text or call you back with a free quote.</p><a class="btn btn-primary" href="{SMS}">{ICON["text"]}Text {BIZ["phone_display"]}</a></div>
<div class="way"><span class="ti">{ICON["phone"]}</span><h2>Give us a call</h2><p>Rather talk it through? Call us {BIZ["hours"]}.</p><a class="btn btn-quiet" href="{TEL}">{ICON["phone"]}Call {BIZ["phone_display"]}</a></div>
</div>
</div></section>

<section class="section stone shotlist-sec"><div class="wrap shotlist">
<div class="viewfinder" aria-hidden="true">{img("storm-damaged-oak", "", "(max-width: 900px) 100vw, 480px", [480, 900])}<span class="vf c1"></span><span class="vf c2"></span><span class="vf c3"></span><span class="vf c4"></span><span class="vf-rec">● Photo for Log Hog</span></div>
<div>
<h2 class="hd">What to <em>send us</em></h2>
<p class="muted">Photos show us exactly which trees you mean before we come take a look. Here's the shot list:</p>
<ol class="shots">
<li>A photo of the whole tree, from far enough back to see the top</li>
<li>A photo of the base or stump</li>
<li>Anything close by: the house, fence, pool, driveway or power lines</li>
<li>Your address</li>
<li>What you'd like done: removed, trimmed, stump ground or hauled</li>
<li>Anything we should know, like a locked gate and how wide it is</li>
</ol>
<a class="btn btn-primary" href="{SMS}">{ICON["text"]}Text us your photos</a>
</div>
</div></section>

<section class="facts"><div class="wrap facts-row">
<div><span class="facts-k">When</span><strong>{BIZ["hours"]}</strong><p>Text anytime and we'll get back to you.</p></div>
<div><span class="facts-k">Where</span><strong>Pensacola &amp; nearby</strong><p>Gulf Breeze, Pensacola Beach, Perdido Key, Cantonment, Pace, Milton, Lillian and Seminole, AL, and the communities in between. <a href="/service-areas">See everywhere we work</a>.</p></div>
<div><span class="facts-k">Peace of mind</span><strong>Licensed &amp; insured</strong><p>Veteran-owned and fully covered on every job.</p></div>
</div></section>

{reviews_block("service", 3, "Why your neighbors call <em>Log Hog</em>")}
"""
    return page("/contact", "Free Tree Service Quote | Call or Text Log Hog in Pensacola, FL",
                "Text a photo of your tree and your address to (850) 426-4220 for a fast, free quote. Tree removal, trimming and stump grinding in Pensacola. Mon–Sat 8am–5pm.",
                body, current="/contact", extra_schema=[schema_breadcrumbs(trail)])


def areas_page():
    trail = [("Home", "/"), ("Service areas", "/service-areas")]
    svc = "".join(f'<li><a href="/services/{s["slug"]}"><strong>{escape(s["name"].capitalize())}</strong><span>{escape(s["short"])}</span></a></li>' for s in SERVICES)
    body = f"""
{inner_hero(trail, "Taking care of trees all around Pensacola", "We're based in Pensacola and work throughout Escambia and Santa Rosa counties, plus Lillian and Seminole, Alabama.", photo=("oaks-trimmed-front-yard", "Freshly trimmed oaks over a Pensacola front yard", [480, 900]))}

<section class="section areas-sec light"><div class="wrap areas-grid">
<div>
<div class="section-head"><h2>Where <em>we work</em></h2><p class="lede">Tap a town to find it on the map.</p></div>
{area_chips()}
<div class="areas-cta"><a class="btn btn-primary" href="{TOWN_SMS}" data-fixed>{ICON["text"]}Don't see your town? Text us</a></div>
</div>
{area_map()}
</div></section>

<section class="section"><div class="wrap with-aside">
<div class="svc-body">
<div class="sb sb-text"><h2>Trees we know well</h2><div><p>Live oaks, laurel and water oaks, longleaf and slash pines, magnolias, crepe myrtles and every kind of palm. Sandy soil, a long hurricane season and our summer storms make dead limbs and leaning pines common around here, so regular trimming and quick cleanup after storms matter more on the Gulf Coast than most places.</p></div></div>
<div class="sb"><h2>How we can help</h2><ul class="sb-cards">{svc}</ul></div>
</div>
{aside()}
</div></section>

{reviews_block("service", 3)}
{band()}
"""
    return page("/service-areas", "Service Areas | Log Hog Tree Service, Pensacola FL",
                "Log Hog Tree Service serves Pensacola, Gulf Breeze, Pensacola Beach, Perdido Key, Cantonment, Pace, Milton, Lillian and Seminole AL, and nearby communities. Text a photo for a free quote.",
                body, current="/service-areas", extra_schema=[schema_breadcrumbs(trail)])


def not_found():
    body = f"""
<section class="page-hero"><div class="wrap">
<h1>Looks like this page fell over</h1>
<p class="lede">We couldn't find the page you were looking for. Head back to the homepage, or text us a photo for a free quote.</p>
<div class="btns"><a class="btn btn-primary" href="/">Go to the homepage</a><a class="btn btn-quiet" href="{SMS}">Text us a photo</a></div>
</div></section>"""
    html = page("/404", "Page not found | Log Hog Tree Service", "Page not found.", body)
    return html.replace('<link rel="canonical" href="https://loghogtreeservice.com/404">', '<meta name="robots" content="noindex">')


# ---------------------------------------------------------------- build
def render_fallback(limit):
    return subprocess.run(["node", str(ROOT / "scripts/render-reviews.mjs"), str(limit)],
                          capture_output=True, text=True, check=True).stdout


def main():
    global FALLBACK, CSS_VERSION
    FALLBACK = {n: render_fallback(n) for n in (3, 4)}
    css = (ROOT / "src/site/site.css").read_text()
    import hashlib
    CSS_VERSION = hashlib.sha1(css.encode()).hexdigest()[:8]
    (OUT / "site.css").write_text(css)

    # Remove the old Simvoly export (kept untouched in pages-original/)
    for old in ["index.html", "about-us.html", "contact.html", "service-areas.html"]:
        (OUT / old).unlink(missing_ok=True)
    shutil.rmtree(OUT / "assets", ignore_errors=True)
    shutil.rmtree(OUT / "services", ignore_errors=True)
    (OUT / "services").mkdir()

    files = {
        "index.html": home(),
        "about-us.html": about(),
        "contact.html": contact(),
        "service-areas.html": areas_page(),
        "404.html": not_found(),
    }
    for s in SERVICES:
        files[f"services/{s['slug']}.html"] = service_page(s)
    for name, html in files.items():
        (OUT / name).write_text(html)
        print("wrote", name, len(html) // 1024, "KB")

    urls = ["/", "/about-us", "/contact", "/service-areas"] + [f"/services/{s['slug']}" for s in SERVICES]
    (OUT / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "".join(f"  <url><loc>{SITE}{u}</loc><lastmod>{TODAY}</lastmod></url>\n" for u in urls)
        + "</urlset>\n")
    (OUT / "robots.txt").write_text(f"User-agent: *\nAllow: /\n\nSitemap: {SITE}/sitemap.xml\n")
    (OUT / "_redirects").write_text(
        "/home / 301\n/index.html / 301\n/about /about-us 301\n/services / 301\n"
        "/tree-removal /services/tree-removal 301\n/stump-grinding /services/stump-grinding 301\n")
    print("wrote sitemap.xml, robots.txt, _redirects")


FALLBACK = {}
CSS_VERSION = "dev"

if __name__ == "__main__":
    main()
