"""Server health dashboard -- CPU/memory/disk for ndr-production and
ndr-playground at admin.ahfl.in/server-health?host=<name>.

Three deliberately separate data sources per host:
  - Hetzner Cloud metrics API: cpu %, disk I/O (bandwidth/iops), network
    (bandwidth/pps). Hetzner already retains ~29+ days of this per server
    (verified live 2026-11-14) -- queried on each page load, 5min cache,
    nothing stored locally for these. Same for both hosts, just a
    different server id.
  - A live system report: memory %, swap %, load avg, disk used/free/total,
    container restart/OOM flags.
      - ndr-production: this container (hermes-apps) shares the host's
        procfs and root filesystem view (verified empirically 2026-11-14 --
        MemTotal and df % matched the host exactly), so a direct /proc read
        IS the host's numbers, not this container's cgroup limits.
      - ndr-playground: this container can't see that host's /proc, so a
        tiny read-only report is pulled over SSH instead (asyncssh, key at
        /secrets/server_health_playground_key). That key's authorized_keys
        entry on playground is command="/usr/local/bin/server-health-
        readonly.sh" -- it cannot run anything else no matter what this
        code sends it. Host key is pinned (/secrets/playground_known_hosts),
        not verification-disabled.
  - A small local sqlite file (mem_used_pct / swap_used_pct / disk_used_gb
    sampled every ~10min, one row per host) -- the one thing Hetzner's API
    can't give us, since it has no memory metric and "disk" there means
    I/O, not usage. History starts accumulating from first deploy of this
    file; there is no way to backfill a real 30-day trend before that.

Hetzner API token lives in a plain file (/secrets/hetzner_api_token), not
an env var -- avoids a container recreation (new env vars need one) just
to wire in a read-only token. /secrets is already a writable host mount
on this container.

KNOWN GAP: asyncssh was pip-installed directly into this container's
/opt/venv-admin at runtime (2026-11-14), not added to any requirements.txt
baked into the image. It will vanish on the next full image rebuild/
recreate (not on a plain process/container restart) unless added there too.
"""
from __future__ import annotations

import asyncio
import logging
import os
import shutil
import sqlite3
import threading
import time
from datetime import datetime, timedelta, timezone

import asyncssh
import httpx
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from .jinja_env import env

router = APIRouter()
logger = logging.getLogger("admin-app.server_health")

HETZNER_TOKEN_PATH = "/secrets/hetzner_api_token"
HETZNER_API = "https://api.hetzner.cloud/v1"

# Single registry per host: Hetzner server id (for cpu/disk-io/network +
# core-count normalization) and how to reach its own mem/disk/load/
# container numbers.
HOSTS: dict[str, dict] = {
    "ndr-production": {
        "hetzner_id": 158869657,
        "cores": 4,  # cpx32
        "access": "local",
    },
    "ndr-playground": {
        "hetzner_id": 128476111,
        "cores": 2,  # cax11
        "access": "ssh",
        "ssh_host": "178.105.35.94",
        "ssh_key": "/secrets/server_health_playground_key",
        "ssh_known_hosts": "/secrets/playground_known_hosts",
    },
}
DEFAULT_HOST = "ndr-production"

DB_PATH = "/data/server-health/host_metrics.db"
SAMPLE_INTERVAL_S = 600  # 10 min
_HETZNER_CACHE: dict[str, tuple[float, dict]] = {}
_HETZNER_CACHE_TTL = 300  # 5 min
_REMOTE_CACHE: dict[str, tuple[float, dict]] = {}
_REMOTE_CACHE_TTL = 60  # an SSH round trip is a lot costlier than a local file read
_DAY_S = 86400


def _hetzner_token() -> str:
    try:
        with open(HETZNER_TOKEN_PATH) as f:
            return f.read().strip()
    except OSError:
        return ""


def _db() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "CREATE TABLE IF NOT EXISTS samples ("
        "host TEXT NOT NULL, ts INTEGER NOT NULL, "
        "mem_used_pct REAL, swap_used_pct REAL, disk_used_gb REAL)"
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_samples_host_ts ON samples(host, ts)")
    return conn


# ---------------------------------------------------------------------------
# Parsers -- pure text in, dict out. Shared between the local /proc reads
# (ndr-production) and the SSH-fetched report text (ndr-playground) so
# there is exactly one place that knows the /proc/meminfo or loadavg shape.
# ---------------------------------------------------------------------------

def _parse_meminfo_text(text: str) -> dict:
    info: dict[str, int] = {}
    for line in text.splitlines():
        k, _, v = line.partition(":")
        try:
            info[k.strip()] = int(v.strip().split()[0])  # kB
        except (ValueError, IndexError):
            pass
    mem_total = info.get("MemTotal", 0)
    mem_avail = info.get("MemAvailable", 0)
    swap_total = info.get("SwapTotal", 0)
    swap_free = info.get("SwapFree", 0)
    mem_used_pct = (1 - mem_avail / mem_total) * 100 if mem_total else 0.0
    swap_used_pct = (1 - swap_free / swap_total) * 100 if swap_total else 0.0
    return {
        "mem_total_gb": mem_total / 1024 / 1024,
        "mem_used_pct": mem_used_pct,
        "swap_total_gb": swap_total / 1024 / 1024,
        "swap_used_pct": swap_used_pct,
    }


def _parse_loadavg_text(text: str) -> dict:
    parts = text.split()
    return {"load1": float(parts[0]), "load5": float(parts[1]), "load15": float(parts[2])}


def _parse_df_line(line: str) -> dict:
    """Parse one `df -k /` data line (Filesystem 1K-blocks Used Available Use% Mounted)."""
    parts = line.split()
    total_kb, used_kb, avail_kb = float(parts[-5]), float(parts[-4]), float(parts[-3])
    kb_per_gb = 1024.0 * 1024.0
    return {
        "disk_total_gb": total_kb / kb_per_gb,
        "disk_used_gb": used_kb / kb_per_gb,
        "disk_avail_gb": avail_kb / kb_per_gb,
        "disk_used_pct": used_kb / total_kb * 100 if total_kb else 0.0,
    }


def _parse_containers_block(text: str) -> list[dict]:
    rows = []
    for line in text.splitlines():
        line = line.strip()
        if "|" not in line:
            continue
        parts = line.split("|")
        if len(parts) != 4:
            continue
        name, status, restarts, oom = parts
        try:
            restart_count = int(restarts)
        except ValueError:
            continue
        oom_killed = oom.strip().lower() == "true"
        if restart_count > 0 or oom_killed or status.strip() != "running":
            rows.append({
                "name": name, "status": status,
                "restart_count": restart_count, "oom_killed": oom_killed,
            })
    return rows


# ---------------------------------------------------------------------------
# Local (ndr-production) readers -- this container IS that host.
# ---------------------------------------------------------------------------

def _read_proc_meminfo() -> dict:
    with open("/proc/meminfo") as f:
        return _parse_meminfo_text(f.read())


def _read_loadavg() -> dict:
    with open("/proc/loadavg") as f:
        return _parse_loadavg_text(f.read())


def _read_disk_usage() -> dict:
    total, used, free = shutil.disk_usage("/")
    gb = 1024 ** 3
    return {
        "disk_total_gb": total / gb,
        "disk_used_gb": used / gb,
        "disk_avail_gb": free / gb,
        "disk_used_pct": used / total * 100 if total else 0.0,
    }


async def _docker_ps_health() -> list[dict]:
    """Restart counts + OOM flags for every container on this host.

    Flags only containers that aren't simply running cleanly -- a healthy
    page should show an empty list, not a wall of zeros.
    """
    try:
        proc = await asyncio.create_subprocess_exec(
            "docker", "ps", "-a", "--format", "{{.Names}}",
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.DEVNULL,
        )
        out, _ = await asyncio.wait_for(proc.communicate(), timeout=15)
        names = [n for n in out.decode().splitlines() if n.strip()]
    except Exception:
        logger.exception("docker ps failed")
        return []

    async def _inspect(name: str) -> dict | None:
        try:
            proc = await asyncio.create_subprocess_exec(
                "docker", "inspect", name,
                "--format", "{{.State.Status}}|{{.RestartCount}}|{{.State.OOMKilled}}",
                stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.DEVNULL,
            )
            out, _ = await asyncio.wait_for(proc.communicate(), timeout=10)
            status, restarts, oom = out.decode().strip().split("|")
            return {
                "name": name, "status": status,
                "restart_count": int(restarts), "oom_killed": oom == "true",
            }
        except Exception:
            return None

    results = await asyncio.gather(*[_inspect(n) for n in names])
    return [
        r for r in results
        if r and (r["restart_count"] > 0 or r["oom_killed"] or r["status"] != "running")
    ]


# ---------------------------------------------------------------------------
# Remote (ndr-playground) reader -- one SSH round trip runs the fixed,
# command-restricted script and returns everything at once.
# ---------------------------------------------------------------------------

async def _ssh_report(host: str, cfg: dict) -> dict:
    now = time.time()
    cached = _REMOTE_CACHE.get(host)
    if cached and now - cached[0] < _REMOTE_CACHE_TTL:
        return cached[1]

    try:
        async with asyncssh.connect(
            cfg["ssh_host"], username="root",
            client_keys=[cfg["ssh_key"]],
            known_hosts=cfg["ssh_known_hosts"],
            connect_timeout=10,
        ) as conn:
            r = await asyncio.wait_for(conn.run("ignored-by-forced-command", check=False), timeout=20)
            text = r.stdout
    except Exception as exc:  # noqa: BLE001 - render the page with a banner, not a 500
        logger.warning("ssh report fetch failed for %s: %s", cfg["ssh_host"], exc)
        return {"error": str(exc)}

    try:
        mem_block = text.split("---MEMINFO---", 1)[1].split("---LOADAVG---")[0]
        load_block = text.split("---LOADAVG---", 1)[1].split("---DISKUSAGE---")[0]
        disk_block = text.split("---DISKUSAGE---", 1)[1].split("---CONTAINERS---")[0]
        containers_block = text.split("---CONTAINERS---", 1)[1].split("---END---")[0]
        result = {
            "mem": _parse_meminfo_text(mem_block),
            "load": _parse_loadavg_text(load_block),
            "disk": _parse_df_line(disk_block.strip().splitlines()[0]),
            "containers": _parse_containers_block(containers_block),
        }
    except Exception as exc:  # noqa: BLE001
        logger.warning("ssh report for %s came back malformed: %s", cfg["ssh_host"], exc)
        return {"error": f"malformed report: {exc}"}

    _REMOTE_CACHE[host] = (now, result)
    return result


async def _get_host_stats(host: str) -> dict:
    """Uniform {mem, disk, load, containers, error} for either access mode."""
    cfg = HOSTS[host]
    if cfg["access"] == "local":
        return {
            "mem": _read_proc_meminfo(),
            "disk": _read_disk_usage(),
            "load": _read_loadavg(),
            "containers": await _docker_ps_health(),
            "error": None,
        }
    report = await _ssh_report(host, cfg)
    if "error" in report:
        return {"mem": {}, "disk": {}, "load": {}, "containers": [], "error": report["error"]}
    return {**report, "error": None}


# ---------------------------------------------------------------------------
# Hetzner Cloud metrics -- identical for both hosts, just a different id.
# ---------------------------------------------------------------------------

async def _hetzner_metrics(server_id: int, days: int = 29) -> dict:
    cache_key = f"{server_id}:{days}"
    now = time.time()
    cached = _HETZNER_CACHE.get(cache_key)
    if cached and now - cached[0] < _HETZNER_CACHE_TTL:
        return cached[1]

    token = _hetzner_token()
    if not token:
        return {"error": f"no Hetzner API token at {HETZNER_TOKEN_PATH}"}

    start = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%SZ")
    end = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.get(
                f"{HETZNER_API}/servers/{server_id}/metrics",
                params={"type": "cpu,disk,network", "start": start, "end": end},
                headers={"Authorization": f"Bearer {token}"},
            )
        resp.raise_for_status()
        data = resp.json()["metrics"]["time_series"]
    except Exception as exc:  # noqa: BLE001 - render the page with a banner, not a 500
        logger.warning("Hetzner metrics fetch failed for %s: %s", server_id, exc)
        return {"error": str(exc)}

    result = {"series": data}
    _HETZNER_CACHE[cache_key] = (now, result)
    return result


def _series_stats(values: list, since_s: float) -> dict:
    """avg/peak/current over the whole series, and over the last since_s."""
    if not values:
        return {"avg": None, "peak": None, "current": None, "avg_recent": None, "peak_recent": None}
    nums = [float(v[1]) for v in values]
    cutoff = time.time() - since_s
    recent = [float(v[1]) for v in values if v[0] >= cutoff]
    return {
        "avg": sum(nums) / len(nums),
        "peak": max(nums),
        "current": nums[-1],
        "avg_recent": (sum(recent) / len(recent)) if recent else None,
        "peak_recent": max(recent) if recent else None,
    }


def _fmt_bw(bytes_per_s: float | None) -> str:
    if bytes_per_s is None:
        return "-"
    return f"{bytes_per_s / 1e6:.2f} MB/s"


# ---------------------------------------------------------------------------
# Local history (sqlite) -- the one thing neither Hetzner nor a live read
# can give us: trend over time for memory/swap/disk.
# ---------------------------------------------------------------------------

def _disk_growth(host: str) -> dict:
    """Linear fit of disk_used_gb over stored samples -> GB/day + ETA to full."""
    conn = _db()
    rows = conn.execute(
        "SELECT ts, disk_used_gb FROM samples WHERE host=? AND disk_used_gb IS NOT NULL ORDER BY ts",
        (host,),
    ).fetchall()
    conn.close()
    if len(rows) < 2:
        return {"status": "collecting", "n_samples": len(rows)}

    t0 = rows[0][0]
    xs = [(r[0] - t0) / _DAY_S for r in rows]
    ys = [r[1] for r in rows]
    n = len(xs)
    mean_x, mean_y = sum(xs) / n, sum(ys) / n
    num = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    den = sum((x - mean_x) ** 2 for x in xs)
    slope_gb_per_day = (num / den) if den else 0.0
    return {
        "status": "ok",
        "n_samples": n,
        "span_days": round(xs[-1], 1),
        "gb_per_day": round(slope_gb_per_day, 3),
        "oldest_sample_at": datetime.fromtimestamp(t0, tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
    }


def _local_history(host: str, since_s: float) -> dict:
    conn = _db()
    rows = conn.execute(
        "SELECT ts, mem_used_pct, swap_used_pct FROM samples WHERE host=? ORDER BY ts",
        (host,),
    ).fetchall()
    conn.close()
    if not rows:
        return {"mem": {}, "swap": {}}
    cutoff = time.time() - since_s

    def _stats(col: int) -> dict:
        allv = [r[col] for r in rows if r[col] is not None]
        recent = [r[col] for r in rows if r[0] >= cutoff and r[col] is not None]
        return {
            "avg_30d": (sum(allv) / len(allv)) if allv else None,
            "peak_30d": max(allv) if allv else None,
            "avg_24h": (sum(recent) / len(recent)) if recent else None,
            "peak_24h": max(recent) if recent else None,
        }

    return {"mem": _stats(1), "swap": _stats(2)}


async def _sample_once(host: str) -> None:
    stats = await _get_host_stats(host)
    mem, disk = stats.get("mem") or {}, stats.get("disk") or {}
    if not mem or not disk:
        logger.warning("skipping sample for %s: %s", host, stats.get("error"))
        return
    conn = _db()
    conn.execute(
        "INSERT INTO samples (host, ts, mem_used_pct, swap_used_pct, disk_used_gb) VALUES (?,?,?,?,?)",
        (host, int(time.time()), mem["mem_used_pct"], mem["swap_used_pct"], disk["disk_used_gb"]),
    )
    conn.commit()
    conn.close()


async def _sample_all() -> None:
    for host in HOSTS:
        try:
            await _sample_once(host)
        except Exception:  # noqa: BLE001
            logger.exception("server_health sampler tick failed for %s", host)


def start_sampler() -> None:
    """Background thread, same pattern as openwebui.ensure_chat_defaults_in_background."""
    def _loop() -> None:
        while True:
            try:
                asyncio.run(_sample_all())
            except Exception:  # noqa: BLE001
                logger.exception("server_health sampler tick failed")
            time.sleep(SAMPLE_INTERVAL_S)

    threading.Thread(target=_loop, name="server-health-sampler", daemon=True).start()


# ---------------------------------------------------------------------------
# Route
# ---------------------------------------------------------------------------

@router.get("/server-health")
async def server_health_page(request: Request, host: str = DEFAULT_HOST):
    if host not in HOSTS:
        host = DEFAULT_HOST
    cfg = HOSTS[host]

    hetzner, stats = await asyncio.gather(
        _hetzner_metrics(cfg["hetzner_id"]), _get_host_stats(host),
    )

    cpu_stats: dict = {}
    disk_io_rows: list[dict] = []
    net_rows: list[dict] = []
    if "series" in hetzner:
        series = hetzner["series"]
        raw_cpu = _series_stats(series.get("cpu", {}).get("values", []), _DAY_S)
        cores = cfg["cores"]
        cpu_stats = {k: (v / cores if v is not None else None) for k, v in raw_cpu.items()}
        for key, label in (
            ("disk.0.bandwidth.read", "Disk read"), ("disk.0.bandwidth.write", "Disk write"),
        ):
            s = _series_stats(series.get(key, {}).get("values", []), _DAY_S)
            disk_io_rows.append({"label": label, **{k: _fmt_bw(v) for k, v in s.items()}})
        for key, label in (
            ("disk.0.iops.read", "Disk read IOPS"), ("disk.0.iops.write", "Disk write IOPS"),
        ):
            s = _series_stats(series.get(key, {}).get("values", []), _DAY_S)
            disk_io_rows.append({"label": label, **{k: (f"{v:.1f}" if v is not None else "-") for k, v in s.items()}})
        for key, label, fmt in (
            ("network.0.bandwidth.in", "Network in", _fmt_bw),
            ("network.0.bandwidth.out", "Network out", _fmt_bw),
            ("network.0.pps.in", "Packets in", lambda v: f"{v:.1f} pps" if v is not None else "-"),
            ("network.0.pps.out", "Packets out", lambda v: f"{v:.1f} pps" if v is not None else "-"),
        ):
            s = _series_stats(series.get(key, {}).get("values", []), _DAY_S)
            net_rows.append({"label": label, **{k: fmt(v) for k, v in s.items()}})

    stats_error = stats.get("error")
    live_mem = stats.get("mem") or {}
    live_disk = stats.get("disk") or {}
    live_load = stats.get("load") or {}
    containers = stats.get("containers") or []
    local_hist = _local_history(host, _DAY_S)
    growth = _disk_growth(host)

    eta = None
    if growth.get("status") == "ok" and growth["gb_per_day"] > 0.01 and live_disk.get("disk_avail_gb") is not None:
        days_left = live_disk["disk_avail_gb"] / growth["gb_per_day"]
        eta = {
            "days_left": round(days_left, 1),
            "eta_date": (datetime.now(timezone.utc) + timedelta(days=days_left)).date().isoformat(),
        }

    return HTMLResponse(env.get_template("server_health.html").render(
        user=request.session.get("user"),
        host=host,
        hosts=list(HOSTS.keys()),
        hetzner_error=hetzner.get("error"),
        stats_error=stats_error,
        cpu_stats=cpu_stats,
        disk_io_rows=disk_io_rows,
        net_rows=net_rows,
        live_mem=live_mem,
        live_disk=live_disk,
        live_load=live_load,
        local_hist=local_hist,
        growth=growth,
        eta=eta,
        containers=containers,
    ))
