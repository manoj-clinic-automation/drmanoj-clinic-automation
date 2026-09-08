# RETIRED AT S234 — 08-Sep-2026

Nothing in this folder is live. Nothing here should be pasted into Google, run,
or treated as a source of record. It is kept rather than deleted so that a
future session finds the reason instead of the absence.

---

## `VPS_Push_UPI.gs.STALE_200LINE_S234` — was `gas/VPS_Push_UPI.gs`

**Retired because it was a stale copy of a load-bearing live script, sitting in
the one folder that looked like the working copy.**

D432 detour item 5 named "the `VPS_Push_UPI.gs` duplicate — a 200-line copy and
the live 263-line one, both in the repo (D202/F-201)". **Measured at S234, there
were THREE copies, not two:**

| path | lines | functions | what it is |
|---|---|---|---|
| `deploy_kits/S217_HUB_FINAL/VPS_Push_UPI.gs` | 263 | 7 | the kit that shipped the live version — **a frozen kit, exempt** |
| `deploy_kits/S230_GAS_EXPORT/UPIReconciliation/VPS_Push_UPI.gs` | 262 | 7 | the 07-Sep-2026 recovery export — **a frozen dated snapshot, exempt**; byte-identical to the S217 kit but for a trailing newline |
| `gas/VPS_Push_UPI.gs` | **200** | **6** | ⬅ **this file. A generation behind, and the only one that looked editable.** |

**The danger was not that it was stale. It was WHAT was missing.** The 200-line
copy has no `checkUpiArrival` — the 15:00 watchdog that shouts when the day's
ICICI statement has not arrived. HOLD 1 (owner, 07-Sep-2026) puts the ICICI →
VPS chain under an explicit do-not-disarm rule, and `VPS_Push_UPI.gs` is named in
it as a crucial limb.

So anyone opening `gas/` — the obvious place to look for the Apps Script working
copy, and a folder holding exactly one file — and pasting it back into Google to
"restore" the script would have **silently removed a live watchdog from a
load-bearing financial chain.** That is a downgrade wearing the clothes of a
restore.

**Where the current copy lives now:**
`deploy_kits/S230_GAS_EXPORT/UPIReconciliation/`, which from S234 is refreshed
and diffed every Sunday by `deploy_kits/S234_GAS_WEEKLY/`. **One place, and it is
the place the drift check watches.** The empty `gas/` directory left behind is
not tracked by git and disappears on the next publish.

---
*Retired at S234, 08-Sep-2026. Measured before moving: three copies, line counts
and function sets compared file by file.*
