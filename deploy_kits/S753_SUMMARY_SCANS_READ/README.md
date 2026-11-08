# S753_SUMMARY_SCANS_READ — the summary scans, read right (Sanjeevni session 408, 08-Nov-2026)

**The owner's word (17:19 – 17:32 IST 08-Nov):** staff scan a dealer's month summary on the pharmacy lane like any bill, tick or no tick — the system recognises it (the Scan App's half, asked by `S408_SCANAPP_PROMPT_SUMMARY_READ.md`). The dealer's printed name first; when none is printed, the bills on the paper name the dealer — *a fallback*. Never the pharmacy itself. The month from the bills listed. A complete statement is never "page 2" (the Scan App's). The count of bills beside their total on the viewer. **This kit is the Sanjeevni half — two files of this project, READ ONLY changes, no table, no writer.**

## What was wrong (read live 17:16 IST, as the doctor)
- Every summary scan on row 7 — the folded viewer and *Open the scan in a new tab* — answered **404 "Yeh scan nahi mila"**: `/api/s738/scan/<id>` (`_s446_file_bytes`) served only `kind='Pharmacy'`; S750 had landed summaries as `kind='Summary'` and its walk never opened one.
- **Daanshi B-0303** read with vendor *SANJEEVNI MEDICOS* (the buyer) and the printed "as on 02-11" as its date: counted under November, no dealer; Daanshi *awaited* for October.
- **L.K. Drug House B-0296** prints no seller name (the Scan App set it aside as Janta's page 2 — its half).

## What changes (make_s753.py on the live bytes fdb0960f / 262cafd3 → the TO pins in TO_PINS.md5)
- `purchase_app.py`: `_s446_file_bytes(sid, kinds=("Pharmacy",))` — the s738 door passes `("Pharmacy", "Summary")`. The doctor opens any; Amir only a scan on his list (`s738_scan_ok`, unchanged) — a Summary is never on it. `/api/scan-file/` (Amir's download) is unchanged.
- `scan_register.py` — `s750_summary_scans`: the lines are read first; the month = the majority month of the *bill* lines' dates (`_s753_lines_month`), then period_to, then reception's month, then the scan's; a tie falls through. `_s750_dealer_of`: both candidates pass `_s753_not_us` (the pharmacy's own name is never a dealer); when no name matched, `_s753_dealer_by_bills` — each bill line's exact paise amount looked up in `purchase_bill`, the number matched by `_s753_same_no` (equal digits when either is short; a tail when both are long — a 'Z-1' never claims every number ending in 1); the one dealer with the most matched lines wins, a tie is nobody (the owner picks, as before). `s["dealer_by_bills"]` marks it. The unknown row's name never carries our own name. `_s750_panel`'s footer: `12 bills ₹65,357` (`1 bill` singular) and *dealer named by its bills*.
- The owner's pick (`s750_dealer_of`) still stands first; every S750 word, table and door is unchanged.

## Proof
- `walk_s753.py` = S750's walk whole (its 82 S750 checks stay green) + the S753 section: the viewer 200/PDF for the doctor, 403 for Amir, 404 unknown; Daanshi's statement read as the buyer under November → October, Daanshi, agrees; L.K.'s nameless statement → L.K. by its two bills; a bill two dealers hold → nobody; the buyer's name with no Marg bill → nobody and the row never says Sanjeevni; a two-month tie → the period; `3 bills ₹5,237`, `1 bill ₹7,978`, *dealer named by its bills*. **GREEN** `walk_s753: 0 check(s) failed (0 of them S753 checks, 0 S750 checks)`; **CONTROL on the live files** `10 check(s) failed (10 of them S753 checks, 0 S750 checks)`.
- The earlier kits' walks on the TO files (S750, S749, S740, S738, S736): the same reds as the live files, none new.
- `proof_s753.py` (read only, both databases `mode=ro`): every summary scan on the box — stamp, month, dealer, state, bill count, whether the viewer opens it, *dealer by its bills*, *month by its bills (printed …)*, *the paper names the BUYER* — by the live files and by the kit's. The installer prints both whole.
- `rehearse_s753.sh` on a made-up root: setup · dry · real · again · red (the forced red at [7/7] restored the FROM bytes) — all ok, 08-Nov 17:5x IST.

## The owner's lines (after his publish)
DRY first (nothing written; the proof printed by both — read it before the real line):
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s753kit && cp -rp /root/deploy/repo/deploy_kits/S753_SUMMARY_SCANS_READ /tmp/s753kit && DRY=1 bash /tmp/s753kit/install_S753_SUMMARY_SCANS_READ.sh
```
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s753kit && cp -rp /root/deploy/repo/deploy_kits/S753_SUMMARY_SCANS_READ /tmp/s753kit && bash /tmp/s753kit/install_S753_SUMMARY_SCANS_READ.sh
```
Gates: SUMS · KIT_ID · the window 04:00–23:30 IST · the build lock · the two live pins · the rebuild to the TO pins (both pythons compile) · the walk green · the control red as expected · the earlier kits' walks (no new red) · the proof by both · health. After placing: `clinic-finance` restarted, health, the pages refuse a stranger, the journal (new PIDs only), the walk and the proof on the placed files; a red puts the FROM bytes back. Backups `*.bak_S753_<from8>` beside the live files; the undo line is printed.

**What the owner sees after:** row 7's viewer opens every summary; *Scanned 08-11 15:11 · 12 bills ₹65,357*; Daanshi counts under October by its bill (once the Scan App's half or a re-read gives B-0303 a dealer name — until then this kit names it by its bill A000217 and says so). L.K.'s B-0296 reaches row 7 only after the Scan App's one-off brings it back from *set aside*; it will then read 1–15 October, its three later bills not on its paper.
