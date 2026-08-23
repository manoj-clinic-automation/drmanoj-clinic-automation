# HANDOFF RUNBOOK — v131 (Session 197 · the fold-in · 23 Aug 2026)

**Tier 0. §0 what happened · §1 mental models · §2 the live backlog · §3 install discipline · §4 the EOS automation boundary.**

---

## §0 — WHAT HAPPENED (Session 197 — EOS-light, the S185 precedent)

**A dedicated fold-in session. No live code touched, no live data changed, no pin moved.** The canonical KB had been folded only to **S192** while four full build sessions ran (S193–S196 lived as standalone `claude/S19x_*` close docs); `verify_live_pins.py` had been unprotecting since S193 because its list is generated from Register v5.40. This session cleared all of it in one pass, owner-delegated end to end.

1. **The F-series fork reconciled FIRST** (it froze all bare F-numbers at the S196 close). Evidence swept across the repo and project knowledge; resolution: **every circulated number keeps its meaning.** F-155–F-159 are S193's (F-155 consumed the canonical next-free; all five closed same-session). F-160–F-162 are S196's (no S194/S195 doc had used a bare F-160+ token). S194's recorded "F-160 candidate" (the email-agent over-fetch) is minted **F-163**. S195's five unnumbered faults are minted **F-164–F-168**. Numbering is deliberately non-chronological across F-160–F-168 — recorded, not silently reordered (the F-108 family at register scale). **F-168 is the only new OPEN finding** (the read-only medical share).
2. **Archive v1.43 → v1.44** — §S193…§S196 appended, pure-append, the 800,148 bytes before v1.43's END marker **proven byte-identical by direct comparison** (+34,510).
3. **Fault Register v2.32 → v2.33** — F-155…F-168 landed (§7 index + three new §7.1 sections); F-148 and F-153 rows updated to CLOSED-S193; next free **F-169**. **Reverse-application-proven** onto the `a52fa154…` pin.
4. **KB Register v5.40 → v5.41** — ~12 moved live pins folded into the live-file table; **D333** (cash-position model) and **D334** (present-request policy) into the decisions index; findings index extended; reserved next-free decision corrected D317→**D335**; lineage row; pointers advanced. **Reverse-application-proven** onto the `788139ae…` pin.
5. **Manifest rebuilt** — new STATUS head, CURRENT rows repointed (Register v5.41 · Archive v1.44 · Fault v2.33 · Runbook v131 · START_HERE 198), a §S193–S197 fold block, new Tier-1 rows for the durable S19x reference docs. **`live_pins.txt` regenerated from Register v5.41 (A8).**
6. **The F-107 filing** — every S192-owed and S193–S196 narrative/design/finding/pin doc that had lived only in project knowledge was filed into the repo (`deploy_kits/KB_canon_S197fold/filed/`) and hash-covered, closing the standing absence-blindness condition for those sessions.
7. **Cold kit TAKEN** (was due — 4 of 3–5 since S192).

**No live pins moved this session.** The authoritative pin list to trust remains the S196 close set: `finance_app.py 388c8ac0…` · `portal.py ee749cd9…` · `staff_ledger.py acd7b538…` · `staff_register.py 9087954c…` (v0.4) · `att_month_report.py 9ab98313…` (v2.6) · `email_agent.py e535c4f8…` · Marg `signatures.json 1b21f3bf…`.

---

## §1 — MENTAL MODELS (added this session)

- **A four-session canon debt is the F-108 pattern at scale.** The findings register said "next free F-155" for four sessions while the sessions themselves minted through F-168 in standalone docs — the same drift F-108 named at one-session scale, just larger. A dedicated fold clears it; the fix is not to let it reach four again. The S185/S186-close rule stands: fold every session, or flag the debt explicitly in the manifest STATUS and the START_HERE so the next Phase 0 does not read a mismatch as corruption.
- **Reconcile a number fork by circulation, not by chronology.** When two branches both spent F-160, the cheap correct move is to keep every number already in use and mint the collision forward — never renumber a circulated token, because a renumber invalidates every doc that already cites it. Record the non-chronological gap out loud.
- **A fold is proven the same way a code change is.** Pure-append prefix proof for the Archive; reverse application onto the pinned hash for the Register and Fault Register. A fold that only *asserts* zero loss is exactly the F-23 stump risk the whole tiering exists to prevent.
- **File the doc before the close, not at it.** The S192 three-doc debt and the S193–S196 docs were all "in project knowledge, owed to the repo" — the F-107 condition, carried forward five times. Filed here; the lesson restated: a Tier-0/Tier-1 doc that Phase 0 must read has no canonical existence until it is in the repo and hash-covered.

---

## §2 — THE LIVE BACKLOG

**⭐0 — owner actions (unchanged, carried; the copy-block in the S196 close chat):**
- **Token rotation** — `FINANCE_MARG_TOKEN` + `FINANCE_CRON_TOKEN` (cron token also in GAS "UPI Reconciliation"). Exposed in chat 21-Aug. **Still the highest-severity open item, now aging two days further.**
- Darpan's signed-application scan → approve advance `0cc0b26b38c5` **before the August close** (else the ₹8,000 first step shifts).
- 17-Aug ₹20,000 → Staff Ledger. File 21-Aug (auto-replay then loads its pending 37-bill Marg push — F-155 behaviour, not a fault). 18-Aug 8-bill attribution. The correction-checklist day + 4 UPI/bank disagreement days. July salary sheet. Staff-phone PWA installs. Drive-for-Desktop on the medical PC (closes F-168). Labmate sample export.

**⭐1 — the Auditor's first reports.** Weekly, Mondays ~07:05 IST (`trig_01XBRt7dcsXcjtmgdmemnR3x`). First firing 24-Aug = slice 1 (cash trail) calibration; report lands as `claude/AUDIT_RUN_*` with AF-# findings + push/email summary. Triage its ≤3 recommendations. An auditor finding nothing on slice 1 is broken.

**⭐2 — August month-end.** First full run on SL5–SL7 + F6 + the v2.6 present-request fold + D331/D332 rules. Watch, don't assume.

**⭐3 — builder backlog (carried):** Club 3 router signatures (needs sample exports) · Club 4 (Amir/accountant answers) · expense-scan viewer · entry-page disabled-File explanation · NEFT assembly · refresh the repo mirrors of the live `finance/`/`portal/` trees (they are S180/S182-stale — do it alongside the Auditor's slice work).

**Doc-drift CLOSED at this fold:** the **v6** close-out routine (A9, S194) had lived only in project knowledge under a misnamed `END_OF_SESSION_PROMPT_v5.md`, never in git (an F-107 condition). Fixed: `END_OF_SESSION_PROMPT_v6.md` (`32b6092c…`) filed and pinned CURRENT; the genuine A0–A8 v5 retained. The evergreen START-HERE custom-instructions still name `_v4` — the owner updates that pointer.

---

## §3 — INSTALL DISCIPLINE (unchanged)

No installs this session (docs only). The standing chain holds for the next build: hash-verified base bytes (recover live bytes by hash from kit tarballs — the repo `finance/`/`portal/` trees are stale) · offline pre-flight (`py_compile` · `pyflakes` · `check_late_locals` · `check_row_keys`) · the seeded-store differential before any finance kit · currency gates on every live file a kit touches · `bash -n` every installer · the projection written before measuring · **the publish destination read from `PUBLISH_ALL.bat`'s `REPO_DIR`, never assumed from the folder root (F-160).**

---

## §4 — THE EOS AUTOMATION BOUNDARY (held)

The assistant executed the entire fold: the F-series reconcile, Archive/Register/Fault-Register bumps with mechanical proofs, the manifest rebuild, the `live_pins.txt` regeneration, the F-107 filing, and the cold kit. **Owner residual: one `PUBLISH_ALL.bat` double-click, then on the box `git pull` and copy `live_pins_S197fold.txt` → `/root/deploy/live_pins.txt`, then run `verify_live_pins.py` — expect GREEN, match 45, `source: VERIFIED`** (the first GREEN since S192; the list had been stale four sessions).

---

*HANDOFF_RUNBOOK v131 · Session 197 fold · supersedes v130. If §0, §2 or this end-marker is absent, this file is truncated and must not be used as canonical.*
