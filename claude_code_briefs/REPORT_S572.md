# REPORT_S572 — S572_TWO_MORE_LINES (16-Oct-2026)

**For Dr Manoj (plain English):**
- Amir's card now has the two more jobs, under *Ek baar ke kaam*, each with a *Kar diya* button: "FOLITRAX 15 MG TAB — Marg mein STOCK ISSUE kijiye: 1 patte + 1 goli" and "OSTOVAXL DM — Marg mein STOCK ISSUE kijiye: 4 goli". They sit below KT ROS DT and VINBACTUM DS, so there are four in all.
- Before adding them, I confirmed the stock check still says these two lines do not agree with Marg. It tested fine on a copy first. Then the jobs went into the live data at 13:52 IST, after a backup.
- Nothing else on his card changed, no program changed, and nothing was restarted.

---

## 1. The assertion before inserting (read only, `/finance/stock/api/pad/hub/1` as owner, on a backup-API copy; read 13:52:46 IST by `live`, and the same at 13:50 and 13:52:14)
```
proof: state now stage C; text "Stage C: lot 3 — 4 voucher(s) do not agree with Marg's closing of 15-10-2026"
wrong row: FOLITRAX 15 MG TAB need -6 (-1 patte + 1 goli) moved 0.0 (0 patte) packing 1*5 closing 15-10-2026 keys ['2|ISSUE|7']
wrong row: KT ROS DT need -101 (-6 patte + 11 goli) moved 0.0 (0 patte) packing 1*15 closing 15-10-2026 keys ['2|ISSUE|8']
wrong row: VINBACTUM DS need -25 (-25 nag) moved 0.0 (0 nag) packing 1*1 closing 15-10-2026 keys ['2|ISSUE|17']
wrong row: OSTOVAXL DM need 21 (+2 patte + 1 goli) moved 25.0 (+2 patte + 5 goli) packing 1*10 closing 15-10-2026 keys ['5|RECEIVE|3']
qty_words(6, 1*5) for FOLITRAX 15 MG TAB = '1 patte + 1 goli' (the brief: '1 patte + 1 goli')
qty_words(4, 1*10) for OSTOVAXL DM = '4 goli' (the brief: '4 goli')
```
Both lines are still wrong with the brief's numbers, and `qty_words` (`/root/finance/qty_words.py 706db7cc…`, `words(n, packing, lang="hi", name=item)`) gives the brief's words. So both rows were added with the brief's text.

## 2. The walk (`add_jobs_s572.py walk`, box, 13:52:14–13:52:38 IST; the same file as in the kit, md5 `19768f68…`)
Backup-API copies of finance.db and spine.db. A **walk-only portal**: a random secret and its own user store in the scratch folder, with the live `portal_config.py` and user store never copied. Amir signs in through the portal, and his cookie is the only auth the card sees.
```
GREEN W1  the proof still names both lines wrong with the brief's numbers; qty_words = the brief's words
GREEN W4  amir signs in as 'amir'; the tile 'Amir ka kaam' is on his home
GREEN W5  /finance/amir -> 303 -> /finance/amir/step/1 200
GREEN W6  the door /finance/amir/step/6: 'Ek baar ke kaam' shown
GREEN W7  'FOLITRAX 15 MG TAB — Marg mein STOCK ISSUE kijiye: 1 patte + 1 goli' / '6 Sep ki stock ginti · voucher 8 ki line' / Kar diya (tap:11)
GREEN W7  'OSTOVAXL DM — Marg mein STOCK ISSUE kijiye: 4 goli' / '6 Sep ki stock ginti · receive voucher 6 ki line' / Kar diya (tap:12)
GREEN W8  DUTY_MAP amir.marg_jobs due_sql: n 2 -> 4 (+2)
GREEN W7b the four lines under Ek baar ke kaam: S569's two + these two (4)
GREEN W12 S569's rows untouched (byte-equal before/after) [9, 10]
GREEN W9  nothing else on his card changed: 6 segments added (2 x line, sub-line, Kar diya), none removed
GREEN W9b /finance/amir: no other change
GREEN W2  2 rows, the brief's shape;  GREEN W3  2 job_added by system {"kit": "S572", "owner_word": "16-Oct 13:47"}
GREEN W10 a second run: ALREADY x2, rows and audits unchanged;  GREEN W11 no verdict / "check" / "chhoot" words (D708)
CONTROL (the same card checks on the card without the two rows = the old state): W7 RED, W7 RED, W8 RED -> RED as it must
WALK GREEN: 0 red; control ok
```

## 3. Live (`add_jobs_s572.py live`, 13:52:46–13:52:57 IST, under the build lock)
```
backup: /root/finance/finance.db.bak_S572_20261016_135251 (38580224 bytes, integrity ok)
before: amir_job rows 10; DUTY_MAP amir.marg_jobs due [2, '2026-10-16']
row id 11 key 'fix:S572:FOLITRAX 15 MG TAB' kind tap subject 'FOLITRAX 15 MG TAB' created_at = show_from 2026-10-16 13:52:51 created_by S572
          text_hi 'FOLITRAX 15 MG TAB — Marg mein STOCK ISSUE kijiye: 1 patte + 1 goli' | sub_hi '6 Sep ki stock ginti · voucher 8 ki line'
row id 12 key 'fix:S572:OSTOVAXL DM'        kind tap subject 'OSTOVAXL DM'        created_at = show_from 2026-10-16 13:52:51 created_by S572
          text_hi 'OSTOVAXL DM — Marg mein STOCK ISSUE kijiye: 4 goli' | sub_hi '6 Sep ki stock ginti · receive voucher 6 ki line'
audit 937 / 938  at 2026-10-16 13:52:51  who system  action job_added  detail {"kit": "S572", "owner_word": "16-Oct 13:47"}
after: amir_job rows 12; DUTY_MAP amir.marg_jobs due [4, '2026-10-16']; S569 rows unchanged True
read-back (a copy taken after the insert), amir's door /finance/amir/step/6 200, 'Ek baar ke kaam':
  KT ROS DT … 6 patte + 11 goli · VINBACTUM DS … 25 nag · FOLITRAX 15 MG TAB … 1 patte + 1 goli · OSTOVAXL DM … 4 goli — each with 'Kar diya'
LIVE DONE
```
All other fields of the two rows are NULL. Afterwards: `/finance/healthz` 200. `stock_app.py 050587dfb5951da65f95937615ddf144` and
`amir_day.py 73882a8391fde24f31e07b0191c5bd89` were the same at the open (13:50) and after. **No `.py` changed, no service restarted.**
**DUTY_MAP not changed**: the duty is the existing `amir.marg_jobs` (tile *Amir ka kaam*, door `/finance/amir/step/6`, marker *Ek baar ke kaam*).

## 4. Charter, numbers, lock
- Kit `deploy_kits/S572_TWO_MORE_LINES/`: `add_jobs_s572.py 19768f68…`, `README.md`, `KIT_ID.txt`, `SUMS.md5`. It is S569's script with one change:
  the assertion reads the owner's proof (`proof.C.wrong`) instead of the voucher cards, as the brief asks. It also adds W7b/W12 for S569's two lines.
  There is no install `.sh`, since the kit is data only, the same shape as S569.
- Board `_numbers` v456 → v457: not reachable from Claude Code. **The chat should append S572's DONE line**: data only, amir_job ids 11 and 12,
  audit 937–938, backup `finance.db.bak_S572_20261016_135251`, live 16-Oct 13:52 IST.
- Build lock `/root/deploy/.claude_code_build.lock` taken at 13:52:10 IST (owner S572_TWO_MORE_LINES). **Released at 2026-10-16 13:54:09 IST** (read on the box) with `rm …/owner; rmdir …`.
- Published with `PUBLISH_ALL.bat`: commit `378f857` (NO_PHONE_NUMBERS clean, 38 files). That commit also carried files another chat had left pending: the S571 kit, `REPORT_S571.md`, `S571_FIX1.md` and this brief. `/root/deploy/repo` was pulled to `378f857`, and `md5sum -c SUMS.md5` gave OK for every file. The kit's `add_jobs_s572.py` is byte-identical to the copy that ran (`19768f68…`). healthz 200 at 13:54. This line is published by a second `PUBLISH_ALL.bat`.
- Box scratch: the scripts delete their own database copies. The pre-look's copies in `/tmp/s572probe` were deleted by the script. Code only remains in `/tmp/s572kit` and `/tmp/s572probe`.
- Seen, not touched (outside the brief): as S569 noted, Amir's four `category` jobs (ids 1–4) still have `show_from` NULL.
  Also, `qty_words` writes "1 patte" for a single strip (plural form). It is the estate's own speller, and the brief says to use what it returns.
