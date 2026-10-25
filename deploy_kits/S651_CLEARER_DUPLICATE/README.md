# S651_CLEARER_DUPLICATE — when two scans are one paper, the clearer one is kept (D761)

**Why.** D761 (the owner, 22-Oct-2026), F-992's scan-app half: Kedar A000211 was scanned three times — B-0157 (the bottom total
only, no item lines) was kept and B-0159 (the whole bill, three item lines) set aside. The rule for this project's files came from
the Sanjeevni chat (board message `sanjeevni_S339_1`): keep the scan with item lines over one with none, with guards. START_HERE_SESSION_352
B3. Board `_numbers` v691 → v692 (kit S651). Built in the Scan App chat, session 352.

**What changes.** Wherever two scans are decided to be one paper — the checker's **Duplicate** tap, the desk's **same paper** on a
held paper, the owner's **same** on Scan ka kaam, the server's sure double-scan rule and its after-reading check — the scan with item
lines is kept and the one with none set aside (`dup_of` the kept one; the reason names D761; both audited — `duplicate` and
`kept_clearer`; the scan_check_s441 verdicts follow). The words say so: *"B-0159 kept; B-0157 is set aside as its second scan."* Otherwise nothing changes (the older kept, as before).

**Where it applies.** The clinic's own lanes only — **not the pharmacy lane** (its copies are the Sanjeevni side's, whose order list
already reads the clearer copy of each family). Both scans read; the same lane, kind, document kind (a challan is never kept over
its bill), person (Dr MK / Dr Bhawna) and month (a month confirmed on either one alone blocks it).

**The guards — the swap happens only when the scan that would be given up is untouched:** not approved or already set aside; no joined page and not a page; not a rescan and none of its own; no other copy pointing at it; no record of
the scan app on it (any table with a `bill_id` — a machine, a procedure-room line or order role, stationery, a warranty, a payment);
nothing a person did to it after the scan (desk saves, joins, challans, payments, a group, kind, lane or month changed, a rescan,
*not a duplicate*, an earlier Scan ka kaam answer); no X-ray mark; and no link in the finance database — by id (`asset_bill_id`, `scan_bill_id`, `scan_id`, `done_bill_id`) or by stamp
(`scan_ref`, `stamp`), the columns read from the live schema (the 25-Oct nightly copy, read only, on manojz: no other column named
*scan*). When the finance database cannot be read, or has a column named *scan* the rule does not know, nothing is swapped; the
installer reads the live schema and refuses on such a column. **Papers already set aside stay as they are.** After a swap the
kept scan's amber and open question about the one set aside are closed and its verdict reads clear, so no later tap can set the
kept scan aside onto it; and no door sets a scan aside onto one already set aside onto it. The swap in `_mark_dup` runs inside a
savepoint: any error undoes it whole and the old rule applies. The paper then carries the kept scan's number too.

**Files and pins (FROM → TO).** `/root/shared/scan_checks_s441.py` `b9ba6839` → `10787cbf` (5 counted edits; VERSION S441.2:
`clearer()` and `settle_swap()`, used by `answer()` and the sure rule) · `/root/assetapp/asset_register.py` `068440f7` → `63a8b15b` (3: `_mark_dup`
returns the scan kept and swaps by the rule; the checker's words) · `/root/assetapp/sorting_desk.py` `ca9fda74` → `bb206e5d` (1: the
desk's words). `build_s651.py` in the kit (the installer applies it to the live bytes and needs the TO pins). No data step. The finance app reads `scan_checks_s441.answered_recent`
only — unchanged (the installer checks it still imports); it takes the new file at its own next restart. Read only, pinned:
`procroom.py f6578535`, `claude_reader.py 1277e80d`, `clinic_papers.py 89a3cd0a`, `asset_machine.py 7dbd5e0c`, `stationery.py
b6ce217a`, `batteries.py bb082b4c`, `xray_costs.py 5823bae2`, `claude_reread.py ed7023d2`.

**Kit.** `make_s651.py` · the three files · `walk_s651_app.py` (A0, D1–D9, D4b, D4c over 17 guards, R1, R2 on the real app, made-up papers —
each read one carries the reading's *filled* mark, as live — and a made-up finance database; `--expect-red` on the live files: only
A0, D1, D4c, D5, D6, D7, D8, D9 red) · `walk_s648_app.py` (the whole app
with the two new app files) · `install_s651.sh` · `rehearse_s651.sh` (R1–R8) · `PIN_*.txt` · `KIT_ID.txt` · `SUMS.md5`.

**Install (the owner, after publishing):** `cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S651_CLEARER_DUPLICATE/install_s651.sh`

**UNDO (one line):** `\cp -p /root/shared/scan_checks_s441.py.bak_S651_b9ba6839 /root/shared/scan_checks_s441.py && \cp -p /root/assetapp/asset_register.py.bak_S651_068440f7 /root/assetapp/asset_register.py && \cp -p /root/assetapp/sorting_desk.py.bak_S651_ca9fda74 /root/assetapp/sorting_desk.py && systemctl restart assetapp`
