#!/usr/bin/env python3
"""
Reusable template: process a batch of calling campaign results from a JSON file
and update Kelsa Pipeline 10 (DRA Sales Leads).

Reads a JSON array of lead objects, searches each by phone in Kelsa, adds a
note documenting the call outcome, and optionally moves the lead to a new stage.

Usage:
  python3 process_calling_batch.py <batch_file.json> [--pipeline 10] [--delay 0.5]

Batch JSON format (one object per lead):
  {
    "sno": "1",              // Row number from export
    "name": "Customer Name", // Lead/client name
    "phone": "919876543210", // Phone with country code (91 prefix)
    "call_status": "answered" | "not_answered",
    "lead_stage": "incoming" | "unqualified" | "prospect" | "opportunity",
    "remarks": "Free text notes from calling team",
    "action": "junk" | "not_answered" | "warm" | "note_only",
    "new_stage": "junked" | null
  }

Action mapping:
  - not_answered → add note, no stage change
  - junk → add note, no stage change (Junk stage is retired, not reachable by move_stage)
  - warm → add note, move to Warm (stage ID 2) — requires cf_requirements to be set
  - psc → add note, move to PSC (stage ID 281)
  - note_only → add note, no stage change

Known pitfalls (see kelsa-write → references/calling-campaign-update.md):
  - "Record is already in stage" = no-op, not a failure
  - Cannot jump backward to earlier stage (Opportunity → Warm rejected)
  - Retired stages (Junk) not reachable by move_stage
  - Stage moves are async — verify with get_draft_status between chained moves
"""

import os, sys, json, re, httpx, time, argparse

os.environ['GWS_VAULT_SOCKET'] = '/run/gws-vault/vault.sock'
sys.path.insert(0, '/opt/hermes')
from tools.kelsa_auth import get_valid_access_token

PIPELINE_ID = 10  # DRA Sales Leads

# Standard note templates per action type
NOTES = {
    "not_answered": "Attempt by Chennai team - Not Answered",
    "junk": "Attempt by Chennai team - Answered - Unqualified - Marked as Junk",
    "warm": "Attempt by Chennai team - Answered - Prospect - Pushed to Warm",
    "psc": "Attempt by Chennai team - Answered - Opportunity - Confirmed site visit (no date) - Pushed to PSC",
    "note_only": "Attempt by Chennai team - Answered",
}

# Stage targets per action (None = skip stage move)
STAGES = {
    "not_answered": None,
    "junk": None,        # Junk is retired — can't move_stage to it
    "warm": "Warm",      # stage ID 2
    "psc": "PSC",        # stage ID 281
    "note_only": None,
}

def main():
    parser = argparse.ArgumentParser(description="Process calling campaign batch results into Kelsa Pipeline 10")
    parser.add_argument("batch_file", help="Path to JSON batch file")
    parser.add_argument("--pipeline", type=int, default=10, help="Kelsa pipeline ID (default: 10)")
    parser.add_argument("--delay", type=float, default=0.5, help="Delay between API calls (default: 0.5s)")
    args = parser.parse_args()

    # Authenticate
    token = get_valid_access_token()
    mcp_url = "https://kelsa.io/mcp"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    # Initialize MCP session
    init = {"jsonrpc":"2.0","method":"initialize",
            "params":{"protocolVersion":"2025-03-26","capabilities":{},
                      "clientInfo":{"name":"hermes","version":"1.0"}},"id":1}
    httpx.post(mcp_url, json=init, headers=headers, timeout=10)

    def mcp_call(name, args=None, id=2):
        """Call a Kelsa MCP tool and return the text response."""
        payload = {"jsonrpc":"2.0","method":"tools/call",
                   "params":{"name":name,"arguments":args or {}},"id":id}
        try:
            resp = httpx.post(mcp_url, json=payload, headers=headers, timeout=30)
            data = resp.json()
            content = data.get("result", {}).get("content", [])
            text = content[0].get("text", "") if content else str(data)
            is_error = data.get("result", {}).get("isError", False)
            return {"text": text, "is_error": is_error, "raw": data}
        except Exception as e:
            return {"text": f"EXCEPTION: {e}", "is_error": True, "raw": str(e)}

    def extract_lead_id(search_text):
        """Extract lead ID from search result like '[#54864912] Name-...'"""
        m = re.search(r'\[#(\d+)\]', search_text)
        return int(m.group(1)) if m else None

    # Load batch
    with open(args.batch_file) as f:
        leads = json.load(f)

    print(f"Loaded {len(leads)} leads from {args.batch_file}")
    print("=" * 70)

    results = {
        "total": len(leads),
        "found": 0,
        "not_found": 0,
        "actions_taken": {},
        "details": []
    }

    for i, lead in enumerate(leads):
        sno = lead.get("sno", "?")
        name = lead.get("name", "?")
        phone = lead.get("phone", "")
        action = lead.get("action", "")
        remarks = lead.get("remarks", "")

        entry = {
            "sno": sno, "name": name, "phone": phone,
            "action": action, "status": "pending",
            "lead_id": None, "note_result": None, "stage_result": None, "error": None
        }

        print(f"\n[{i+1}/{len(leads)}] Sno #{sno} | {name} | {phone} | action={action}")

        # Search by phone
        search_res = mcp_call("search_leads", {"pipeline_id": args.pipeline, "query": phone})
        lead_id = extract_lead_id(search_res["text"])

        if not lead_id:
            print(f"  ⚠️  Lead NOT FOUND for phone {phone}")
            entry["status"] = "not_found"
            entry["error"] = search_res["text"][:200]
            results["not_found"] += 1
            results["details"].append(entry)
            continue

        entry["lead_id"] = lead_id
        results["found"] += 1
        print(f"  ✅ Found lead #{lead_id}")

        # Determine action
        note_text = NOTES.get(action)
        target_stage = STAGES.get(action)

        if not note_text:
            print(f"  ⚠️  Unknown action '{action}' — skipping")
            entry["status"] = "skipped"
            entry["error"] = f"Unknown action: {action}"
            results["details"].append(entry)
            continue

        results["actions_taken"].setdefault(action, {"count": 0, "note_added": 0, "stage_changed": 0})
        results["actions_taken"][action]["count"] += 1

        # Add note
        note_res = mcp_call("add_note", {"pipeline_id": args.pipeline, "lead_id": lead_id, "text": note_text})
        entry["note_result"] = note_res["text"]
        if "successfully" in note_res["text"].lower():
            results["actions_taken"][action]["note_added"] += 1
            print(f"  📝 Note added: \"{note_text[:50]}...\"")
        else:
            print(f"  ⚠️  Note failed: {note_res['text'][:100]}")

        # Move stage if applicable
        if target_stage:
            stage_res = mcp_call("move_stage", {"pipeline_id": args.pipeline, "lead_id": lead_id, "stage_id": target_stage})
            entry["stage_result"] = stage_res["text"]
            if "queued" in stage_res["text"].lower() or "moved" in stage_res["text"].lower():
                results["actions_taken"][action]["stage_changed"] += 1
                print(f"  🔄 Stage moved to {target_stage}")
            else:
                # Known no-ops: "already in stage", "cannot jump" — both are expected
                print(f"  ➡️  Stage move skipped: {stage_res['text'][:100]}")
        else:
            entry["stage_result"] = "no_stage_change_needed"
            print(f"  ➡️  No stage change needed")

        entry["status"] = "processed"
        results["details"].append(entry)
        time.sleep(args.delay)

    # Summary
    print("\n" + "=" * 70)
    print("BATCH PROCESSING COMPLETE")
    print("=" * 70)
    print(f"Total leads: {results['total']}")
    print(f"Found in Kelsa: {results['found']}")
    print(f"Not found: {results['not_found']}")
    print(f"\nActions breakdown:")
    for action_name, counts in sorted(results["actions_taken"].items()):
        print(f"  {action_name}: {counts['count']} total, {counts['note_added']} notes, {counts['stage_changed']} stages moved")

    output_path = args.batch_file.replace(".json", "_results.json")
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\nDetailed results: {output_path}")
    return results

if __name__ == "__main__":
    main()