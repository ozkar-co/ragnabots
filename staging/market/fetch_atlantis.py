#!/usr/bin/env python3
"""Batch-fetch item price stats from atlantis.play-ro.com (respectful, resumable).

Single item:
  python staging/market/fetch_atlantis.py --items 501

Overnight batch (3s delay, resume):
  python staging/market/fetch_atlantis.py --items-file staging/market/atlantis_playro/item_ids.txt \\
      --delay 3 --batch-pause-every 50 --batch-pause 30 --resume

Output: staging/market/atlantis_playro/bulk/items/{id}.json
Progress: staging/market/atlantis_playro/bulk/progress.json
"""
from __future__ import annotations

import argparse
import json
import random
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

BASE_URL = "http://atlantis.play-ro.com/index.php"
STAGING = Path(__file__).resolve().parent / "atlantis_playro"
BULK_DIR = STAGING / "bulk" / "items"
PROGRESS_FILE = STAGING / "bulk" / "progress.json"

USER_AGENT = "RagnaBots-Staging/0.1 (personal research; contact via github if issues)"

# HTML parsing — table row after "Precio Promedio" header
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


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_int(s: str) -> int | None:
    s = s.strip().replace(",", "").replace("&nbsp;", "").strip()
    if not s:
        return None
    try:
        return int(s)
    except ValueError:
        return None


def _parse_stats(html: str) -> dict:
    item_id_m = _RE_ITEM_ID.search(html)
    ant_m = _RE_ANT_NOTE.search(html)
    row_m = _RE_STATS_ROW.search(html)
    if not row_m:
        raise ValueError("stats table not found in response")
    cells = [_parse_int(m.group("val")) for m in _RE_CELL.finditer(row_m.group("cells"))]
    if len(cells) < 5:
        raise ValueError(f"expected 5 stat cells, got {len(cells)}")
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


def fetch_item(
    item_id: int,
    *,
    ant: str = "ALL",
    timeout: float = 30,
    retries: int = 3,
) -> dict:
    data = urllib.parse.urlencode({
        "item": str(item_id),
        "send": "Buscar",
        "tsort": "ACTUA",
        "ref": "ALL",
        "lim": "30",
        "carta": "ALL",
        "ant": ant,
        "forja": "ALL",
    }).encode("latin1", errors="replace")
    req = urllib.request.Request(
        BASE_URL,
        data=data,
        headers={
            "User-Agent": USER_AGENT,
            "Content-Type": "application/x-www-form-urlencoded",
        },
        method="POST",
    )
    last_err: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                html = resp.read().decode("latin1", errors="replace")
            parsed = _parse_stats(html)
            if "Resumen Transacciones" not in html:
                raise ValueError("no transaction summary — item may not exist")
            return {
                "fetched_at": _now(),
                "source": "atlantis_playro",
                "url": BASE_URL,
                "request": {"item_id": item_id, "ant": ant},
                **parsed,
            }
        except (urllib.error.URLError, TimeoutError, ValueError) as e:
            last_err = e
            if attempt < retries:
                time.sleep(2 ** attempt + random.uniform(0, 1))
    raise RuntimeError(f"item {item_id} failed after {retries} tries: {last_err}")


def _load_progress() -> dict:
    if PROGRESS_FILE.exists():
        return json.loads(PROGRESS_FILE.read_text(encoding="utf-8"))
    return {"completed": [], "failed": {}, "started_at": _now()}


def _save_progress(progress: dict) -> None:
    progress["updated_at"] = _now()
    PROGRESS_FILE.parent.mkdir(parents=True, exist_ok=True)
    PROGRESS_FILE.write_text(json.dumps(progress, indent=2) + "\n", encoding="utf-8")


def _save_item(payload: dict) -> Path:
    item_id = payload["item_id"] or payload["request"]["item_id"]
    BULK_DIR.mkdir(parents=True, exist_ok=True)
    path = BULK_DIR / f"{item_id}.json"
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def _load_ids_file(path: Path) -> list[int]:
    ids: list[int] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.split("#", 1)[0].strip()
        if line:
            ids.append(int(line))
    return ids


def run_batch(
    item_ids: list[int],
    *,
    ant: str,
    delay: float,
    timeout: float,
    batch_pause_every: int,
    batch_pause: float,
    resume: bool,
    jitter: float,
) -> None:
    progress = _load_progress() if resume else {"completed": [], "failed": {}, "started_at": _now()}
    done = set(progress.get("completed", []))
    pending = [i for i in item_ids if i not in done]
    print(f"items total={len(item_ids)} pending={len(pending)} already_done={len(done)}")

    for n, item_id in enumerate(pending, 1):
        out_path = BULK_DIR / f"{item_id}.json"
        if resume and out_path.exists():
            try:
                existing = json.loads(out_path.read_text(encoding="utf-8"))
                if existing.get("stats"):
                    progress.setdefault("completed", []).append(item_id)
                    done.add(item_id)
                    _save_progress(progress)
                    print(f"[{n}/{len(pending)}] skip {item_id} (cached)")
                    continue
            except json.JSONDecodeError:
                pass

        try:
            payload = fetch_item(item_id, ant=ant, timeout=timeout)
            path = _save_item(payload)
            progress.setdefault("completed", []).append(item_id)
            progress.get("failed", {}).pop(str(item_id), None)
            avg = payload["stats"]["avg"]
            print(f"[{n}/{len(pending)}] ok {item_id} avg={avg} -> {path.name}")
        except Exception as e:
            progress.setdefault("failed", {})[str(item_id)] = str(e)
            print(f"[{n}/{len(pending)}] FAIL {item_id}: {e}")

        _save_progress(progress)

        if n < len(pending):
            sleep_for = delay + random.uniform(0, jitter)
            if batch_pause_every > 0 and n % batch_pause_every == 0:
                print(f"--- batch pause {batch_pause}s after {n} items ---")
                time.sleep(batch_pause)
            else:
                time.sleep(sleep_for)

    failed = progress.get("failed", {})
    print(f"done. completed={len(progress.get('completed', []))} failed={len(failed)}")
    if failed:
        print("failed ids:", ", ".join(sorted(failed, key=int)))


def main() -> None:
    parser = argparse.ArgumentParser(description="Batch fetch Atlantis Play-RO price stats")
    parser.add_argument("--items", default="", help="Comma-separated item IDs")
    parser.add_argument("--items-file", type=Path, help="File with one item ID per line")
    parser.add_argument("--ant", default="ALL", help="Data age: 90, 180, 365, ALL")
    parser.add_argument("--delay", type=float, default=3.0, help="Seconds between requests")
    parser.add_argument("--jitter", type=float, default=1.0, help="Random extra delay 0..jitter")
    parser.add_argument("--timeout", type=float, default=30.0, help="HTTP timeout seconds")
    parser.add_argument("--batch-pause-every", type=int, default=50, help="Extra pause every N items (0=off)")
    parser.add_argument("--batch-pause", type=float, default=30.0, help="Extra pause duration seconds")
    parser.add_argument("--resume", action="store_true", help="Skip completed items in progress.json")
    args = parser.parse_args()

    ids: list[int] = []
    if args.items:
        ids.extend(int(x) for x in args.items.split(",") if x.strip())
    if args.items_file:
        ids.extend(_load_ids_file(args.items_file))
    if not ids:
        raise SystemExit("provide --items and/or --items-file")

    # preserve order, dedupe
    seen: set[int] = set()
    unique: list[int] = []
    for i in ids:
        if i not in seen:
            seen.add(i)
            unique.append(i)

    run_batch(
        unique,
        ant=args.ant,
        delay=args.delay,
        timeout=args.timeout,
        batch_pause_every=args.batch_pause_every,
        batch_pause=args.batch_pause,
        resume=args.resume,
        jitter=args.jitter,
    )


if __name__ == "__main__":
    main()
