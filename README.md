# morelandassoc.com

The website for Moreland Associates: static HTML, hosted on GitHub Pages.

- Page content: `src/pages/` (one file per page; the comment at the top holds its title, description and address)
- The six Market Traction stages: `src/stages.json`
- Menu, contact details, redirects and form settings: top of `build.py`
- Styles, scripts, fonts and images: `docs/assets/`
- The published site: `docs/`. This is generated, so edit `src/` and rebuild instead.

```
python3 build.py               # preview build (cellwood.github.io/morelandassoc-website)
python3 build.py --production  # live build (www.morelandassoc.com)
```

Needs only Python 3. There are no other dependencies.
