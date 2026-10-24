#!/usr/bin/env python3
"""Build the Moreland Associates website.

Reads page bodies from src/pages/ and writes finished HTML into docs/, which
GitHub Pages publishes. Also writes the old-URL redirects, sitemap.xml,
robots.txt and 404.html. Uses only the Python standard library.

    python3 build.py              # preview build (served from cellwood.github.io/morelandassoc-website)
    python3 build.py --production # live build (served from www.morelandassoc.com)
"""
import html
from html.parser import HTMLParser
import json
import re
import sys
from datetime import date
from pathlib import Path
from urllib.parse import urljoin

ROOT = Path(__file__).parent
SRC = ROOT / "src" / "pages"
OUT = ROOT / "docs"

SITE_URL = "https://www.morelandassoc.com"
PREVIEW_BASE = "/morelandassoc-website"
PRODUCTION = "--production" in sys.argv
BASE = "" if PRODUCTION else PREVIEW_BASE

# Form service. Create the form at formspree.io and paste its ID here.
FORM_ENDPOINT = "https://formspree.io/f/maeeyrko"
GA_ID = "G-6KYK9C1W08"

BUSINESS = {
    "name": "Moreland Associates",
    "phone": "(510) 833-7308",
    "phone_e164": "+15108337308",
    "email": "info@morelandassoc.com",
    "street": "2532 Santa Clara Avenue, Suite 413",
    "city": "Alameda",
    "region": "CA",
    "postal": "94501",
}

NAV = [
    ("Home", "/"),
    ("Interim Executive", "/services/interim-executive/"),
    ("Market Traction", [
        ("About Market Traction", "/market-traction/"),
        ("Take the Test", "/market-traction/test/"),
        ("The Six Stages", "/market-traction/stages/"),
    ]),
    ("About", "/about/"),
    ("Contact", "/contact/"),
]

# Old Squarespace URL -> new URL. GitHub Pages serves /old-url from old-url.html.
REDIRECTS = {
    "home": "/",
    "new-page": "/market-traction/",
    "new-page-1": "/services/interim-executive/",
    "new-page-3": "/services/interim-executive/",
    "new-page-4": "/services/interim-executive/",
    "interim-executive": "/services/interim-executive/",
    "moreland-services": "/services/interim-executive/",
    "market-traction-test": "/market-traction/test/",
    "market-traction-stages": "/market-traction/stages/",
    "eureka": "/market-traction/stages/eureka/",
    "kaa-ching": "/market-traction/stages/kaa-ching/",
    "two-thumbs-up": "/market-traction/stages/two-thumbs-up/",
    "momentum": "/market-traction/stages/momentum/",
    "building-buzz": "/market-traction/stages/building-buzz/",
    "market-traction-completed": "/market-traction/stages/market-traction/",
    "market-traction-signup": "/get-started/?topic=market-traction",
    "pipeline-acceleration-signup": "/get-started/?topic=pipeline-acceleration",
    "revenue-lifecycle-signup": "/get-started/?topic=revenue-lifecycle",
    "interim-executive-information": "/get-started/?topic=interim-executive",
    "event-in-a-box": "/services/interim-executive/",
    # Service pages retired in October 2026 (copy archived in the playbook)
    "services/product-marketing/": "/services/interim-executive/",
    "services/corporate-marketing/": "/services/interim-executive/",
    "services/revenue-lifecycle/": "/services/interim-executive/",
    "services/field-events/": "/services/interim-executive/",
}

FORMS = {
    # kind: (phone required, message required, message hint, submit subject)
    "contact": (False, False, "", "Website contact form"),
    "about": (False, True, "Anything we should know before we get in touch?", "Website enquiry (About page)"),
    "get-started": (True, False, "Any information we should know before we contact you?", "Get Started request"),
    "field-events": (False, True, "Any additional information we should know before we give you a call?", "Field Events enquiry"),
}

esc = html.escape
CURRENT = ' aria-current="page"'


def url(path):
    return BASE + path


def form_html(kind):
    phone_req, msg_req, hint, subject = FORMS[kind]
    req = '<span class="req">(required)</span>'
    return f"""<form class="form" data-form action="{FORM_ENDPOINT}" method="POST">
  <input type="hidden" name="_subject" value="{esc(subject)}">
  <input type="hidden" name="topic" value="{kind}">
  <div class="hp" aria-hidden="true"><label>Leave this empty <input type="text" name="_gotcha" tabindex="-1" autocomplete="off"></label></div>
  <div class="row">
    <div><label for="{kind}-first">First name {req}</label><input id="{kind}-first" name="first_name" autocomplete="given-name" required></div>
    <div><label for="{kind}-last">Last name {req}</label><input id="{kind}-last" name="last_name" autocomplete="family-name" required></div>
  </div>
  <div><label for="{kind}-email">Email address {req}</label><input id="{kind}-email" type="email" name="email" autocomplete="email" required></div>
  <div><label for="{kind}-phone">Phone {req if phone_req else ''}<span class="hint">What’s the best number to reach you?</span></label><input id="{kind}-phone" type="tel" name="phone" autocomplete="tel"{" required" if phone_req else ""}></div>
  <div><label for="{kind}-message">Message {req if msg_req else ''}{f'<span class="hint">{esc(hint)}</span>' if hint else ''}</label><textarea id="{kind}-message" name="message"{" required" if msg_req else ""}></textarea></div>
  <div><button class="btn" type="submit">Submit</button></div>
  <p class="form-status" role="status" aria-live="polite"></p>
</form>"""


CTA = """<section class="cta-band" aria-labelledby="cta-title">
  <div class="wrap">
    <div>
      <h2 id="cta-title">Ready to build market traction?</h2>
      <p>Talk with a Moreland executive about where your company is today and what it will take to reach the next milestone.</p>
    </div>
    <a class="btn" href="{{base}}/contact/">Contact us</a>
  </div>
</section>"""


def nav_html(path):
    items = []
    for label, target in NAV:
        if isinstance(target, list):
            current = any(path == p for _, p in target)
            subs = "".join(
                f'<li><a href="{url(p)}"{CURRENT if p == path else ""}>{esc(l)}</a></li>'
                for l, p in target
            )
            items.append(
                f'<li class="nav-group{" is-current" if current else ""}"><button type="button" aria-expanded="false">{esc(label)}</button>'
                f'<ul class="subnav">{subs}</ul></li>'
            )
        else:
            items.append(f'<li><a href="{url(target)}"{CURRENT if target == path else ""}>{esc(label)}</a></li>')
    return "".join(items)


ORG_ID = SITE_URL + "/#org"
SITE_ID = SITE_URL + "/#website"
FRAMEWORK_ID = SITE_URL + "/market-traction/#milestones"

# Short names for breadcrumbs (pages not listed here are skipped as intermediate crumbs)
CRUMBS = {
    "/": "Home",
    "/services/interim-executive/": "Interim Executive",
    "/market-traction/": "Market Traction",
    "/market-traction/test/": "Market Traction Test",
    "/market-traction/stages/": "The six stages",
    "/about/": "About",
    "/contact/": "Contact",
    "/get-started/": "Get Started",
}

ROLES = [
    ("Interim Chief Marketing Officer (CMO)", "Own the market with an AI-first go-to-market: positioning, messaging, awareness and the engine that turns it into pipeline, including visibility in AI search and chat assistants."),
    ("Interim Chief Operating Officer (COO)", "Turn a promising company into a well-run one with an AI-first operating model: the cadence, processes, tools and team to scale."),
    ("Interim Chief Commercial Officer (CCO)", "Lead the whole commercial engine, from marketing through sales, onboarding and customer success, with AI-first commercial operations."),
]


def org_node():
    b = BUSINESS
    return {
        "@type": "ProfessionalService",
        "@id": ORG_ID,
        "name": b["name"],
        "url": SITE_URL + "/",
        "logo": SITE_URL + "/assets/img/moreland-logo.png",
        "image": SITE_URL + "/assets/img/share-card.png",
        "description": "Moreland Associates provides interim executive leaders (interim CMO, COO and CCO) who take technology companies to market traction, with an AI-first approach to go-to-market and operations.",
        "slogan": "Interim executive leaders who take technology companies to market traction.",
        "telephone": b["phone_e164"],
        "email": b["email"],
        "address": {
            "@type": "PostalAddress",
            "streetAddress": b["street"],
            "addressLocality": b["city"],
            "addressRegion": b["region"],
            "postalCode": b["postal"],
            "addressCountry": "US",
        },
        "openingHours": "Mo-Fr 08:00-17:00",
        "areaServed": "US",
        # Profiles elsewhere that describe the same company, so search and AI tools link them as one entity
        "sameAs": ["https://www.linkedin.com/company/104217/"],
        "knowsAbout": ["Interim executive leadership", "Interim CMO", "Interim COO", "Interim CCO",
                       "Market traction", "Beachhead market segment", "Go-to-market strategy",
                       "AI-first go-to-market", "Commercial operations", "Technology start-ups"],
    }


def framework_node():
    return {
        "@type": "DefinedTermSet",
        "@id": FRAMEWORK_ID,
        "name": "The Milestones to Market Traction",
        "description": "Moreland Associates' six-stage model of how a technology company progresses from a working product to a dominant position in one market segment.",
        "url": SITE_URL + "/market-traction/",
        "creator": {"@id": ORG_ID},
        "hasDefinedTerm": [
            {"@type": "DefinedTerm", "@id": SITE_URL + f"/market-traction/stages/{st['slug']}/#term",
             "name": st["name"], "termCode": str(i), "description": st["description"],
             "url": SITE_URL + f"/market-traction/stages/{st['slug']}/"}
            for i, st in enumerate(STAGES, 1)
        ],
    }


def breadcrumb_node(path):
    trail, cur = ["/"], "/"
    for part in path.strip("/").split("/"):
        if not part:
            continue
        cur += part + "/"
        trail.append(cur)
    stage_names = {f"/market-traction/stages/{st['slug']}/": st["name"] for st in STAGES}
    items = []
    for p in trail:
        name = CRUMBS.get(p) or stage_names.get(p)
        if name:
            items.append({"@type": "ListItem", "position": len(items) + 1, "name": name, "item": SITE_URL + p})
    return {"@type": "BreadcrumbList", "@id": SITE_URL + path + "#breadcrumb", "itemListElement": items}


def page_jsonld(meta, path, title):
    """Structured data for a page: always the WebPage (+ breadcrumbs), plus page-specific nodes."""
    if path == "/404":
        return ""
    page_type = {"/about/": "AboutPage", "/contact/": "ContactPage"}.get(path, "WebPage")
    page = {"@type": page_type, "@id": SITE_URL + path + "#webpage", "url": SITE_URL + path,
            "name": title, "description": meta["description"], "inLanguage": "en-US",
            "isPartOf": {"@id": SITE_ID}, "about": {"@id": ORG_ID}}
    graph = [page]
    if path != "/":
        graph.append(breadcrumb_node(path))
        page["breadcrumb"] = {"@id": SITE_URL + path + "#breadcrumb"}
    if path == "/":
        graph += [org_node(), {"@type": "WebSite", "@id": SITE_ID, "url": SITE_URL + "/",
                               "name": "Moreland Associates", "publisher": {"@id": ORG_ID}, "inLanguage": "en-US"}]
    if path == "/services/interim-executive/":
        graph.append({
            "@type": "Service", "@id": SITE_URL + path + "#service",
            "name": "Interim executive leadership", "serviceType": "Interim executive services",
            "description": "Full-time interim CMO, COO and CCO leadership for technology companies, with an AI-first approach to go-to-market, operations and commercial operations. Interim, not fractional.",
            "provider": {"@id": ORG_ID}, "areaServed": "US",
            "audience": {"@type": "BusinessAudience", "audienceType": "Technology companies, founders, CEOs, boards and venture capital partners"},
            "hasOfferCatalog": {"@type": "OfferCatalog", "name": "Interim executive roles", "itemListElement": [
                {"@type": "Offer", "itemOffered": {"@type": "Service", "name": n, "description": d}} for n, d in ROLES]},
        })
    if path in ("/market-traction/", "/market-traction/stages/"):
        graph.append(framework_node())
        page["mainEntity"] = {"@id": FRAMEWORK_ID}
    if path == "/market-traction/":
        graph += [
            {"@type": "DefinedTerm", "name": "Market traction",
             "description": "A company has achieved market traction when its product is being predictably sold to buyers in the same market segment, giving it a dominant position (a beachhead) in that segment.",
             "url": SITE_URL + "/market-traction/"},
            {"@type": "DefinedTerm", "name": "Beachhead",
             "description": "A defensible, dominant position in one market segment: not necessarily a majority share, but bigger than anyone else in that segment.",
             "url": SITE_URL + "/market-traction/#momentum"},
        ]
    stage = next((st for st in STAGES if path == f"/market-traction/stages/{st['slug']}/"), None)
    if stage:
        page["mainEntity"] = {"@id": SITE_URL + path + "#term"}
        graph.append({"@type": "DefinedTerm", "@id": SITE_URL + path + "#term", "name": stage["name"],
                      "description": stage["description"], "url": SITE_URL + path,
                      "inDefinedTermSet": {"@id": FRAMEWORK_ID}})
    if meta.get("faq"):
        graph.append({"@type": "FAQPage", "@id": SITE_URL + path + "#faq", "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in meta["faq"]]})
    data = {"@context": "https://schema.org", "@graph": graph}
    return '<script type="application/ld+json">' + json.dumps(data, ensure_ascii=False, separators=(",", ":")) + "</script>"


def layout(meta, body, path):
    title = meta["title"] if meta.get("exact_title") else f'{meta["title"]} | Moreland Associates'
    canonical = SITE_URL + path
    og_title = meta.get("og_title", title)
    og_desc = meta.get("og_description", meta["description"])
    card = share_card(path)
    og_image = SITE_URL + "/assets/img/" + card
    og_alt = f"{og_title}, Moreland Associates" if card != "share-card.png" else "Moreland Associates logo"
    md_link = "" if meta.get("noindex") else f'<link rel="alternate" type="text/markdown" href="{url(md_path(path))}" title="Markdown version">'
    # The preview copy on github.io must never be indexed in place of the real site.
    robots = '<meta name="robots" content="noindex">' if meta.get("noindex") or not PRODUCTION else ""
    jsonld = page_jsonld(meta, path, title)
    hero = re.search(r"class=\"hero\" style=\"background-image: url\('([^']+)'\)", body)
    hero_preload = f'<link rel="preload" as="image" href="{hero.group(1)}" fetchpriority="high">' if hero else ""
    ga = f"""<script async src="https://www.googletagmanager.com/gtag/js?id={GA_ID}"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag('js',new Date());gtag('config','{GA_ID}');</script>""" if PRODUCTION else ""
    b = BUSINESS
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{esc(title)}</title>
<meta name="description" content="{esc(meta['description'])}">
{robots}
<link rel="canonical" href="{canonical}">
{md_link}
<meta property="og:type" content="website">
<meta property="og:site_name" content="Moreland Associates">
<meta property="og:locale" content="en_US">
<meta property="og:title" content="{esc(og_title)}">
<meta property="og:description" content="{esc(og_desc)}">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="{og_image}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="{esc(og_alt)}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{esc(og_title)}">
<meta name="twitter:description" content="{esc(og_desc)}">
<meta name="twitter:image" content="{og_image}">
<link rel="icon" href="{url('/favicon.ico')}" sizes="any">
<link rel="icon" href="{url('/favicon.svg')}" type="image/svg+xml">
<link rel="icon" type="image/png" sizes="32x32" href="{url('/assets/img/favicon-32.png')}">
<link rel="apple-touch-icon" href="{url('/assets/img/apple-touch-icon.png')}">
<link rel="preload" href="{url('/assets/fonts/jost.woff2')}" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="{url('/assets/fonts/mulish.woff2')}" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="{url('/assets/css/site.css')}">
{hero_preload}
{jsonld}
{ga}
</head>
<body>
<a class="skip-link" href="#main">Skip to content</a>
<header class="site-header">
  <div class="wrap">
    <a class="brand" href="{url('/')}"><img src="{url('/assets/img/moreland-logo.svg')}" alt="Moreland Associates" width="640" height="147"></a>
    <button class="nav-toggle" type="button" aria-expanded="false" aria-controls="site-nav">Menu</button>
    <nav class="site-nav" id="site-nav" aria-label="Main"><ul>{nav_html(path)}</ul></nav>
  </div>
</header>
<main id="main">
{body}
</main>
<footer class="site-footer">
  <div class="wrap">
    <div>
      <h2>Moreland Associates</h2>
      <p>Interim executive leaders who take technology companies to market traction.</p>
    </div>
    <div>
      <h2>Contact</h2>
      <ul>
        <li><a href="tel:{b['phone_e164']}">{b['phone']}</a></li>
        <li><a href="mailto:{b['email']}">{b['email']}</a></li>
        <li>{esc(b['street'])}<br>{b['city']}, {b['region']} {b['postal']}</li>
      </ul>
    </div>
    <div>
      <h2>Explore</h2>
      <ul>
        <li><a href="{url('/services/interim-executive/')}">Interim Executive</a></li>
        <li><a href="{url('/market-traction/test/')}">Market Traction Test</a></li>
        <li><a href="{url('/about/')}">About Moreland</a></li>
        <li><a href="{url('/contact/')}">Contact</a></li>
      </ul>
    </div>
    <p class="legal">&copy; {date.today().year} Moreland Associates. All rights reserved.</p>
  </div>
</footer>
<script src="{url('/assets/js/site.js')}" defer></script>
</body>
</html>
"""


SIDEBARS = {
    "market-traction": ("Market Traction", NAV[2][1]),
}


def sidebar_html(name, path):
    heading, links = SIDEBARS[name]
    lis = "".join(f'<li><a href="{url(p)}"{CURRENT if p == path else ""}>{esc(l)}</a></li>' for l, p in links)
    return f'<aside class="sidebar" aria-label="{esc(heading)}"><h2>{esc(heading)}</h2><ul>{lis}</ul></aside>'


def render_tokens(body, path):
    body = body.replace("{{cta}}", CTA)
    body = body.replace("{{milestones}}", milestones_svg())
    body = re.sub(r"\{\{form:([\w-]+)\}\}", lambda m: form_html(m.group(1)), body)
    body = re.sub(r"\{\{sidebar:([\w-]+)\}\}", lambda m: sidebar_html(m.group(1), path), body)
    return body.replace("{{base}}", BASE)


# ---------- Market Traction milestones graphic ----------
# Recreated from Kim Leedy's original (identity guide, p.4): six milestone photos along an S-curve
# that runs flat along the bottom, climbs steeply through the middle and levels off top right.
# Drawn on the original's 1726 x 1408 canvas so tile and label positions match it exactly.
# Inline SVG, so text uses the site fonts and each tile links to its stage page.

MILESTONE_TILES = "photo"   # "photo" = the original 2006 tile photos; "icon" = line icons (kept as an alternative)

# Line icons, adapted from Feather (MIT) and Lucide (ISC), on a 24-unit grid. Used when MILESTONE_TILES = "icon".
ICONS = {
    "eureka": '<path d="M15 14c.2-1 .7-1.7 1.5-2.5 1-.9 1.5-2.2 1.5-3.5A6 6 0 0 0 6 8c0 1 .2 2.2 1.5 3.5.7.7 1.3 1.5 1.5 2.5"/><path d="M9 18h6M10 22h4"/>',
    "kaa-ching": '<circle cx="12" cy="12" r="10"/><path d="M15.5 8.5H11a2 2 0 0 0 0 4h2a2 2 0 0 1 0 4H8.5M12 6v2.5M12 16.5V19"/>',
    "two-thumbs-up": '<path d="M7 10v12M15 5.88 14 10h5.83a2 2 0 0 1 1.92 2.56l-2.33 8A2 2 0 0 1 17.5 22H4a2 2 0 0 1-2-2v-8a2 2 0 0 1 2-2h2.76a2 2 0 0 0 1.79-1.11L12 2a3.13 3.13 0 0 1 3 3.88Z"/>',
    "momentum": '<path d="M2 6c.6.5 1.2 1 2.5 1C7 7 7 5 9.5 5c2.6 0 2.4 2 5 2 2.5 0 2.5-2 5-2 1.3 0 1.9.5 2.5 1M2 12c.6.5 1.2 1 2.5 1 2.5 0 2.5-2 5-2 2.6 0 2.4 2 5 2 2.5 0 2.5-2 5-2 1.3 0 1.9.5 2.5 1M2 18c.6.5 1.2 1 2.5 1 2.5 0 2.5-2 5-2 2.6 0 2.4 2 5 2 2.5 0 2.5-2 5-2 1.3 0 1.9.5 2.5 1"/>',
    "building-buzz": '<path d="M9.94 15.5A2 2 0 0 0 8.5 14.06l-6.14-1.58a.5.5 0 0 1 0-.96L8.5 9.94A2 2 0 0 0 9.94 8.5l1.58-6.14a.5.5 0 0 1 .96 0l1.58 6.14a2 2 0 0 0 1.44 1.44l6.14 1.58a.5.5 0 0 1 0 .96l-6.14 1.58a2 2 0 0 0-1.44 1.44l-1.58 6.14a.5.5 0 0 1-.96 0z"/><path d="M20 3v4M22 5h-4"/>',
    "market-traction": '<path d="M6 9H4.5a2.5 2.5 0 0 1 0-5H6M18 9h1.5a2.5 2.5 0 0 0 0-5H18M4 22h16M10 14.66V17c0 .55-.47.98-.97 1.21C7.85 18.75 7 20.24 7 22M14 14.66V17c0 .55.47.98.97 1.21C16.15 18.75 17 20.24 17 22M18 2H6v7a6 6 0 0 0 12 0V2Z"/>',
}

# Tile top-left corners (200 x 200) and label anchors, measured from the original.
TILES = {
    "eureka": ((40, 1145), (140, 1392), ["Eureka"]),
    "kaa-ching": ((428, 1110), (528, 1356), ["Kaa Ching"]),
    "two-thumbs-up": ((768, 895), (868, 1142), ["Two", "Thumbs Up"]),
    "momentum": ((944, 527), (1044, 774), ["Momentum"]),
    "building-buzz": ((1162, 157), (1262, 404), ["Building", "Buzz"]),
    "market-traction": ((1489, 38), (1589, 284), ["Market", "Traction"]),
}
# Centre line of the S-curve, traced from the original artwork.
S_CURVE = [(-60, 1270), (150, 1261), (288, 1256), (408, 1252), (530, 1240), (648, 1210), (720, 1168),
           (800, 1108), (860, 1040), (910, 968), (960, 885), (1008, 790), (1056, 690), (1104, 572),
           (1152, 451), (1210, 370), (1270, 287), (1368, 161), (1440, 111), (1530, 88), (1704, 68), (1800, 62)]


def _curve(p):
    """Smooth path through points (Catmull-Rom converted to cubic Beziers)."""
    d = f"M{p[0][0]},{p[0][1]}"
    for i in range(len(p) - 1):
        p0, p1, p2 = p[max(i - 1, 0)], p[i], p[i + 1]
        p3 = p[min(i + 2, len(p) - 1)]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        d += f" C{c1[0]:.0f},{c1[1]:.0f} {c2[0]:.0f},{c2[1]:.0f} {p2[0]},{p2[1]}"
    return d


def _tile_art(slug, x, y, state, photo_href):
    if MILESTONE_TILES == "photo":
        return (f'<rect x="{x}" y="{y}" width="200" height="200" fill="#fff" stroke="#7d868c" stroke-width="3"/>'
                f'<image href="{photo_href(slug)}" x="{x + 6}" y="{y + 6}" width="188" height="188" preserveAspectRatio="xMidYMid slice"/>')
    fill, stroke = ("#2c5b8c", "#ffffff") if state == "active" else ("#ffffff", "#2c5b8c")
    return (f'<rect x="{x}" y="{y}" width="200" height="200" rx="16" fill="{fill}" stroke="#acc1e8" stroke-width="4"/>'
            f'<g transform="translate({x + 46} {y + 46}) scale(4.5)" fill="none" stroke="{stroke}" stroke-width="1.6" '
            f'stroke-linecap="round" stroke-linejoin="round">{ICONS[slug]}</g>')


def milestones_svg(active=None, link=True, uid="m", photo_href=None):
    """The Milestones to Market Traction. `active` = slug to highlight (earlier stages are marked passed)."""
    photo_href = photo_href or (lambda slug: url(f"/assets/img/milestones/{slug}.webp"))
    idx = next((i for i, s in enumerate(STAGES) if s["slug"] == active), None)
    tiles = []
    for i, s in enumerate(STAGES):
        (x, y), (lx, ly), lines = TILES[s["slug"]]
        state = "active" if i == idx else "passed" if idx is not None and i < idx else "ahead"
        art = _tile_art(s["slug"], x, y, state, photo_href)
        mark = ""
        if state == "active":
            mark = f'<rect x="{x - 12}" y="{y - 12}" width="224" height="224" rx="6" fill="none" stroke="#2c5b8c" stroke-width="10"/>'
        elif state == "passed":
            mark = (f'<circle cx="{x + 196}" cy="{y + 4}" r="30" fill="#2c5b8c" stroke="#fff" stroke-width="5"/>'
                    f'<path d="M{x + 181} {y + 4}l10 10 18-20" fill="none" stroke="#fff" stroke-width="7" stroke-linecap="round" stroke-linejoin="round"/>')
        spans = "".join(f'<tspan x="{lx}" dy="{"0" if j == 0 else "1.15em"}">{esc(t)}</tspan>' for j, t in enumerate(lines))
        colour = "#1d2226" if state == "active" else "#2c5b8c"
        label = f'<text class="ms-label" x="{lx}" y="{ly + (16 if state == "active" else 0)}" text-anchor="middle" font-size="36" font-weight="600" fill="{colour}">{spans}</text>'
        tip = f'<title>Stage {i + 1}: {esc(s["name"])}. {esc(s["headline"])}</title>'
        body = art + mark + label
        if link:
            cur = ' aria-current="step"' if state == "active" else ""
            tiles.append(f'<a href="{url("/market-traction/stages/" + s["slug"] + "/")}" class="ms-tile"{cur}>{tip}{body}</a>')
        else:
            tiles.append(f"<g>{tip}{body}</g>")

    names = ", ".join(s["name"] for s in STAGES)
    summary = f"The Milestones to Market Traction: {names}."
    if idx is not None:
        summary += f" Stage {idx + 1}, {STAGES[idx]['name']}, is highlighted."
    text = '<text class="ms-title" x="50" y="128" font-size="40" font-weight="600" fill="#2c5b8c">The Milestones to Market Traction</text>'
    if idx is None:
        text += ('<text class="ms-desc" font-size="34" fill="#3a434a">'
                 '<tspan x="50" y="185">This model describes the evolution of a</tspan>'
                 '<tspan x="50" dy="1.65em">technology company from inception through</tspan>'
                 '<tspan x="50" dy="1.65em">the achievement of market traction.</tspan></text>')
        test = f'<a href="{url("/market-traction/test/")}">' if link else "<g>"
        test_end = "</a>" if link else "</g>"
        text += (f'<g class="ms-callout"><rect x="78" y="460" width="645" height="310" fill="#fff" stroke="#2c5b8c" stroke-width="3"/>'
                 '<text x="400" y="545" text-anchor="middle" font-size="32" fill="#3a434a">Select a milestone for</text>'
                 '<text x="400" y="592" text-anchor="middle" font-size="32" fill="#3a434a">an explanation of each, then</text>'
                 f'{test}<text x="400" y="680" text-anchor="middle" font-size="38" font-weight="600" fill="#2c5b8c" text-decoration="underline">Take the Traction Test</text>{test_end}</g>')
        svc = f'<a href="{url("/services/interim-executive/")}">' if link else "<g>"
        svc_end = "</a>" if link else "</g>"
        text += ('<text class="ms-services" font-size="34" font-weight="600" fill="#5d6870">'
                 f'<tspan x="1166" y="1188">Moreland has </tspan>{svc}<tspan fill="#2c5b8c" text-decoration="underline">services</tspan>{svc_end}'
                 '<tspan x="1166" dy="1.45em">to address your needs</tspan>'
                 '<tspan x="1166" dy="1.45em">along the road to</tspan>'
                 '<tspan x="1166" dy="1.45em">market traction.</tspan></text>')
    else:
        text += f'<text class="ms-desc" x="50" y="185" font-size="34" fill="#3a434a">Stage {idx + 1} of 6: the milestones you\u2019ve passed and those ahead</text>'

    return (f'<svg class="milestones" viewBox="0 0 1726 1408" role="group" aria-labelledby="{uid}-t" '
            f'font-family="Jost, Futura, \'Century Gothic\', sans-serif">'
            f'<title id="{uid}-t">{esc(summary)}</title>'
            f'<defs><linearGradient id="{uid}-bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#dae4f5"/><stop offset="1" stop-color="#c8d3e8"/></linearGradient>'
            f'<clipPath id="{uid}-clip"><rect width="1726" height="1408" rx="18"/></clipPath></defs>'
            f'<g clip-path="url(#{uid}-clip)"><rect width="1726" height="1408" fill="url(#{uid}-bg)"/>'
            f'<path d="{_curve(S_CURVE)}" fill="none" stroke="#acc1e8" stroke-width="48"/></g>'
            + text + "".join(tiles) + "</svg>")


# ---------- Market Traction stages (one data file feeds the overview and the six stage pages) ----------

ORDINALS = ["one", "two", "three", "four", "five", "six"]


def stage_article(i, s, heading_tag, link_title, graphic=True):
    name = f'<a href="{url("/market-traction/stages/" + s["slug"] + "/")}">{esc(s["name"])}</a>' if link_title else esc(s["name"])
    nxt = f'<h3>What’s next?</h3><p>{s["next"]}</p>' if s.get("next") else ""
    if s.get("deep_dive"):
        nxt += f'<p><a href="{url(s["deep_dive"]["href"])}">{esc(s["deep_dive"]["text"])}</a></p>'
    fig = f'<figure class="stage-graphic">{milestones_svg(s["slug"], uid="ms-" + s["slug"])}</figure>' if graphic else ""
    return f"""<article class="stage" id="{s['slug']}">
  <p class="eyebrow">Stage {ORDINALS[i]} of six</p>
  <{heading_tag}>{name}</{heading_tag}>
  {fig}
  <h3>{s['headline']}</h3>
  <p>{s['body']}</p>
  {nxt}
</article>"""


def stage_sidebar(current):
    lis = "".join(
        f'<li><a href="{url("/market-traction/stages/" + s["slug"] + "/")}"{CURRENT if s["slug"] == current else ""}>{esc(s["name"])}</a></li>'
        for s in STAGES
    )
    return f'<aside class="sidebar" aria-label="Market traction stages"><h2>The six stages</h2><ul class="stage-nav">{lis}</ul></aside>'


def stage_pages():
    """Yield (meta, body, path) for the stages overview and each stage."""
    arts = '<figure class="figure-graphic">' + milestones_svg(uid="ms-all") + "</figure>\n"
    arts += "\n".join(stage_article(i, s, "h2", True, graphic=False) for i, s in enumerate(STAGES))
    yield ({
        "title": "The Six Stages of Market Traction",
        "description": "The six milestones a technology company passes on the road to market traction: Eureka, Kaa Ching, Two Thumbs Up, Momentum, Building Buzz and Market Traction.",
        "og_description": "From a working product to segment dominance: the six milestones, and what marketing and sales need at each one.",
    }, f"""<div class="page-head"><div class="wrap">
  <p class="eyebrow">Market Traction</p>
  <h1>The six stages of market traction</h1>
  <p class="lead">From a working product to segment dominance, there are predictable milestones on the way. Each has its own marketing and sales requirements.</p>
</div></div>
<section class="section"><div class="wrap with-sidebar">
  {stage_sidebar(None)}
  <div class="prose">
    {arts}
    <div class="actions"><a class="btn" href="{url('/market-traction/test/')}">Find your stage: take the test</a><a class="btn btn--ghost" href="{url('/get-started/?topic=market-traction')}">Talk with us</a></div>
  </div>
</div></section>
{{{{cta}}}}""", "/market-traction/stages/")

    for i, s in enumerate(STAGES):
        prev_s = STAGES[i - 1] if i > 0 else None
        next_s = STAGES[i + 1] if i + 1 < len(STAGES) else None
        pager = '<nav class="pager" aria-label="Stages">'
        pager += f'<a href="{url("/market-traction/stages/" + prev_s["slug"] + "/")}">← {esc(prev_s["name"])}</a>' if prev_s else "<span></span>"
        pager += f'<a href="{url("/market-traction/stages/" + next_s["slug"] + "/")}">{esc(next_s["name"])} →</a>' if next_s else "<span></span>"
        pager += "</nav>"
        yield ({
            "title": f'{s["name"]}: Market Traction Stage {i + 1} | Moreland',
            "exact_title": True,
            "description": s.get("seo_description", s["description"]),
            "og_title": f'{s["name"]}: Stage {i + 1} of the Milestones to Market Traction',
            "og_description": s["description"],
        }, f"""<section class="section"><div class="wrap with-sidebar">
  {stage_sidebar(s['slug'])}
  <div class="prose">
    {stage_article(i, s, "h1", False)}
    <div class="actions"><a class="btn" href="{url('/get-started/?topic=market-traction')}">Talk with us about your next milestone</a><a class="btn btn--ghost" href="{url('/market-traction/test/')}">Retake the test</a></div>
    {pager}
  </div>
</div></section>""", f'/market-traction/stages/{s["slug"]}/')


STAGES = json.loads((ROOT / "src" / "stages.json").read_text(encoding="utf-8"))


def redirect_html(target):
    full = BASE + target
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>Moved | Moreland Associates</title>
<link rel="canonical" href="{SITE_URL}{target}">
<meta name="robots" content="noindex">
<meta http-equiv="refresh" content="0; url={full}">
<script>location.replace({json.dumps(full)} + location.hash);</script>
</head><body><p>This page has moved to <a href="{full}">{SITE_URL}{target}</a>.</p></body></html>
"""


def main():
    sources = []
    for src in sorted(SRC.rglob("*.html")):
        text = src.read_text(encoding="utf-8")
        m = re.match(r"\s*<!--\s*(\{.*?\})\s*-->\s*", text, re.S)
        if not m:
            sys.exit(f"{src}: missing metadata comment")
        meta = json.loads(m.group(1))
        sources.append((meta, text[m.end():], meta["path"]))
    sources.extend(stage_pages())

    pages, markdown = [], []
    for meta, raw, path in sources:
        body = render_tokens(raw, path).replace("{{faq}}", faq_html(meta.get("faq", [])))
        dest = OUT / "404.html" if path == "/404" else OUT / path.strip("/") / "index.html"
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(layout(meta, body, path), encoding="utf-8")
        if not meta.get("noindex"):
            pages.append(path)
            md = page_markdown(meta, body, path)
            (OUT / md_path(path).lstrip("/")).write_text(md, encoding="utf-8")
            markdown.append((path, md))

    for old, new in REDIRECTS.items():
        # "folder/" keys become folder/index.html so the trailing-slash address keeps working
        dest = OUT / old / "index.html" if old.endswith("/") else OUT / f"{old}.html"
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(redirect_html(new), encoding="utf-8")

    today = date.today().isoformat()
    entries = "".join(f"  <url><loc>{SITE_URL}{p}</loc><lastmod>{today}</lastmod></url>\n" for p in sorted(pages))
    (OUT / "sitemap.xml").write_text(
        f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{entries}</urlset>\n',
        encoding="utf-8",
    )
    (OUT / "robots.txt").write_text(f"User-agent: *\nAllow: /\n\nSitemap: {SITE_URL}/sitemap.xml\n", encoding="utf-8")
    (OUT / ".nojekyll").write_text("", encoding="utf-8")
    (OUT / "llms.txt").write_text(llms_txt(), encoding="utf-8")
    # Every page in one file, in site order, for agents that want the whole site at once
    order = {p: i for i, p in enumerate(LLMS_PAGES)}
    full = "\n\n".join(md for p, md in sorted(markdown, key=lambda pm: (order.get(pm[0], 99), pm[0])))
    (OUT / "llms-full.txt").write_text(full, encoding="utf-8")
    # GitHub Pages custom domain: only in the live build (it would redirect the github.io preview)
    cname = OUT / "CNAME"
    if PRODUCTION:
        cname.write_text("www.morelandassoc.com\n", encoding="utf-8")
    elif cname.exists():
        cname.unlink()
    print(f"Built {len(pages)} pages and {len(REDIRECTS)} redirects ({'production' if PRODUCTION else 'preview'}, base='{BASE}')")


def share_card(path):
    """Per-page social image from tools/make_share_cards.py, or the logo card."""
    name = f'share/{path.strip("/").replace("/", "-") or "home"}.jpg'
    return name if (OUT / "assets" / "img" / name).exists() else "share-card.png"


def md_path(path):
    """Markdown twin of a page, following the llmstxt.org convention (folder URLs get index.html.md)."""
    return path + "index.html.md" if path.endswith("/") else path + ".md"


class MarkdownWriter(HTMLParser):
    """Turns a rendered page body into clean Markdown for AI agents: no navigation, forms or graphics."""
    SKIP = {"svg", "script", "style", "noscript", "button", "select", "textarea", "aside", "nav", "label"}
    VOID = {"input", "img", "br", "hr", "meta", "link", "source", "wbr"}
    BLOCKS = {"p", "h1", "h2", "h3", "h4", "li", "figcaption", "summary", "legend", "blockquote", "div", "section", "footer", "ul", "ol", "details", "figure", "fieldset"}

    def __init__(self, page_url):
        super().__init__(convert_charrefs=True)
        self.page_url, self.blocks, self.buf = page_url, [], []
        self.skip, self.lists, self.hrefs, self.quote, self.prefix, self.wrap = 0, [], [], 0, "", ""

    def flush(self):
        text = re.sub(r"[ \t]+", " ", "".join(self.buf)).strip()
        text = re.sub(r"\*\*\s*\*\*|__", "", text)
        if text:
            line = self.prefix + self.wrap + text + self.wrap
            if self.quote:
                line = "> " + line
            self.blocks.append(("li" if self.prefix.lstrip().startswith(("-", "1", "2", "3", "4", "5", "6", "7", "8", "9")) else "p", line))
        self.buf, self.prefix, self.wrap = [], "", ""

    def handle_startendtag(self, tag, attrs):
        if not self.skip:
            self.handle_starttag(tag, attrs)

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        cls = (a.get("class") or "").split()
        if self.skip:
            self.skip += tag not in self.VOID
            return
        if tag == "svg" and "milestones" in cls:
            # The graphic becomes a plain list of the six milestones
            self.flush()
            for i, st in enumerate(STAGES, 1):
                self.blocks.append(("li", f"{i}. [{st['name']}]({SITE_URL}/market-traction/stages/{st['slug']}/): {st['description']}"))
            self.skip = 1
            return
        if tag in self.SKIP or a.get("aria-hidden") == "true" or "n" in cls or "skip-link" in cls:
            self.skip = 1
            return
        if tag == "form" and "quiz" not in cls:
            self.flush()
            self.blocks.append(("p", f"_A contact form appears here on the web page ({self.page_url}). You can also email info@morelandassoc.com or call (510) 833-7308._"))
            self.skip = 1
            return
        if tag in self.BLOCKS:
            self.flush()
        if tag in ("ul", "ol"):
            self.lists.append([tag, 0, cls])
        elif tag == "form":
            self.lists.append(["ol", 0, cls])
        elif tag in ("li", "legend") and self.lists:
            kind = self.lists[-1]
            kind[1] += 1
            self.prefix = "  " * (len(self.lists) - 1) + (f"{kind[1]}. " if kind[0] == "ol" else "- ")
            if tag == "legend":
                self.wrap = ""
        elif tag in ("h1", "h2", "h3", "h4"):
            self.prefix = "#" * int(tag[1]) + " "
        elif tag == "summary":
            self.prefix = "### "
        elif tag == "figcaption":
            self.wrap = "_"
        elif tag == "blockquote":
            self.quote += 1
        elif tag == "footer" and self.quote:
            self.prefix = "— "
        elif tag == "a":
            if self.buf and self.buf[-1].startswith("]("):
                self.buf.append(" · ")
            self.hrefs.append(a.get("href", ""))
            self.buf.append("[")
        elif tag in ("strong", "b"):
            self.buf.append("**")
        elif tag in ("em", "i"):
            self.buf.append("_")
        elif tag == "br":
            self.buf.append(" ")
        elif tag == "img" and a.get("alt"):
            self.buf.append(f'![{a["alt"]}]({urljoin(self.page_url, a.get("src", ""))})')

    def handle_endtag(self, tag):
        if self.skip:
            self.skip -= 1
            return
        if tag == "a" and self.hrefs:
            href = self.hrefs.pop()
            self.buf.append(f"]({urljoin(self.page_url, href)})" if href else "]")
        elif tag in ("strong", "b"):
            self.buf.append(":** " if self.lists and "contact-list" in self.lists[-1][2] else "**")
        elif tag in ("em", "i"):
            self.buf.append("_")
        elif tag in self.BLOCKS or tag == "form":
            self.flush()
            if tag in ("ul", "ol", "form") and self.lists:
                self.lists.pop()
            if tag == "blockquote":
                self.quote -= 1

    def handle_data(self, data):
        if not self.skip:
            self.buf.append(re.sub(r"\s+", " ", data))

    def markdown(self):
        self.flush()
        out, prev = [], None
        for kind, line in self.blocks:
            if out and not (kind == prev == "li"):
                out.append("")
            out.append(line)
            prev = kind
        return "\n".join(out)


def page_markdown(meta, body, path):
    page_url = SITE_URL + path
    title = meta["title"].split(" | ")[0]
    w = MarkdownWriter(page_url)
    w.feed(body.replace(BASE + "/", "/") if BASE else body)
    b = BUSINESS
    return f"""---
title: {json.dumps(title, ensure_ascii=False)}
url: {page_url}
description: {json.dumps(meta["description"], ensure_ascii=False)}
---

{w.markdown()}

---

Moreland Associates · {b['phone']} · {b['email']} · {b['street']}, {b['city']}, {b['region']} {b['postal']} · {SITE_URL}/
"""


LLMS_PAGES = ["/", "/services/interim-executive/", "/about/", "/market-traction/", "/market-traction/stages/",
              *[f"/market-traction/stages/{st}/" for st in ("eureka", "kaa-ching", "two-thumbs-up", "momentum", "building-buzz", "market-traction")],
              "/market-traction/test/", "/contact/", "/get-started/"]


def faq_html(faq):
    """Visible FAQ section; the same questions feed the FAQPage structured data."""
    if not faq:
        return ""
    items = "".join(f"<details><summary>{esc(q)}</summary><p>{esc(a)}</p></details>" for q, a in faq)
    return f'<section class="faq" aria-labelledby="faq-title"><h2 id="faq-title">Frequently asked questions</h2>{items}</section>'


def llms_txt():
    """Plain-language site summary for AI assistants (llmstxt.org convention)."""
    b = BUSINESS
    stages = "\n".join(f"{i}. [{st['name']}]({SITE_URL}/market-traction/stages/{st['slug']}/): {st['description']}"
                        for i, st in enumerate(STAGES, 1))
    roles = "\n".join(f"- **{n}:** {d}" for n, d in ROLES)
    return f"""# Moreland Associates

> Moreland Associates provides interim executive leaders (interim CMO, COO and CCO) who take technology companies to market traction, with an AI-first approach to go-to-market and operations. Based in {b['city']}, California, serving companies across the US.

## Interim executive leadership

Every company's road to market traction runs through a series of milestones. When the next one calls for a different leader than the one a company has, or one it doesn't have yet, Moreland's interim executives step in. They lead from the inside, setting the strategy, executing it, and building the team and systems that keep delivering after the engagement ends.

{roles}

**Interim, not fractional.** CMO, COO and CCO are cross-functional roles at the centre of the business. Part-time leadership in these seats slows everyone down; fractional works well for finance or IT, but the roles that run the business need someone in the seat.

**When companies bring in an interim executive:** after a pivot or when reaching a milestone; once the beachhead segment is chosen and the company needs someone to lead now and help hire the permanent leader; when go-to-market needs rebuilding, AI-first; when founders aren't sure what the role should look like; or when help is needed immediately rather than after a long search.

## The Milestones to Market Traction

Moreland's six-stage model of how a technology company progresses from a working product to a dominant position (a beachhead) in one market segment. A company has market traction when its product is being predictably sold to buyers in the same segment.

{stages}

Momentum is the inflection point, where a company chooses its beachhead segment. Moreland's guidance: make competitive differentiation the first criterion; test candidate segments by trying to achieve repeat sales; and choose only after at least two (ideally three or four) segments have been tested.

## Pages

Each page has a Markdown version at the same address plus `index.html.md`; [llms-full.txt]({SITE_URL}/llms-full.txt) has every page in one file.

- [Home]({SITE_URL}/index.html.md)
- [Interim Executive services]({SITE_URL}/services/interim-executive/index.html.md): interim CMO, COO and CCO roles, why interim not fractional, when to use one, FAQs
- [About Moreland Associates]({SITE_URL}/about/index.html.md): who we are, how we work, what clients say
- [What is market traction?]({SITE_URL}/market-traction/index.html.md): definition, the milestones graphic, choosing a beachhead segment, FAQs
- [The six stages]({SITE_URL}/market-traction/stages/index.html.md)
- [Market Traction Test]({SITE_URL}/market-traction/test/index.html.md): six yes/no questions that place a company on the milestones
- [Contact]({SITE_URL}/contact/index.html.md)

## Contact

{b['phone']} · {b['email']} · {b['street']}, {b['city']}, {b['region']} {b['postal']}
"""


if __name__ == "__main__":
    main()
