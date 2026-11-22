#!/usr/bin/env python3
"""BoominDeals static site builder.

Reads config.json + deals.json and writes the full site to ./site/.
To add a deal: append an entry to deals.json and run `python3 build.py`.
"""
import json, html, os, datetime, shutil, re
from email.utils import format_datetime

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "site")
cfg = json.load(open(os.path.join(ROOT, "config.json")))
deals = json.load(open(os.path.join(ROOT, "deals.json")))
E = html.escape
NAME = cfg["site_name"]
from urllib.parse import urlparse
PREFIX = urlparse(cfg["base_url"]).path.rstrip("/")  # e.g. /boomindeals on GitHub Pages
AMZ_DISCLOSURE = "As an Amazon Associate I earn from qualifying purchases."

STORES = {
    "amazon": ("Amazon", "#ff9900"), "walmart": ("Walmart", "#0071dc"), "target": ("Target", "#cc0000"),
    "woot": ("Woot", "#3ab54a"), "bestbuy": ("Best Buy", "#0046be"), "lowes": ("Lowe's", "#004990"),
    "kohls": ("Kohl's", "#860035"),
}

def dt(s):
    return datetime.datetime.fromisoformat(s)

def nice_date(s):
    d = dt(s)
    return d.strftime("%b %-d, %Y · %-I:%M %p ET")

def amazon_url(asin):
    u = f"https://www.amazon.com/dp/{asin}"
    return u + (f"?tag={cfg['amazon_tag']}" if cfg.get("amazon_tag") else "")

def deal_url(d):
    return amazon_url(d["asin"]) if d.get("store") == "amazon" else d.get("url", "")

CSS = """
:root{--ink:#14161a;--muted:#5d6470;--line:#e7e9ee;--bg:#f7f7f4;--card:#fff;--brand:#ff5a1f;--brand2:#ffb800;--ok:#0a7d3e}
*{box-sizing:border-box}html{-webkit-text-size-adjust:100%}
body{margin:0;font:16px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Inter,Roboto,Helvetica,Arial,sans-serif;color:var(--ink);background:var(--bg)}
a{color:inherit}
.wrap{max-width:1080px;margin:0 auto;padding:0 20px}
header.top{background:var(--ink);color:#fff}
header.top .wrap{display:flex;align-items:center;justify-content:space-between;gap:16px;padding-top:14px;padding-bottom:14px;flex-wrap:wrap}
.logo{font-weight:900;font-size:26px;letter-spacing:-.5px;text-decoration:none}
.logo span{color:var(--brand2)}
.logo b{color:var(--brand)}
nav.main a{color:#d9dce2;text-decoration:none;margin-left:18px;font-weight:600;font-size:15px}
nav.main a:hover{color:#fff}
.disc-bar{background:#fff4e6;border-bottom:1px solid #ffd9a8;font-size:13.5px;color:#7a4300;text-align:center;padding:7px 14px}
.hero{padding:36px 0 18px}
.hero h1{font-size:clamp(28px,4.5vw,44px);line-height:1.1;margin:0 0 8px;letter-spacing:-1px}
.hero p{color:var(--muted);margin:0;font-size:18px}
.filters{display:flex;flex-wrap:wrap;gap:8px;margin:18px 0 6px}
.filters button{border:1px solid var(--line);background:#fff;border-radius:999px;padding:7px 14px;font:inherit;font-size:14px;cursor:pointer}
.filters button.on{background:var(--ink);color:#fff;border-color:var(--ink)}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:18px;padding:18px 0 40px}
.card{background:var(--card);border:1px solid var(--line);border-radius:16px;overflow:hidden;display:flex;flex-direction:column;text-decoration:none;transition:transform .12s,box-shadow .12s}
.card:hover{transform:translateY(-2px);box-shadow:0 8px 24px rgba(0,0,0,.07)}
.tile{height:120px;display:flex;align-items:center;justify-content:center;font-size:56px;background:linear-gradient(135deg,#fff3ea,#fff9e0)}
.cbody{padding:16px 18px 18px;display:flex;flex-direction:column;gap:8px;flex:1}
.meta{display:flex;gap:8px;align-items:center;flex-wrap:wrap;font-size:12.5px;color:var(--muted)}
.store{color:#fff;border-radius:6px;padding:2px 8px;font-weight:700;font-size:12px}
.cat{border:1px solid var(--line);border-radius:6px;padding:1px 7px}
.card h3{margin:0;font-size:18px;line-height:1.3}
.card p{margin:0;color:var(--muted);font-size:14.5px}
.price{font-weight:800;font-size:20px}.was{color:var(--muted);text-decoration:line-through;font-weight:500;font-size:14px;margin-left:6px}
.checkprice{font-weight:700;color:var(--brand)}
article.post{background:#fff;border:1px solid var(--line);border-radius:18px;padding:28px clamp(18px,4vw,40px);margin:28px 0 40px}
article.post h1{font-size:clamp(26px,4vw,38px);line-height:1.15;margin:8px 0 10px;letter-spacing:-.5px}
.lede{font-size:19px;color:#333;margin:0 0 18px}
.buy{display:flex;flex-wrap:wrap;align-items:center;gap:14px;background:#fafaf7;border:1px solid var(--line);border-radius:14px;padding:16px 18px;margin:18px 0}
.btn{display:inline-block;background:var(--brand);color:#fff;text-decoration:none;font-weight:800;border-radius:10px;padding:12px 20px}
.btn.alt{background:var(--ink)}
.stamp{font-size:13px;color:var(--muted)}
.note{font-size:13px;color:var(--muted);background:#f4f6f8;border-radius:10px;padding:10px 12px;margin-top:6px}
h2{font-size:21px;margin:26px 0 8px}
ul{padding-left:20px}
.verdict{border-left:4px solid var(--ok);background:#effaf3;padding:12px 16px;border-radius:8px;font-weight:600}
.page{background:#fff;border:1px solid var(--line);border-radius:18px;padding:28px clamp(18px,4vw,40px);margin:28px 0 40px}
.page h1{margin-top:0}
footer{background:var(--ink);color:#b9bec8;font-size:14px;padding:28px 0 36px;margin-top:20px}
footer a{color:#fff}
footer .cols{display:flex;flex-wrap:wrap;gap:24px;justify-content:space-between}
footer .fine{margin-top:18px;font-size:13px;color:#9aa0aa}
.back{display:inline-block;margin-top:24px;color:var(--muted);font-size:14px}
"""

def layout(title, body, desc="", path=""):
    return _layout(title, body, desc, path).replace('href="/', f'href="{PREFIX}/')

def _layout(title, body, desc="", path=""):
    canon = cfg["base_url"].rstrip("/") + "/" + path
    return f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{E(title)}</title>
<meta name="description" content="{E(desc or cfg['tagline'])}">
<link rel="canonical" href="{E(canon)}">
<link rel="alternate" type="application/rss+xml" title="{NAME}" href="/rss.xml">
<meta property="og:title" content="{E(title)}"><meta property="og:site_name" content="{NAME}">
<link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>💥</text></svg>">
<style>{CSS}</style>
</head><body>
<header class="top"><div class="wrap">
<a class="logo" href="/">💥 <b>Boomin</b><span>Deals</span></a>
<nav class="main"><a href="/">Deals</a><a href="/guides.html">Guides</a><a href="/about.html">About</a><a href="/disclosure.html">Disclosure</a><a href="/contact.html">Contact</a></nav>
</div></header>
<div class="disc-bar">{AMZ_DISCLOSURE} We may also earn commissions from other stores linked on this site. <a href="/disclosure.html">Learn more</a>.</div>
<main class="wrap">{body}</main>
<footer><div class="wrap">
<div class="cols"><div><strong style="color:#fff">💥 {NAME}</strong><br>{E(cfg['tagline'])}</div>
<div><a href="/about.html">About</a> · <a href="/disclosure.html">Affiliate disclosure</a> · <a href="/privacy.html">Privacy policy</a> · <a href="/contact.html">Contact</a> · <a href="/rss.xml">RSS</a></div></div>
<div class="fine">{AMZ_DISCLOSURE} {NAME} also participates in other affiliate programs, including programs for Walmart, Target and Woot, and may earn a commission when you buy through links on this site, at no extra cost to you. Prices and availability are accurate as of the date and time shown on each post and are subject to change. Amazon and the Amazon logo are trademarks of Amazon.com, Inc. or its affiliates.<br>© {datetime.date.today().year} {NAME}.</div>
</div></footer>
</body></html>"""

def store_badge(d):
    if d.get("type") == "guide":
        return '<span class="store" style="background:#14161a">Guide</span>'
    n, c = STORES.get(d["store"], (d["store"], "#555"))
    return f'<span class="store" style="background:{c}">{E(n)}</span>'

def price_html(d):
    if d.get("type") == "guide":
        return ""
    if d["store"] == "amazon":
        return '<span class="checkprice">See today\'s price on Amazon →</span>'
    w = f'<span class="was">{E(d["was"])}</span>' if d.get("was") and d["was"] != "—" else ""
    return f'<span class="price">{E(d["price"])}</span>{w}'

def card(d):
    href = ("guides/" if d.get("type") == "guide" else "deals/") + d["slug"] + ".html"
    return f"""<a class="card" href="/{href}" data-cat="{E(d['category'])}">
<div class="tile">{d.get('emoji','🔥')}</div>
<div class="cbody"><div class="meta">{store_badge(d)}<span class="cat">{E(d['category'])}</span><span>{E(dt(d['date']).strftime('%b %-d'))}</span></div>
<h3>{E(d['title'])}</h3><p>{E(d['summary'])}</p><div>{price_html(d)}</div></div></a>"""

def deal_page(d):
    n, c = STORES[d["store"]]
    url = deal_url(d)
    rel = 'rel="nofollow sponsored noopener" target="_blank"'
    if d["store"] == "amazon":
        buy = f"""<div class="buy"><a class="btn" href="{E(url)}" {rel}>Check today's price on Amazon</a>
<div class="stamp">We checked this deal on {E(nice_date(d['date']))}. Amazon prices change often, so the current price is shown on Amazon.<br>{AMZ_DISCLOSURE}</div></div>"""
    else:
        extra = "".join(f'<a class="btn alt" href="{E(u)}" {rel}>{E(t)}</a>' for t, u in d.get("extra_links", []))
        aff = "Affiliate link: we may earn a commission at no extra cost to you." if d.get("affiliate") else "Direct link to the store."
        buy = f"""<div class="buy"><div><span class="price">{E(d['price'])}</span>{'<span class="was">'+E(d['was'])+'</span>' if d.get('was') else ''}</div>
<a class="btn" href="{E(url)}" {rel}>Get this deal at {E(n)}</a>{extra}
<div class="stamp">Price as of {E(nice_date(d['date']))}. Prices and availability are subject to change. {aff}</div></div>"""
    who = "".join(f"<li>{E(x)}</li>" for x in d["who"])
    body = f"""<article class="post"><div class="meta">{store_badge(d)}<span class="cat">{E(d['category'])}</span><span>Posted {E(nice_date(d['date']))}</span></div>
<h1>{d.get('emoji','')} {E(d['title'])}</h1><p class="lede">{E(d['summary'])}</p>{buy}
<h2>Why it's a good deal</h2><p>{E(d['why'])}</p>
<h2>Who it's for</h2><ul>{who}</ul>
<h2>What to watch out for</h2><p>{E(d['watch'])}</p>
<h2>Our take</h2><p class="verdict">{E(d['verdict'])}</p>
<a class="back" href="/">← All deals</a></article>"""
    return layout(f"{d['title']} | {NAME}", body, d["summary"], f"deals/{d['slug']}.html")

def guide_page(d):
    paras = "".join(f"<p>{E(p)}</p>" for p in d["body"])
    body = f"""<article class="post"><div class="meta">{store_badge(d)}<span>Posted {E(nice_date(d['date']))}</span></div>
<h1>{d.get('emoji','')} {E(d['title'])}</h1><p class="lede">{E(d['summary'])}</p>{paras}
<a class="back" href="/guides.html">← All guides</a></article>"""
    return layout(f"{d['title']} | {NAME}", body, d["summary"], f"guides/{d['slug']}.html")

def static_page(fname, title, inner):
    return layout(f"{title} | {NAME}", f'<div class="page">{inner}</div>', title, fname)

def build():
    if os.path.exists(OUT):
        shutil.rmtree(OUT)
    os.makedirs(os.path.join(OUT, "deals")); os.makedirs(os.path.join(OUT, "guides"))
    items = sorted(deals, key=lambda d: d["date"], reverse=True)
    dl = [d for d in items if d.get("type") != "guide"]
    gl = [d for d in items if d.get("type") == "guide"]
    cats = sorted({d["category"] for d in dl})
    filt = '<button class="on" data-f="all">All</button>' + "".join(f'<button data-f="{E(c)}">{E(c)}</button>' for c in cats)
    upd = nice_date(items[0]["date"]) if items else ""
    home = f"""<section class="hero"><h1>Today's best deals, checked by hand.</h1>
<p>We dig through Amazon, Walmart, Target, Best Buy, Lowe's, Kohl's and Woot and post only the deals worth your money, with a plain-English take on each one. Last updated {E(upd)}.</p></section>
<div class="filters">{filt}</div>
<div class="grid" id="grid">{''.join(card(d) for d in dl)}</div>
<h2>Latest guides</h2><div class="grid">{''.join(card(d) for d in gl[:3])}</div>
<script>document.querySelectorAll('.filters button').forEach(b=>b.onclick=()=>{{document.querySelectorAll('.filters button').forEach(x=>x.classList.remove('on'));b.classList.add('on');const f=b.dataset.f;document.querySelectorAll('#grid .card').forEach(c=>c.style.display=(f==='all'||c.dataset.cat===f)?'':'none')}})</script>"""
    open(os.path.join(OUT, "index.html"), "w").write(layout(f"{NAME} — {cfg['tagline']}", home, cfg["tagline"], ""))
    for d in dl:
        open(os.path.join(OUT, "deals", d["slug"] + ".html"), "w").write(deal_page(d))
    for d in gl:
        open(os.path.join(OUT, "guides", d["slug"] + ".html"), "w").write(guide_page(d))
    open(os.path.join(OUT, "guides.html"), "w").write(layout(f"Guides | {NAME}", f'<section class="hero"><h1>Guides</h1><p>Shopping advice, deal-hunting tips and honest takes.</p></section><div class="grid">{"".join(card(d) for d in gl)}</div>', "Guides", "guides.html"))
    em = E(cfg["contact_email"])
    open(os.path.join(OUT, "about.html"), "w").write(static_page("about.html", "About", f"""<h1>About {NAME}</h1>
<p>{NAME} is a deal site run by {E(cfg['owner'])}. We spend hours every day going through the big retailers (Amazon, Walmart, Target, Best Buy, Lowe's, Kohl's and Woot) and post only the deals we would actually tell a friend about.</p>
<p>Every post is checked by hand on the store's own page before it goes up, and each one comes with our own write-up: why it's a good deal, who it's for, and what to watch out for. If a "sale" price isn't really a deal, we skip it.</p>
<p>We also write guides on how to tell a real discount from marketing, what's worth buying during big sales, and what can wait.</p>
<h2>How we make money</h2><p>Some links on this site are affiliate links. If you buy through them, we may earn a small commission at no extra cost to you. That never changes which deals we post. See our <a href="/disclosure.html">affiliate disclosure</a>.</p>
<p>Questions or a deal tip? <a href="/contact.html">Get in touch</a>.</p>"""))
    open(os.path.join(OUT, "disclosure.html"), "w").write(static_page("disclosure.html", "Affiliate disclosure", f"""<h1>Affiliate disclosure</h1>
<p><strong>{NAME} is a participant in the Amazon Services LLC Associates Program, an affiliate advertising program designed to provide a means for sites to earn advertising fees by advertising and linking to Amazon.com. {AMZ_DISCLOSURE}</strong></p>
<p>{NAME} also takes part in other affiliate programs, including programs that cover Walmart, Target and Woot (for example, through the Mavely creator platform). When you click a link on this site and make a purchase, we may receive a commission. This comes at no additional cost to you.</p>
<p>Affiliate relationships never affect which deals we choose to post or what we say about them. Our write-ups are our own opinions.</p>
<p>Prices and availability are accurate as of the date and time shown on each post and are subject to change. Any price and availability information shown on the retailer's site at the time of purchase will apply to your purchase. For Amazon products we don't show a price on this site. Use the button on each post to see the current price on Amazon.</p>"""))
    today = datetime.date.today().strftime("%B %-d, %Y")
    open(os.path.join(OUT, "privacy.html"), "w").write(static_page("privacy.html", "Privacy policy", f"""<h1>Privacy policy</h1><p><em>Last updated {today}</em></p>
<p>This policy explains what information {NAME} ("we") collects when you visit this site and how it's used.</p>
<h2>Information we collect</h2><p>We don't require accounts and we don't ask for personal information to browse the site. Like most websites, our hosting provider may automatically log basic technical information (such as IP address, browser type and pages visited) for security and performance.</p>
<h2>Cookies and affiliate links</h2><p>This site contains affiliate links to third-party retailers, including Amazon. {AMZ_DISCLOSURE} When you click one of these links, the retailer (for example, Amazon) or the affiliate network may place cookies on your browser to track the referral and attribute any qualifying purchase to us. Those cookies are controlled by the third party and are covered by their own privacy policies.</p>
<p>Third parties, including Amazon and other advertisers, may serve content and advertisements, collect information directly from visitors, and place or recognize cookies on visitors' browsers.</p>
<h2>Analytics</h2><p>If we add privacy-friendly analytics in the future, we will update this policy to describe it.</p>
<h2>Your choices</h2><p>You can block or delete cookies in your browser settings. Doing so may affect whether retailers can credit our referrals, but it won't affect your ability to use this site.</p>
<h2>Children</h2><p>This site is not directed at children under 13, and we do not knowingly collect information from them.</p>
<h2>Contact</h2><p>Questions about this policy: <a href="mailto:{em}">{em}</a>.</p>"""))
    open(os.path.join(OUT, "contact.html"), "w").write(static_page("contact.html", "Contact", f"""<h1>Contact us</h1>
<p>Have a deal tip, a correction or a question? Email us at <a href="mailto:{em}">{em}</a>. We read everything.</p>
<p>If a deal on the site has expired or the price changed, let us know and we'll update the post.</p>"""))
    base = cfg["base_url"].rstrip("/")
    urls = ["", "guides.html", "about.html", "disclosure.html", "privacy.html", "contact.html"] + [f"deals/{d['slug']}.html" for d in dl] + [f"guides/{d['slug']}.html" for d in gl]
    open(os.path.join(OUT, "sitemap.xml"), "w").write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + "".join(f"<url><loc>{base}/{u}</loc></url>" for u in urls) + "</urlset>")
    open(os.path.join(OUT, "robots.txt"), "w").write(f"User-agent: *\nAllow: /\nSitemap: {base}/sitemap.xml\n")
    rss_items = "".join(f"<item><title>{E(d['title'])}</title><link>{base}/{'guides' if d.get('type')=='guide' else 'deals'}/{d['slug']}.html</link><guid>{base}/{d['slug']}</guid><pubDate>{format_datetime(dt(d['date']))}</pubDate><description>{E(d['summary'])}</description></item>" for d in items[:50])
    open(os.path.join(OUT, "rss.xml"), "w").write(f'<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel><title>{NAME}</title><link>{base}/</link><description>{E(cfg["tagline"])}</description>{rss_items}</channel></rss>')
    if "github.io" not in base:
        open(os.path.join(OUT, "CNAME"), "w").write(base.replace("https://", "").replace("http://", "").split("/")[0] + "\n")
    print(f"Built {len(dl)} deals + {len(gl)} guides into {OUT}")

if __name__ == "__main__":
    build()
