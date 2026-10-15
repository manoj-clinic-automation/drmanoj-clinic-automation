# REPORT S564_SMS_KEY_OWNER_ONLY — 15-Oct-2026

The phone's secret key on the bank-SMS page is now shown to your login only. Shavez, Dr Bhawna and any other login that can open the page no longer see it; the rest of the page is unchanged.
Installed at 16:48 IST (read from the installer) and checked: your login sees the *Phone setup — MacroDroid* fold with the key; Shavez and Dr Bhawna get the same page without that fold. Step 4 of the fold now says what your phone sends today.

---

## For the chat

**Kit:** `deploy_kits/S564_SMS_KEY_OWNER_ONLY/` (make_s564.py, walk_s564.py, install_S564_SMS_KEY_OWNER_ONLY.sh, rehearse_s564.sh, README.md, KIT_ID.txt, SUMS.md5). The run was the kit copied to `/tmp/s564kit` (`md5sum -c SUMS.md5` OK), byte-identical to the repository's.

### Pins — read back on the box after placing
| file | FROM | TO (read back) |
|---|---|---|
| `/root/finance/bank_sms.py` | `053d4ccb85d64403daf9918a0ba6f46c` (= brief) | `aa5278403ec85c898d808486e4c3cde3` |
| `/root/finance/bank_standin.py` (read only) | `fd635862c75e1ab44f770a6ffd79511a` (= brief) | `fd635862c75e1ab44f770a6ffd79511a` unchanged |

Four counted anchored edits on the live bytes (each anchor exactly once, built in memory, TO pin checked): (1) an S564 note in the module text;
(2) `page()`'s owner test wrapped fail-soft (`is_owner` raising → `owner = False`); (3) the fold, and the `_key()` read, only `if owner:` —
for anyone else nothing at all is drawn; (4) step 4 → *"What the phone sends: the SMS `[sms_message]` in a query parameter on the URL, plus a field
named `from` = `[sms_number]` (the SMS number) — the macro as set on 15-Oct-2026."* Step 5 (the S439 note of the field names the door reads) is
unchanged. The door `POST /finance/api/bank-sms` and the key file are untouched.

### The walk (on scratch copies on the box, a made-up key file, made-up W564 logins) — 20 checks green
- a — manoj: 200, the fold once with the key, the new step 4; byte for byte the old page with only step 4 changed.
- b — `w564_clin` (clinic checker) and `w564_med` (medical checker): 200, no fold, no key, no key-file path, no key header name; byte for byte the old page minus the fold.
  Staff-eye: the real shavez and bhawna 200 as before, no fold, otherwise the old page; no DUTY_MAP duty (50 read) has `/finance/bank-sms` as its door.
- c — `w564_view` (a medical viewer only) 403 as before; `w564_none` (no role) 302 to /portal by the finance gate, as before.
- d — the door, new file and old file alike: right key → 200 stored (clinic and Sanjeevni); wrong key → 401; no key → 401.
- e — `is_owner` raising: the page renders 200 for manoj and for a checker, no fold, no switch offered.
- **Negative control** (the same walk on the old file): **10 of 10 `C:` checks red** (the key shown to every checker and to shavez/bhawna; the old page fails with 500 when `is_owner` raises).
- Rehearsal on a made-up root with a made-up key file: forced red after placing → file restored byte-identically (exit 1); green; second run ALREADY INSTALLED — `REHEARSAL OK S564`.

### The look after install (the placed file copied, a copy of the live database, the real key file, the walk's own session; counts/yes-no only)
manoj 200, fold yes, the key on the page yes · shavez 200, fold no, the key no · bhawna 200, fold no, the key no — `PAGE OK S564`.

### Backups, restart, health
- `/root/finance/finance.db.bak_S564_20261015_164837` (sqlite backup API, mode 600) and `/root/finance/bank_sms.py.bak_S564_053d4ccb` (md5 = FROM).
- Restarted **clinic-finance only**, at 16:48:50 IST; active; `/finance/healthz` 200; `/finance/bank-sms` 302 without a login (the login gate, expected); journal clean.
- Housekeeping: `/tmp/s562kit` (7 files) and `/tmp/s562probe` (7 files) checked — no secret-shaped file, no copy of the key, no phone-shaped number — removed.
- Build lock `/root/deploy/.claude_code_build.lock` held (owner S564) from 16:45:48 IST until after this report and the publish.

### Undo
```
\cp -p /root/finance/bank_sms.py.bak_S564_053d4ccb /root/finance/bank_sms.py && systemctl restart clinic-finance
```

### Decisions where the brief is silent
- **The owner test made fail-soft for the whole page**, not just the fold: the live line `owner = bool(BS is not None and BS.is_owner(con, u))` would raise and take
  the page down (the control shows 500), so walk (e) could not pass without it. If `is_owner` cannot be read, the page now also hides S562's switch and the difference
  column (both follow `owner`) — they are safe-side for a non-owner. With `is_owner` working, nothing else changes (walk a/b: byte for byte).
- **Made-up checker logins carry a medical viewer row.** The finance front gate sends a login with no role on its own unit to /portal (302) before the page is reached;
  the real clinic checkers (shavez, bhawna) have a medical *viewer* row, so `w564_clin` was given the same. The "login the page refuses" is a medical viewer only (403, the
  page's own refusal); a login with no role is still sent away by the gate (302) — both as today.
- **Step 4 wording:** the brief names the query parameter but not its name; the stored refusals show the phone posting a bare query with no field name, so step 4
  says "in a query parameter on the URL" and names no parameter.
- **No duty change**, so DUTY_MAP.md/.json are not touched (no duty has this page as its door).
- My own probe folder `/tmp/s564probe` (counts and status lines only, no key, no SMS text) was removed at the end; the kit copy `/tmp/s564kit` is left for the next kit's housekeeping, as with earlier kits.

### Outside the brief (noticed, not touched)
- None new.

### Cost
About US$2.5 of API credits at the time of writing (read from the session's budget line).
