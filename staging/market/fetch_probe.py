#!/usr/bin/env python3
"""Fetch small samples from external RO APIs into staging/market/*/samples/.

Usage:
  python staging/market/fetch_probe.py latam_tools --items 501,909 --server FREYA
  python staging/market/fetch_probe.py ragnapi --items 501 --monsters 1002
  python staging/market/fetch_probe.py divine_pride --items 501
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STAGING = Path(__file__).resolve().parent


def _get(url: str, headers: dict | None = None) -> dict:
    req = urllib.request.Request(url, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        raise SystemExit(f"HTTP {e.code} {url}\n{body[:500]}") from e
    except urllib.error.URLError as e:
        raise SystemExit(f"Request failed: {url}\n{e}") from e


def _save(source: str, name: str, payload: dict) -> Path:
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_dir = STAGING / source / "samples"
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{ts}_{name}.json"
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def fetch_latam_tools(items: list[int], server: str) -> None:
    if server not in ("FREYA", "NIDHOGG"):
        raise SystemExit("server must be FREYA or NIDHOGG")
    ids = ",".join(str(i) for i in items)
    url = f"https://mercado.latam-tools.com.br/api/v1/prices?items={ids}&server={server}"
    data = _get(url)
    path = _save("latam_tools", f"batch_{server}_{ids.replace(',', '-')}", {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "source": "latam_tools",
        "server": server,
        "item_ids": items,
        "url": url,
        "response": data,
    })
    print(f"saved {path}")


def fetch_ragnapi(items: list[int], monsters: list[int]) -> None:
    results: dict = {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "source": "ragnapi",
        "items": {},
        "monsters": {},
    }
    for iid in items:
        url = f"https://ragnapi.com/api/v1/re-newal/items/{iid}"
        results["items"][str(iid)] = {"url": url, "data": _get(url)}
    for mid in monsters:
        url = f"https://ragnapi.com/api/v1/re-newal/monsters/{mid}"
        results["monsters"][str(mid)] = {"url": url, "data": _get(url)}
    name_parts = []
    if items:
        name_parts.append("items-" + "-".join(map(str, items[:5])))
    if monsters:
        name_parts.append("mobs-" + "-".join(map(str, monsters[:5])))
    path = _save("ragnapi", "_".join(name_parts) or "empty", results)
    print(f"saved {path}")


def fetch_divine_pride(items: list[int], region: str) -> None:
    key = os.environ.get("DIVINE_PRIDE_API_KEY")
    if not key:
        raise SystemExit("DIVINE_PRIDE_API_KEY not set — get key at https://www.divine-pride.net/api")
    results: dict = {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "source": "divine_pride",
        "region": region,
        "items": {},
    }
    for iid in items:
        q = urllib.parse.urlencode({"apiKey": key})
        url = f"https://www.divine-pride.net/api/database/Item/{iid}?{q}"
        results["items"][str(iid)] = {
            "url": f"https://www.divine-pride.net/api/database/Item/{iid}",
            "data": _get(url, headers={"x-server": region, "Accept-Language": "en"}),
        }
    path = _save("divine_pride", "items-" + "-".join(map(str, items[:5])), results)
    print(f"saved {path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch external RO market samples to staging/")
    parser.add_argument("source", choices=["latam_tools", "ragnapi", "divine_pride"])
    parser.add_argument("--items", default="", help="Comma-separated item IDs")
    parser.add_argument("--monsters", default="", help="Comma-separated monster IDs (ragnapi)")
    parser.add_argument("--server", default="FREYA", help="FREYA or NIDHOGG (latam_tools)")
    parser.add_argument("--region", default="iRO", help="Divine Pride region header")
    args = parser.parse_args()

    items = [int(x) for x in args.items.split(",") if x.strip()]
    monsters = [int(x) for x in args.monsters.split(",") if x.strip()]

    if args.source == "latam_tools":
        if not items:
            raise SystemExit("--items required for latam_tools")
        fetch_latam_tools(items, args.server.upper())
    elif args.source == "ragnapi":
        if not items and not monsters:
            raise SystemExit("--items and/or --monsters required for ragnapi")
        fetch_ragnapi(items, monsters)
    else:
        if not items:
            raise SystemExit("--items required for divine_pride")
        fetch_divine_pride(items, args.region.upper())


if __name__ == "__main__":
    main()
