# S965_VOUCHER_JUDGE — Marg's stock vouchers judged, on Stock check and the item ledger (built at Sanjeevni session 532, 26-Nov-2026)

**What he asked (D1083, D1086):** stock vouchers and unexplained moves flagged on the Stock check and the item ledger, with Marg's voucher number
and date; each voucher's lines inline, collapsed, expandable. **His "Ok" 20:30 IST on mock-up v5** (`https://claude.ai/artifact/W3U9BfeW9K5QKpsgZ6YoqF`,
fed by the real 26-Nov reports), with AD00010's two cut lines named from his Marg screen (photos 20:16–20:23 IST).

## The judge — NEW `/root/finance/voucher_judge.py` (read only; it writes nothing but the name table at install)
Marg's own Stock Issue / Stock Receive lines (S963/S964: `mi_voucher_line_now`) against every correction asked of Amir:
the count rounds' vouchers (`stock_voucher_line` + his typed number in `stock_voucher_entered`), his tap jobs that ask a STOCK ISSUE /
RECEIVE in their own words (`amir_job`), the Expiry watch's wrong-batch fixes (`stock_batch_fix`, a receive + an issue). Each ask is matched
to one Marg line — kind, item, units, on or after the ask (a day's grace), batch for batch for a fix; Amir's typed number claims its own line
first. Stages: exact · two corrections in one line · an unasked issue + receive that cancel (same item, batch, units, within 7 days) · a fix
keyed from the wrong batch · a different figure (more / less) · more-than-asked evened later by a job. Ask states: in Marg · waiting · Amir
said done, not in Marg · wrong batch · not as asked · Marg's batch figures agree, no voucher · before the reports · superseded. Line states:
asked · keyed twice · more / less · nobody asked · keyed and undone · wrong batch · evened · size not printed.
**Names:** Marg's report cuts a name at 15/20/24 letters; the full name is the one Marg item it fits (the newest whole closing + the stock of
record); a line his word named (`mi_voucher_name`, seeded: AD00010 lines 1–2 = KNEE IMMOBILIZER L UNISON / M TYNOR); else a one-item Stock
Register that holds the voucher; else "size not printed" on the page, and those items' registers are asked on his list (marg_billwatch's own
`reg_ask_item`, never twice). The closing-stock guess is NOT used (it would have missed AD00010's M TYNOR).

## The pages
* `stock_check.py` 26665c78 → v1.5: `GET /finance/stockcheck/api/vouchers` (the judge's page JSON, cached 60 s).
* `stock_check.html` 13e348a9: the two boxes on top — *Marg's stock changed — nobody asked* and *Corrections asked of Amir* (not in Marg ·
  not as asked · waiting · as asked, folded · keyed and undone · batch put right without a voucher) — each voucher's lines folded (D1086);
  F-1690: the one-item Stock Registers he took; every item row's tags.
* `item_ledger.py` d2f68ee9: inside the days the reports cover, the voucher rows are Marg's own lines (number, batch, judgment, **Voucher ▾**
  opens all its lines); Amir's typed numbers only outside them; the item's open asks above the ledger. The spine books no voucher (S704), so
  nothing is counted twice.

## F-1701 — `/root/marg_ingest/marg_vouchers.py` 92318068
A text the medical PC held and retried is named `RETRY__EXPORT__…`; `export_stamp` takes the export's own stamp (the second), `restamp` puts
every kept sheet on it — at install and at every five-minute collection (heal). **F-1702** (the medical PC's own report list, cosmetic) is
not in this kit: it needs the PC's Drive `_kit` folder, not connected this session — next Sanjeevni kit.

## Proof
`walk_s965.py` 32/32 on made-up data (twice on one layout); control red on the live files (no judge) and, with the judge alone, red on the
ledger checks. Rehearsal 10/10 on a made-up root (dry · red@4 · red@5 · install · again · undo · again · wrong FROM · lock · corrupt kit).
Live-shape (the real 26-Nov database copy, device VM only): 53 vouchers / 254 lines / 302 asks; nobody asked 3 (AD00010, L000031, and
AD00012's ROSIKA FORTE receive 12 -- asked only by a fix since superseded) · Amir said done, not in Marg 4 · not as asked 9 · waiting 13 ·
as asked 40 · cut 0 · named 2. The installer repeats it on a copy of the live database.

## Reviews
Cold review (a separate agent): NOT SAFE -- M1 a card done after the newest report's last day read 'not in Marg' (now: 'after the newest
report -- the next one decides'); M2 F-1701's stamp rule missed the real names `MEDICAL__RETRY__EXPORT__…` (fixed; the walk uses that shape).
SHOULDs built in: S3 those asks shown; S4 a superseded fix never claims a line; S5 each report's own period, a gap covered by none; S6 a size
family's new name before its split day stays on the old key (spine_build.Zd); S7 the cut-name list drawn; S8 only his roles make the register
asks, each asked once ever (mi_voucher_regask). NOTES 11, 13 fixed; 9, 10, 12, 14 noted (pack 1 fallback for an uncounted item's 'a:b' card;
the job-key prefixes; 'Amir's voucher' label on an unasked line; prefix links of three name pairs, harmless today).

## Install
His publish, then one server line (in the installer's head). marg_vouchers is placed under the Marg collection's own lock; clinic-finance
restarted. **Undo:** `bash /root/deploy/repo/deploy_kits/S965_VOUCHER_JUDGE/undo_s965.sh` (the four files back, the judge set aside; the name
table and the restamped times stay — nothing reads the first, the second only orders a retried sheet by its export).

**Second look** (a separate agent, on the fixed kit): every cold-review fix confirmed (S6's source text parsed as spine_build writes it; the
second `_require` call is pure; the commit is on the request's own connection; 19 real two-stamp names all read right). **M1**: a card done
on the newest report's export day, after the export, read red -- now 'after the newest report' (the newest covering report's own export day;
walk R1b). NOTES built in: a gap day reads 'no report covers its day' (N1); its own row tags (N2); a register ask lost to a busy database is
asked again (N3). Noted: the rules' two family keys get no Marg voucher lines (N4, as before this kit); a cut name fitting several items is on
no ledger until named (N5, none today).
