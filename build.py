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
:root{--bg:#120626;--bg2:#1d0b3a;--card:#1f0f3d;--ink:#fff7fb;--muted:#c9b7e6;--line:rgba(255,255,255,.12);
--pink:#ff2e93;--cyan:#16e0ff;--orange:#ff8a1f;--yellow:#ffd23f;--purple:#8b3dff;--ok:#2dffb3;
--sun:linear-gradient(135deg,#ff2e93 0%,#ff8a1f 55%,#ffd23f 100%);--sea:linear-gradient(135deg,#16e0ff,#8b3dff)}
*{box-sizing:border-box}html{-webkit-text-size-adjust:100%}
body{margin:0;font:16px/1.6 Inter,-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;color:var(--ink);
background:radial-gradient(1200px 600px at 85% -10%,rgba(255,46,147,.28),transparent 60%),radial-gradient(900px 500px at -10% 10%,rgba(22,224,255,.18),transparent 60%),var(--bg);background-attachment:fixed}
a{color:inherit}
.wrap{max-width:1120px;margin:0 auto;padding:0 20px}
.disp{font-family:"Bebas Neue",Impact,"Arial Narrow",sans-serif;letter-spacing:.5px;font-weight:400}
.disc-bar{background:linear-gradient(90deg,#2a0d4f,#3a0f4a);border-bottom:1px solid rgba(255,46,147,.35);font-size:13.5px;color:#ffd9ec;padding:8px 0}
.disc-bar .wrap{display:flex;gap:10px;align-items:center}
.ad{background:var(--pink);color:#fff;font-weight:900;font-size:11px;border-radius:5px;padding:2px 7px;box-shadow:0 0 12px rgba(255,46,147,.7);flex:none}
.disc-bar a{color:var(--cyan);font-weight:700}
header.top{position:sticky;top:0;z-index:10;background:rgba(18,6,38,.82);backdrop-filter:blur(10px);border-bottom:1px solid var(--line)}
header.top .wrap{display:flex;align-items:center;justify-content:space-between;gap:16px;padding-top:12px;padding-bottom:12px;flex-wrap:wrap}
.logo{font-size:34px;line-height:1;text-decoration:none;display:flex;align-items:center;gap:8px}
.logo .b{background:var(--sun);-webkit-background-clip:text;background-clip:text;color:transparent;filter:drop-shadow(0 0 10px rgba(255,46,147,.55))}
.logo .d{color:var(--cyan);text-shadow:0 0 12px rgba(22,224,255,.8)}
nav.main a{color:var(--muted);text-decoration:none;margin-left:18px;font-weight:700;font-size:15px}
nav.main a:hover{color:var(--cyan);text-shadow:0 0 10px rgba(22,224,255,.7)}
.hero{position:relative;text-align:center;padding:56px 0 40px;overflow:hidden}
.hero:after{content:"";position:absolute;left:50%;bottom:-170px;width:420px;height:420px;transform:translateX(-50%);border-radius:50%;
background:repeating-linear-gradient(180deg,transparent 0 18px,var(--bg) 18px 24px),var(--sun);opacity:.22;z-index:-1;filter:blur(1px)}
.pill{display:inline-block;background:rgba(255,46,147,.15);border:1px solid var(--pink);color:#ff9cc9;border-radius:999px;padding:5px 14px;font-weight:800;font-size:12.5px;letter-spacing:1px;text-transform:uppercase;box-shadow:0 0 18px rgba(255,46,147,.35)}
.hero h1{font-size:clamp(48px,9vw,96px);line-height:.95;margin:18px 0 14px}
.hero h1 .l2{display:block;background:var(--sun);-webkit-background-clip:text;background-clip:text;color:transparent;filter:drop-shadow(0 0 18px rgba(255,138,31,.45))}
.hero p{color:var(--muted);margin:0 auto;font-size:18px;max-width:640px}
.cta{display:flex;gap:12px;justify-content:center;flex-wrap:wrap;margin:24px 0 18px}
.btn{display:inline-block;background:var(--sun);color:#1a0526;text-decoration:none;font-weight:900;border-radius:12px;padding:13px 24px;box-shadow:0 0 24px rgba(255,46,147,.45);transition:transform .12s,box-shadow .12s}
.btn:hover{transform:translateY(-2px);box-shadow:0 0 36px rgba(255,46,147,.7)}
.btn.alt{background:transparent;color:var(--cyan);border:2px solid var(--cyan);box-shadow:0 0 18px rgba(22,224,255,.3)}
.btn.big{display:block;text-align:center;font-size:18px;padding:16px}
.trust{display:flex;gap:18px;justify-content:center;flex-wrap:wrap;color:var(--muted);font-size:14px;font-weight:600}
.trust span:before{content:"✦ ";color:var(--yellow)}
.sect{font-size:clamp(34px,5vw,48px);margin:24px 0 6px}
.sect span{color:var(--cyan);text-shadow:0 0 14px rgba(22,224,255,.6)}
.filters{display:flex;flex-wrap:wrap;gap:8px;margin:12px 0 6px}
.filters button{border:1px solid var(--line);background:rgba(255,255,255,.05);color:var(--ink);border-radius:999px;padding:7px 15px;font:inherit;font-size:14px;font-weight:700;cursor:pointer}
.filters button:hover{border-color:var(--cyan)}
.filters button.on{background:var(--sea);border-color:transparent;box-shadow:0 0 16px rgba(22,224,255,.45)}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(290px,1fr));gap:20px;padding:18px 0 40px}
.card{background:linear-gradient(180deg,rgba(255,255,255,.06),rgba(255,255,255,.02));border:1px solid var(--line);border-radius:18px;overflow:hidden;display:flex;flex-direction:column;text-decoration:none;transition:transform .15s,box-shadow .15s,border-color .15s}
.card:hover{transform:translateY(-4px);border-color:var(--pink);box-shadow:0 10px 40px rgba(255,46,147,.3)}
.tile{height:150px;display:flex;align-items:center;justify-content:center;font-size:66px;position:relative;overflow:hidden}
.tile:before{content:"";position:absolute;inset:0;background:repeating-linear-gradient(0deg,rgba(255,255,255,.06) 0 1px,transparent 1px 22px),repeating-linear-gradient(90deg,rgba(255,255,255,.06) 0 1px,transparent 1px 22px)}
.tile span{position:relative;filter:drop-shadow(0 6px 14px rgba(0,0,0,.45))}
.t0{background:linear-gradient(135deg,#ff2e93,#ff8a1f)}.t1{background:linear-gradient(135deg,#16e0ff,#8b3dff)}.t2{background:linear-gradient(135deg,#8b3dff,#ff2e93)}.t3{background:linear-gradient(135deg,#ff8a1f,#ffd23f)}.t4{background:linear-gradient(135deg,#00c2a8,#16e0ff)}
.tile.ph{padding:3px;height:210px}
.tile.ph img{position:relative;width:100%;height:100%;object-fit:contain;background:#fff;border-radius:14px 14px 0 0;padding:6px}
article.post .tile.ph{height:340px}article.post .tile.ph img{border-radius:13px}
.cbody{padding:16px 18px 20px;display:flex;flex-direction:column;gap:9px;flex:1}
.meta{display:flex;gap:8px;align-items:center;flex-wrap:wrap;font-size:12.5px;color:var(--muted)}
.store{color:#fff;border-radius:6px;padding:2px 8px;font-weight:800;font-size:12px}
.cat{border:1px solid rgba(22,224,255,.5);color:#9cf1ff;border-radius:999px;padding:1px 9px;font-weight:700;text-transform:uppercase;font-size:11px;letter-spacing:.6px}
.card h3{margin:0;font-size:18px;line-height:1.3}
.card p{margin:0;color:var(--muted);font-size:14.5px}
.price{font-weight:900;font-size:24px;color:var(--yellow);text-shadow:0 0 14px rgba(255,210,63,.45)}
.was{color:var(--muted);text-decoration:line-through;font-weight:500;font-size:14px;margin-left:8px}
.checkprice{font-weight:800;color:var(--cyan)}
.crumbs{font-size:13.5px;color:var(--muted);margin:24px 0 0}.crumbs a{text-decoration:none;color:var(--cyan)}
article.post,.page{background:linear-gradient(180deg,rgba(255,255,255,.07),rgba(255,255,255,.03));border:1px solid var(--line);border-radius:22px;padding:28px clamp(18px,4vw,40px);margin:16px 0 40px}
article.post .tile{height:220px;border-radius:16px;font-size:96px;margin-bottom:18px}
article.post h1{font-size:clamp(28px,4.2vw,42px);line-height:1.12;margin:10px 0 10px}
.lede{font-size:19px;color:#f1e6ff;margin:0 0 18px}
.buy{background:rgba(0,0,0,.25);border:1px solid rgba(255,46,147,.4);border-radius:16px;padding:18px;margin:18px 0;display:flex;flex-direction:column;gap:12px}
.buy .row{display:flex;gap:10px;flex-wrap:wrap}
.discbox{border:1px solid rgba(255,210,63,.55);background:rgba(255,210,63,.08);color:#ffe9a6;border-radius:12px;padding:10px 14px;font-size:13.5px}
.stamp{font-size:13px;color:var(--muted)}
h2{font-size:22px;margin:28px 0 8px;color:#fff}
article.post h2:before{content:"";display:inline-block;width:10px;height:10px;border-radius:50%;background:var(--pink);box-shadow:0 0 10px var(--pink);margin-right:10px;vertical-align:middle}
ul.checks{list-style:none;padding:0}ul.checks li{padding-left:28px;position:relative;margin:6px 0}
ul.checks li:before{content:"✔";position:absolute;left:0;color:var(--ok);text-shadow:0 0 8px rgba(45,255,179,.6)}
ul{padding-left:20px}
.verdict{border-left:4px solid var(--cyan);background:rgba(22,224,255,.08);padding:12px 16px;border-radius:10px;font-weight:700}
.page h1{margin-top:0;font-size:clamp(28px,4vw,40px)}.page a{color:var(--cyan)}
footer{background:linear-gradient(180deg,transparent,#0b0318 30%);border-top:1px solid var(--line);color:var(--muted);font-size:14px;padding:36px 0 40px;margin-top:30px}
footer a{color:#fff;text-decoration:none}footer a:hover{color:var(--cyan)}
footer .cols{display:grid;grid-template-columns:2fr 1fr 1fr 1fr;gap:24px}
footer h4{margin:0 0 8px;color:var(--pink);text-transform:uppercase;font-size:13px;letter-spacing:1px}
footer ul{list-style:none;padding:0;margin:0}footer li{margin:4px 0}
footer .fine{margin-top:24px;font-size:12.5px;color:#9a88b8;border-top:1px solid var(--line);padding-top:16px}
@media(max-width:760px){footer .cols{grid-template-columns:1fr 1fr}nav.main a{margin-left:12px}}
.back{display:inline-block;margin-top:24px;color:var(--cyan);font-size:14px;text-decoration:none}
"""

def layout(title, body, desc="", path=""):
    return _layout(title, body, desc, path).replace('href="/', f'href="{PREFIX}/').replace('src="/', f'src="{PREFIX}/')

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
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Inter:wght@400;600;700;800;900&display=swap" rel="stylesheet">
<meta name="theme-color" content="#120626">
<style>{CSS}</style>
</head><body>
<div class="disc-bar"><div class="wrap"><span class="ad">#AD</span><span><strong>Affiliate disclosure:</strong> {AMZ_DISCLOSURE} <a href="/disclosure.html">Details</a></span></div></div>
<header class="top"><div class="wrap">
<a class="logo disp" href="/">💥 <span class="b">BOOMIN</span><span class="d">DEALS</span></a>
<nav class="main"><a href="/">Deals</a><a href="/guides.html">Guides</a><a href="/about.html">About</a><a href="/disclosure.html">Disclosure</a><a href="/contact.html">Contact</a></nav>
</div></header>
<main class="wrap">{body}</main>
<footer><div class="wrap">
<div class="cols"><div><a class="logo disp" href="/">💥 <span class="b">BOOMIN</span><span class="d">DEALS</span></a><p>{E(cfg['tagline'])}</p></div>
<div><h4>Navigate</h4><ul><li><a href="/">Latest deals</a></li><li><a href="/guides.html">Guides</a></li><li><a href="/about.html">About</a></li><li><a href="/contact.html">Contact</a></li><li><a href="/rss.xml">RSS</a></li></ul></div>
<div><h4>Legal</h4><ul><li><a href="/disclosure.html">Affiliate disclosure</a></li><li><a href="/privacy.html">Privacy policy</a></li></ul></div>
<div><h4>Why us</h4><ul><li>✦ Checked by hand</li><li>✦ Real discounts only</li><li>✦ Plain-English takes</li></ul></div></div>
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

def has_img(d):
    return os.path.exists(os.path.join(ROOT, "img", d["slug"] + ".jpg"))

def tile(d):
    if has_img(d):
        return f'<div class="tile ph {tcls(d)}"><img src="/img/{E(d["slug"])}.jpg" alt="{E(d["title"])}" loading="lazy"></div>'
    return f'<div class="tile {tcls(d)}"><span>{d.get("emoji","🔥")}</span></div>'

def tcls(d):
    return "t%d" % (sum(map(ord, d["slug"])) % 5)

def card(d):
    href = ("guides/" if d.get("type") == "guide" else "deals/") + d["slug"] + ".html"
    return f"""<a class="card" href="/{href}" data-cat="{E(d['category'])}">
{tile(d)}
<div class="cbody"><div class="meta">{store_badge(d)}<span class="cat">{E(d['category'])}</span><span>{E(dt(d['date']).strftime('%b %-d'))}</span></div>
<h3>{E(d['title'])}</h3><p>{E(d['summary'])}</p><div>{price_html(d)}</div></div></a>"""

def deal_page(d):
    n, c = STORES[d["store"]]
    url = deal_url(d)
    rel = 'rel="nofollow sponsored noopener" target="_blank"'
    if d["store"] == "amazon":
        buy = f"""<div class="buy"><a class="btn big" href="{E(url)}" {rel}>Check today's price on Amazon →</a>
<div class="discbox">ⓘ <strong>Affiliate disclosure:</strong> {AMZ_DISCLOSURE} Amazon prices change often, so the current price is shown on Amazon.</div>
<div class="stamp">We checked this deal on {E(nice_date(d['date']))}.</div></div>"""
    else:
        extra = "".join(f'<a class="btn alt" href="{E(u)}" {rel}>{E(t)}</a>' for t, u in d.get("extra_links", []))
        aff = "Affiliate link: we may earn a commission at no extra cost to you." if d.get("affiliate") else "Direct link to the store."
        buy = f"""<div class="buy"><div><span class="price">{E(d['price'])}</span>{'<span class="was">'+E(d['was'])+'</span>' if d.get('was') else ''}</div>
<a class="btn big" href="{E(url)}" {rel}>Get this deal at {E(n)} →</a>{'<div class="row">'+extra+'</div>' if extra else ''}
<div class="discbox">ⓘ {aff} Prices and availability are subject to change.</div>
<div class="stamp">Price as of {E(nice_date(d['date']))}.</div></div>"""
    who = "".join(f"<li>{E(x)}</li>" for x in d["who"])
    body = f"""<div class="crumbs"><a href="/">Home</a> / <a href="/">Deals</a> / {E(d['category'])}</div><article class="post">{tile(d)}<div class="meta">{store_badge(d)}<span class="cat">{E(d['category'])}</span><span>Posted {E(nice_date(d['date']))}</span></div>
<h1>{E(d['title'])}</h1><p class="lede">{E(d['summary'])}</p>{buy}
<h2>Why it's a good deal</h2><p>{E(d['why'])}</p>
<h2>Who it's for</h2><ul class="checks">{who}</ul>
<h2>What to watch out for</h2><p>{E(d['watch'])}</p>
<h2>Our take</h2><p class="verdict">{E(d['verdict'])}</p>
<a class="back" href="/">← All deals</a></article>"""
    return layout(f"{d['title']} | {NAME}", body, d["summary"], f"deals/{d['slug']}.html")

def guide_page(d):
    paras = "".join(f"<p>{E(p)}</p>" for p in d["body"])
    body = f"""<div class="crumbs"><a href="/">Home</a> / <a href="/guides.html">Guides</a></div><article class="post"><div class="meta">{store_badge(d)}<span>Posted {E(nice_date(d['date']))}</span></div>
<h1>{d.get('emoji','')} {E(d['title'])}</h1><p class="lede">{E(d['summary'])}</p>{paras}
<a class="back" href="/guides.html">← All guides</a></article>"""
    return layout(f"{d['title']} | {NAME}", body, d["summary"], f"guides/{d['slug']}.html")

def static_page(fname, title, inner):
    return layout(f"{title} | {NAME}", f'<div class="page">{inner}</div>', title, fname)

def build():
    if os.path.exists(OUT):
        shutil.rmtree(OUT)
    os.makedirs(os.path.join(OUT, "deals")); os.makedirs(os.path.join(OUT, "guides"))
    if os.path.isdir(os.path.join(ROOT, "img")):
        shutil.copytree(os.path.join(ROOT, "img"), os.path.join(OUT, "img"))
    items = sorted(deals, key=lambda d: d["date"], reverse=True)
    dl = [d for d in items if d.get("type") != "guide"]
    gl = [d for d in items if d.get("type") == "guide"]
    cats = sorted({d["category"] for d in dl})
    filt = '<button class="on" data-f="all">All</button>' + "".join(f'<button data-f="{E(c)}">{E(c)}</button>' for c in cats)
    upd = nice_date(items[0]["date"]) if items else ""
    home = f"""<section class="hero"><span class="pill">⚡ Fresh deals, checked by hand</span>
<h1 class="disp">Real deals.<span class="l2">No noise.</span></h1>
<p>We dig through Amazon, Walmart, Target, Best Buy, Lowe's, Kohl's and Woot and only post the deals worth your money, each with a plain-English take. Last updated {E(upd)}.</p>
<div class="cta"><a class="btn" href="#deals">Browse all deals →</a><a class="btn alt" href="/guides/how-we-pick-deals.html">How we pick deals</a></div>
<div class="trust"><span>Checked daily</span><span>100% free</span><span>Hand-picked</span><span>Direct store links</span></div></section>
<h2 class="sect disp" id="deals">Today's <span>hot drops</span></h2>
<div class="filters">{filt}</div>
<div class="grid" id="grid">{''.join(card(d) for d in dl)}</div>
<h2 class="sect disp">Latest <span>guides</span></h2><div class="grid">{''.join(card(d) for d in gl[:3])}</div>
<script>document.querySelectorAll('.filters button').forEach(b=>b.onclick=()=>{{document.querySelectorAll('.filters button').forEach(x=>x.classList.remove('on'));b.classList.add('on');const f=b.dataset.f;document.querySelectorAll('#grid .card').forEach(c=>c.style.display=(f==='all'||c.dataset.cat===f)?'':'none')}})</script>"""
    open(os.path.join(OUT, "index.html"), "w").write(layout(f"{NAME} — {cfg['tagline']}", home, cfg["tagline"], ""))
    for d in dl:
        open(os.path.join(OUT, "deals", d["slug"] + ".html"), "w").write(deal_page(d))
    for d in gl:
        open(os.path.join(OUT, "guides", d["slug"] + ".html"), "w").write(guide_page(d))
    open(os.path.join(OUT, "guides.html"), "w").write(layout(f"Guides | {NAME}", f'<section class="hero"><span class="pill">Guides</span><h1 class="disp">Shop <span class="l2">smarter.</span></h1><p>Shopping advice, deal-hunting tips and honest takes.</p></section><div class="grid">{"".join(card(d) for d in gl)}</div>', "Guides", "guides.html"))
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
