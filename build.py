#!/usr/bin/env python3
"""Build the Moreland Associates website.

Reads page bodies from src/pages/ and writes finished HTML into docs/, which
GitHub Pages publishes. Also writes the old-URL redirects, sitemap.xml,
robots.txt and 404.html. Uses only the Python standard library.

    python3 build.py              # preview build (served from cellwood.github.io/morelandassoc-website)
    python3 build.py --production # live build (served from www.morelandassoc.com)
"""
import html
import json
import re
import sys
from datetime import date
from pathlib import Path

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
    ("Services", [
        ("Interim Executive", "/services/interim-executive/"),
        ("Product Marketing", "/services/product-marketing/"),
        ("Corporate Marketing", "/services/corporate-marketing/"),
        ("Revenue Lifecycle", "/services/revenue-lifecycle/"),
        ("Field Events", "/services/field-events/"),
    ]),
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
    "new-page-1": "/services/corporate-marketing/",
    "new-page-3": "/services/revenue-lifecycle/",
    "new-page-4": "/services/product-marketing/",
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
    "event-in-a-box": "/services/field-events/",
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


def org_jsonld():
    b = BUSINESS
    data = {
        "@context": "https://schema.org",
        "@type": "ProfessionalService",
        "name": b["name"],
        "url": SITE_URL + "/",
        "logo": SITE_URL + "/assets/img/moreland-logo.png",
        "image": SITE_URL + "/assets/img/share-card.png",
        "description": "Moreland Associates is a consulting firm of seasoned executives who help technology companies achieve market traction, with interim executive, product marketing, corporate marketing and revenue lifecycle services.",
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
    }
    return '<script type="application/ld+json">' + json.dumps(data, indent=1) + "</script>"


def layout(meta, body, path):
    title = meta["title"] if meta.get("exact_title") else f'{meta["title"]} | Moreland Associates'
    canonical = SITE_URL + path
    og_image = SITE_URL + "/assets/img/" + meta.get("og_image", "share-card.png")
    # The preview copy on github.io must never be indexed in place of the real site.
    robots = '<meta name="robots" content="noindex">' if meta.get("noindex") or not PRODUCTION else ""
    jsonld = org_jsonld() if path == "/" else ""
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
<meta property="og:type" content="website">
<meta property="og:site_name" content="Moreland Associates">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(meta['description'])}">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="{og_image}">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="{url('/favicon.ico')}" sizes="any">
<link rel="icon" href="{url('/favicon.svg')}" type="image/svg+xml">
<link rel="icon" type="image/png" sizes="32x32" href="{url('/assets/img/favicon-32.png')}">
<link rel="apple-touch-icon" href="{url('/assets/img/apple-touch-icon.png')}">
<link rel="preload" href="{url('/assets/fonts/jost.woff2')}" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="{url('/assets/fonts/mulish.woff2')}" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="{url('/assets/css/site.css')}">
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
      <p>Seasoned executive entrepreneurs helping technology companies build market traction.</p>
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
        <li><a href="{url('/services/interim-executive/')}">Services</a></li>
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
    "services": ("Services", NAV[1][1]),
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
# Recreated from the original Moreland site (identity guide, Kim Leedy): six milestone tiles
# climbing an S-curve. Inline SVG so labels use the site fonts and each tile links to its stage.
# Icons are adapted from Feather (MIT) and Lucide (ISC), drawn on a 24-unit grid.

ICONS = {
    "eureka": '<path d="M15 14c.2-1 .7-1.7 1.5-2.5 1-.9 1.5-2.2 1.5-3.5A6 6 0 0 0 6 8c0 1 .2 2.2 1.5 3.5.7.7 1.3 1.5 1.5 2.5"/><path d="M9 18h6M10 22h4"/>',
    "kaa-ching": '<circle cx="12" cy="12" r="10"/><path d="M15.5 8.5H11a2 2 0 0 0 0 4h2a2 2 0 0 1 0 4H8.5M12 6v2.5M12 16.5V19"/>',
    "two-thumbs-up": '<path d="M7 10v12M15 5.88 14 10h5.83a2 2 0 0 1 1.92 2.56l-2.33 8A2 2 0 0 1 17.5 22H4a2 2 0 0 1-2-2v-8a2 2 0 0 1 2-2h2.76a2 2 0 0 0 1.79-1.11L12 2a3.13 3.13 0 0 1 3 3.88Z"/>',
    "momentum": '<path d="M2 6c.6.5 1.2 1 2.5 1C7 7 7 5 9.5 5c2.6 0 2.4 2 5 2 2.5 0 2.5-2 5-2 1.3 0 1.9.5 2.5 1M2 12c.6.5 1.2 1 2.5 1 2.5 0 2.5-2 5-2 2.6 0 2.4 2 5 2 2.5 0 2.5-2 5-2 1.3 0 1.9.5 2.5 1M2 18c.6.5 1.2 1 2.5 1 2.5 0 2.5-2 5-2 2.6 0 2.4 2 5 2 2.5 0 2.5-2 5-2 1.3 0 1.9.5 2.5 1"/>',
    "building-buzz": '<path d="M9.94 15.5A2 2 0 0 0 8.5 14.06l-6.14-1.58a.5.5 0 0 1 0-.96L8.5 9.94A2 2 0 0 0 9.94 8.5l1.58-6.14a.5.5 0 0 1 .96 0l1.58 6.14a2 2 0 0 0 1.44 1.44l6.14 1.58a.5.5 0 0 1 0 .96l-6.14 1.58a2 2 0 0 0-1.44 1.44l-1.58 6.14a.5.5 0 0 1-.96 0z"/><path d="M20 3v4M22 5h-4"/>',
    "market-traction": '<path d="M6 9H4.5a2.5 2.5 0 0 1 0-5H6M18 9h1.5a2.5 2.5 0 0 0 0-5H18M4 22h16M10 14.66V17c0 .55-.47.98-.97 1.21C7.85 18.75 7 20.24 7 22M14 14.66V17c0 .55.47.98.97 1.21C16.15 18.75 17 20.24 17 22M18 2H6v7a6 6 0 0 0 12 0V2Z"/>',
}
# Tile centres on a 1000 x 600 canvas, following the original S-curve layout.
TILE_POS = [(95, 478), (262, 462), (424, 372), (556, 252), (696, 150), (880, 100)]
LABEL_LINES = {"two-thumbs-up": ["Two", "Thumbs Up"], "building-buzz": ["Building", "Buzz"], "market-traction": ["Market", "Traction"]}


def _curve(points):
    """Smooth path through points (Catmull-Rom converted to cubic Béziers)."""
    p = [(-40, 505)] + points + [(1040, 70)]
    d = f"M{p[0][0]},{p[0][1]}"
    for i in range(len(p) - 1):
        p0, p1, p2 = p[max(i - 1, 0)], p[i], p[i + 1]
        p3 = p[min(i + 2, len(p) - 1)]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        d += f" C{c1[0]:.0f},{c1[1]:.0f} {c2[0]:.0f},{c2[1]:.0f} {p2[0]},{p2[1]}"
    return d


def milestones_svg(active=None, link=True, uid="m"):
    """The six-milestone road map. `active` = slug of the stage to highlight (earlier stages show as passed)."""
    idx = next((i for i, s in enumerate(STAGES) if s["slug"] == active), None)
    tiles = []
    for i, (s, (x, y)) in enumerate(zip(STAGES, TILE_POS)):
        state = "active" if i == idx else "passed" if idx is not None and i < idx else "ahead"
        tile_fill, icon_col, ring = {
            "active": ("#2c5b8c", "#ffffff", "#2c5b8c"),
            "passed": ("#ffffff", "#2c5b8c", "#71a1d5"),
            "ahead": ("#ffffff", "#2c5b8c", "#acc1e8"),
        }[state]
        badge = (f'<circle cx="{x - 46}" cy="{y - 46}" r="15" fill="#71a1d5"/>'
                 f'<path d="M{x - 53} {y - 46}l5 5 9-10" fill="none" stroke="#fff" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>'
                 if state == "passed" else
                 f'<circle cx="{x - 46}" cy="{y - 46}" r="15" fill="{"#1d2226" if state == "active" else "#71a1d5"}"/>'
                 f'<text x="{x - 46}" y="{y - 40}" text-anchor="middle" font-size="17" font-weight="600" fill="#fff">{i + 1}</text>')
        lines = LABEL_LINES.get(s["slug"], [s["name"]])
        label = "".join(f'<tspan x="{x}" dy="{0 if j == 0 else '1.1em'}">{esc(t)}</tspan>' for j, t in enumerate(lines))
        weight = "600" if state == "active" else "500"
        halo = f'<rect x="{x - 64}" y="{y - 64}" width="128" height="128" rx="16" fill="none" stroke="#2c5b8c" stroke-opacity=".25" stroke-width="6"/>' if state == "active" else ""
        body = (f'{halo}<rect x="{x - 52}" y="{y - 52}" width="104" height="104" rx="10" fill="{tile_fill}" stroke="{ring}" stroke-width="3"/>'
                f'<g transform="translate({x - 28} {y - 28}) scale(2.333)" fill="none" stroke="{icon_col}" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">{ICONS[s["slug"]]}</g>'
                f'{badge}<text class="ms-label" x="{x}" y="{y + 90}" text-anchor="middle" font-size="22" font-weight="{weight}" fill="{"#1d2226" if state == "active" else "#2c5b8c"}">{label}</text>')
        tip = f'<title>Stage {i + 1}: {esc(s["name"])}. {esc(s["headline"])}</title>'
        if link:
            href = url(f'/market-traction/stages/{s["slug"]}/')
            cur = ' aria-current="step"' if state == "active" else ""
            tiles.append(f'<a href="{href}" class="ms-tile"{cur}>{tip}{body}</a>')
        else:
            tiles.append(f'<g>{tip}{body}</g>')
    names = ", ".join(s["name"] for s in STAGES)
    summary = f"The road to market traction in six milestones: {names}."
    if idx is not None:
        summary += f" Stage {idx + 1}, {STAGES[idx]['name']}, is highlighted."
    return (f'<svg class="milestones" viewBox="0 0 1000 600" role="group" aria-labelledby="{uid}-t" '
            f'font-family="Jost, Futura, \'Century Gothic\', sans-serif">'
            f'<title id="{uid}-t">{esc(summary)}</title>'
            f'<rect width="1000" height="600" rx="14" fill="#dae4f5"/>'
            f'<text class="ms-title" x="44" y="70" font-size="32" font-weight="500" fill="#2c5b8c">Moreland’s Market Traction Milestones</text>'
            f'<text class="ms-sub" x="44" y="106" font-size="21" fill="#3a434a">{"From inception to segment dominance" if idx is None else "Your stage and the milestones ahead"}</text>'
            f'<path d="{_curve(TILE_POS)}" fill="none" stroke="#acc1e8" stroke-width="34" stroke-linecap="round"/>'
            f'<path d="{_curve(TILE_POS)}" fill="none" stroke="#ffffff" stroke-opacity=".55" stroke-width="4" stroke-linecap="round" stroke-dasharray="2 14"/>'
            + "".join(tiles) + "</svg>")


# ---------- Market Traction stages (one data file feeds the overview and the six stage pages) ----------

ORDINALS = ["one", "two", "three", "four", "five", "six"]


def stage_article(i, s, heading_tag, link_title, graphic=True):
    name = f'<a href="{url("/market-traction/stages/" + s["slug"] + "/")}">{esc(s["name"])}</a>' if link_title else esc(s["name"])
    nxt = f'<h3>What’s next?</h3><p>{s["next"]}</p>' if s.get("next") else ""
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
        "description": "The six milestones a technology start-up passes on the road to market traction: Eureka, Kaa Ching, Two Thumbs Up, Momentum, Building Buzz and Market Traction.",
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
            "title": f'{s["name"]}: Stage {ORDINALS[i].title()} of Market Traction',
            "description": s["description"],
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

    pages = []
    for meta, raw, path in sources:
        body = render_tokens(raw, path)
        dest = OUT / "404.html" if path == "/404" else OUT / path.strip("/") / "index.html"
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(layout(meta, body, path), encoding="utf-8")
        if not meta.get("noindex"):
            pages.append(path)

    for old, new in REDIRECTS.items():
        (OUT / f"{old}.html").write_text(redirect_html(new), encoding="utf-8")

    today = date.today().isoformat()
    entries = "".join(f"  <url><loc>{SITE_URL}{p}</loc><lastmod>{today}</lastmod></url>\n" for p in sorted(pages))
    (OUT / "sitemap.xml").write_text(
        f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{entries}</urlset>\n',
        encoding="utf-8",
    )
    (OUT / "robots.txt").write_text(f"User-agent: *\nAllow: /\n\nSitemap: {SITE_URL}/sitemap.xml\n", encoding="utf-8")
    (OUT / ".nojekyll").write_text("", encoding="utf-8")
    print(f"Built {len(pages)} pages and {len(REDIRECTS)} redirects ({'production' if PRODUCTION else 'preview'}, base='{BASE}')")


if __name__ == "__main__":
    main()
