# S803_MARG_WATCH_BILLS — the Marg watch, Kit 1: bills changed after their day

*The Sanjeevni chat · session 438 · 12-Nov-2026 · the owner's "Go" 17:49 IST · plan `S434_MARG_WATCH_PLAN_v3.md` §0A row 1, §6, with D923–D928, D935, D936.*

**What it is.** One owner page — `https://followup.dr-manoj.in/finance/sanjeevni/marg-watch` (the doctor only). The same bill, seen in two Marg reports of the same period taken on different days: removed, added late, re-dated, or its lines changed. It reads the server's own name-free line tables (`purchase_line`, `mi_sale_line`) — never a raw Marg file. **Read-only on Marg and on every table that exists.** Section A (stock moved with no record) is Kit 2; the door's store rule (plan §4) is its own kit, next.

| file | change |
|---|---|
| `/root/finance/marg_billwatch.py` | **NEW** — the compare with the five noise rules; the page; View opens the Purchase bills page's own panel in the row (D936); his closes (D923). Its own tables `billwatch_seen`, `billwatch_act`; settings `billchange.since`, `.on`, `.sig` |
| `/root/finance/sanjeevni_approvals.py` | 569c5ee4 → TO — `init()` also mounts `marg_billwatch`, fail-soft (one block) |
| `/root/finance/owner_notice.py` | 537b7c32 → TO — the S803 block before the command-line guard: once he turns the notice on, a NEW changed bill is told once, opening the Marg watch; history is never told |
| `/root/finance/finance_ui/finance_approvals.html` | 6a4178ea → TO — the Sanjeevni Hub, *Go to ▾ → Purchases & dealers*: one link added, **Marg watch — bills changed after their day** |

**Not touched:** `purchase_app.py`, `provisional_s781.py`, `scan_register.py` (their functions are called, never changed), Marg, stock, `purchase_bill`, `purchase_line`, the scans.

**The rules.** Noise: (1) a part print is set aside whole, and a filtered first print is no baseline; (2) "added late" needs the bill dated 3+ days before the earlier report was taken; (3) paise — under one rupee — are for the record; (4) a renamed item is for the record unless both names still hold stock; (5) case and spaces in a bill number never make two bills. **Found on the live tables:** Marg's own purchase rate is re-set on old bills and moves Marg's "amount" column while the bill's net money stays — for the record (the plan's "11 small amount changes" were these). **D935:** a bill agrees with its paper to the rupee or it stays open. **D926:** a changed bill that now agrees with its paper, where the paper can tell the old entry from the new, is *Settled by the scanned bill* — by the Purchase bills page's own judgement, read. **D917:** a sale bill's money-only change is for the record.

**The install** (after the owner's publish), on the server:

```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s803kit && cp -rp /root/deploy/repo/deploy_kits/S803_MARG_WATCH_BILLS /tmp/s803kit && bash /tmp/s803kit/install_S803_MARG_WATCH_BILLS.sh
```

It rebuilds the two changed files from the box's own live bytes (`make_s803.py`), checks them against `TO_PINS.md5`, runs `walk_s803.py` (made-up rows; each noise rule proved with its own control) and its control on the live files, runs `proof_s803.py` on a copy of `finance.db` with the box's scans, places the three files, runs the **history fill** (everything found so far = *Before this page*, never announced), proves `owner_notice.py collect` runs clean, restarts `clinic-finance`, reads the journal, and walks the placed files. Any red after placing puts both files back and removes the new one. `DRY=1` before `bash` writes nothing.

**Undo (one line, printed by the installer):** the two backups back, `marg_billwatch.py` removed, `clinic-finance` restarted. The two tables and three settings stay; nothing reads them.

**The phone notice ships OFF.** He turns it on himself, on the page (*Phone notice of a newly changed bill: Off — Turn on*; `billchange.on`, `billchange.tell_from`). Turned on, it tells only a finding found after that moment, that counts, is open, he has not touched and its paper does not settle — once, one bill at most once in seven days, never more than six messages a day, between `owner_notice.hand_from` and `hand_to`. `/root/finance/_off/ALL_OFF`, `OWNER_NOTICE_OFF` and `owner_notice.on` stop it too. The page only reads.

**Proved offline (S438):** walk 74/74 GREEN in the device VM (68/68 of the R1 build also in the cloud), control RED on the live files; the proof on the 12-Nov database copy: 19 counted (11 changed, 1 removed, 7 added late), 4 settled by the scanned bill, 9 with no paper, 24 for the record, 2 part lists set aside; the installer rehearsed on a stand-in root (`rehearse_s803.sh` 8/8); the page headless at 1366 / 884 / 360 (no script error, nothing off-screen).

**Two cold reviews, both SAFE AFTER FIXES, every must-fix built and walked.** R1: a sale line carries Marg's rate per pack (its money is rate × quantity); a report of an older day that arrives late is history, never new. R2: one bill is told at most once a week (a change re-read from another report is the same news); the forward part rule drops "added late" only when the baseline held under a third of its bills, and says so in its own words; a sale line's rate is called a rate. Should-fixes built: financial year in a bill's identity and key; the paise rule without a percentage arm; the notice judged once in the tick, the part only reads; a row he closed is not pushed; a batch covers by the moment of judging. **R2's fixes were proved by the walk, not by a third review — which is why the notice ships off.**
