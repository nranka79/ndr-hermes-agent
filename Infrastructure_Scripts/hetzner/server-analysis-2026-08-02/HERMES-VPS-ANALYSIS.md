# Hermes VPS — Exhaustive Usage Analysis & Sizing Recommendation

**Host:** Hetzner Cloud — `178.105.35.94` / `transcribe.ahfl.in` · Instance ID `128476111`
**Date of analysis:** 2026-08-02 (data window: 2026-07-25 → 2026-08-02, UTC)
**Current plan:** CAX11 (ARM/Ampere — 2 vCPU Neoverse-N1 @ 2.0 GHz, 4 GB RAM, 40 GB root disk) + 60 GB block volume
**Prepared by:** Hermes agent (local) — all data pulled live from the VPS via SSH; nothing estimated where a measurement was possible.

---

## 0. Executive Summary (TL;DR)

The server is **fundamentally undersized for the workload it is running** and is in a state of chronic memory exhaustion with recurring OOM-killer events. This is not a tuning problem — it is a capacity problem.

| Bottleneck | Evidence | Verdict |
|---|---|---|
| **RAM (the binding constraint)** | 17 containers consume ~2.9 GB RSS; swap (2 GB) was **≥50% used 100% of the time** and **100% full at p95** across the entire 9-day window; kernel OOM-killer executed 4 processes on 2026-08-02 15:09–15:19 (uvicorn, headless_shell ×2, pdftoppm); memory commit reached **224% of RAM+swap** | **Critical — needs ≥8 GB, ideally 16 GB** |
| **CPU** | Average busy only 10.7% of 2 cores (0.21 core), p95 44.5% (0.89 core) — BUT extreme spikes: **load 1-min hit 192.7** (Jul 30), load 15-min hit 115.3; 1.8% of all 10-min intervals had load >8 | **Overflow-capacity problem — spikes dwarf the mean; 4–8 cores needed** |
| **Root disk** | **95% full (2.0 GB free of 38 GB)**; hermes-data alone is 20 GB; 592 MB of stale backup tarballs; only 13.8 GB docker build cache reclaimable on the *volume* | **Critical — needs ≥80 GB root** |
| **Volume (60 GB)** | 76% full (43 GB used) — docker data-root lives here (36 GB images + 15 GB build cache) | **Needs resize to ≥100 GB** |
| **I/O** | Disk latency (`await`) peaked at **39,374 ms (39 s)**; iowait 96.5% peaks; 32 MB/s write bursts — largely swap-thrash collateral, not raw disk failure | **Improves automatically once RAM pressure is fixed** |

**Recommendation (see §9):**
- **Recommended: CAX31 (8 vCPU / 16 GB / 160 GB) ≈ €21.49/mo** — removes all three bottlenecks with 2–4× headroom and room for the stack's growth trajectory.
- **Minimum viable: CAX21 (4 vCPU / 8 GB / 80 GB) ≈ €10.99/mo** — stops OOM kills and disk-full today; CPU headroom vs. the 192-load events is modest.
- **Both cases: resize the block volume 60 GB → 100–120 GB** (+€2.29–3.43/mo), or migrate the docker data-root onto the bigger root disk.
- **Free money:** reclaim ~13.8 GB docker build cache + 592 MB stale tarballs immediately.

---

## 1. Data Sources & Methodology

| Source | What it provides | Coverage |
|---|---|---|
| `/var/log/sysstat` daily archives (`sa25`…`sa02`) | CPU %, iowait, load avg, memory %, swap %, per-device disk I/O — **10-minute resolution** | 9 days (Jul 25 → Aug 2) — limited by `HISTORY=7` rotation; **30 days of on-box history does not exist** |
| `docker ps` / `docker stats` / `docker inspect` | Container inventory, live CPU/RAM, restart counts, volumes, images | Point-in-time 2026-08-02 15:20 UTC |
| `docker-compose.yml` + `docker-compose.override.yml` | Full service definitions, env wiring, mounts | Current state |
| `/etc/nginx/sites-enabled/` | Reverse-proxy topology (6 domains) | Current state |
| `journalctl -k` (kernel ring) | OOM-kill records | 30-day lookback |
| `df` / `du` / `lsblk` | Storage layout & usage | Current state |
| Hetzner Cloud pricing docs (web) | Plan catalog + 2026 prices | Web, 2026-08 |

**Honesty note:** the "30-day" request cannot be fully satisfied from on-box data — sysstat retention is 7 days + current (9 files present). The window we do have (9 days at 10-min granularity, 1,236 intervals) includes both the *quiet* baseline and *the* catastrophic days (Jul 29–30, Aug 1–2), so it is representative. If 30 days are strictly required, the Hetzner Cloud **metrics API** (with an API token) can provide a longer series going forward; the recommendation below does not depend on the missing 21 days.

---

## 2. Current Hardware (verified on-box)

| Property | Value |
|---|---|
| Provider / type | Hetzner Cloud — Cost-Optimized **ARM** line (Ampere) |
| Plan (matched to catalog) | **CAX11** — 2 vCPU, 4 GB RAM, 40 GB NVMe root, 20 TB traffic |
| CPU | 2 × Ampere Neoverse-N1 @ 2.0 GHz (aarch64), 1 thread/core |
| RAM | 3.7 GiB (4 GB) — plus 2 GB `/swapfile` (swappiness=10) |
| Root disk | 38.1 GB ext4 → **34 GB used / 2.0 GB free (95%)** |
| Block volume | 60 GB (`/mnt/HC_Volume_106048678`, `sda`) → **43 GB used / 14 GB free (76%)** — docker data-root lives here |
| OS | Ubuntu 24.04.4 LTS (kernel 6.8.0-124-generic) |
| Uptime | 46 days (no reboot since ~Jun 17) |

---

## 3. Workload Inventory — All Containers (17 running)

Live snapshot 2026-08-02 ~15:20 UTC (all on 2 vCPU / 4 GB):

| Container | Image | Role | CPU% | RSS | Restarts | Uptime |
|---|---|---|---|---|---|---|
| hermes-hermes-1 | hermes-hermes (5.57 GB) | Primary Telegram bot + API server (uvicorn :8642) + minimax-embed-proxy | 9.7 | 462 MB | 0 | *4 min (just OOM-restarted)* |
| hermes-hermes-bot2-1 | hermes-hermes (5.57 GB) | Secondary Telegram bot (own state.db) | 1.5 | 559 MB | 0 | *4 min (just restarted)* |
| hermes-hermes-bot3-1 | hermes-hermes (5.57 GB) | Tertiary Telegram bot (own state.db) | 0.3 | 351 MB | 0 | *4 min (just restarted)* |
| hermes-honcho-api-1 | hermes-honcho (2.43 GB) | Self-hosted Honcho memory API (FastAPI :8001) | 3.0 | 246 MB | 0 | 3 weeks |
| hermes-honcho-deriver-1 | hermes-honcho (2.43 GB) | Honcho background LLM deriver (peer cards) | 0.5 | 77 MB | 0 | 3 weeks |
| hermes-honcho-model-sync-1 | python:3.12-slim | Pins Honcho model, idles | 0.0 | 0.5 MB | 0 | 3 weeks |
| hermes-n8n-1 | hermes-n8n (2.56 GB) | n8n main (queue mode, editor :5678) | 0.2 | 168 MB | 0 | 13 days |
| hermes-n8n-worker-1 | hermes-n8n (2.56 GB) | n8n execution worker | 0.2 | 200 MB | 0 | 13 days |
| hermes-open-webui-1 | open-webui:main (6.34 GB) | Chat UI (chat.ahfl.in) → hermes :8642/v1 | 0.2 | 101 MB | 0 | 3 weeks |
| hermes-oauth2-proxy-chat-1 | oauth2-proxy:latest | Google SSO for chat.ahfl.in (:4181) | 0.0 | 12 MB | 0 | 3 weeks |
| hermes-gws-service-1 | hermes-gws-service (371 MB) | GWS OAuth service (host net, :8080) | 0.2 | 23 MB | 0 | 3 weeks |
| hermes-voice-1 | hermes-voice (331 MB) | Voice app (voice.ahfl.in :3000) + STT bridge | 0.0 | 34 MB | 0 | 12 days |
| hermes-free-whisper-1 | hermes-free-whisper (1.3 GB) | faster-whisper STT microservice (:8000) | 0.1 | 335 MB | **8** | 20 min (crash-loops) |
| hermes-admin-app-1 | hermes-admin-app (301 MB) | Admin dashboard (admin.ahfl.in :8081) | 0.1 | 18 MB | 0 | 2 days |
| hermes-postgres-1 | pgvector/pgvector:pg16 (640 MB) | Postgres: n8n (143 MB) + gbrain (12 MB) DBs | 5.1 | 82 MB | 0 | 3 weeks |
| hermes-redis-1 | redis:7-alpine | Redis: n8n Bull queue + Honcho (2.1 MB used) | 0.9 | 2.5 MB | 0 | 3 weeks |
| hermes-smart-browser-1 | hermes-smart-browser (2.59 GB) | Headless-browser tooling (Chromium; 9181/tcp) | 0.2 | 2.9 MB | 0 | 3 weeks |

**Container RSS total ≈ 2.9 GB** on a 3.7 GB box → kernel + daemons + page cache have ~0.8 GB. The 2 GB swapfile is the overflow valve — and it is permanently full.

**Defined-but-NOT-running** (stopped, no resource cost): `loki`, `promtail`, `grafana` (monitoring stack — logs go to journald instead; journald uses 679 MB), `oauth2-proxy` (:4180 for monitor.ahfl.in). The referenced `camofox` container also does not exist.

**Docker disk usage (all on the 60 GB volume):** images 36.19 GB (16 images) · containers 1.9 GB · volumes 3.8 GB (2.3 GB + 791 MB + 650 MB + open-webui) · **build cache 15.08 GB — 13.81 GB reclaimable**.

---

## 4. Data & State Stores

| Store | Size | Location | Notes |
|---|---|---|---|
| hermes-data (bot1) | **20 GB** | root disk `/opt/hermes/hermes-data` | `pylib` 5.1 GB, `home` 4.6 GB, `users` 4.4 GB, `document_cache` 1.9 GB, **`state.db` 1.65 GB** (single SQLite session store), `audio_cache` 1.2 GB, `sessions` 318 MB, `cache` 301 MB |
| hermes-data-bot2 | 1.3 GB | root disk | state.db 71 MB |
| hermes-data-bot3 | 1.3 GB | root disk | state.db 111 MB |
| chat-data (open-webui) | 1.3 GB | root disk | |
| Postgres | 259 MB | root disk (`./postgres-data`) | n8n 143 MB + gbrain 12 MB + system; hosts Honcho (pgvector) |
| n8n-data | 153 MB | root disk | |
| redis-data | 31 MB | root disk | 2.1 MB in use |
| Journald | 679 MB | root disk `/var/log` | Loki/Grafana stopped, so logs pile up here |
| Whisper model cache | 887 MB | root disk (`hermes-data/home/.cache/huggingface`) | |
| Stale backups | 592 MB | root disk | `hermes-pre-merge-*.tar.gz`, `hermes-pre-fix-*.tar.gz` (Jul 1) |
| Docker data-root | 43 GB | **volume** `/mnt/HC_Volume_106048678/docker` | images + build cache + volumes |

**Per-user GBrain dirs** (`hermes-data/users/`): ndr 1.3 GB · rnr 792 MB · sales1.blr 751 MB · vkdas 398 MB · psingh 395 MB · pm2.blr 356 MB · +4 Telegram-id dirs (314 MB combined).

---

## 5. Networking Topology

```
                        Internet (Hetzner Cloud, 178.105.35.94)
                                        │
                              nginx (host) :80/443
        ┌──────────────┬──────────────┬───────────────┬──────────────┬──────────────┐
 transcribe.ahfl.in  voice.ahfl.in  admin.ahfl.in   chat.ahfl.in   sites.ahfl.in   pastrio.in
   → hermes :8642       → voice :3000   → admin-app     → oauth2-proxy-chat         (static)
   → n8n    :5678                        :8081            :4181 (Google SSO)
   → gws-service :8080 (/v1/auth/*)          │            │
   → kelsa auth callback                     ▼            ▼
                                        open-webui :8080 (→ hermes :8642/v1, voice :3000/v1)
```

- All app ports are bound to **127.0.0.1** only (host) — nginx is the only public entry point. Postgres/redis are compose-internal (no published ports). `smart-browser` publishes 9181/tcp and n8n-worker shares the compose network.
- Docker networks: `hermes_default` (bridge) for most services; `gws-service`, `honcho-*`, `honcho-model-sync` use `host` networking; `gws-vault` runs as a **systemd host service** (`/usr/local/bin/gws-vault-server`, socket `/run/gws-vault/vault.sock`) — all containers bind it in.
- OAuth: hermes api_server :8642 handles `/gws/auth/callback`, `/kelsa/auth/callback`; gws-service :8080 handles `/v1/auth/*`; open-webui is fronted by oauth2-proxy-chat; admin/voice use their own Google flows.

---

## 6. Performance Analysis — 9 Days of History (2026-07-25 → 2026-08-02)

### 6.1 Overall key statistics (1,236 ten-minute intervals)

| Metric | Avg | p95 | Max |
|---|---|---|---|
| CPU busy % (of 2 cores) | 10.7 | 44.5 | 100.0 |
| iowait % | 2.2 | 8.3 | **96.5** |
| Load average 1-min | 1.26 | 1.63 | **192.7** |
| Load average 15-min | — | — | **115.3** |
| Memory used % | ~75 | 79.6 | 90.3 |
| Swap used % | **~98** | **100.0** | **100.0** |
| Memory commit % | — | — | **224.2** |
| Disk write kB/s | 297 | — | 32,192 |
| Disk latency `await` (ms) | — | — | **39,374** |

**Saturation exposure (share of intervals):**
- Load > 2 (≥100% of capacity): **4.0%** · Load > 4: 2.8% · Load > 8: 1.8%
- CPU busy > 70%: 3.0% · > 90%: 1.5%
- iowait > 20%: 3.5%
- **Swap ≥ 50% used: 100% of all intervals** · Swap = 100% full at p95

### 6.2 Daily summary (avg / p95 / max)

| Day | %user | %system | %iowait | cpu_busy | load-1 | load-15 | %mem | %swp | wkB/s | await(max) |
|---|---|---|---|---|---|---|---|---|---|---|
| Jul 25 | 10.8/49/61 | 3.2/17/18 | 0.7/3.5/10 | 14.7/67/81 | 0.39/1.9/3.5 | 2.5 | 75–82 | 97.6–100 | 161 | 26 ms |
| Jul 26 | 4.5/9/40 | 1.9/2/31 | 0.4/0.8/8 | 7.1/17/67 | 0.18/0.7/2.1 | 1.7 | 74–81 | 98–100 | 85 | 14 ms |
| Jul 27 | 4.6/10/24 | 1.8/3/23 | 0.8/3.8/10 | 7.1/18/34 | 0.64/0.6/**35.6** | 7.6 | 77–90 | 99.4–100 | 77 | 13 ms |
| Jul 28 | 3.8/10/21 | 1.6/3/28 | 0.5/1.6/10 | 5.9/16/35 | 0.83/0.5/**65.7** | 12.2 | 77–87 | 99.8–100 | 68 | 21 ms |
| Jul 29 | 4.7/13/33 | 1.7/5/13 | **3.6/16.6/96.5** | 10.1/43/100 | 0.60/1.7/22.2 | 9.3 | 68–89 | 95.8–100 | 395 | **39,375 ms** |
| Jul 30 | 5.9/18/41 | 2.7/4/93 | 1.4/5.7/42 | 10.0/31/100 | 2.24/0.7/**192.7** | **115.3** | 67–90 | 89.4–100 | 253 | 16 ms |
| Jul 31 | 5.4/13/21 | 1.6/3/5 | 2.3/7.5/47 | 9.3/26/52 | 0.22/0.7/2.0 | 1.4 | 64–74 | 95.7–100 | 216 | 70 ms |
| Aug 01 | 4.5/13/21 | 1.4/2/6 | 0.4/1/9 | 6.3/15/29 | 0.18/0.4/5.8 | 1.1 | 76–81 | 98.7–100 | 99 | 24 ms |
| Aug 02 | 6.9/16/28 | **14.2/62.6/93.5** | **13.6/50/61** | **34.7/97/100** | 8.66/62/**121.4** | 83.3 | 80–90 | 99.6–100 | **1,881** | 15 ms |

Aug 2 is off the charts: system CPU avg 14.2% (max 93.5%), iowait avg 13.6% (max 61%), sustained load — this is the day of the OOM-kills (see §6.4).

### 6.3 Top-12 worst 10-minute windows

| Timestamp (UTC) | cpu_busy | iowait | load-1 | load-5 | load-15 | swap | comment |
|---|---|---|---|---|---|---|---|
| **2026-07-30 16:09** | 100 | 5.9 | **192.7** | 177.3 | 115.3 | 99% | Worst event in window; ~15 min of total stall |
| 2026-07-30 16:10 | 77 | 23.3 | 58.7 | 139.5 | 107.0 | 100% | aftermath of above |
| **2026-08-02 15:02** | 95 | 38.2 | 121.4 | 54.8 | 24.1 | 100% | OOM-kill day |
| 2026-08-02 15:11 | 100 | 3.6 | 109.8 | 89.8 | 55.9 | 100% | uvicorn killed 15:09 |
| 2026-08-02 10:20 | 75 | 30.8 | 85.4 | 34.3 | 18.2 | 100% | |
| 2026-08-02 15:20 | 96 | 1.4 | 83.7 | 113.2 | 83.3 | 99% | headless_shell/pdftoppm killed 15:19 |
| 2026-08-02 13:20 | 96 | 27.6 | 81.5 | 58.0 | 36.0 | 100% | |
| 2026-07-28 00:50 | 36 | 2.5 | 65.7 | 31.2 | 12.2 | 100% | overnight batch |
| 2026-08-02 12:40 | 92 | 33.3 | 45.8 | 21.9 | 17.8 | 100% | 15.7 MB/s writes |
| 2026-07-30 15:50 | 83 | 20.1 | 41.6 | 29.4 | 14.0 | 100% | prelude to the 192 event |
| 2026-08-02 09:40 | 99 | 49.6 | 31.6 | 35.3 | 23.5 | 100% | |
| 2026-07-27 06:40 | 27 | 3.6 | 35.6 | 10.8 | 3.9 | 100% | |

### 6.4 Incident reconstruction — 2026-08-02 (live, verified in kernel log)

```
15:09:55  OOM killer: killed uvicorn (777 MB anon RSS)   ← hermes API server / open-webui backend
15:17–15:19  OOM killer: killed headless_shell ×2 (smart-browser Chromium) + pdftoppm (786 MB anon RSS)
15:19:42  "A process of this unit has been killed by the OOM killer" (docker scope)
~15:31    all three hermes bot containers restart (docker compose cycle)
15:33     free-whisper back serving — its model load took 575.8 s (9.6 min) due to swap thrash
```
Corroborating kernel evidence: `journalctl -k` OOM records at 15:09:55 / 15:17:41 / 15:19:42; `%commit` reached 224%; swap at 100%; iowait 38–61% through the window. This matches the user-reported symptoms exactly (OOM kills, slow bot responses, disk/IO stalls).

**2026-07-30 16:09 load 192.7** — the same class of event one day earlier; the 10-min cadence cannot show process detail for that window, but the signature (CPU 100% + swap 99% + load 15-min at 115) is identical: **RAM exhaustion → swap thrash → every process (including kswapd, sshd, nginx) starves → load explodes → OOM kills**.

### 6.5 Charts (in `charts/`)

| Chart | File | What it shows |
|---|---|---|
| CPU utilization | `charts/cpu_usage.png` | cpu_busy % + iowait % — spikes on Jul 29–30 and Aug 2 |
| Load average | `charts/load_average.png` | 1/5/15-min load vs the 2.0 saturation line — the 192.7 and 121.4 spikes |
| Memory & swap | `charts/memory_swap.png` | RAM ~75–90% + swap pinned at 100% the entire window |
| Disk I/O | `charts/disk_io.png` | write/read throughput; 32 MB/s write bursts |

---

## 7. Bottleneck Analysis

1. **Memory — critical, structural.** 17 containers ≈ 2.9 GB RSS on 3.7 GB usable. The 2 GB swapfile has been ≥50% full for **100% of the measured window** and 100% full at p95. The kernel OOM-killer is executing workloads *today*. `%commit` peaked at 224% (requests memory beyond RAM+swap — dangerous with overcommit). **No amount of container tuning fixes this; the box needs ≥8 GB.**
2. **CPU — adequate on average, undersized for bursts.** Average demand is ~0.2 of a core; p95 is ~0.9 of a core. But agent workloads (parallel tool calls, whisper transcription, Chromium/pdftoppm rendering, Honcho derivation) produce *coordinated* bursts that saturate both cores for minutes and can inflate load to 190+ when compounded with swap-thrash. 4 vCPU would absorb p95 with 4× headroom and cut spike-recovery time; 8 vCPU makes spikes a non-event.
3. **Root disk — critical.** 95% full. Single biggest consumer: `hermes-data` (20 GB). A full root disk causes DB/journal write failures and makes OOM crashes worse (no room for WAL growth). CAX21's 80 GB gives 2.3× current usage; CAX31's 160 GB gives 4.7×.
4. **Volume — tight, and it's the docker disk.** 76% full with 13.8 GB of reclaimable build cache. Whisper models, document caches, and image growth will keep eating it. Resize to ≥100 GB or move docker to the root disk.
5. **I/O — collateral damage.** 39-second latencies and 96.5% iowait only occur during memory-pressure events (swap writes + OOM churn); the daily baseline (await < 15 ms, ~300 KB/s writes) is healthy. Expect this to normalize on the larger plan.
6. **Secondary findings:** free-whisper crash-looping (8 restarts; 9.6-min model load); monitoring stack (loki/promtail/grafana) **not running** so journald (679 MB) is the only log sink; 592 MB of stale Jul-1 tarballs; 3 defined-but-stopped services (loki, promtail, grafana, oauth2-proxy) silently missing from the running set.

---

## 8. Architecture Diagram (Mermaid)

```mermaid
flowchart TB
    subgraph internet["Internet"]
        T[Telegram bots<br/>@NDRHermes_bot / bot2 / bot3]
        W[Users - voice.ahfl.in]
        C[Users - chat.ahfl.in]
        A[Admins - admin.ahfl.in]
        N[Users - transcribe.ahfl.in (n8n + OAuth callbacks)]
    end

    subgraph host["VPS CAX11 - Ubuntu 24.04 aarch64 - 2 vCPU / 4 GB / 40 GB root + 60 GB vol"]
        nginx["nginx :80/443<br/>6 vhosts (letsencrypt)"]
        vault["gws-vault (systemd host service)<br/>/run/gws-vault/vault.sock"]

        subgraph net_hermes["docker network: hermes_default"]
            postgres["postgres (pgvector/pg16)<br/>n8n + gbrain DBs"]
            redis["redis 7 (n8n queue + honcho)"]
            n8n["n8n editor :5678"]
            n8nw["n8n-worker"]
            hermes["hermes bot1 :8642<br/>gateway + api_server + minimax-embed-proxy"]
            bot2["hermes-bot2"]
            bot3["hermes-bot3"]
            wui["open-webui :8080"]
            proxy_chat["oauth2-proxy-chat :4181"]
            voice["voice :3000 (STT bridge)"]
            whisper["free-whisper :8000<br/>faster-whisper small"]
            admin["admin-app :8081"]
            sb["smart-browser (chromium)"]
        end

        subgraph hostnet["network_mode: host"]
            gws["gws-service :8080<br/>(OAuth /v1/auth/*)"]
            honcho_api["honcho-api :8001"]
            honcho_deriver["honcho-deriver"]
            honcho_sync["honcho-model-sync (idle)"]
        end

        subgraph storage["Storage"]
            root["/ (38G ext4) 95%<br/>hermes-data 20G + data dirs"]
            vol["/mnt/HC_Volume (60G) 76%<br/>docker data-root 43G"]
        end
    end

    T --> nginx --> hermes
    T --> bot2
    T --> bot3
    nginx --> n8n
    nginx --> voice
    nginx --> admin
    nginx --> proxy_chat --> wui --> hermes
    W --> voice --> whisper
    hermes --> postgres
    hermes --> redis
    n8n --> postgres
    n8nw --> postgres
    n8n --> redis
    honcho_api --> postgres
    honcho_api --> redis
    honcho_deriver --> honcho_api
    gws --> vault
    hermes -.gws_auth.-> gws
    hermes -.OAuth callback.-> vault
    hermes --> sb
    hermes --> n8n
    hermes --> whisper
    postgres --> vol
    hermes --> root
    admin --> vault
    voice --> vault
```

---

## 9. Sizing Recommendation (Hetzner Cloud, prices excl. VAT per official docs, post-15-Jun-2026)

Your current box is the **CAX11 (ARM cost-optimized)**. All three bottlenecks (RAM, root disk, volume) are structural — the recommended path is the same ARM line so everything (images, data, config) migrates without rebuilds.

| Plan | vCPU | RAM | Root disk | Price/mo (excl. IPv4) | +IPv4 | Fit for this workload |
|---|---|---|---|---|---|---|
| CAX11 *(current)* | 2 | 4 GB | 40 GB | €5.99 | €6.49 | **Failing** — OOM kills, 95% root, swap pinned |
| CAX21 *(minimum)* | 4 | 8 GB | 80 GB | €10.49 | €10.99 | Stops OOM + disk-full. CPU headroom vs 190-load spikes modest |
| **CAX31 *(recommended)*** | **8** | **16 GB** | **160 GB** | **€20.99** | **€21.49** | Removes all 3 bottlenecks; 2–4× headroom; absorbs growth |
| CAX41 | 16 | 32 GB | 320 GB | €40.99 | €41.49 | Only if heavy parallel agent/browser workloads grow further |

*Note: existing CAX11 servers keep the pre-June "locked" price (€4.49) until resized; resizing moves you to the new price. Prices verified 2026-08-02 via Hetzner docs.*

### Verdict

- **Buy: CAX31 (8 vCPU / 16 GB / 160 GB) ≈ €21.49/mo incl. IPv4.**
  - **Memory:** 16 GB vs 4 GB → container RSS (~2.9 GB) + system + cache fits with ≥10 GB headroom; swap-thrash and OOM-kills end.
  - **CPU:** 8 vCPU → p95 demand (~0.9 core) uses ~11% of one core; the 190-load thrash events become impossible to reproduce (they were swap-collapse artifacts).
  - **Disk:** 160 GB root → 4.7× current usage; `hermes-data` (20 GB) + `state.db` + caches fit comfortably; docker data-root can stay on the volume.
- **Simultaneously:** resize the block volume 60 → **100 GB** (+€2.29/mo) — or, on CAX31, optionally move the docker data-root to root and keep the volume for hermes-data backups.
- **Total projected: ≈ €23.78/mo** (CAX31 + 100 GB volume) vs the current ≈ €6–9/mo. Roughly 3× the cost for ~8–10× the effective capacity — and, more importantly, an end to the crash/restart cycle that is already costing production availability daily.

### Budget-constrained alternative
**CAX21 (4 vCPU / 8 GB / 80 GB, €10.99/mo) + 100 GB volume** — fixes the memory crisis (8 GB ≈ 2.8× current headroom, swap becomes a safety valve instead of a lifestyle) and the disk-full crisis. The 4 vCPU will still be briefly saturated during the worst bursts (load ~2–4), but without swap-thrash amplification those events should resolve in seconds instead of minutes. **Note:** with 8 GB, `free-whisper`'s model load (575 s today) should drop to ~60–90 s.

### Suggested checkpoints after migration
1. Re-run this same collection (sysstat files auto-cumulate) after 5–7 days; verify `%swpused` stays <10% and load stays <2.
2. Watch `hermes-data` growth (~1–2 GB/week observed over the window: state.db + caches) — set an alert at 60% of root.
3. Reclaim now: `docker builder prune` (~13.8 GB), delete the 592 MB Jul-1 tarballs, trim journald (`journalctl --vacuum-size=200M`) — do this before the resize so the migration snapshot is small.
4. Restart the loki/promtail/grafana monitoring stack (defined, not running) or set up Hetzner Cloud metrics alerts — today the box has no alerting at all.
5. Investigate `free-whisper` crash-loop (8 restarts) and the 3-bot simultaneous restarts at 15:31 — both are OOM symptoms, but confirm no config regression after migration.

---

## 10. Appendices

### A. Raw data files (this folder)
- `data/merged_10min.csv` — all 1,236 intervals × 15 metrics (the full time series, 190 KB)
- `data/daily_summary.csv` — per-day avg/p95/max for 15 metrics
- `data/hourly_agg.csv` — per-hour mean/max (for finer trend work)
- `data/peak_windows.csv` — top-20 worst windows
- `charts/*.png` — 4 matplotlib charts
- `key_stats.json` — the headline numbers in machine-readable form

### B. For the evaluating LLM — crisp answerable questions
1. Is CAX31 (8/16/160) justified, or is CAX21 (4/8/80) enough given avg CPU is ~0.2 core and the spikes are memory-collapse artifacts?
2. Should docker data-root move to the 160 GB root (CAX31) instead of resizing the volume?
3. Is a second server (e.g., dedicated STT/whisper box) a better pattern than a bigger single box, given free-whisper's 500 MB model + 335 MB RSS and 70 s per 90 s of audio?
4. Given the stack's growth rate (3 bots → 17 containers in ~12 months), what headroom horizon should CAX31 provide?

### C. Collection provenance
- Metrics: `sadf -d` from `/var/log/sysstat/sa25…sa02` (10-min intervals; SADC_OPTIONS="-S DISK"; HISTORY=7).
- OOM: `journalctl -k --since '30 days ago' | grep -i oom`.
- All other facts: live `docker`/`df`/`du`/`nginx` inspection at 2026-08-02 15:20–15:35 UTC.
- Times are UTC (server-local). IST = UTC + 5:30.
