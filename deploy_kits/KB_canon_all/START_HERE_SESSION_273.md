# START HERE — SESSION 273 — written at the S271 close, 20-Sep-2026

**Project: Dr Manoj Clinic — Systems & Automation (the parent).** Open in a fresh chat in this project.
Run `START_HERE_PROMPT_v10` (the project's custom instructions) Phase 0 first, then this file.

*Claim 273 on the System Board before you name a scratch folder (F-509 · F-515). If the board has moved past
it, take the next free number and say so in your first line.*

---

## 0 · HIS INSTRUCTION FOR THIS SESSION

> *"a lot of discussion and research and planning has been done … so that we build this in a fresh chat
> in this project"* — and earlier: *"after all discussion is made then we will build in one go."*

**Build the 360° patient-record plan, in his accepted order.** Read **`S271_BUILD_BRIEF.md` §2 first — it is
the whole design, with every ruling he gave.** Do not re-ask what the brief settles. Do not put technical
choices to him. Start with step 1 and the two things to settle before it (Drive space, the reception PC's
Drive path) — both are yours to find, not his.

1. Blood PDFs into the clinic Drive + the 360° page (visits, procedures, pharmacy bills and returns, reports).
2. The X-ray inbox — read-only **test run first**, then live, then the one-time import of old X-rays.
3. "Check karein" at reception (Shavez the checker) + his one collapsed line.
4. Reports patients send on the clinic WhatsApp — confirmed by reception before filing.
5. Outside MRI/CT scans + hospital/surgery events ("Add event").
6. Sending reports to patients on WhatsApp — once sending is cleared (F-82).

---

## 1 · THE CURRENT CANON — the manifest wins, this is only the index

| what | file |
|---|---|
| Register | `KB_Register_v5_112_S271close.md` (clone only, D550) |
| History Archive | `KB_History_Archive_v1_109_S271close.md` |
| Fault → Action Register | `Fault_Action_Register_v2_97.md` |
| Runbook | `HANDOFF_RUNBOOK_2026-09-20_Session271close_v192.md` |
| close routine | `END_OF_SESSION_PROMPT_v16.md` |
| evergreen prompt | `START_HERE_PROMPT_v10.md` (the project's custom instructions) |
| live pins | `live_pins_S271close.txt` |
| build brief | `S271_BUILD_BRIEF.md` |

**Next free: D564 · F-556 · A-D25 · kit S332 · Session 274.** *(272 is the Sanjeevni chat's, open beside this close; it holds kit S331. The parent's next session is therefore 273 — this file.)*

---

## 2 · WHAT IS LIVE THAT WAS NOT, AS OF THIS CLOSE

| machine | file | pin |
|---|---|---|
| VPS | `/root/finance/slip_log.py` | `0b3195d2610e64a4b637e0ed89eb8454` |
| VPS | `/root/finance/finance_app.py` | `41e0ffb4ce8c94a76c251294ef3e5d31` |
| VPS | `/root/portal/portal.py` | `4085b76781696f80f64283aa1eef57bb` |
| VPS | `/root/portal/tile_grants.json` | `fe38b97494ee7a43091323dfd64e7836` (v22) |
| Apps Script | drmka.ortho → UPIReconciliation → `VPS_Push_Lab` | every 15 min, since 19-Sep 19:40 IST |

```
https://followup.dr-manoj.in/finance/slips
```
```
https://followup.dr-manoj.in/finance/slips/report
```

---

## 3 · THE SIX THINGS THIS SESSION LEARNED THE HARD WAY

1. **Take a maximum over events, not over a register** (F-551).
2. **A walk compares before/after of what it did not touch** (F-552).
3. **On a live page, change data through the row's own form, never by pixel** — and read the list back (F-553).
4. **No `__pycache__` under a kit before the publish** (F-554).
5. **A rule he states is not relaxed to cure a one-off** (F-555).
6. **Nothing is asked of staff during patient flow** (D559).

---

## 4 · WHAT IS WAITING ON HIM — keep it this short

1. The publish of this close's canon: `D:\dr-manoj-git\drmanoj-clinic-automation\PUBLISH_ALL.bat`.
2. His word to start the records build — he has given it (*"build this in a fresh chat"*).

**How he wants to be spoken to:** short, human-readable, English; one paste or one double-click; decide the
technical questions yourself; full paths and full URLs in their own copy blocks.

---

*Written at the S271 close, 20-Sep-2026. Canon: Register v5.112 · Archive v1.109 · Fault v2.97 · Runbook v192 ·
routine END_OF_SESSION_PROMPT_v16 · pins live_pins_S271close.txt.*
