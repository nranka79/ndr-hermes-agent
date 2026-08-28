#!/usr/bin/env python3
"""Scan all of a user's DRA pipelines for pending Kelsa tasks assigned to them.

There is NO account-level task-queue MCP tool; this reconstructs it by:
  1. search_leads(assignee:me;next_task?) per pipeline, sorted by updated_at desc
  2. list_lead_tasks per record, keeping [pending] tasks whose "assigned to"
     matches the target user
  3. dedupe by task ID, sort by record recency (current work first)

Usage (run from terminal(), NOT execute_code — needs GWS_VAULT_SOCKET):
  /opt/hermes/.venv/bin/python3 kelsa_my_pending_tasks.py

Env overrides (defaults = Anbarasan):
  TELEGRAM_ID=[REDACTED-TID]      # requesting user's telegram id (vault identity)
  TARGET_NAME=anbarasan       # substring match on task assignee name (case-insensitive)
  TARGET_ID=682               # numeric Kelsa user id fallback match
  MAX_PER_PIPELINE=50         # how many candidate records to drill into

See references/my-pending-tasks-workflow.md for the worked example and the
sorting/triage insight (due-date sort surfaces legacy backlog; updated_at recency
finds current work).
"""
import sys, json, os, re
os.environ.setdefault("GWS_VAULT_SOCKET", "/run/gws-vault/vault.sock")
sys.path.insert(0, "/opt/hermes")

from tools import gws_vault_client as vault
from tools.gws_auth import canonical_uid

TELEGRAM_ID = os.environ.get("TELEGRAM_ID", "[REDACTED-TID]")
TARGET_NAME = os.environ.get("TARGET_NAME", "anbarasan").lower()
TARGET_ID = os.environ.get("TARGET_ID", "682")
MAX_PER_PIPELINE = int(os.environ.get("MAX_PER_PIPELINE", "50"))

uid = canonical_uid(TELEGRAM_ID)
raw = vault.get_token(uid, "mcp-kelsa-read", session_uid=uid)
TOKEN = json.loads(raw).get("access_token", "")

import httpx
URL = "https://kelsa.io/mcp"

def call_tool(name, args=None):
    payload = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
               "params": {"name": name, "arguments": args or {}}}
    resp = httpx.post(URL, json=payload,
                      headers={"Authorization": f"Bearer {TOKEN}"}, timeout=30)
    data = resp.json()
    if "error" in data:
        raise Exception(f"MCP error: {data['error']}")
    result = data.get("result", {})
    for item in result.get("content", []):
        if item.get("type") == "text":
            text = item["text"]
            try:
                return json.loads(text)
            except (json.JSONDecodeError, ValueError):
                return text
    return result

# Pipelines the DRA construction/infra team actually works in (extend as needed)
PIPELINES = {
    514: "DRA Materials Receipt",
    556: "DRA Snags",
    516: "DRA Invoice Processing",
    537: "DRA PO-WO Issuing",
    971: "DRA Engineering Daily Jobs",
    517: "DRA Request For Material",
    2335: "Curing - Iris",
}

REC_RE = re.compile(
    r"\s*\[#(\d+)\]\s*(.*?)\s*·\s*(.*?)\s*·\s*@\w+.*?(?:updated\s*([\w ]+?)\s*·)?\s*"
    r"https://kelsa\.io/\d+/leads\?current_item_id=\d+"
)
TASK_RE = re.compile(
    r"\s*\[(\w+)\]\s*\(ID:\s*(\d+)\)\s*(.*?)\s*·\s*assigned to\s*(.*?)\s*·\s*due\s*([\d\-]+)"
)

results = []
for pid, pname in PIPELINES.items():
    try:
        page = call_tool("search_leads", {"pipeline_id": pid, "query": "assignee:me;next_task?",
                                          "sort": "updated_at", "order": "desc", "per_page": 100})
    except Exception as e:
        print(f"[{pname}] search failed: {e}")
        continue
    text = page if isinstance(page, str) else str(page)
    records = []
    for line in text.splitlines():
        m = REC_RE.match(line)
        if m:
            records.append({"id": int(m.group(1)), "name": m.group(2).strip(),
                            "stage": m.group(3).strip(),
                            "updated": (m.group(4).strip() if m.lastindex >= 4 and m.group(4) else "")})
    print(f"[{pname}] {len(records)} records with next_task")
    if not records:
        continue
    for rec in records[:MAX_PER_PIPELINE]:
        try:
            tasks_text = call_tool("list_lead_tasks", {"lead_id": rec["id"], "limit": 100})
        except Exception:
            continue
        if not isinstance(tasks_text, str):
            continue
        for tline in tasks_text.splitlines():
            tm = TASK_RE.match(tline)
            if not tm:
                continue
            status, task_id, desc, assignee, due = tm.groups()
            if status.lower() != "pending":
                continue
            if TARGET_NAME in assignee.lower() or assignee.strip() == TARGET_ID:
                results.append({
                    "due": due, "task_id": task_id, "desc": desc.strip(),
                    "assignee": assignee.strip(), "lead_id": rec["id"],
                    "lead_name": rec["name"], "stage": rec["stage"],
                    "pipeline": pname, "updated": rec.get("updated", ""),
                    "link": f"https://kelsa.io/{pid}/leads?current_item_id={rec['id']}"
                })

seen = set()
uniq = []
for r in results:
    if r["task_id"] not in seen:
        seen.add(r["task_id"])
        uniq.append(r)

def recency_key(r):
    u = r["updated"]
    if not u:
        return 10**9
    m = re.match(r"(\d+)\s*([a-z]+)", u)
    if not m:
        return 10**9
    n, unit = int(m.group(1)), m.group(2)[0]
    mult = {"m": 1, "h": 60, "d": 1440}.get(unit, 10**9)
    return n * mult

uniq.sort(key=recency_key)
print(f"=== {len(uniq)} PENDING TASKS ASSIGNED TO {TARGET_NAME} ({TARGET_ID}), sorted by record recency ===")
for r in uniq[:20]:
    print(f"[rec updated {r['updated'] or '?'}] due {r['due']} | {r['pipeline']} | "
          f"{r['lead_name']} [{r['stage']}] | {r['desc'][:80]} | task {r['task_id']} | {r['link']}")
