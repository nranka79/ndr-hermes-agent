# TMP staging → live project tree: move checklist

The TMP hard rule is: every chat-session file starts under root `TMP/`, never
My Drive root and never directly inside a live project folder. This file covers
the *second half* of the lifecycle — what to do when NDR then says "move it into
the right project folder" — and the two ways that move goes wrong.

## Failure mode 1 — building the project tree instead of finding it

Observed (Oct 2026, BuxRanka DRC work): asked to file a title report, the agent
created `My Drive > BuxRanka > BRDPL > Proposal by Rajesh` from scratch. NDR's
response: *"Remember everything is to be made under TMP folder always. We never
write anything to drive."* The folders had landed in the live 2019 project
tree. They had to be deleted and the whole thing rebuilt under TMP.

Root cause: `name contains 'BuxRanka'` returned the *TMP copy first* (it was the
newest), so the agent never noticed the real `BuxRanka` folder (id
`1G_Jfh01PI2S5bkPPeRJ1tC7rGNZU-wFn`, created 2019) already existed with a full
structure inside it.

**Rule: search results include your own TMP scaffolding.** Before creating any
folder in a project tree, look at `createdTime` and `parents` on every hit. A
folder created minutes ago is yours, not theirs.

## Failure mode 2 — inventing a new layer

Even when moving into a live tree, do NOT invent a new top-level layer
(`BRDPL/`, `Proposal by X/` at project root). Find the folder that already
holds the same class of document.

BuxRanka worked example — the correct destination was
`BuxRanka > BuxRanka Legal Docs` (id `1-1mN_LN_cJe5a2XPFX7sOrhh2wx-evPJ`),
because it already held the BRDPL MOA/AOA, PAN, GST, LEI, EC copies, Hudson NOC
analysis and prior title-report drafts. Two other BRDPL folders existed and were
both wrong: Pradeep's 2022 `BRDPL - BRH - Legal DD Documents`, and sales-team
dumps (`BRDPL _IDBI _ GFM...`, `BRDPL Documents Signed on...`).

Checklist for choosing the destination:

1. List candidate parent folders by name (`name contains '<entity>'`).
2. For each, `gws_drive_list` its children. Prefer the one whose existing
   contents are the same *document class*, not merely the same entity name.
3. Reject folders owned by someone else (`owners: pbranka@...`) and folders
   that are clearly a team's working dump.
4. State the chosen path and the reason in the reply, and name the folders you
   rejected — NDR wants to know why you picked it.

## Move procedure (verified pattern)

```
gws_drive_move(
  file_id        = <folder being moved>,
  add_parents    = [<destination folder id>],
  remove_parents = [<TMP parent id>],
)
```

Then verify all three, do not assume:

1. `gws_drive_get(<moved id>)` → `parents` must be exactly the destination.
2. `gws_drive_list(folder_id=<moved id>)` → same file count and names as before.
3. `gws_drive_list(folder_id=<old TMP parent>)` → `count: 0`.

Only then delete the empty TMP chain, deepest first, and re-list the TMP root
afterwards to confirm nothing of yours is left under it.

Note: `gws_drive_delete` trashes; a deleted folder is recoverable from Drive
trash, so cleanup of an empty scaffold folder is low-risk.

## Permission inheritance — check BEFORE you move (important)

A Google Drive folder shares its ACL with everything inside it. Moving a folder
(and its contents) into a shared project folder silently grants every existing
collaborator of that folder access to your files.

Real numbers from the BuxRanka move: `BuxRanka Legal Docs` was shared with
writers Pradeep B. Ranka, Vinod Kumar Das, Bharat, Roshini, Bhagya and Sanjay
AV, plus Puneeth K. Gowda as reader. After the move, an internal DD report
containing candid "this vendor opinion is not bankable" judgements and
negotiation strategy was readable by all of them.

So:

1. `gws_drive_get(<destination>)` and read `permissions` before moving.
2. If anything inside the folder is internal work product (our own analysis,
   draft opinion, negotiation notes, internal report), say so in the reply and
   offer the fix: a subfolder (e.g. `Internal Analysis`) inside the destination
   with inherited access removed, holding only the internal material, so
   third-party documents stay visible and our work product does not.
3. Do not silently move internal analysis into a broadly-shared folder and stay
   quiet about it.

## Naming on arrival

Keep the existing `YYYYMMDD_<Entity>_<Asset>_<DocType>_<Source>` convention —
renaming is part of the move, not a separate step. When the move is between
folders only, names should already be correct from the TMP staging pass; do not
re-rename.
