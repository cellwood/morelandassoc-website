"""Make the 1200 x 630 share images (Open Graph / LinkedIn / Slack previews) for each page.

Needs Pillow (pip install pillow). Run from the website folder:
    python3 tools/make_share_cards.py
then rebuild. build.py picks up docs/assets/img/share/<page>.jpg automatically;
pages without a card fall back to share-card.png (the logo).
"""
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parent.parent
IMG = ROOT / "docs" / "assets" / "img"
FONTS = ROOT / "docs" / "assets" / "fonts"
OUT = IMG / "share"
# Higher-resolution originals live in the private playbook next to this repo; fall back to the site copies.
PLAYBOOK = ROOT.parent / "playbook" / "brand"

W, H, SPLIT = 1200, 630, 700
WASH, BAND, INK, MUTED, LINK, BLUE = "#f4f3f3", "#c8d3e8", "#1d2226", "#5d6870", "#2c5b8c", "#70a1d6"

STAGES = json.loads((ROOT / "src" / "stages.json").read_text(encoding="utf-8"))
ORDINAL = ["one", "two", "three", "four", "five", "six"]


def font(name, size, weight):
    f = ImageFont.truetype(str(FONTS / f"{name}.woff2"), size)
    f.set_variation_by_axes([weight])
    return f


def hero():
    src = PLAYBOOK / "photos" / "hero-rowing-moreland-blue.png"
    return Image.open(src if src.exists() else IMG / "hero-rowing-graded.webp").convert("RGB")


def tile(i):
    st = STAGES[i]
    src = PLAYBOOK / "graphics" / "photos-ai" / "final" / f"{i + 1}-{st['slug']}.png"
    return Image.open(src if src.exists() else IMG / "milestones" / f"{st['slug']}.webp").convert("RGB")


def mosaic():
    """All six milestone tiles, 2 across by 3 down, in stage order."""
    w, h, gap = (W - SPLIT) // 2, H // 3, 4
    m = Image.new("RGB", (W - SPLIT, H), "white")
    for i in range(6):
        t = ImageOps.fit(tile(i), (w - gap, h - gap), Image.LANCZOS)
        m.paste(t, ((i % 2) * w + gap // 2, (i // 2) * h + gap // 2))
    return m


def wrap(draw, text, f, width):
    lines, line = [], ""
    for word in text.split(" "):  # non-breaking spaces keep words together
        test = f"{line} {word}".strip()
        if draw.textlength(test, font=f) <= width:
            line = test
        else:
            lines.append(line)
            line = word
    return lines + [line]


def card(slug, eyebrow, headline, sub, picture, centering=(0.5, 0.5)):
    img = Image.new("RGB", (W, H), WASH)
    img.paste(ImageOps.fit(picture, (W - SPLIT, H), Image.LANCZOS, centering=centering), (SPLIT, 0))
    d = ImageDraw.Draw(img)
    logo = Image.open(IMG / "moreland-logo.png").convert("RGBA")
    logo = logo.resize((300, round(300 * logo.height / logo.width)), Image.LANCZOS)
    img.paste(logo, (64, 52), logo)

    x, width = 64, SPLIT - 64 - 56
    # Shrink the headline until it fits in three lines
    for size in (58, 52, 46, 42):
        hf = font("jost", size, 300)
        lines = wrap(d, headline, hf, width)
        if len(lines) <= 3:
            break
    sf = font("mulish", 25, 500)
    sub_lines = wrap(d, sub, sf, width) if sub else []
    block = 34 + len(lines) * round(size * 1.15) + (18 + len(sub_lines) * 36 if sub_lines else 0)
    y = 150 + (400 - block) // 2

    ef = font("jost", 20, 500)
    cx = x
    for ch in eyebrow.upper():  # letter-spaced like the site's eyebrows
        d.text((cx, y), ch, font=ef, fill=MUTED)
        cx += d.textlength(ch, font=ef) + 4
    y += 34
    for line in lines:
        d.text((x, y), line, font=hf, fill=INK)
        y += round(size * 1.15)
    if sub_lines:
        y += 18
        for line in sub_lines:
            d.text((x, y), line, font=sf, fill=MUTED)
            y += 36

    d.text((x, H - 70), "morelandassoc.com", font=font("jost", 22, 500), fill=LINK)
    d.rectangle([0, H - 14, SPLIT, H], fill=BAND)
    d.rectangle([SPLIT - 6, 0, SPLIT, H], fill=BLUE)
    OUT.mkdir(parents=True, exist_ok=True)
    img.save(OUT / f"{slug}.jpg", quality=86, optimize=True, progressive=True)
    print("wrote", f"share/{slug}.jpg")


def main():
    row = hero()
    tiles = mosaic()
    card("home", "Interim executive leadership", "Seasoned interim executives who lead tech companies to market traction",
         "Interim CMO, COO and CCO", row)
    card("services-interim-executive", "Interim executive", "Interim CMO, COO\u00a0&\u00a0CCO",
         "AI-first go-to-market and operations. Interim, not fractional.", row, (0.35, 0.5))
    card("about", "About Moreland", "Interim leaders who leave companies stronger than they found them", "", row, (0.65, 0.5))
    card("contact", "Contact", "Let's talk about your next milestone", "(510) 833-7308 · info@morelandassoc.com", row, (0.8, 0.5))
    card("get-started", "Get started", "Let's talk about your next milestone", "We'll be in touch right away.", row, (0.8, 0.5))
    card("market-traction", "Market traction", "What is market traction?", "The six milestones from a working product to a beachhead", tiles)
    card("market-traction-stages", "Market traction", "The six stages of market traction",
         "What marketing and sales need at each milestone", tiles)
    card("market-traction-test", "Market Traction Test", "Where is your company on the road to market traction?",
         "Six questions. 30 seconds.", tiles)
    card("insights", "Insights", "Straight answers on interim executive leadership", "Interim CMO, COO and CCO", row, (0.3, 0.5))
    card("insights-interim-vs-fractional-cmo", "Insights", "Interim CMO vs fractional CMO: which do you need?", "", row, (0.45, 0.5))
    card("insights-how-long-interim-executive-engagement", "Insights", "How long does an interim executive engagement last?", "", row, (0.6, 0.5))
    card("insights-when-to-hire-interim-coo", "Insights", "When should a start-up hire an interim COO?", "", row, (0.4, 0.5))
    card("insights-what-does-a-cco-do", "Insights", "What does a Chief Commercial Officer do?", "", row, (0.7, 0.5))
    card("insights-ai-first-go-to-market", "Insights", "What is an AI-first go-to-market?", "", row, (0.55, 0.5))
    subs = ["Your product works and is ready for customers.",
            "First revenue: your cash register rings.",
            "Credible reference customers your buyers recognize.",
            "The whole company focused on one beachhead segment.",
            "A recognized key player in your target segment.",
            "You dominate your segment and can expand to the next."]
    for i, st in enumerate(STAGES):
        card(f"market-traction-stages-{st['slug']}", f"Stage {ORDINAL[i]} of six", st["name"], subs[i], tile(i))


if __name__ == "__main__":
    main()
