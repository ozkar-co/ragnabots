"""Shared batch fetch utilities — delays, resume, progress, HTTP."""
from __future__ import annotations

import json
import random
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

MARKET_DIR = Path(__file__).resolve().parent
DEFAULT_IDS_FILE = MARKET_DIR / "item_ids_all.txt"
USER_AGENT = "RagnaBots-Staging/0.1 (personal research; contact via github if issues)"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_ids_file(path: Path) -> list[int]:
    ids: list[int] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.split("#", 1)[0].strip()
        if line:
            ids.append(int(line))
    return dedupe_ids(ids)


def dedupe_ids(ids: list[int]) -> list[int]:
    seen: set[int] = set()
    out: list[int] = []
    for i in ids:
        if i not in seen:
            seen.add(i)
            out.append(i)
    return out


@dataclass
class BatchOpts:
    delay: float = 3.0
    jitter: float = 1.0
    timeout: float = 30.0
    batch_pause_every: int = 50
    batch_pause: float = 60.0
    retries: int = 3
    resume: bool = False


class Progress:
    def __init__(self, path: Path, resume: bool) -> None:
        self.path = path
        if resume and path.exists():
            self.data = json.loads(path.read_text(encoding="utf-8"))
        else:
            self.data = {"completed": [], "failed": {}, "started_at": utc_now()}

    @property
    def completed(self) -> set[int]:
        return set(self.data.get("completed", []))

    def mark_ok(self, item_id: int) -> None:
        if item_id not in self.data.setdefault("completed", []):
            self.data["completed"].append(item_id)
        self.data.get("failed", {}).pop(str(item_id), None)

    def mark_fail(self, item_id: int, err: str) -> None:
        self.data.setdefault("failed", {})[str(item_id)] = err

    def save(self) -> None:
        self.data["updated_at"] = utc_now()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.data, indent=2) + "\n", encoding="utf-8")


def sleep_between(opts: BatchOpts, n: int, total: int) -> None:
    if n >= total:
        return
    if opts.batch_pause_every > 0 and n % opts.batch_pause_every == 0:
        print(f"--- batch pause {opts.batch_pause}s after {n} ---")
        time.sleep(opts.batch_pause)
    else:
        time.sleep(opts.delay + random.uniform(0, opts.jitter))


def http_get_json(url: str, *, timeout: float, headers: dict | None = None, retries: int = 3) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, **(headers or {})})
    raw = _request_bytes(req, timeout=timeout, retries=retries)
    return json.loads(raw.decode())


def http_post_form(url: str, data: bytes, *, timeout: float, headers: dict | None = None, retries: int = 3) -> bytes:
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "User-Agent": USER_AGENT,
            "Content-Type": "application/x-www-form-urlencoded",
            **(headers or {}),
        },
        method="POST",
    )
    return _request_bytes(req, timeout=timeout, retries=retries)


def _request_bytes(req: urllib.request.Request, *, timeout: float, retries: int = 3) -> bytes:
    last: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read()
        except urllib.error.HTTPError as e:
            last = e
            if attempt < retries and e.code >= 500:
                time.sleep(2 ** attempt + random.uniform(0, 1))
                continue
            raise RuntimeError(f"HTTP {e.code} {req.full_url}") from e
        except (urllib.error.URLError, TimeoutError) as e:
            last = e
            if attempt < retries:
                time.sleep(2 ** attempt + random.uniform(0, 1))
    raise RuntimeError(f"request failed after {retries} tries: {last}")


def save_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def item_cached_ok(path: Path) -> bool:
    if not path.exists():
        return False
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return "fetched_at" in data
    except json.JSONDecodeError:
        return False
