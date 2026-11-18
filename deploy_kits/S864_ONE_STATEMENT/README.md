# S864_ONE_STATEMENT — one bill statement, the pair once more over the finished month (18-Nov-2026, Sanjeevni session 479)

**Why.** The owner, 18-Nov 07:49 IST: *"deeply analyze the need for sequential exports of reports from Marg and optimize those rather than keep
on adding the exports without compromising the accuracy of the data in any way."* The analysis (`claude/S479_MARG_EXPORTS_ANALYSIS.md`):
Marg's **bill-wise** and **supplier-wise** purchase statements carry the same five figures per bill (supplier, bill no, date, cash, credit) — one
report in two groupings. They "disagree" only when Marg was edited between the two exports (October's ₹549). Every rule built on that
disagreement — rev-4's cross-check, S855's re-ask, D1000 as agreed on 17-Nov — managed a redundancy. His **go** 08:21 IST on the proposal.

**Now.**
- **One family** (`purchase_app.py`): the push retires every older statement of EITHER kind whose period the incoming one contains (the rev-4
  containment rule, across the family); the month's figure per bill is the live statement with the NEWER Marg stamp; no disagreement bucket
  (`disagree_p` 0, `month_disagree_p` 0). The month needs **two** reports after it ends (`_S604_REPORTS`: a statement covering the whole month —
  bill-wise, or supplier-wise if that is what came — and the item lines), not three. The cross-check (`_verify_statement`) reads the newest
  statement of either kind: every bill on the sheet carried by it, and its own printed grand total against the sheet. S371's self-resolution
  (`_resolve_wrong`) reads the newest statement. **The one-off** (`s864_one_off`, run by the installer after the restart; DRY on the copy first):
  for counted, non-FINAL months, a live statement contained in a newer live statement of either kind is retired (the S795 part guard holds: a small part list retires nothing and is itself kept as a part of the fuller statement, as the push does — audited `s864_part_retired`; audited `s864_superseded` with both row counts and the bills only the old one carried),
  then the Wrong marks the newest statement shows are resolved — on the 18-Nov copy, October: the 06-Nov supplier-wise retired by the 11-Nov
  bill-wise, the figure ₹3,72,609 (= its printed total), Kedar A000211 / Yogendra 19612 / Shivaaz 3854 resolved by themselves.
- **A re-export of the same bytes** (the duplicate md5 at the push door): a LIVE statement takes the newer capture stamp (`duplicate_restamped`, audited `push_again`), so an ask that waits for a statement newer than a correction clears and Amir's step 4 sees today's export; a superseded one is left as it is.
- **The asks** (`month_asks.py` 2.0): a finished month's PAIR — BILL WISE PURCHASE STATEMENT + SUPPLIER/ITEM WISE PURCHASE STATEMENT, FROM the 1st
  TO the last day — asked when no statement / no lines covering the whole month have arrived, and again ONLY for a reason it names: a bill of the
  month on Amir's correction list (S738, open), his own *meri entry galat thi* after the statement, a scanned bill of the month answered
  *enter it in Marg* and not yet in Marg (S849). The supplier-wise is never asked. Words: his payment sheet / purchase check card ("Amir exports last
  month's pair once more … Why: …"), row 8 (two lines), the check's open item (one line for the pair), the Needs-you; `amir_pairs()` for his steps;
  `amir_lines()` for his card (Hindi, with the reason). `disagree` is always `[]` (kept for the callers' shape).
- **Amir's steps** (`amir_day.py`, one tail block): step 3 lists *Pehle pichhle mahine (October 2026) ki report* ABOVE *Is mahine ki do report* —
  both reports, FROM/TO, the reason in Hindi; step 4 shows each of them ✓ (time) / at the door / not yet. Never a gate.
- **The export watch** (`export_watch.py`): on the 1st–5th a whole-month BILL-WISE (or supplier-wise) after month end satisfies the month-end
  expectation; its label names the bill-wise. The owner's own words of 11-Sep stand ("why burden anybody for exporting a report which is not required").

**Files:** `purchase_app.py` 1ac9d1ef · `month_asks.py` cf72cde9 · `amir_day.py` 97e56bc7 · `export_watch.py` f6845ec5 — by `make_s864.py`
(exact anchors, each once; `amir_day_tail_s864.py` appended; month_asks whole). **OFF:** `/root/finance/_off/S855_OFF` (the asks) as before.
**Proof:** `synth_s864.py` (T0–T27 + T19b–f on a made-up ended month 2025-02 in a copy — the family at the one-off and at the push door, the part guard, a bill only the retired statement carried, the cross-check's 'not carried', the Wrong mark resolved at the push, the duplicate re-stamp, the hub and month page drawn; `--real` adds R1–R3 on copies of the live databases and the one-off
DRY); the control (live files + the new month_asks) red; `export_watch --selftest` 21/0; walks s781/s761/s750/753/755 + synth_s849/s850 (+ s814/s845
on the box) the same on old and new under `MONTH_ASKS_FROZEN_WALK=1`; `rehearse_s864.sh` R1–R10. Cold review (a second agent, read-only): 1 MUST (the part guard in the one-off) + 4 SHOULD built in; second look: SAFE TO INSTALL, its one SHOULD (a part left live at the one-off; a statement not carrying the sheet's bills asking nothing) built in as T26/T27b.
**Install:** publish, then the one server line in the installer's head. **Undo:** `bash /root/deploy/repo/deploy_kits/S864_ONE_STATEMENT/undo_s864.sh`
(the one-off's audited data stays; the old code reads the figures as before).
