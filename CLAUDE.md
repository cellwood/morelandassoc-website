# morelandassoc.com — instructions for Claude

This repository is the live website for Moreland Associates (www.morelandassoc.com), served by GitHub Pages from `main:/docs`. The site owner is non-technical: explain steps plainly, one at a time, and never publish without their approval.

## How the site is built

- Page sources: `src/pages/**/*.html` (JSON front-matter comment at the top: path, title, description, og_title, og_description, faq, article). Stage pages come from `src/stages.json`.
- Build: `python3 build.py --production` writes the live site to `docs/` (pages, redirects, sitemap, robots.txt, llms.txt, llms-full.txt, a Markdown copy of every page as `index.html.md`). Always use `--production` before publishing; without it the build is a hidden preview.
- Share images: `tools/make_share_cards.py` (needs Pillow) writes `docs/assets/img/share/*.jpg`; run it when a page title or new page needs a card, then rebuild.
- Publish: commit and push to `main`. GitHub Pages deploys in about a minute.
- Before publishing, check that no internal link is broken and the JSON-LD parses.
- Never change DNS, the CNAME file's domain, or anything about email.

## The website playbook (rules for all text and images)

The private repository `cellwood/website-playbook` holds brand identity, voice and tone, messaging, the web style guide, site operations and search/AI visibility guidance. Read the relevant files before writing or changing content. Key rules:

- Name no people on the site. The founder is "Moreland's founder"; testimonials are attributed by role and company type.
- US English, sentence-case headings, serial comma, em dash with spaces for asides, phone as (510) 833-7308.
- Facts must match Google Business Profile and LinkedIn: 2532 Santa Clara Avenue, Suite 413, Alameda, CA 94501 · Monday to Friday, 9am–5pm Pacific · founded 2002.
- SEO title under 60 characters; meta description under 155.

## Content doc: where the owner edits page text

Google Doc **morelandassoc.com – Website Content**
https://docs.google.com/document/d/1Rh0uX0Aca0E2brksWuQOlhYzTVL69vEoU3kRcX91pi4/edit
(in the owner's Google Drive › Websites folder; needs the Google Docs and Google Drive connectors)

- Tab `t.0`, **📋 Index & rules**: a table of every page (Status · Page (tab) · Address · Last published), the editing rules and the status key.
- One tab per page. Each starts with **Page settings** (Address, SEO title, Meta description, Share title, Share description), then **Page text**, using Heading 1 for the page title and Heading 2/3 for sections.
- Status emoji at the start of each tab name and in the Index table: 🟢 live · 🟡 edited, needs publishing · 🔴 new page.
- An Apps Script in the doc (copy in the playbook, `tools/content-doc/auto-status.gs`) turns edited 🟢 tabs 🟡 every minute from 7am to 9pm Pacific. It re-snapshots a tab whenever Claude sets it back to 🟢.
- Text in [square brackets] and comments are notes to Claude, never published. [Remove this page] means retire the page and redirect its address.

Tab IDs:

| Page | Tab ID |
|---|---|
| / | t.7ba1x86n0nwz |
| /services/interim-executive/ | t.s3c95xyukovc |
| /about/ | t.hhf05djy5hu9 |
| /market-traction/ | t.u5xqbmssb8vl |
| /market-traction/stages/ | t.pi5n69ca1d6p |
| /market-traction/stages/eureka/ | t.2eh2mm2twcso |
| /market-traction/stages/kaa-ching/ | t.vgcyx3vh7oi |
| /market-traction/stages/two-thumbs-up/ | t.5j9ck5dla45v |
| /market-traction/stages/momentum/ | t.mqxknr32gvgl |
| /market-traction/stages/building-buzz/ | t.8a647dde6l3f |
| /market-traction/stages/market-traction/ | t.bh414zs3ckmx |
| /market-traction/test/ | t.ccvd6f5dl74t |
| /insights/ | t.se8ckeb6y56g |
| /insights/interim-vs-fractional-cmo/ | t.uk6afh2n6ipi |
| /insights/how-long-interim-executive-engagement/ | t.plmkgbuc2fp0 |
| /insights/when-to-hire-interim-coo/ | t.1krba8lhwx5s |
| /insights/what-does-a-cco-do/ | t.6ad9ur1988uq |
| /insights/ai-first-go-to-market/ | t.4ee28w1d4s86 |
| /contact/ | t.9d0jtakrtro6 |
| /get-started/ | t.8eu0z3267ld8 |

New pages get new tabs; read the tab list from the doc rather than relying only on this table.

## "Sync the content doc"

When the owner says "sync" (or "sync the Moreland content doc", "push the updates live"):

1. Read the doc (Drive `read_file_content` with `includeComments: true` for text; Docs `read_doc` for tab names, IDs and positions).
2. Compare **every** page tab with the live page (its source in `src/`, or the built `docs/<path>/index.html.md`), not only tabs already marked 🟡. Mark any changed 🟢 tab 🟡 in its name and the Index table before going on. New tabs (🔴) are new pages.
3. For each 🟡 or 🔴 page, apply the changes to the source: page text into `src/pages/...` (or `src/stages.json`), Page settings into the front-matter (`title`, `description`, `og_title`, `og_description`). Keep the existing layout and markup; follow the playbook and fix anything that breaks its rules, telling the owner what you changed and why. New pages also need nav/footer links where appropriate, an `LLMS_PAGES` entry and a share card.
4. Build with `--production`, check links, and show the owner a local preview plus a plain list of every change, page by page.
5. Publish only after the owner approves: commit and push, wait for GitHub Pages, and confirm the live pages show the change.
6. In the doc, set each published page back to 🟢 in its tab name and the Index table, and set its **Last published** date to today (format "24 Oct 2026"). Guard Docs edits with `writeControl.requiredRevisionId` from a fresh read.
7. If the doc and the site disagree because someone changed the site directly, ask the owner which version wins before overwriting anything.
