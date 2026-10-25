# S350 BUILD BRIEF — the Sanjeevni chat, 25-Oct-2026 (06:34 → 08:28 IST) — Kit II, the buying model, live

*Part A is for the owner. Part B is for the next Sanjeevni chat (session 353, reserved). Written at the S350 close under `END_OF_SESSION_PROMPT_v18`; the same text in project knowledge, `D:\Downloads\ClaudeCowork\03_WORKING_PAPERS\S350\` and `F:\ClinicBackup\DrManojClinic_Automation\03_BUILD_BRIEFS\`.*

## Part A — for the owner

**What is live since 08:22 this morning.** The system's own order list is now made the new way behind one setting on your approvals page — *Buying rules for medicines* → **How the list is made: Levels**. Each supplier is reviewed at its own rhythm, learnt from its bills (Kedar stays Monday + Friday as you ruled); quantities are the shop's usual lots; yesterday's sales are in the list; the shelf always keeps enough for the largest single sale of the last four weeks; an extra order between reviews goes only when the stock truly will not last. **Nothing changed for the staff** — Darpan's Marg sheet stays the order. The old way is one button away (*Change to Fixed days — as before*) and was proved line-for-line equal to yesterday's engine before the install.

**What happens next, without you.** From tomorrow (Monday 26-Oct) at 09:00 the list is made the new way every morning and scored every night against what was actually bought. The new list's first weekly score appears on your page on the night of **1-Nov**; the 14-day figure a week later. **After three good weeks** (85 % of what was bought was on the list beforehand · 80 % of the list bought within 14 days · no more medicines ran out than under Darpan's sheet) I bring you the switch to the system's list for your word — never before, never by itself.

**The evidence it stands on.** Re-run this morning on the 25-Oct database: on the 19 days the model had never seen (4–22 Oct), the shop had 27 empty-shelf days, today's engine 26, the new model 10 — at 18.8 supplier orders a week against Darpan's 15.1. Every rule earned its place when taken out in turn. The replay inside the kit matched the reference exactly.

**Amir's work (your question of 07:01).** Nothing has been done yet and nothing could have been: his card has carried the 4 expired batches (Cartilox sachet, Exlain A, Runvace TP, Vinbactum DS — expired Feb 2025, 25 pieces) and the 30 negative batches since Saturday 22:53; no Marg export has come in since. The four expired items drop to zero in the daily closing the morning after his vouchers — I check after his next visit; the 30 batch corrections show only in a Batch Stock export.

**Yours (on your board):** the publish of this close (one double-click); before 1-Nov VOM L, REEBORN D, RIFAVAX 550; the two September payment messages on the reception phone; Shivani's Marg reports login. Nothing else.

## Part B — for the next chat

**Kit S644_BUYING_MODEL** (D678 built; D785 the go-ahead) — six files, FROM → TO, DECLARED-PENDING until the 26-Oct bundle: `order_rules.py` 8d078dbe → 8a116cbd · `porders_s454.py` 673883e8 → 438714b8 · `spine/spine_read.py` 10697b38 → ad441b1d · `spine/order_rehearsal.py` 104d366d → c5d019ef · `spine/selftest_spine.py` 7d0edb4a → a05229e1 · `finance_ui/finance_approvals.html` a7016a4e → 885f6f31 (the parent's template; `finance_app.py` not touched). Data: four columns on `order_supplier_rule`, eleven `order.*` settings, `order.model = levels`; `order.source` NOT written. No crontab change. The kit's README, `REPORT_S644.md` (published, `c79ff2e3`) and `claude/S350_KIT_II_PLAN.md` carry the design, the walk whole and the real-day table.

**What this chat decided (D785 and the chat's calls):** one kit (Part A's fixes live or folded in); the owner's door inside the existing *Buying rules* fold (no fourth fold); B.6 dropped, B.5 read-only on his fold; `first_seen` not read (new = the spine's earliest purchase line); the kit's replay on the tables of the nightly copy (the reference's store — `spine.db` is in no bundle); Darpan's tab untouched (the B.2a header line goes with the kit that moves the source); `_line_out` adds `model` to every row (fixed rows say `fixed`). S308's (i) (ii) (iii) were S593's already.

**What the open reads (START_HERE_SESSION_353 §0 A):** the 26-Oct bundle against the six pins; the model's first morning (Monday 09:00 — `order_proposal` with `lines[].model`, the `made_through` stamp, the fold's *last list stood on*, the old page); F-1016's Monday 10:30 read; Amir's four expired items in the next closing; the spine's *EXCEPT 191 items* line (`spine_compare_latest.txt`) — the spine's carry or Marg's exports.

**Then (§0 B):** the shadow weeks — read, not built (the fifteen largest differences each Monday; D673's bar); F-987, `staff_send`, `order.lead_days`, the S335 small list, F-1023; Darpan's header line with the source-moving kit, after its mock and his yes.

**Lessons kept:** a walk's control row is the walk's own, found by key (F-998 — the (a) check first injected a buy for a supplier with a real buy that day); the install window is a gate, not a fault; read the live file at every line before carrying a review's list (three of nine were already built); the spine for an offline walk comes from a MargArchive tar (PHI — `_to_delete` at the close) through `spine_evidence.py` → `spine_build.py`.

**Numbers at this close:** session 350 · kit S644 · D785 · no F · session 353 reserved for the Sanjeevni chat. **Canon:** Register v5.188 · Archive v1.185 · Fault v2.172 (§7.106) · Runbook v268 (§2B) · Book v1.35 (§15Z) · `live_pins_S350close.txt` · `START_HERE_SESSION_353.md`.
