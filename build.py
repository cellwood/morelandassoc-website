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
FORM_ENDPOINT = "https://formspree.io/f/REPLACE_WITH_FORM_ID"
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
    body = re.sub(r"\{\{form:([\w-]+)\}\}", lambda m: form_html(m.group(1)), body)
    body = re.sub(r"\{\{sidebar:([\w-]+)\}\}", lambda m: sidebar_html(m.group(1), path), body)
    return body.replace("{{base}}", BASE)


# ---------- Market Traction stages (one data file feeds the overview and the six stage pages) ----------

ORDINALS = ["one", "two", "three", "four", "five", "six"]


def stage_article(i, s, heading_tag, link_title):
    name = f'<a href="{url("/market-traction/stages/" + s["slug"] + "/")}">{esc(s["name"])}</a>' if link_title else esc(s["name"])
    nxt = f'<h3>What’s next?</h3><p>{s["next"]}</p>' if s.get("next") else ""
    return f"""<article class="stage" id="{s['slug']}">
  <p class="eyebrow">Stage {ORDINALS[i]} of six</p>
  <{heading_tag}>{name}</{heading_tag}>
  <figure class="stage-graphic"><img src="{url('/assets/img/' + s['image'])}" alt="Market traction road map with {esc(s['name'])} highlighted: Eureka, Kaa Ching, Two Thumbs Up, Momentum, Building Buzz, Market Traction" width="1400" height="492" loading="lazy"></figure>
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
    arts = "\n".join(stage_article(i, s, "h2", True) for i, s in enumerate(STAGES))
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
