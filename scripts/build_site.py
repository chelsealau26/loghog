"""Builds the Log Hog Tree Service website into ./pages.

Edit the content below, then run from the repo root:
    python3 scripts/build_site.py

Pages are plain HTML (fast, no frameworks). Live Google reviews are added by
the Cloudflare Worker (src/index.js) into the [data-lh-reviews] sections.
"""
import json
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
    "email": "loghogllc@gmail.com",
    "hours": "Mon–Sat, 8am–5pm",
    "maps": "https://maps.google.com/?cid=3271970089992802073",
    "review": "https://g.page/r/CRlPuRF2X2gtEBM/review",
    "facebook": "https://www.facebook.com/profile.php?id=100085501815881",
    "instagram": "https://www.instagram.com/log_hog_tree_debris/",
}
SMS = "sms:+18504264220?&body=" + "Hi%20Log%20Hog%21%20I%27d%20like%20a%20free%20quote.%20My%20address%20is%3A%20"
TEL = "tel:+18504264220"

# Keep in sync with the Google Business Profile service areas.
AREAS = [
    "Pensacola", "West Pensacola", "Pensacola Beach", "Gulf Breeze", "Perdido Key",
    "Warrington", "Myrtle Grove", "Bellview", "Brent", "Ensley", "Ferry Pass",
    "Gonzalez", "Cantonment", "Muscogee", "McDavid", "Goulding", "Seminole",
    "Pace", "Milton", "Lillian, AL",
]

ICON = {
    "phone": '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M6.6 10.8a15.1 15.1 0 0 0 6.6 6.6l2.2-2.2c.3-.3.7-.4 1-.2 1.1.4 2.3.6 3.6.6.6 0 1 .4 1 1V20c0 .6-.4 1-1 1A17 17 0 0 1 3 4c0-.6.4-1 1-1h3.5c.6 0 1 .4 1 1 0 1.3.2 2.5.6 3.6.1.3 0 .7-.2 1z"/></svg>',
    "text": '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M4 3h16a2 2 0 0 1 2 2v11a2 2 0 0 1-2 2H8l-4.6 3.7A.9.9 0 0 1 2 21V5c0-1.1.9-2 2-2zm3.5 6.5a1.5 1.5 0 1 0 0 3 1.5 1.5 0 0 0 0-3zm4.5 0a1.5 1.5 0 1 0 0 3 1.5 1.5 0 0 0 0-3zm4.5 0a1.5 1.5 0 1 0 0 3 1.5 1.5 0 0 0 0-3z"/></svg>',
    "shield": '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M12 2 4 5v6c0 5 3.4 9.7 8 11 4.6-1.3 8-6 8-11V5l-8-3zm-1.2 14.2-3.5-3.5 1.4-1.4 2.1 2.1 4.6-4.6 1.4 1.4-6 6z"/></svg>',
    "flag": '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M5 2h2v20H5V2zm3 1h11l-2.5 4.5L19 12H8V3z"/></svg>',
    "star": '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="m12 2 2.9 6.6 7.1.6-5.4 4.7 1.6 7L12 17.3 5.8 21l1.6-7L2 9.2l7.1-.6L12 2z"/></svg>',
    "menu": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M3 6h18M3 12h18M3 18h18" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"/></svg>',
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
        "photo": ("pine-takedown", "Dave Lau high in a tall pine during a tree removal", [480, 880]),
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
<li>A free quote from a photo, with no obligation</li>
<li>Careful sectional takedown near homes, fences and lines</li>
<li>Cleanup and hauling of branches and debris</li>
<li>Stump grinding available in the same visit if you want the stump gone too</li>
<li>Licensed and insured work</li>
</ul>
<h2>Getting a quote</h2>
<p>Text a photo of the whole tree and your address to <a href="{SMS}">(850) 426-4220</a>. A second photo of the base and of anything it's close to (house, fence, wires) helps us give you an accurate price without a visit.</p>
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
        "photo": ("dave-climbing-oak", "Dave Lau climbing a live oak to trim it", [480, 880]),
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
        "photo": ("stump-in-woods", "A cut tree stump ready for grinding", [640, 1080]),
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
        "photo": ("chainsaw-cut", "A chainsaw cutting through a fallen tree trunk", [640, 1080]),
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
<p>Text photos of the damage and your address to <a href="{SMS}">(850) 426-4220</a>. Photos let us see what equipment the job needs and give you a price without a site visit, which matters when everyone's phone is ringing after a storm.</p>
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
        "name": "Palm trimming & skinning",
        "title": "Palm Tree Trimming & Skinning in Pensacola, FL",
        "short": "Dead fronds and seed pods cut back, trunks skinned clean, bushes and shrubs shaped.",
        "lede": "Brown fronds and seed pods make a palm look tired. We trim palms back to healthy green, skin the trunks clean, and shape your bushes and shrubs while we're there.",
        "photo": ("dave-in-tree-selfie", "Dave Lau working up in a tree canopy", [640, 1200]),
        "body": """
<h2>Palm trimming</h2>
<p>We cut off dead and dying fronds, seed pods and flower stalks, which keeps palms looking clean and stops heavy fronds from dropping on cars, roofs and people. We leave the healthy green fronds alone: over-trimming (the “hurricane cut”) weakens palms.</p>
<h2>Palm skinning</h2>
<p>Skinning removes the old frond bases (the “boots”) to give the trunk a smooth, clean look. It's popular on sabal and Canary Island date palms around Pensacola and the beaches.</p>
<h2>Bushes and shrubs</h2>
<p>We shape overgrown hedges, bushes and shrubs and cut back anything crowding the house, walkways or windows.</p>
<h2>What's included</h2>
<ul class="checks">
<li>Dead frond, seed pod and flower stalk removal</li>
<li>Trunk skinning on request</li>
<li>Hedge, bush and shrub shaping</li>
<li>Cleanup and hauling of everything we cut</li>
</ul>
""",
        "faq": [
            ("How often should palms be trimmed?", "Most palms look best with a trim once or twice a year. Trimming out seed pods before they drop saves a lot of mess."),
            ("Is it bad to cut off green fronds?", "Yes. Palms feed through their green fronds, so we leave them on. We only remove dead, dying and hanging fronds unless they're in the way."),
            ("Do you trim tall palms?", "Yes. Send a photo and let us know roughly how tall it is."),
        ],
    },
    {
        "slug": "debris-hauling",
        "name": "Debris hauling",
        "title": "Brush & Debris Hauling in Pensacola, FL",
        "short": "Branches, brush piles and yard debris loaded up and hauled away.",
        "lede": "Got a brush pile from a weekend of yard work, or limbs from the last storm? We load it up and haul it away.",
        "photo": ("oak-canopy", "A large oak tree canopy", [480, 880]),
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
        "email": BIZ["email"],
        "description": "Christian and veteran-owned, licensed and insured tree service in Pensacola, FL: tree removal, trimming and pruning, storm cleanup, palm trimming and skinning, stump grinding, and debris hauling.",
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


NAV = [("Services", "/#services"), ("About", "/about-us"), ("Service areas", "/service-areas"), ("Contact", "/contact")]


def header(current):
    links = "".join(
        f'<a href="{u}"{" aria-current=page" if u == current else ""}>{n}</a>' for n, u in NAV)
    return f"""<a class="skip" href="#main">Skip to content</a>
<header class="site-header"><div class="wrap">
<a class="brand" href="/"><img src="/img/logo-96.webp" width="54" height="54" alt=""><span>Log Hog Tree Service</span></a>
<nav class="nav" id="nav" aria-label="Main">{links}</nav>
<a class="head-call" href="{TEL}">{BIZ["phone_display"]}</a>
<a class="btn btn-saw" href="{SMS}">{ICON["text"]}Text a photo</a>
<button class="menu-btn" aria-controls="nav" aria-expanded="false" aria-label="Menu">{ICON["menu"]}</button>
</div></header>"""


def footer():
    svc = "".join(f'<li><a href="/services/{s["slug"]}">{escape(s["name"].capitalize())}</a></li>' for s in SERVICES)
    return f"""<footer class="site-footer"><div class="wrap">
<div class="foot-brand"><img src="/img/logo-192.webp" width="88" height="88" alt="Log Hog Tree Service logo" loading="lazy">
<p>Veteran-owned, licensed and insured tree service in Pensacola, Florida.</p></div>
<div><h2>Services</h2><ul>{svc}</ul></div>
<div><h2>Company</h2><ul><li><a href="/about-us">About Dave</a></li><li><a href="/service-areas">Service areas</a></li><li><a href="/contact">Get a free quote</a></li><li><a href="{BIZ["review"]}" rel="noopener">Leave a review</a></li></ul></div>
<div><h2>Contact</h2><ul>
<li><a href="{TEL}">{BIZ["phone_display"]}</a> (call or text)</li>
<li><a href="mailto:{BIZ["email"]}">{BIZ["email"]}</a></li>
<li>{BIZ["hours"]}</li>
<li>Pensacola, FL and surrounding areas</li>
<li><a href="{BIZ["facebook"]}" rel="noopener">Facebook</a> &nbsp; <a href="{BIZ["instagram"]}" rel="noopener">Instagram</a></li>
</ul></div>
<p class="foot-legal">© {date.today().year} Log Hog Tree Service. Licensed and insured.</p>
</div></footer>
<div class="mobile-bar"><a class="btn btn-line" href="{TEL}">{ICON["phone"]}Call</a><a class="btn btn-saw" href="{SMS}">{ICON["text"]}Text a photo</a></div>
<script>
(function(){{var b=document.querySelector('.menu-btn'),n=document.getElementById('nav');if(b)b.addEventListener('click',function(){{var o=n.classList.toggle('open');b.setAttribute('aria-expanded',o)}});
document.querySelectorAll('[data-yt]').forEach(function(v){{v.addEventListener('click',function(){{v.innerHTML='<iframe src="https://www.youtube-nocookie.com/embed/'+v.dataset.yt+'?autoplay=1" title="'+v.getAttribute('aria-label')+'" allow="autoplay; encrypted-media; picture-in-picture" allowfullscreen></iframe>'}},{{once:true}})}})}})();
</script>"""


def page(path, title, description, body, *, current=None, extra_schema=(), og_image="/img/og-image.jpg"):
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
<meta name="theme-color" content="#24170f">
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
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Atkinson+Hyperlegible+Next:wght@400;700&family=Big+Shoulders+Display:wght@800&display=swap">
<link rel="stylesheet" href="/site.css?v={CSS_VERSION}">
{ld}
</head>
<body>
{header(current)}
<main id="main">
{body}
</main>
{footer()}
</body>
</html>
"""


def reviews_block(page_key, limit, heading="What customers say", intro=None, tint=True):
    intro_html = f"<p>{intro}</p>" if intro else ""
    return f"""<section class="section{' tint' if tint else ''}" id="reviews"><div class="wrap">
<div class="section-head"><h2>{heading}</h2>{intro_html}</div>
<div data-lh-reviews="{page_key}">{FALLBACK[limit]}</div>
</div></section>"""


def quote_band(heading="Get your free quote", text="Text a photo of the tree and your address. We'll text you back with a price."):
    return f"""<section class="band"><div class="wrap">
<div><h2>{heading}</h2><p>{text}</p></div>
<div class="btns"><a class="btn btn-saw" href="{SMS}">{ICON["text"]}Text a photo</a><a class="btn btn-line" href="{TEL}">{ICON["phone"]}Call {BIZ["phone_display"]}</a></div>
</div></section>"""


def areas_list():
    return '<ul class="areas">' + "".join(f"<li>{escape(a)}</li>" for a in AREAS) + "</ul>"


def faq_html(faq):
    return '<div class="faq">' + "".join(
        f"<details><summary>{escape(q)}</summary><p>{escape(a)}</p></details>" for q, a in faq) + "</div>"


RATING_FALLBACK = f'<a href="{BIZ["maps"]}" rel="noopener">See our Google reviews</a>'


def trust_row():
    return f"""<ul class="trust">
<li>{ICON["flag"]}Veteran-owned</li>
<li>{ICON["shield"]}Licensed &amp; insured</li>
<li>{ICON["star"]}<span data-lh-rating>{RATING_FALLBACK}</span></li>
</ul>"""


# ---------------------------------------------------------------- pages
HOME_FAQ = [
    ("How do I get a quote?", "Text a photo of the tree or job and your address to (850) 426-4220, or give us a call. Quotes are free and there's no obligation."),
    ("Are you licensed and insured?", "Yes. Log Hog Tree Service is licensed and insured."),
    ("Do you clean up after the job?", "Yes. Hauling away branches and debris and cleaning up the yard is part of every job."),
    ("Can you grind the stump when you remove a tree?", "Yes. Stump grinding can be added to any tree removal. Just mention it when you ask for your quote."),
    ("What are your hours?", "Monday through Saturday, 8am to 5pm."),
    ("What areas do you serve?", "Pensacola and the surrounding area, including Gulf Breeze, Pensacola Beach, Perdido Key, Cantonment, Pace, Milton and Lillian, AL. See the full list on our service areas page."),
]


def home():
    services = "".join(
        f'<a class="service" href="/services/{s["slug"]}"><h3>{escape(s["name"].capitalize())}</h3><p>{escape(s["short"])}</p></a>'
        for s in SERVICES)
    body = f"""
<section class="hero on-dark"><div class="wrap">
<div>
<h1>Tree removal and trimming in Pensacola</h1>
<p class="lede">Log Hog is Dave Lau, a retired Navy Chief who runs every job himself. Text a photo of your tree and get a free quote.</p>
<div class="btns"><a class="btn btn-saw" href="{SMS}">{ICON["text"]}Text a photo for a quote</a><a class="btn btn-line" href="{TEL}">{ICON["phone"]}Call {BIZ["phone_display"]}</a></div>
{trust_row()}
</div>
<div class="hero-photo">
{img("dave-climbing-oak", "Dave Lau of Log Hog Tree Service climbing a live oak", "(max-width: 960px) 360px, 440px", [480, 880], eager=True, w=440, h=587)}
<div class="thread" aria-label="Example of a text message quote request">
<div class="thread-head"><span>Example</span><span>Log Hog</span></div>
<p class="bubble out photo">{img("pine-takedown", "Photo of a tall pine sent for a quote", "150px", [480], w=150, h=112)}</p>
<p class="bubble out">This pine is leaning toward the house. I'm off 9th Ave in Pensacola. Can you take a look?</p>
<p class="bubble in">Got it, thanks for the photo! I'll text you a quote shortly.</p>
</div>
</div>
</div></section>

<section class="section" id="services"><div class="wrap">
<div class="section-head"><h2>Tree services</h2><p>From one dead limb to clearing a whole lot. Every job includes cleanup.</p></div>
<div class="services">{services}</div>
</div></section>

<section class="section dark on-dark"><div class="wrap">
<div class="section-head"><h2>How to get a quote</h2><p>No forms, no waiting for someone to come measure.</p></div>
<ol class="steps">
<li><h3>Text a photo</h3><p>Send a photo or two of the tree, stump or mess to {BIZ["phone_display"]}, along with your address.</p></li>
<li><h3>Get your price</h3><p>Dave looks it over and texts you back a free, no-obligation quote.</p></li>
<li><h3>We do the work</h3><p>We show up when we say we will, do the job safely, and haul everything away.</p></li>
</ol>
<p style="margin-top:36px"><a class="btn btn-saw" href="{SMS}">{ICON["text"]}Text a photo now</a></p>
</div></section>

<section class="section"><div class="wrap split">
{img("dave-lau-founder", "Dave Lau, founder of Log Hog Tree Service, sitting in a front yard with his climbing gear", "(max-width: 860px) 100vw, 580px", [640, 1100], w=580, h=527)}
<div>
<h2>A Navy Chief up your tree</h2>
<p>Dave Lau was born and raised in Mobile, Alabama, and served 22 years in the U.S. Navy, retiring as a Chief. Years as an aviation mechanic taught him to do things carefully, safely and right the first time, and that's how he runs Log Hog.</p>
<p>When you hire Log Hog, Dave is on the job. Customers mention the same things again and again: he's on time, he's professional, and the yard looks better when he leaves than when he arrived.</p>
<p><a class="btn btn-line" href="/about-us">More about Dave</a></p>
</div>
</div></section>

{reviews_block("home", 4, "What Pensacola customers say")}

<section class="section dark on-dark" id="areas"><div class="wrap">
<div class="section-head"><h2>Serving Pensacola and nearby</h2><p>Escambia and Santa Rosa counties and the edge of Baldwin County, Alabama. Not sure if we come to you? Just ask.</p></div>
{areas_list()}
<a class="btn btn-line" href="/service-areas">See all service areas</a>
</div></section>

<section class="section"><div class="wrap narrow">
<h2>Common questions</h2>
{faq_html(HOME_FAQ)}
</div></section>

{quote_band()}
"""
    return page("/", "Tree Removal & Trimming in Pensacola, FL | Log Hog Tree Service",
                "Veteran-owned tree service in Pensacola, FL. Tree removal, trimming, stump grinding, storm cleanup and palm trimming. Licensed & insured. Text a photo to (850) 426-4220 for a free quote.",
                body, current="/", extra_schema=[schema_faq(HOME_FAQ)])


def service_page(s):
    trail = [("Home", "/"), ("Services", "/#services"), (s["name"].capitalize(), f"/services/{s['slug']}")]
    others = "".join(f'<li><a href="/services/{o["slug"]}">{escape(o["name"].capitalize())}</a></li>'
                     for o in SERVICES if o is not s)
    p_name, p_alt, p_w = s["photo"]
    body = f"""
<section class="page-hero on-dark"><div class="wrap">
{crumbs_html(trail)}
<h1>{escape(s["title"])}</h1>
<p class="lede">{escape(s["lede"])}</p>
<div class="btns"><a class="btn btn-saw" href="{SMS}">{ICON["text"]}Text a photo for a quote</a><a class="btn btn-line" href="{TEL}">{ICON["phone"]}Call {BIZ["phone_display"]}</a></div>
{trust_row()}
</div></section>

<section class="section"><div class="wrap with-aside">
<article class="prose">{s["body"].replace("{SMS}", SMS)}
<h2>Questions about {escape(s["name"].lower())}</h2>
{faq_html(s["faq"])}
</article>
<aside class="aside">
{img(p_name, p_alt, "(max-width: 960px) 100vw, 340px", p_w)}
<h2>Free quote by text</h2>
<p>Send a photo and your address. Dave will text you back with a price.</p>
<a class="btn btn-saw" href="{SMS}">{ICON["text"]}Text a photo</a>
<a class="btn btn-line" href="{TEL}">{ICON["phone"]}{BIZ["phone_display"]}</a>
<p>{BIZ["hours"]}<br>Licensed &amp; insured</p>
<h3>Other services</h3>
<ul>{others}</ul>
</aside>
</div></section>

{reviews_block("service", 3)}

<section class="section"><div class="wrap">
<div class="section-head"><h2>{escape(s["name"].capitalize())} near you</h2><p>We serve Pensacola and these nearby communities:</p></div>
{areas_list()}
</div></section>

{quote_band()}
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


def about():
    trail = [("Home", "/"), ("About", "/about-us")]
    body = f"""
<section class="page-hero on-dark"><div class="wrap">
{crumbs_html(trail)}
<h1>Meet Dave Lau, the man behind Log Hog</h1>
<p class="lede">22 years in the U.S. Navy, now taking care of trees across Pensacola, one yard at a time.</p>
</div></section>

<section class="section"><div class="wrap split">
{img("dave-lau-founder", "Dave Lau, founder of Log Hog Tree Service", "(max-width: 860px) 100vw, 580px", [640, 1100], w=580, h=527)}
<div class="prose">
<p class="lede" style="color:var(--ink)">Dave Lau was born and raised in Mobile, Alabama, and served 22 years in the U.S. Navy, retiring as a Navy Chief.</p>
<p>With a background in aviation mechanics, he brings precision, safety and hard work to every tree job. For Dave, tree care is more than a job. It's a passion: he loves making trees look their best and seeing customers happy with their yards.</p>
<p>A devoted Christian, Dave aims to serve every customer with integrity and respect. When you hire Log Hog, you get a skilled, reliable partner who cares about the beauty and safety of your property.</p>
<ul class="checks"><li>Retired U.S. Navy Chief, 22 years of service</li><li>Licensed and insured</li><li>Christian and veteran-owned</li><li>Rated {"<span data-lh-rating-short>highly</span>"} on Google</li></ul>
</div>
</div></section>

<section class="section tint"><div class="wrap narrow">
<h2>See Log Hog at work</h2>
<button class="video" type="button" data-yt="zsXi8T0tEgA" aria-label="Play video: Log Hog Tree Service at work">
<img src="https://i.ytimg.com/vi/zsXi8T0tEgA/hqdefault.jpg" alt="" loading="lazy" width="480" height="360"><span>{ICON["play"]}</span></button>
</div></section>

{reviews_block("about", 3, "What customers say about Dave", tint=False)}

{quote_band("Ready to get your yard back?", "Text a photo of the job and your address to get a free quote.")}
"""
    return page("/about-us", "About Log Hog | Veteran-Owned Tree Service in Pensacola, FL",
                "Meet Dave Lau, the retired Navy Chief behind Log Hog Tree Service. Licensed and insured tree removal, trimming and stump grinding in Pensacola and surrounding areas.",
                body, current="/about-us", extra_schema=[schema_breadcrumbs(trail)])


def contact():
    trail = [("Home", "/"), ("Contact", "/contact")]
    body = f"""
<section class="page-hero on-dark"><div class="wrap">
{crumbs_html(trail)}
<h1>Get a free tree service quote</h1>
<p class="lede">The fastest way is a text with a photo. No forms, no waiting on a callback.</p>
</div></section>

<section class="section"><div class="wrap">
<div class="ways">
<div class="way main"><h2>Text a photo</h2><p>Send a photo or two of the tree or job, plus your address, to {BIZ["phone_display"]}. We'll text you back with a price.</p><a class="btn btn-saw" href="{SMS}">{ICON["text"]}Text {BIZ["phone_display"]}</a></div>
<div class="way"><h2>Call</h2><p>Prefer to talk it through? Call Dave directly, {BIZ["hours"]}.</p><a class="btn btn-line" href="{TEL}">{ICON["phone"]}Call {BIZ["phone_display"]}</a></div>
<div class="way"><h2>Email</h2><p>Photos by email work too. Include your address and phone number.</p><a class="btn btn-line" href="mailto:{BIZ["email"]}">{BIZ["email"]}</a></div>
</div>
</div></section>

<section class="section tint"><div class="wrap split" style="align-items:start">
<div class="prose">
<h2>What to send for an accurate quote</h2>
<ul class="checks">
<li>A photo of the whole tree, from far enough back to see the top</li>
<li>A photo of the base or stump</li>
<li>Anything nearby: the house, fence, pool, driveway or power lines</li>
<li>Your address</li>
<li>What you'd like done (removed, trimmed, stump ground, hauled)</li>
<li>Access notes, like a locked gate and how wide it is</li>
</ul>
</div>
<div class="prose">
<h2>Hours and area</h2>
<p><strong>{BIZ["hours"]}</strong></p>
<p>We serve Pensacola, Gulf Breeze, Pensacola Beach, Perdido Key, Cantonment, Pace, Milton, Lillian, AL and the communities in between. <a href="/service-areas">See all service areas</a>.</p>
<p>Licensed and insured.</p>
</div>
</div></section>
"""
    return page("/contact", "Free Tree Service Quote | Call or Text Log Hog in Pensacola, FL",
                "Text a photo of your tree and your address to (850) 426-4220 for a fast, free quote. Tree removal, trimming and stump grinding in Pensacola. Mon–Sat 8am–5pm.",
                body, current="/contact", extra_schema=[schema_breadcrumbs(trail)])


def areas_page():
    trail = [("Home", "/"), ("Service areas", "/service-areas")]
    svc = "".join(f'<li><a href="/services/{s["slug"]}">{escape(s["name"].capitalize())}</a></li>' for s in SERVICES)
    body = f"""
<section class="page-hero on-dark"><div class="wrap">
{crumbs_html(trail)}
<h1>Tree service across the Pensacola area</h1>
<p class="lede">Based in Pensacola and serving Escambia and Santa Rosa counties, plus Lillian, Alabama.</p>
</div></section>

<section class="section"><div class="wrap with-aside">
<div class="prose">
<h2>Where we work</h2>
{areas_list()}
<p>Don't see your neighborhood? Text us your address. If you're close by, we can probably help.</p>
<h2>Trees we see around here</h2>
<p>Live oaks, laurel and water oaks, longleaf and slash pines, magnolias, crepe myrtles and every kind of palm. Sandy soil, a long hurricane season and frequent summer storms make dead limbs and leaning pines common, so regular trimming and quick cleanup after storms matter here more than most places.</p>
<h2>Services in every area</h2>
<ul>{svc}</ul>
</div>
<aside class="aside">
<h2>Free quote by text</h2>
<p>Send a photo and your address. Dave will text you back with a price.</p>
<a class="btn btn-saw" href="{SMS}">{ICON["text"]}Text a photo</a>
<a class="btn btn-line" href="{TEL}">{ICON["phone"]}{BIZ["phone_display"]}</a>
<p>{BIZ["hours"]}</p>
</aside>
</div></section>

{reviews_block("service", 3)}
{quote_band()}
"""
    return page("/service-areas", "Service Areas | Log Hog Tree Service, Pensacola FL",
                "Log Hog Tree Service serves Pensacola, Gulf Breeze, Pensacola Beach, Perdido Key, Cantonment, Pace, Milton, Lillian AL and nearby communities. Text a photo for a free quote.",
                body, current="/service-areas", extra_schema=[schema_breadcrumbs(trail)])


def not_found():
    body = f"""
<section class="page-hero on-dark"><div class="wrap">
<h1>This page fell over</h1>
<p class="lede">The page you're looking for doesn't exist anymore. Try the homepage, or text us a photo for a free quote.</p>
<div class="btns"><a class="btn btn-saw" href="/">Go to the homepage</a><a class="btn btn-line" href="{SMS}">Text a photo</a></div>
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
