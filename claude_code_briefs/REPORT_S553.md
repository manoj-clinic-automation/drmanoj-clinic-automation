# REPORT S553_BHATI_SLIP_DUTY — 14-Oct-2026

**For the owner**
- Bhati's *Aaj ka kaam* list now has the line **"Physio slips register mein likhiye — reception ke hisaab se nahin mil rahi"**. It shows when his slip entries for a day (from 14-Oct) are missing or don't match the cash and UPI reception wrote for that day. Its button opens his Physio register on that day. The line goes away by itself once his entries match.
- It is live and working. You won't see it today: no day can be checked until today is over. The earliest it can appear is tomorrow morning, for today's slips.
- The old line *"Physiotherapy ka hisaab dekhiye: Theek hai"* (the tick in the petty book) is still on his list and now does nearly the same job. Switch it off on your panel if you no longer want it.

---

## For the chat

**Live files, FROM → TO, md5 read back on the box (05:59 IST, after the restart):**

| file | FROM (pin matched) | TO (read back) |
|---|---|---|
| `/root/finance/aaj_duties.json` | 2d6d30ebe73ff721d5591743c86eebb1 | cb8ac36aa60768216b82c918874a65af |
| `/root/finance/aaj_seed.py` | 156ded1ee17b852b4a30e94be453ca61 | a97cd07bfc7270184c62c16dff4dff48 |

The installer checked these files against their pins, unchanged: `aaj_kaam.py` cd232b1c987417aa07d341d498c5effc and `physio_book.py` 745130164014ec8d6f90cda839f5521b.
The kit was rebuilt on the box from the live bytes with `make_s553.py`: 1 counted edit to the duties file and 2 to the seed. The rebuild matched the kit byte for byte. The kit in the repository at 413305c passed `md5sum -c SUMS.md5` in `/root/deploy/repo`, and the installer ran from there.

**What was built:**
- `aaj_duties.json` gets an `extra` duty `bhati.physio_register`, copying the shape of `reception.docterz_consultation`: person bhati, kind sql, group open, allowed_days 1, tile Physiotherapy, door `/finance/physio/book`. It uses the brief's `hi`/`en` word for word, both with `{since}`. Its SQL is one read-only SELECT. It counts days D with `'2026-10-14' <= D < date('now','localtime')` where `clinic_physio_day` cash + UPI > 0 and Bhati's live clinic `physio_session` sums do not match reception's cash and UPI mode by mode. `since` = the oldest such day.
- Before writing the SQL in, I ran it read-only on the live database: (0, None). With the floor moved to 01-Oct, just to see it read real rows: (9, 2026-10-01). Query plan: index searches only.
- `aaj_seed.py` gets `ENGINE['bhati.physio_register'] = {'door': '/finance/physio/book?day={since}'}`. `day` is the parameter `physio_book.py`'s clinic tab reads. It also gets Bhati's panel line `when 'day'`, `on True`, opens Physiotherapy, placed after `bhati.petty_cash_match`. No other person's lines were touched, and `bhati.physio_tick` is unchanged.

**Calls I made (brief vs code):**
1. **The staff line has no day in it.** In `aaj_kaam.py`, `person_list` shows a panel line's `hi` exactly as written. Only the owner's English and the door get `{since}` filled in. Using the brief's wording on the panel line would have put a literal "{since}" on Bhati's screen. So the duty keeps the brief's `hi`/`en` with `{since}` (the owner's console fills its `en`), and the panel line Bhati reads is "Physio slips register mein likhiye — reception ke hisaab se nahin mil rahi". The button carries the day.
2. **A saved panel.** `aaj_kaam._merge` adds a new seed line to a saved panel **switched OFF**, marked new. It does not switch it on, which is what the brief assumed. So the kit has an idempotent data step, `cfg_s553.py`. If a saved `aaj_cfg` row for bhati exists, it adds the line to that panel switched on. If the owner removed the line, it stays removed. It touches nobody else. It moves `edited_at`, so a panel open on another screen reloads instead of saving over the line. **On the live box `aaj_cfg` does not exist yet, so it changed nothing.** The walk proves both behaviours on a made-up saved panel.
3. **The duty map.** The CLAUDE.md row was added to `claude_code_briefs/DUTY_MAP.md`. **`DUTY_MAP.json` was not changed**, and this is a decision for you: `aaj_kaam.build_all` reads both DUTY_MAP.json and aaj_duties.json, so the same id in both would show twice on the owner's console. The parent's other extra lines (`bhati.petty_today`, `reception.docterz_*`) are also only in aaj_duties.json. No Needs-you line: the duty has a door on Bhati's own home.
4. `.gitignore`: added the exact-path line `!deploy_kits/S553_BHATI_SLIP_DUTY/aaj_duties.json.kit`, as the brief asks. Note that the `.kit` name was never matched by `*.json`, so this line is a guard against a future rule change, not a fix.

**The walk** (`walk_s553.py`, on the box, scratch copies in /tmp; made-up March-2031 rows found by key; real finance app with header sign-in for that process only): **WALK OK S553: 26 checks green.**
- The duty's SQL as shipped was run at a fixed clock (the floor and `now` each replaced once). All made-up days: n = 2, since 2031-03-11. Day by day:
  - before the floor: never
  - no Bhati entries: due
  - ₹500 cash agrees: not due
  - cash agrees, UPI differs: due
  - a voided slip and a home visit are ignored
  - reception's 0: not due
  - today: never
- Moving the clock and the floor one day each makes n = 3 both times, so both exclusions really work.
- Signed in as bhati: the line shows under *Aaj* with door `/finance/physio/book?day=2031-03-11`, tile Physiotherapy, and the panel line's words.
- manoj `?as=bhati` shows it. alisha, shivani, reception, shavez, darpan, sukhveer, amir and manoj (`?as=`), and alisha signed in, do not.
- The console item: n = 2, `en` "Bhati: physiotherapy slips of 11…".
- **Staff-eye:** bhati's portal home (real `portal.py` + grants) carries Physiotherapy → /finance/physio. The door page as bhati shows "Milaan — 11-Mar-2031" and "Farq: Cash ₹ 250 · UPI ₹ 250".
- The saved-panel test passed: OFF and new before the data step, on after it. A second run changes nothing, a removed line stays off, and other people's rows are untouched.
- Once the entries agree, the SQL reads 0 and the line leaves.
- Static: no 10-digit number in the kit, Bhati's name never misspelt, the SQL writes nothing. This check went red once during the build because its own label held the misspelling. The label was fixed, which also shows the check can fail.

**Negative control** (the same walk on the old two files): 10 of 17 checks red, 7 of them the line checks. The duty is not in the file, it is on nobody's list, it is not on the console, the data step can't place it, and so on.

**Rehearsal** (`rehearse_s553.sh`, a made-up root with a stand-in service running the real app on port 18553): REHEARSAL OK.
- Red after placing: both files restored byte-identically, healthz 200, the DB backup kept, the lock released.
- Green: DONE.
- Second run: ALREADY INSTALLED.

**Install** (read from the program's output):
- Started 05:59:12 IST; clinic-finance active since 05:59:17 IST; exit 0 at 05:59:21 IST.
- Backups: `finance.db.bak_S553_20261014_055912` (backup API, mode 600), `aaj_duties.json.bak_S553_2d6d30eb`, `aaj_seed.py.bak_S553_156ded1e` (md5s read back = FROM).
- Restarted **clinic-finance only**. Everything that reads these files (`aaj_kaam`, `aaj_floor`, `owner_console`) runs in that process.
- healthz 200. `/finance/aaj`, `/finance/aaj/api/list` and `/finance/physio/book` answer 302 without a login, as expected. The journal was clean.

**As manoj, `/finance/aaj?as=bhati`** (real app on a copy of the placed box): page 200. The list API returned 200 with 3 lines on Bhati's list. **The new line is NOT shown, which is correct.** The duty's SQL on the live figures reads n = 0. Reception has no physio day from 14-Oct before today, and today is never counted. The first day that can be due is 14-Oct, checked from 15-Oct.

**Undo:** `\cp -p /root/finance/aaj_duties.json.bak_S553_2d6d30eb /root/finance/aaj_duties.json && \cp -p /root/finance/aaj_seed.py.bak_S553_156ded1e /root/finance/aaj_seed.py && systemctl restart clinic-finance`

**Not done, and why:**
- `bhati.physio_tick` was not switched off. The brief says it is yours to decide on your panel.
- DUTY_MAP.json was not changed (call 3).
- No physio table or `clinic_physio_day` was written.

**Noticed outside the brief (not touched):**
1. `physio_book.py`'s clinic tab accepts only today and the six days before (`BACK_DAYS = 7`). If a day stays unmatched for more than a week, the line's button opens today instead of that day, and Bhati can no longer enter or void slips for it. The line would then stay until reception's figure is changed, or until someone with a way to correct older days does so.
2. When the line is not due, the owner's panel shows its door with a literal `{since}` in it (`aaj_kaam._fill` only strips `/{since}`, not `?day={since}`). The register treats that as today. It is harmless, but visible on your panel.
3. The repository's PowerShell has no `git` on PATH. `PUBLISH_ALL.bat` finds GitHub Desktop's own git, so it doesn't matter.

**Repository:** published at 413305c, with the kit `deploy_kits/S553_BHATI_SLIP_DUTY/` (11 files incl. SUMS.md5, KIT_ID.txt, README.md), `.gitignore`, `claude_code_briefs/DUTY_MAP.md` and the brief. This report follows in the next publish. The NO_PHONE_NUMBERS gate was clean.
