# HANDOFF RUNBOOK — v119 (2026-08-17 · Session 185 close — Phase 0 proved the canon intact, F-107 and F-108 were raised from the record's own blind spots, and THREE sessions of canonical debt were cleared in one pass)

*Tier 0. §0 what happened · §1 mental models · §2 live backlog (⭐ top task at head) · §3 install discipline. Companion to KB Register v5.6 (state) + KB History Archive v1.33 (history).*

> **The canon is current again.** S183, S184 and S185 are all folded in. There is **no documentation debt outstanding** at this close — the first time that has been true since S182. One honest gap remains and is named in §2: the `finance_app.py` pin is **partial** (`c66bec2b76…`), because the full md5 was never written down and was not invented.

## §0 — WHAT HAPPENED LAST (S185 — a verification session that became the fold-in session)

**Thread 1 — Phase 0 came back GREEN, and independently so.** Documents were verified against **git bytes**, per the S182 rule that a hash verdict is pronounced only on bytes delivered as a file. `md5sum -c MD5SUMS_ALL.txt` in `deploy_kits/KB_canon_all` → **55 of 55 OK** (kit ID `536961e984832a38e008d9c26524b097`). Then the **F-88 cross-check**, run separately because a passing sums file proves a kit internally consistent rather than current: all **77** md5 tokens in the manifest were matched against real file hashes → **52 matched bytes**, and the **25** that did not are each legitimately not a document (live VPS code pins, Tier-2 artefact digests, the three D316 closed-as-lost rows, two superseded S178 versions). Nothing unaccounted for; nothing halted.

**Thread 2 — F-107: Phase 0 is blind to a document that was never listed.** The S184 close wrote two **Tier-0** documents — `HANDOFF_RUNBOOK v118` and `START_HERE_SESSION_185` — into project knowledge only. Never to the repo, never into `MD5SUMS_ALL.txt`, never rows in the manifest. **So at the S185 open, the two Tier-0 documents Phase 0 is required to read were the two it could not verify.** They were read on trust, and nothing complained — *because nothing looks for a missing row*. Phase 0 asks of each listed row *do these bytes still match?*; it never asks of each document in use *are you listed?* **Both files were filed to the repo at this close, hashed as delivered, and pinned.** Their hashes were deliberately **not** invented beforehand.

**Thread 3 — F-108: findings recorded in one register were never applied to the other.** Found while building the owed append, by checking the Fault Register's next-free number against its last index row. **§7 ended at F-89 and read "Next free finding: F-90"** — while **F-90 … F-95 (S181) had never been applied to it at all**, and F-96 … F-99 (S182) existed only as §7.1 text with no index rows. The KB Register carried all ten, so nothing was lost; but the *findings register* was four sessions behind and said so nowhere. Compounding it, **v2.18 bumped the file and left no changelog row** — reconstructed at this close. **This is the F-45 family**, minted by that very register at S149 for exactly this failure and reconstructed six times at v2.17.

**Thread 4 — the fold-in, executed in one pass at the owner's instruction.**
- **KB History Archive v1.30 → v1.33** — §S183, §S184, §S185 appended in **chronological order as one contiguous append**; prefix proven byte-identical to the `7a673ac6…` pin (+21,183 chars).
- **Fault_Action_Register v2.18 → v2.19** — F-90…F-95, F-100…F-104, F-105…F-106, F-107…F-108 all landed; §7 index extended from F-89 to **F-108**; three new §7.1 continued sections carry full text; v2.18's missing changelog row reconstructed. **One version bump, not four** — the file has one final state, and three extra rewrites would be churn, not provenance.
- **KB Register v5.5 → v5.6** — the two S184 migration markers recorded; **D322** into the decisions index; **F-105…F-108** into the findings index; the stale `v5.4` H1 corrected; `finance_app.py` moved to the S184 build as a **partial pin**.
- **CANONICAL_MANIFEST rebuilt**, `MD5SUMS_ALL` regenerated, `START_HERE_SESSION_186` promoted, the set pushed to GitHub, and a cold kit taken **after** the fold-in so it captures the finalised set.

**No decision minted. F-107, F-108 raised. No incident. No live code or live data changed this session.**

## §1 — MENTAL MODELS WORTH CARRYING

1. **Carried and undiminished from v118:** survey the box before writing to it · a self-test that asserts a data state is a liability (F-106) · the bank arbitrates, the human confirms · a negative drawer is unrecorded movement, not loss — and you cannot book it away without the float · the app enforcing correctness looks like an obstacle and is a feature (F-105) · keep the common path trivial and Hindi-first.
2. **⭐ Verification catches the wrong row and is blind to the missing one (F-107, F-108).** Every check this project owns walks a list and asks *does this still match?* None of them walks reality and asks *is everything here on the list?* So a corrupted document is loud, and an **unlisted** document is silent — and silence is indistinguishable from success. Two findings in one session, in two different documents, from the same blind spot. **Absence, not corruption, is what this project has actually lost things to** (F-89: three canonical documents, lost because a backup that was never taken cannot fail loudly). The remedy is always an *inverse* check, never more diligence.
3. **⭐ Deferral compounds silently, and every individual deferral is defensible.** S183 protected live financial books from a tail-of-marathon write. S184 went straight to the cash correction the clinic actually needed. S185 opened by asking rather than assuming. **Each was right locally; together they were three sessions of drift.** By the third, folding in was itself a large and risky operation. **RULE: the fold-in belongs at the HEAD of a session, never the tail — and a debt that survives two deferrals is a process incident, not a backlog item.**
4. **A document that exists in only one place is not canonical, whatever its header says.** Canonical means: in the repo, hashed in the sums file, listed in the manifest. Anything else is a draft with confident typography — which is precisely how F-107 happened.
5. **Never invent a hash to make a table look complete.** The `finance_app.py` md5 was recorded as eight characters at the S184 close and ten in one other place. The full value is not known to the record, so it is pinned as **partial and flagged**, not filled in plausibly. *"Compute at freeze" means a real hash still owed, not a placeholder to skip.*

## §2 — LIVE BACKLOG

**⭐ 0. Complete the `finance_app.py` pin FROM the box (five minutes, do at the S186 open).** Run `python3 /root/deploy/verify_live_pins.py`. The Register row carries `c66bec2b76…` and says openly that the rest was never written down. Correct it from the machine (D321(d)), then the Register is whole. *This is the only outstanding record gap at this close.*

**⭐ 1. Resolve the opening float, then book.** Get **Darpan's drawer count** + **Dr Bhawna's held cash** into `Sanjeevni_Cash_Reconciliation.xlsx` Tab 1 → the verdict decides:
- **float ≈ 0** → the 29 negatives are real parking-timing; book nothing, they stay labelled.
- **float ≈ 85–99k** → ship the prepped gated **`S184_C3a`** (opening-float-parked-with-Dr-Bhawna).
Booking the negatives away is *mathematically impossible at float 0* — so "no negatives" and "drawer ≈ ₹43k" cannot both be true, and **only a physical count decides which is.** Design and both paths: `S184_Float_Investigation` + Archive §S184. **The count takes five minutes and is the only honest resolution.**

**Then, in rough order:**

2. **Darpan submits 14 & 15 Aug** with the three scans; Manoj approves. **16 Aug** is a Sunday — optional under D322; file only if there was a sale.
3. **Build the reserve / counter-person model.** Schema (counter_person registry + held-by-reserve custody), app (biometric-as-hint, four-way cash destination, multi-day stretch reconciled by Marg + bank), form (picklist, "cash handed to", date range). Sequence AFTER F1b — both touch `finance_app.py`. **Show the Hindi labels for owner approval BEFORE building the UI.**
4. **Build the reconciliation workbench.** Marg ⋈ bank ⋈ entry on one screen; cash→UPI suggestions graded like D315, never auto-applied; correction log via `audit_log`. Highest value / lowest risk — mostly reads data that already exists — and it delivers the **F-91** fix. Add the **drawer-count field (accepts blank, but flagged)** here.
5. **F-104 WALK-IN reclass** — 118 `line_sum_vs_day_total` legacy no-ID Marg bills; clears ~2,062 review items. No money affected.
6. **F-103 — build the Yes Bank cash-deposit reconciliation** parallel to `finance_upi`, plus a named "bank deposit (Yes Bank)" movement type. The 16 deposits were booked at S184; **the mechanism that prevents a recurrence is still missing.**
7. **F-106 follow-up** — split the `finance_app --selftest` into invariant-logic vs seeded-fixture checks, so a legitimate data correction can never again block a code deploy.
8. **F-107 structural fix** — the inverse Phase-0 check: assert every Tier-0 document about to be read has a manifest row. Natural companion to `verify_live_pins.py`. **F-108's twin fix** is mechanical and trivial: assert the Fault Register's next-free number equals its last index row + 1 at every append.
9. **F-97 part 2** — the loaded-in-memory check (a file matching its pin ≠ the running process loaded it, S127) and the PC-side half of the pin verifier; triage the 68 UNTRACKED live files.
10. Carried: WABA go-live (F-82, vendor) · security rotations · console follow-ons · F-92 discount capture · F-93 concession-parser footer.

**Cold-kit count: reset to 1 of 3–5** — `KB_S185_close` taken at this close, **after** the fold-in, so it captures the finalised set rather than freezing debt into a backup.

## §3 — INSTALL DISCIPLINE (unchanged)

The D317 kit chain stands: SUMS → KIT_ID → currency/state gate → smoke/selftest BEFORE swap → backup → apply → verify → an honest red that restores. Standing additions: **`push_kit.bat` v4** refuses to publish if `.gitignore` silently drops a kit file (F-100); the **read-only survey kit** (S184_S1a) — survey the box before writing to it; the **state-adaptive self-test** (F1b, F-106). Financial-book changes remain **gated migrations, offline-rehearsed against a copy of the real store, reversible, never ad-hoc SQL**. `verify_live_pins.py` (D321) at every open and close; the Register is corrected FROM the box. PHI, `finance.db` and raw Marg exports never enter the repo or a kit (F-31 / F-49 / D320).

**END OF HANDOFF RUNBOOK v119 (Session 185).**
