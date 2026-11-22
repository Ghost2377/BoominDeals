#!/usr/bin/env python3
"""Add new deals to BoominDeals, skip duplicates, rebuild the site.

Usage: python3 add_deals.py new_deals.json
new_deals.json is a list of deal objects in the same format as deals.json.
Duplicates (same slug, same Amazon ASIN, or same store URL) are skipped.
Deals older than 60 days are archived out of the homepage automatically by date sorting.
"""
import json, sys, os, re, subprocess
ROOT = os.path.dirname(os.path.abspath(__file__))
P = os.path.join(ROOT, "deals.json")
REQUIRED = ["slug", "date", "title", "store", "category", "summary", "why", "who", "watch", "verdict"]

def key(d):
    return d.get("asin") or re.sub(r"[?#].*$", "", d.get("url", "")) or d["slug"]

def main(path):
    cur = json.load(open(P))
    new = json.load(open(path))
    seen_slugs = {d["slug"] for d in cur}
    seen_keys = {key(d) for d in cur if d.get("type") != "guide"}
    added = []
    for d in new:
        if d.get("type") != "guide":
            missing = [k for k in REQUIRED if not d.get(k)]
            if missing:
                print("SKIP (missing fields:", ", ".join(missing), ")", d.get("title")); continue
            if d["store"] == "amazon":
                d.pop("price", None); d.pop("was", None)  # Amazon prices are never shown on-site
                if not d.get("asin"):
                    print("SKIP (Amazon deal needs asin)", d["title"]); continue
        if d["slug"] in seen_slugs or (d.get("type") != "guide" and key(d) in seen_keys):
            print("SKIP (already posted)", d["title"]); continue
        cur.append(d); added.append(d["title"]); seen_slugs.add(d["slug"]); seen_keys.add(key(d))
    json.dump(cur, open(P, "w"), indent=2, ensure_ascii=False)
    print(f"Added {len(added)} deal(s):", *added, sep="\n  ")
    subprocess.run([sys.executable, os.path.join(ROOT, "build.py")], check=True)

if __name__ == "__main__":
    main(sys.argv[1])
