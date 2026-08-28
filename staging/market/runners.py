"""Per-source batch runners."""
from __future__ import annotations

import os
import re
import urllib.parse
from pathlib import Path

from batch_common import (
    BatchOpts,
    Progress,
    http_get_json,
    http_post_form,
    item_cached_ok,
    load_ids_file,
    save_json,
    sleep_between,
    utc_now,
)

MARKET_DIR = Path(__file__).resolve().parent
LATAM_CHUNK = 100  # API max per request

# --- Atlantis HTML parsing ---
_RE_STATS_ROW = re.compile(
    r"Precio Promedio</td>\s*</tr>\s*"
    r"<tr>(?P<cells>(?:<td[^>]*>[^<]*</td>\s*)+)</tr>",
    re.IGNORECASE | re.DOTALL,
)
_RE_CELL = re.compile(r"<td[^>]*>(?P<val>[^<]*)</td>", re.IGNORECASE)
_RE_ITEM_ID = re.compile(r"Resumen Transacciones Item\s+(\d+)", re.IGNORECASE)
_RE_ANT_NOTE = re.compile(r"Considerando\s+([^)<]+)\)", re.IGNORECASE)
_RE_NPC_ROW = re.compile(
    r"<td class=\"tdedit\" align=\"left\" width=\"40%\">(?P<name>[^<]*)</td>"
    r".*?"
    r"<td class=\"tdedit\" align=\"left\" width=\"10%\">(?P<sell>[^<]*)</td>"
    r"<td class=\"tdedit\" align=\"left\" width=\"10%\">(?P<buy>[^<]*)</td>",
    re.IGNORECASE | re.DOTALL,
)
ATLANTIS_URL = "http://atlantis.play-ro.com/index.php"


def _parse_int(s: str) -> int | None:
    s = s.strip().replace(",", "").replace("&nbsp;", "").strip()
    if not s:
        return None
    try:
        return int(s)
    except ValueError:
        return None


def _parse_atlantis_html(html: str) -> dict:
    row_m = _RE_STATS_ROW.search(html)
    if not row_m:
        raise ValueError("stats table not found")
    cells = [_parse_int(m.group("val")) for m in _RE_CELL.finditer(row_m.group("cells"))]
    if len(cells) < 5:
        raise ValueError(f"expected 5 stat cells, got {len(cells)}")
    item_id_m = _RE_ITEM_ID.search(html)
    ant_m = _RE_ANT_NOTE.search(html)
    npc = {}
    npc_m = _RE_NPC_ROW.search(html)
    if npc_m:
        npc = {
            "name": npc_m.group("name").strip(),
            "sell_to_npc": _parse_int(npc_m.group("sell")),
            "buy_from_npc": _parse_int(npc_m.group("buy")),
        }
    return {
        "item_id": int(item_id_m.group(1)) if item_id_m else None,
        "period_note": ant_m.group(1).strip() if ant_m else None,
        "stats": {
            "min": cells[0],
            "max": cells[1],
            "total_sold": cells[2],
            "std_dev": cells[3],
            "avg": cells[4],
        },
        "npc": npc,
    }


def _fetch_atlantis_item(item_id: int, opts: BatchOpts) -> dict:
    data = urllib.parse.urlencode({
        "item": str(item_id),
        "send": "Buscar",
        "tsort": "ACTUA",
        "ref": "ALL",
        "lim": "30",
        "carta": "ALL",
        "ant": "ALL",
        "forja": "ALL",
    }).encode("latin1", errors="replace")
    html = http_post_form(ATLANTIS_URL, data, timeout=opts.timeout).decode("latin1", errors="replace")
    if "Resumen Transacciones" not in html:
        raise ValueError("no transaction summary")
    return {
        "fetched_at": utc_now(),
        "source": "atlantis_playro",
        "request": {"item_id": item_id, "ant": "ALL"},
        **_parse_atlantis_html(html),
    }


def run_atlantis(ids_file: Path, opts: BatchOpts, *, limit: int | None = None) -> None:
    out_dir = MARKET_DIR / "atlantis_playro" / "bulk" / "items"
    progress = Progress(MARKET_DIR / "atlantis_playro" / "bulk" / "progress.json", opts.resume)
    ids = load_ids_file(ids_file)
    if limit:
        ids = ids[:limit]
    pending = [i for i in ids if i not in progress.completed]
    print(f"atlantis: total={len(ids)} pending={len(pending)}")

    for n, item_id in enumerate(pending, 1):
        path = out_dir / f"{item_id}.json"
        if opts.resume and item_cached_ok(path):
            progress.mark_ok(item_id)
            progress.save()
            continue
        try:
            payload = _fetch_atlantis_item(item_id, opts)
            save_json(path, payload)
            progress.mark_ok(item_id)
            print(f"[{n}/{len(pending)}] ok {item_id} avg={payload['stats']['avg']}")
        except Exception as e:
            progress.mark_fail(item_id, str(e))
            save_json(path, {"item_id": item_id, "error": str(e), "fetched_at": utc_now()})
            print(f"[{n}/{len(pending)}] FAIL {item_id}: {e}")
        progress.save()
        sleep_between(opts, n, len(pending))

    print(f"atlantis done failed={len(progress.data.get('failed', {}))}")


def run_latam(ids_file: Path, opts: BatchOpts, *, server: str, limit: int | None = None) -> None:
    out_dir = MARKET_DIR / "latam_tools" / "bulk" / server / "items"
    progress = Progress(MARKET_DIR / "latam_tools" / "bulk" / server / "progress.json", opts.resume)
    ids = load_ids_file(ids_file)
    if limit:
        ids = ids[:limit]
    pending = [i for i in ids if i not in progress.completed]
    print(f"latam/{server}: total={len(ids)} pending={len(pending)} chunks of {LATAM_CHUNK}")

    chunks = [pending[i:i + LATAM_CHUNK] for i in range(0, len(pending), LATAM_CHUNK)]
    for cn, chunk in enumerate(chunks, 1):
        # skip chunk if all cached
        if opts.resume and all(item_cached_ok(out_dir / f"{i}.json") for i in chunk):
            for i in chunk:
                progress.mark_ok(i)
            progress.save()
            print(f"[chunk {cn}/{len(chunks)}] skip {len(chunk)} cached")
            continue

        ids_param = ",".join(str(i) for i in chunk)
        url = f"https://mercado.latam-tools.com.br/api/v1/prices?items={ids_param}&server={server}"
        try:
            resp = http_get_json(url, timeout=opts.timeout)
            by_id = {p["itemId"]: p for p in resp.get("prices", [])}
            missing = resp.get("missing", [])
            for item_id in chunk:
                path = out_dir / f"{item_id}.json"
                if item_id in by_id:
                    payload = {
                        "fetched_at": utc_now(),
                        "source": "latam_tools",
                        "server": server,
                        "item_id": item_id,
                        "data": by_id[item_id],
                    }
                    save_json(path, payload)
                    progress.mark_ok(item_id)
                elif item_id in missing:
                    save_json(path, {
                        "item_id": item_id,
                        "error": "not_in_market",
                        "fetched_at": utc_now(),
                    })
                    progress.mark_ok(item_id)
                else:
                    progress.mark_fail(item_id, "absent from response")
            print(f"[chunk {cn}/{len(chunks)}] ok {len(chunk)} items")
        except Exception as e:
            for item_id in chunk:
                progress.mark_fail(item_id, str(e))
            print(f"[chunk {cn}/{len(chunks)}] FAIL: {e}")
        progress.save()
        sleep_between(opts, cn, len(chunks))

    print(f"latam/{server} done failed={len(progress.data.get('failed', {}))}")


def run_ragnapi(ids_file: Path, opts: BatchOpts, *, limit: int | None = None) -> None:
    out_dir = MARKET_DIR / "ragnapi" / "bulk" / "items"
    progress = Progress(MARKET_DIR / "ragnapi" / "bulk" / "progress.json", opts.resume)
    ids = load_ids_file(ids_file)
    if limit:
        ids = ids[:limit]
    pending = [i for i in ids if i not in progress.completed]
    print(f"ragnapi: total={len(ids)} pending={len(pending)}")

    for n, item_id in enumerate(pending, 1):
        path = out_dir / f"{item_id}.json"
        if opts.resume and item_cached_ok(path):
            progress.mark_ok(item_id)
            progress.save()
            continue
        url = f"https://ragnapi.com/api/v1/re-newal/items/{item_id}"
        try:
            data = http_get_json(url, timeout=opts.timeout)
            save_json(path, {
                "fetched_at": utc_now(),
                "source": "ragnapi",
                "item_id": item_id,
                "data": data,
            })
            progress.mark_ok(item_id)
            if n % 50 == 0 or n == len(pending):
                print(f"[{n}/{len(pending)}] ok through {item_id}")
        except Exception as e:
            err = str(e)
            if "404" in err or "HTTP 404" in err:
                save_json(path, {"item_id": item_id, "error": "not_found", "fetched_at": utc_now()})
                progress.mark_ok(item_id)
            else:
                progress.mark_fail(item_id, err)
                print(f"[{n}/{len(pending)}] FAIL {item_id}: {e}")
        progress.save()
        sleep_between(opts, n, len(pending))

    print(f"ragnapi done failed={len(progress.data.get('failed', {}))}")


def run_divine_pride(ids_file: Path, opts: BatchOpts, *, region: str, limit: int | None = None) -> None:
    key = os.environ.get("DIVINE_PRIDE_API_KEY")
    if not key:
        raise SystemExit("DIVINE_PRIDE_API_KEY not set")

    out_dir = MARKET_DIR / "divine_pride" / "bulk" / region / "items"
    progress = Progress(MARKET_DIR / "divine_pride" / "bulk" / region / "progress.json", opts.resume)
    ids = load_ids_file(ids_file)
    if limit:
        ids = ids[:limit]
    pending = [i for i in ids if i not in progress.completed]
    print(f"divine_pride/{region}: total={len(ids)} pending={len(pending)}")

    for n, item_id in enumerate(pending, 1):
        path = out_dir / f"{item_id}.json"
        if opts.resume and item_cached_ok(path):
            progress.mark_ok(item_id)
            progress.save()
            continue
        q = urllib.parse.urlencode({"apiKey": key})
        url = f"https://www.divine-pride.net/api/database/Item/{item_id}?{q}"
        try:
            data = http_get_json(url, timeout=opts.timeout, headers={
                "x-server": region,
                "Accept-Language": "en",
            })
            save_json(path, {
                "fetched_at": utc_now(),
                "source": "divine_pride",
                "region": region,
                "item_id": item_id,
                "data": data,
            })
            progress.mark_ok(item_id)
            if n % 50 == 0 or n == len(pending):
                print(f"[{n}/{len(pending)}] ok through {item_id}")
        except Exception as e:
            progress.mark_fail(item_id, str(e))
            print(f"[{n}/{len(pending)}] FAIL {item_id}: {e}")
        progress.save()
        sleep_between(opts, n, len(pending))

    print(f"divine_pride done failed={len(progress.data.get('failed', {}))}")
