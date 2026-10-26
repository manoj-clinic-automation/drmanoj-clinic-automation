# S661_RESTORE_DRILLS — the IN side of the backups, exercised every week · the parent · session 357 · 26-Oct-2026

**For the owner, in three lines.** Until today every backup was proven only on its way OUT — the bytes left the server and Google held them — and never once pulled back and opened. This kit adds two small drills that do exactly that every Sunday night: the code copy is pulled back, unpacked and held to the live server; the locked copy of everything that matters (case packs, consents, the ring card, patients' messages, the staff stores) is pulled back, **unlocked with the key as it is today**, unpacked, and every database inside is opened and checked. The finance database's own drill (which existed but was run twice in two months) now runs weekly too. The install runs both new drills once, for real, before it calls itself done — if either fails, everything is put back and that failure is the week's finding. Four new rows on the health page; one row (Bhati's bill photos) parked, because no photo has ever existed.

## Why — the weekly audit, run 9 (slice 4, 26-Oct-2026), answered
| ask | answer here |
|---|---|
| **AF-15** (carried since 14-Sep): restore surface 0% exercised | `verify_restore_code.py` and `verify_restore_state.py` (NEW, siblings of S230's `verify_restore.py`): weekly by cron, Sunday 02:20 and 02:35; the finance drill joins them at 02:10; the first run of each inside this install |
| **AF-32**: the code bundle (01:35) and the Sheets pull (01:45) had no freshness leg | two `log_mtime` legs, 26 h |
| **AF-33**: the petty-photo leg green forever on an empty lane | the petty book has never held a photo (0 of all entries, read on the 26-Oct database copy): the leg is **parked** (`disabled: true`) with the reason, not deleted |
| **AF-34 / AF-30**: five pinned-LIVE files in no nightly store | the code bundle gains `/usr/local/bin/clinic-doctor`, `/root/portal/static_inbox/*.js`, `/root/assetapp/static/*.js` and `root/deploy/clinic_doctor.py` (DEPLOY_ALLOW); the encrypted bundle gains the three CONFIGS the code bundle's `*.conf` wall keeps out — the website `.htaccess`, the followup `vhost.conf`, the watchdog drop-in. The installer proves all five present on the box first (a named source that is absent would refuse the state bundle's night, FATAL 41) |
| **AF-16** (monthly copy's retake on growth) | **not in this kit** — a change to the writer's monthly logic; its own kit later |

## Files — FROM → TO (every edit anchored; `make_s661.py` rebuilds the three TO files from the live bytes and stops on any other md5)
| live file | FROM | TO | what |
|---|---|---|---|
| `/root/state_backup/verify_restore_code.py` | — | 75e64dd3 | NEW. Downloads the `code_nightly.tar.gz` slot, md5 vs Drive, untars (safe members), every member vs the bundle's MANIFEST, then vs the live file on the box (equal / differs / absent — differs is a report, the box moves daily; FAIL = download, md5, untar or MANIFEST). State `verify_restore_code.state.json`, one summary line. `--dry` = conf, folder, slot; no download. Read-only on Drive. |
| `/root/state_backup/verify_restore_state.py` | — | 5fa0108a | NEW. Downloads `clinic_state_nightly.tar.gz.enc`, md5 vs Drive, decrypts with the box's `ENC_KEY_FILE` (the writer's exact openssl invocation), untars into a 0700 dir, inventory rows vs contents, `PRAGMA integrity_check` on every database (one bad = FAIL), the bundle's own taken-at. **The plaintext is patient data: never listed file by file, deleted in `finally` unless `--keep`.** `--dry` = conf, key (mode 600), openssl, a fixture round trip, slot. Read-only on Drive. |
| `/root/state_backup/code_bundle.py` | 37a5a132 | d6f94b12 | v1.9: three SOURCES entries + one DEPLOY_ALLOW line (never an edit to an old entry) |
| `/root/state_backup/clinic_state_backup.py` | f315bf43 | facfb897 | SRC_FILES + the three configs |
| `/root/finance/freshness_legs.json` | 9df66934 | b6cfacf3 | + 4 legs (code bundle restore drill 200 h · state bundle restore drill 200 h · code bundle (off-box) 26 h · Google Sheets pull 26 h); finance restore drill 4400 h → 200 h; petty leg parked. 38 legs, names unique |
| crontab | — | +3 lines tagged `# S661_RESTORE_DRILLS` | `10 2 * * 0` finance drill · `20 2 * * 0` code drill · `35 2 * * 0` state drill (all `/root/wa/venv/bin/python3`) |

No service restarted. No data step.

## Proven (S357)
- **Offline tests `test_s661.py`: 45 of 45 green** — the code drill PASSES on a good bundle and counts equal/differs/absent against a fake root; a corrupt gz → FAIL; a Drive md5 mismatch → FAIL; the state drill PASSES on a good encrypted bundle; wrong key → FAIL; a corrupt sqlite member → FAIL (db_bad 1); `--dry` on both without network; no member name or key path in any log; **a bundle built by the REAL `code_bundle.build()` → PASS, all equal; a bundle gathered, tarred and encrypted by the REAL `clinic_state_backup` functions → PASS**. Read-only on Drive: no `update_content`/`patch_meta`/PATCH/PUT/POST outside the header comments.
- The new SOURCES entries gather the four files on a fake root (and the deploy wall still drops a file not on DEPLOY_ALLOW).
- **The installer rehearsed on a made-up root** (stubbed crontab): DRY green; the full run placed and read back, backed up and appended the three crontab lines and read them back, released the lock; run again → ALREADY INSTALLED; **a refused crontab write after placing → everything put back** (three files at FROM, the two drills removed, 0 tagged lines).
- **Not provable off the box:** the two preflights against the real conf and the first real drills — the install does both (steps 5 and 8) and stops or restores on red.

## Install (on the server, after the publish; the window is 08:02–23:49 IST; the first real drills run inside it, 2–5 minutes)
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s661kit && cp -rp /root/deploy/repo/deploy_kits/S661_RESTORE_DRILLS /tmp/s661kit && bash /tmp/s661kit/install_S661_RESTORE_DRILLS.sh
```
## Undo (the installer prints it with the exact backup names)
```
\cp -p /root/state_backup/code_bundle.py.bak_S661_37a5a132 /root/state_backup/code_bundle.py && \cp -p /root/state_backup/clinic_state_backup.py.bak_S661_f315bf43 /root/state_backup/clinic_state_backup.py && \cp -p /root/finance/freshness_legs.json.bak_S661_9df66934 /root/finance/freshness_legs.json && rm -f /root/state_backup/verify_restore_code.py /root/state_backup/verify_restore_state.py && crontab /root/finance/crontab.bak_S661_<stamp>
```
