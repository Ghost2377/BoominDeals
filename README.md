# BoominDeals

Static deal site. Built for GitHub Pages, and set up to follow Amazon Associates rules.

## How it works
- `deals.json` holds every post (deals + guides). Each deal includes original commentary: why it's a deal, who it's for, what to watch out for, and our take.
- `config.json` holds the site name, URL, contact email and your Amazon Associates tag.
- `python3 build.py` renders everything into `site/`.
- `python3 add_deals.py new.json` adds new deals (skipping duplicates) and rebuilds.
- GitHub Pages serves the `site/` folder through the included GitHub Actions workflow.

## Amazon Associates compliance built in
- Disclosure "As an Amazon Associate I earn from qualifying purchases." appears in the header bar, the footer, every Amazon button, and the Disclosure page.
- Amazon prices are never shown on the site. Buttons say "Check today's price on Amazon", because Amazon only allows prices that come from its own API or links.
- No Amazon product images are stored on the site (also against the rules unless they come from the API). Posts use emoji tiles instead.
- Links go straight to amazon.com/dp/ASIN with your tag, with no cloaking or redirects, and use rel="nofollow sponsored".
- No price tracking or price-alert features, since Amazon prohibits them.
- Privacy policy (with the third-party cookie language), Affiliate disclosure, About and Contact pages.
- Non-Amazon prices carry an "as of" date/time stamp and a "subject to change" note.

## After Amazon approves you
Put your tracking ID (e.g. `boomindeals-20`) in `config.json` → `amazon_tag` and rebuild. Every Amazon link gets tagged automatically.

## Product photos
Put a square product photo at `img/<deal-slug>.jpg` and the build uses it on the card and the deal page; otherwise the emoji tile is shown.
For Amazon deals, never use Amazon's own images (against Associates rules until you have Product Advertising/Creators API access). Use the same product's photo from Walmart, Best Buy, Target or the brand's own site.

## Short links (HC / Twitter)
Every Amazon deal gets two links, using the lowercase ASIN as the code:
- Deal page: `<base_url>/<asin>`. It shows the deal, #ad, the Amazon disclosure and "Prices and availability are subject to change."
- Go link: `<base_url>/go/<asin>`. It instantly forwards to `amazon.com/dp/<ASIN>?tag=<amazon_tag>`. **Paste this one on HC / Twitter.**
`short_links.json` lists every pair after each build.
