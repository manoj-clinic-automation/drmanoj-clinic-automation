# S219 BUILD BRIEF — the Marg session · 02-Sep-2026

**One brief instead of ten papers. Read this before anything else about S219.**

---

## WHAT IS NOW LIVE THAT WAS NOT THIS MORNING

| system | state | pin |
|---|---|---|
| **M1 · Marg auto-apply** | LIVE 13:42 | `finance_app.py` `b42b1f08…` → (M7) `a57980c2…` |
| **M2 · router signatures** | LIVE | `signatures.json` `99a7214c…`; `marg_router.py` unchanged |
| **Scanner v2.3** | LIVE on 7 surfaces | `scanner_widget.js` `4ae2d29a…` |
| **Pharmacy intake lane** | LIVE 16:17 | `asset_register.py` `958c7fb7…` |
| **M7 · the returns line** | LIVE | `200e4d1c…` · `f4161c7d…` · `a57980c2…` · `735c7958…` + `finance_returns_escalate.py` `35ad7595…` |

Every pin was **predicted offline and then read from the box**. Ten predictions, ten matches.

---

## THE ONE NUMBER TO CARRY FORWARD

**197 credit notes, 01-Apr → 02-Sep-2026, ₹68,099. Zero of them lack a name. 127 lack an ID.**

Clinic-ID capture began in **July 2026**:

```
Apr  0/43     May  0/36     Jun  2/32     Jul 31/39     Aug 33/43     Sep 4/4
```

Consequences, and they are the whole shape of the returns work:

- The **"unnamed returns" population does not exist** and never did (F-279). Documents from S213
  onward named it wrong, and every remedy inherited the error.
- **109 of the 127 ID-less returns are a missing system, not a missing answer.** Nobody caused them.
- The human worklist is **10 returns + 5 identity disputes**, not 127.
- **D361 — the past is accepted**: `returns.act_from`, default 2026-09-02. History keeps its
  verdicts, its money and its place; it raises no task. **It is the detector's baseline — do not
  delete it.**

---

## THE OPEN FAULT THAT OPENS S220

**F-277 · A WRONG CLINIC ID ATTACHES A STRANGER, SILENTLY.**

`finance_ingest.resolve_patient()` — *"Clinic ID first, name only as a hint"* — never compares the
bill's name with the master's. **5 of 43 August returns (12%)** carry an ID belonging to someone
else. Worse than WALK-IN pooling (F-273), because WALK-IN announces that it does not know while a
wrong ID lets every downstream audit speak with full confidence about a stranger's history.

**Owner's ruling: this is the first build of S220.** Propose the shape before touching the money
path. The evidence file already exists: `D:\Downloads\returns_docterz_match_Aug2026.csv`.

---

## THE THREE RULES THIS SESSION PAID FOR

1. **Search this project's own work before deriving anything** (F-276). The proof that three-digit
   clinic IDs are real had been on the owner's disk since S217/218; a shape was inferred from 68
   examples instead, and he corrected it in one line.
2. **Read the screen's own code first** (F-278). The hub's verdict badge is a ladder whose final
   else is red — "identity needed" would have shipped in the loudest colour on the screen.
3. **Run the selftest ON THE BOX, against the live sources.** M7's suite copies the live files, runs
   the kit's own patchers over them and tests the result: 55/55 on the VPS *before* installing.
   That is the join, not just the kit.

---

## STILL OPEN, NAMED HONESTLY

Scanner **A5 vertical resize** (`fitAspect` covers the content box in both directions — owner
deferred it to S220) · the fourth Marg layout (`SALE RETURN LIST`: `BILL NO · DATE · PARTY ·
AMOUNT`) not yet taught to the router — `read_report` correctly REFUSED it rather than guessing
(D188) · F-235's skip message wrong for equal-sized duplicates · `CRON_TOKEN` literal at
`finance_app.py:9021` · 13 F-185 fixtures in the live `marg_report.py` · the F-269 route patch ·
M3 / M4 Phase B / M5 / M6 · August purchase still PROVISIONAL by the owner's hold.

---
*S219_BUILD_BRIEF · 02-Sep-2026 · lives in three places: project knowledge,
`D:\Downloads\ClaudeCowork\03_WORKING_PAPERS\S219\`, and loose on the SSD.*
