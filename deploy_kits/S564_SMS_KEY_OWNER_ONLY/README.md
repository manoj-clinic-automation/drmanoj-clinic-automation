# S564_SMS_KEY_OWNER_ONLY — the phone's key for the owner only

**Brief:** `claude_code_briefs/S564_SMS_KEY_OWNER_ONLY.md` (the parent, session 317, 15-Oct-2026).
**Why:** REPORT_S562, "Outside the brief": the *Phone setup — MacroDroid* fold on `/finance/bank-sms` printed the phone's door key
(`/root/finance/bank_sms.key`) to every login the page admits (the clinic and medical checkers), not only the owner.

## What it does (for the owner)
The phone's secret key on the bank-SMS page is shown to your login only. Shavez, Dr Bhawna and any other login that can open the
page no longer see the fold at all — no placeholder, no hint. The rest of the page is unchanged. Step 4 of the fold now says what
the phone really sends today: the SMS in a query parameter on the URL, plus a field named `from` carrying the SMS number.

## Files — pins FROM → TO (built on the box by `make_s564.py`, counted anchored edits on the live bytes)
| file | FROM | TO | edits |
|---|---|---|---|
| `/root/finance/bank_sms.py` | `053d4ccb85d64403daf9918a0ba6f46c` | `aa5278403ec85c898d808486e4c3cde3` | 4 |

Read only, must be at its pin: `/root/finance/bank_standin.py` `fd635862c75e1ab44f770a6ffd79511a` (`is_owner`).

The four edits: (1) an S564 note in the module text; (2) `page()`'s owner test made fail-soft (if `is_owner` cannot be read, the
login is treated as NOT the owner — the page still renders); (3) the fold, and the read of the key file, only `if owner:`;
(4) step 4's wording. The door `POST /finance/api/bank-sms` and the key file are not touched.

**Data step:** none. **Restarts:** `clinic-finance` only.

## Install (on the server)
```
rm -rf /tmp/s564kit && cp -rp /root/deploy/repo/deploy_kits/S564_SMS_KEY_OWNER_ONLY /tmp/s564kit && bash /tmp/s564kit/install_S564_SMS_KEY_OWNER_ONLY.sh
```
`DRY=1` runs every gate and the walks and writes nothing. `bash rehearse_s564.sh` rehearses on a made-up root with a made-up key file
(red-after-placing restore, green, ALREADY INSTALLED). The installer also removes S562's scratch `/tmp/s562kit` and `/tmp/s562probe`
after checking each holds no secret-shaped file, no copy of the key and no phone-shaped number.

## The walk (`walk_s564.py`)
The real finance app on scratch copies, each code folder in its own child process, a fixed clock, a made-up key file, made-up logins
(W564: a clinic checker, a medical checker, one with no role), made-up merchant tails for the door: (a) manoj — the fold and the key,
the new step 4, otherwise byte for byte the old page; (b) the two checkers — 200, no fold, no key, no key-file path, byte for byte the old
page minus the fold; staff-eye for shavez, bhawna, manoj, and no DUTY_MAP duty at this door; (c) a refused login still 403; (d) the door:
right key 200 stored, wrong / no key 401, as the old file; (e) `is_owner` raising — the page renders, no fold for anyone.
`--expect-red` on the old file: every `C:` check red. The walk prints counts, offsets and yes/no only — never page text or a key.

## Undo
```
\cp -p /root/finance/bank_sms.py.bak_S564_053d4ccb /root/finance/bank_sms.py && systemctl restart clinic-finance
```
