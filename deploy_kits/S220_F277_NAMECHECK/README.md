# S220_F277_NAMECHECK — the ingest name-check

**The finding is the owner's queue-head for S220** (*"the first thing, so as to polish out and
complete the entire Marg system"*), measured at S219 on `returns_docterz_match_Aug2026.csv`.

## What was wrong

`finance_ingest.resolve_patient()` attaches a bill **by clinic ID and never reads the name** on the
branch that fires for every bill carrying an ID; and it returns a bare patient id, so it has **no
channel to say it is unsure** — the row is written at full confidence and the disagreement is not
just unacted-on, it is unrecorded. **4 of 43 August returns** (762 → Daljeet Singh on Paramjeet
Kour's bill; 638; 782; 7837) attached a **stranger silently**, and every audit afterwards judged
her returns against his purchases with complete confidence. (212 is the fifth row on that sheet
and is a different thing: an ID absent from the master — `identity needed` already covers it.)

## What this kit does — the owner's shape

**A disagreement becomes a finding, not a tiebreak.** Attachment stays **by ID only**; the money
path is byte-for-byte unchanged in effect. Alongside, the ingest writes an `identity_dispute` row
(unit · date · bill · ID · the bill's name · the master's name), UNIQUE per bill so a re-ingest
neither duplicates nor loses it, and **closes it itself** when a later export of that bill agrees.
The audit gives such a return the verdict **`identity disputed`** — a *question*, never a money
verdict: no purchase-matching, a note naming both names, the money counted as before. Darpan's
app keeps it out of the flagged count; the hub paints it **amber**; the escalation spine's
allow-list never sees it. D361 holds — the past raises no work.

The name comparison is **tolerant, calibrated on the master's own spellings** (Kanta Parsad /
KANTA PRASAD · Chandrwati / CHANDRAWATI · VIVHA / VIVAH · Kour / Kaur all agree, as the evidence
sheet says) and reproduces that sheet's 43 verdicts exactly: 28 agree · 4 differ · 11 unknown.

## Files

| file | what |
|---|---|
| `patch_ingest_namecheck_s220.py` | finance_ingest.py — helpers + the one call site (2 anchors) |
| `patch_audit_disputed_s220.py` | finance_returns_audit.py — the lookup, the verdict, the discount rule (3 anchors) |
| `patch_darpan_disputed_s220.py` | darpan_app.py — out of the flagged count (1 anchor) |
| `patch_hub_disputed_s220.py` | finance_approvals.html — amber (1 anchor) |
| `selftest_namecheck_s220.py` | 60 checks on a COPY of the live db |
| `walk_namecheck_s220.py` | the live-shape walk: the real `ingest_day`, real source/column map, real master row, real audit — 12 checks |
| `PREDICTED_PINS.txt` | the four pins the owner's md5sum must read after install |

## What it deliberately does not do

No backfill: `sale_item` never stored the bill's name, so the past cannot be re-checked from the
database (only from Marg exports — which is what the S217/218 sheet did). No Hindi list for
Darpan yet (Layer C of the S220 design brief). No `finance_app.py` change (the escalation hook
is an allow-list; nothing needed).

## Recorded while building

`finance_ingest.py`'s own built-in selftest (`python3 finance_ingest.py <db>`) is RED against the
current live db shape — **on the unpatched live bytes too** (a `sale_item_review` lookup that now
returns nothing). Pre-existing; not touched; noted for the Fault Register.
