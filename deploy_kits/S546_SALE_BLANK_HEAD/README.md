# S546_SALE_BLANK_HEAD — the medical PC's sale reader takes a bill with no payment word, and a batch with a space

**Project:** Sanjeevni. **Made by:** the Sanjeevni chat (session 312, 13-Oct-2026) at the owner's "yes" (10:00 IST) to the cause found at 09:5x. **Touches:** Drive `ToMedical\_kit\marg_txt.py` and `KIT_MANIFEST.txt` — and through them the medical PC's `D:\SendToClinic\marg_txt.py`. Nothing on the server, nothing on manojz.

## Why
The 12-10 DAILY SALES text was refused twice by the medical PC (09:23:30 and 09:23:42 IST, 13-Oct): *"line 43: a bill row whose payment head is not where the header says"*. Bills A004143 and A004144 carry a blank D.R. field (the owner: A004143 Rs 1,000 cash + Rs 418 UPI; A004144 Rs 860 UPI) — the first such bills in about 1,500 since June. Behind it, line 189 (MEG QCS, batch `TSF E1222`) would have refused next: a batch with a space in it. The closing stock of the same morning was taken (no payment column).

## What changed in `marg_txt.py` (S490 7fa5136d -> S546 a59a222faf32a72ccc19c8635955cf8d)
- A bill row whose D.R. field is blank (or Marg's lone `#`) after a space is read; its six amounts as on every bill; its D.R. cell `""` or `#`. A D.R. field holding anything else not starting at the head's column still refuses (a shifted `.CASH`, a description run into it).
- An item line's batch is the rest of the line when its words are one space apart (`TSF E1222`); two or more spaces inside still refuse.
- `VERSION = "S546"`; the docstring's S546 paragraph; six new selftest checks.
- Nothing downstream reads the D.R. word: `marg_report` and the spine's `marg_read` take cash from the CASH column and the rest of NET as non-cash.

## Proof (run by the chat on manojz)
- `--selftest`: SELFTEST OK (all earlier checks plus 6 S546 checks).
- 106 kept texts (`_captured_txt` and `_captured_txt\refused` mirror): 98 taken by S490 convert to the SAME bytes under S546, 0 different, 0 lost; 6 refused by both; 2 newly taken = the two 13-Oct sale texts (184 rows, md5 62118a33).
- The converted 12-10 sale read by the spine's `marg_read.read_file`: SALE_BILLWISE, all six checks true (GRAND TOTAL = bills' gross, footer count, every DAY TOTAL, line numbers, dates, every row classified), 0 anomalies.

## Delivery — 13-Oct-2026 10:03:24 IST, by the chat through the file tools (folder access granted by the owner)
FROM pins read first: Drive `marg_txt.py` 7fa5136d, `KIT_MANIFEST.txt` a0bf263b (S499's). Backups beside them, read back: `marg_txt_S490.py.superseded` (7fa5136d), `KIT_MANIFEST_S499.txt.superseded` (a0bf263b). Placed `marg_txt.py` first, then the manifest (CRLF, md5 0bf248e43381bd27f6d011648b8405ee; three comment lines and the reader's md5, nothing else); both read back at TO.

## What followed
The medical PC's heartbeat of 10:19:14 IST reads `marg_txt.py up to date (a59a222f)`. The watcher re-reads the reader on its next conversion (no restart: RESTART_FOR is marg_watch.py only). The two refused 13-Oct texts are offered again at the watcher's next start (within 3 days); a fresh export of the 12-10 DAILY SALES is taken at once.

**Landed:** the fresh export of the 12-10 DAILY SALES was captured 10:40:39 IST 13-Oct and TAKEN 10:40:43 as SALE_BILLWISE VERIFIED (md5 62118a33, byte-identical to the chat's own conversion of the refused text). Findings: F-892 (repaired by this kit), F-893 (the refused-report road, open).
