#!/usr/bin/env python3
"""Process a batch of existing Kelsa leads from a JSON file — add notes, move stages.

Usage:
  HERMES_SESSION_USER_ID=<session_telegram_id> python3 skills/productivity/kelsa-write/scripts/process_batch_json.py <batch_file.json>

Key pitfalls (verified 2026-08-28, 195-lead Ranka Udaya run):
  - MCP connection drops after ~100 calls; split by action type (notes-only first, then stage-move batch via direct kelsa_call_tool).
  - Keep each batch ≤ ~60 leads for reliability.
  - The `_run_on_mcp_loop(_worker())` form is BROKEN — `_worker` is async def _worker(session) and needs a session argument. Correct form: `_run_on_mcp_loop(lambda: _connect_and_run(token, _worker), timeout=600)`.
  - If the Excel export has VLOOKUP formulas pointing at an external workbook (`[1]consolidated File`), the evaluated values live in a sibling `(Data).csv` (read with encoding='latin-1').

Batch JSON format (one object per lead):
  {
    "sno": "1",
    "name": "Customer Name",
    "phone": "919876543210",
    "call_status": "answered" | "not_answered",
    "lead_stage": "incoming" | "unqualified" | "prospect" | "opportunity",
    "remarks": "Free text notes from calling team",
    "action": "junk" | "not_answered" | "warm" | "psc" | "note_only",
    "new_stage": "junked" | null
  }

Action mapping (see references/calling-campaign-update.md for full decision tree):
  not_answered -> add note, no stage change
  junk         -> add note (Junk is retired, can't move_stage to it)
  warm         -> add note + set cf_requirements + move to Warm (stage 2)
  psc          -> add note + move Cold->Warm->PSC sequentially
  note_only    -> add note only

Key pitfalls:
  - Pipeline 10 is SEQUENTIAL: Cold->Warm(2)->PSC(281)->SSV(6). No jumps.
  - move_stage to Warm fails unless cf_requirements is set.
  - move_stage to SSV fails unless cf_interested_in_site_visit_ = True.
  - Stage moves are async — each returns a draft ID. Wait ~2s between chained moves.
  - If lead is already past the target stage, move_stage returns 'already in stage' (benign).
  - Old_token_path (batch_import_leads.py's `get_valid_access_token('[tid]')`) is WRONG.
    Always use `get_valid_access_token()` with HERMES_SESSION_USER_ID env var.
"""

import sys, json, re, time, os

sys.path.insert(0, "/opt/hermes")
from tools.kelsa_auth import get_valid_access_token
from tools.mcp_tool import _ensure_mcp_loop, _run_on_mcp_loop
from tools.kelsa_tool import _connect_and_run

PIPELINE_ID = 10  # DRA Sales Leads

NOTES = {
    "not_answered": "Attempt by Chennai team - Not Answered",
    "junk": "Attempt by Chennai team - Answered - Unqualified - Marked as Junk",
    "warm": "Attempt by Chennai team - Answered - Prospect - Pushed to Warm",
    "psc": (
        "Attempt by Chennai team - Answered - Opportunity"
        " - Confirmed site visit (no date) - Pushed to PSC"
    ),
    "note_only": "Attempt by Chennai team - Answered",
}


def extract_lead_id(text: str) -> int | None:
    m = re.search(r"\[#(\d+)\]", text)
    return int(m.group(1)) if m else None


def extract_draft_id(text: str) -> int | None:
    m = re.search(r"draft ID:\s*(\d+)", text)
    return int(m.group(1)) if m else None


def get_stage(text: str) -> str | None:
    m = re.search(r"Stage:\s*(\S+)", text)
    return m.group(1).lower() if m else None


async def run_mcp(session, tool: str, args: dict) -> str:
    result = await session.call_tool(tool, args)
    for block in result.content or []:
        if hasattr(block, "text"):
            return block.text
    return ""


def process_batch(leads: list[dict]) -> list[dict]:
    _ensure_mcp_loop()
    token = get_valid_access_token()

    async def _worker(session):
        results = []
        for i, lead in enumerate(leads):
            sno = lead.get("sno", "?")
            name = lead.get("name", "?")
            phone = lead.get("phone", "")
            action = lead.get("action", "")
            remarks = lead.get("remarks", "")
            entry = {"sno": sno, "name": name, "phone": phone, "action": action}

            print(f"\n[{i+1}/{len(leads)}] Sno #{sno} | {name} | phone={phone} | action={action}")

            # --- 1. Search by phone ---
            search = await run_mcp(session, "search_leads",
                                   {"pipeline_id": PIPELINE_ID, "query": phone, "per_page": 5})
            lead_id = extract_lead_id(search)
            if not lead_id:
                print("  NOT FOUND — skipping")
                entry["status"] = "not_found"
                results.append(entry)
                continue

            entry["lead_id"] = lead_id
            print(f"  Found lead #{lead_id}")

            # --- 2. Get current stage ---
            detail = await run_mcp(session, "get_lead",
                                   {"pipeline_id": PIPELINE_ID, "lead_id": lead_id})
            current = get_stage(detail)
            entry["current_stage"] = current
            print(f"  Current stage: {current}")

            # --- 3. Add note ---
            note = NOTES.get(action)
            if note:
                note_resp = await run_mcp(session, "add_note",
                                          {"pipeline_id": PIPELINE_ID, "lead_id": lead_id, "text": note})
                entry["note_added"] = "successfully" in note_resp.lower()
                print(f"  Note: {'added' if entry['note_added'] else 'FAILED'}")

            # --- 4. Stage move by action ---
            if action == "not_answered" or action == "note_only":
                entry["stage_move"] = "none_needed"
                print("  No stage change")

            elif action == "junk":
                if current and current != "junk":
                    entry["stage_move"] = "skipped_retired"
                    print("  Junk is retired — note only, no stage move possible")
                else:
                    entry["stage_move"] = "already_junk"
                    print("  Already in Junk")

            elif action == "warm":
                if current in ("psc", "ssv", "hot", "converted"):
                    entry["stage_move"] = f"already_at_{current}"
                    print(f"  Already at {current} — no downgrade needed")
                elif current == "warm":
                    entry["stage_move"] = "already_warm"
                    print("  Already in Warm")
                elif current == "junk":
                    entry["stage_move"] = "junk_cant_upgrade"
                    print("  In Junk — cannot promote out of retired stage")
                elif current == "cold":
                    # Need cf_requirements before Warm
                    reqs = f"Customer enquired about project. {remarks[:100]}"
                    await run_mcp(session, "update_lead",
                                  {"pipeline_id": PIPELINE_ID, "lead_id": lead_id,
                                   "field_values": {"cf_requirements": reqs}})
                    move_resp = await run_mcp(session, "move_stage",
                                              {"pipeline_id": PIPELINE_ID, "lead_id": lead_id, "stage_id": 2})
                    entry["stage_move"] = "moved_to_warm" if "queued" in move_resp.lower() else move_resp[:80]
                    print(f"  Stage move: {entry['stage_move']}")
                else:
                    entry["stage_move"] = f"unhandled_stage_{current}"
                    print(f"  Unknown start stage: {current}")

            elif action == "psc":
                # Need Cold->Warm->PSC (2 sequential moves)
                if current in ("psc", "ssv", "hot", "converted"):
                    entry["stage_move"] = f"already_at_{current}"
                elif current == "cold":
                    reqs = f"Customer interested, confirmed site visit. {remarks[:80]}"
                    await run_mcp(session, "update_lead",
                                  {"pipeline_id": PIPELINE_ID, "lead_id": lead_id,
                                   "field_values": {"cf_requirements": reqs}})
                    r1 = await run_mcp(session, "move_stage",
                                       {"pipeline_id": PIPELINE_ID, "lead_id": lead_id, "stage_id": 2})
                    d1 = extract_draft_id(r1)
                    if d1:
                        time.sleep(2)
                        await run_mcp(session, "get_draft_status",
                                      {"pipeline_id": PIPELINE_ID, "draft_id": d1})
                    r2 = await run_mcp(session, "move_stage",
                                       {"pipeline_id": PIPELINE_ID, "lead_id": lead_id, "stage_id": 281})
                    entry["stage_move"] = "cold_to_warm_to_psc"
                    print("  Cold -> Warm -> PSC")
                elif current == "warm":
                    await run_mcp(session, "move_stage",
                                  {"pipeline_id": PIPELINE_ID, "lead_id": lead_id, "stage_id": 281})
                    entry["stage_move"] = "warm_to_psc"
                    print("  Warm -> PSC")
                else:
                    entry["stage_move"] = f"unhandled_stage_{current}"

            entry["status"] = "processed"
            results.append(entry)
            time.sleep(0.3)  # rate limit buffer

        return results

    return _run_on_mcp_loop(lambda: _connect_and_run(token, _worker), timeout=600)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: process_batch_json.py <batch_file.json>", file=sys.stderr)
        sys.exit(1)

    with open(sys.argv[1]) as f:
        data = json.load(f)

    results = process_batch(data)

    total = len(results)
    found = sum(1 for r in results if r["status"] == "processed")
    not_found = sum(1 for r in results if r["status"] == "not_found")

    print("\n" + "=" * 60)
    print(f"COMPLETE: {total} total, {found} processed, {not_found} not found")
    print("=" * 60)

    # Action breakdown
    from collections import Counter
    by_action = Counter(r["action"] for r in results)
    for a, c in by_action.most_common():
        print(f"  {a}: {c}")

    out_path = sys.argv[1].replace(".json", "_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\nResults saved: {out_path}")