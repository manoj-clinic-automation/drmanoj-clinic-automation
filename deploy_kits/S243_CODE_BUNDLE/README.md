# S243_CODE_BUNDLE -- the live code gets a nightly off-box copy

**Built at Session 243, 12-Sep-2026. v1.1 and v1.2 on 13-Sep-2026 after the first live bundle was inspected -- see "The 07:19 finding".**

## The gap this closes

`/root/finance/finance_app.py` on the VPS is a base plus twelve patches applied
on the box. That exact file -- and the assembled portal, Marg ingest, WA
console, staff register -- exists nowhere but the box. GitHub holds the kits,
not the result. `finance.db` has had a nightly off-box copy since S213
(`finance_drive_backup.py`, cron 01:40); the code that reads it had none.

This kit gives the code the same leg, by the same mechanism:

```
01:35  code_bundle.py run   gather code -> code_nightly.tar.gz (+ MANIFEST.md5, crontab.txt)
                            -> self-verify against the manifest
                            -> keep /root/state_backup/code_nightly.tar.gz (overwritten)
                            -> OVERWRITE the owner-owned Drive slot code_nightly.tar.gz
                            -> read back Drive's md5Checksum, compare, stamp description
01:40  finance_drive_backup.py run   (S213, unchanged)
```

## What is reused, not rewritten

The Drive half of `code_bundle.py` is lifted from the live
`finance_drive_backup.py` (S213 v2, pin `14b406773de7f196abb105114f346080`):
`load_conf`, `find_sa_json`, `make_session`, the `Drive` class
(`list`, `update_content`, `get`, `patch_meta`, `revisions`), `md5_file`,
`_connect`, and the shape of `list` mode. Same conf
(`/root/finance/drive_backup.conf`: `SA_JSON`, `FOLDER_ID`), same key
discovery, same folder, same update-in-place with read-back. A service account
has zero Drive quota (proven live at S213), so the slot file must be created
once from the owner's account; the job then overwrites its content forever.

## What goes in, what never does

Included: `/root/finance` (py sql html sh) and `finance_ui/*.html`;
`/root/portal` (py html json, minus any name containing `users` or `secret`);
`/root/marg_ingest` (py json) and everything under `lib/`; `/root/wa/*.py`,
`call-hook/*.py`, `recordings-archive/*.py`; `/root/staff_register` (py json,
minus names containing `settings` or `advances`); `/root/staff_ledger_reconcile/*.py`;
`/root/state_backup/*.py`; `/root/*.py`; the `clinic-*`, `wa-*`, `call-*`
systemd units; the root crontab as `crontab.txt`.

Never, whatever the pattern said: `.env*`, `*.env`, `*.conf`, `*.db*`, `*.log`,
`*.bak*`, `token*`, `*key*.json`, `patient_fp.env`, `*config*.py`, `*_config.py`,
and any path through `_retired*`, `__pycache__`, `backups`, `deploy`. The
excludes run after the includes.

Named outright, whatever else says: `att_config.py`, `portal_config.py`.

And, by CONTENT: every candidate file is read with the repository's own
publish-gate credential heuristic (`deploy_kits/NO_PHONE_NUMBERS.py`, ported
verbatim: a secret-shaped NAME assigned a literal of 16+ characters that is
not a constant, a path, a filename, a placeholder, a hash pin or interpolated;
a Bearer literal; a private-key block). A file the gate would refuse is left
out and named: `excluded_secret=N (basenames)`. Over the 217 files of the
captured live tree the port reports exactly what the gate reports, and it
flags one file: `portal_config.py`.

## The 07:19 finding (why v1.1)

The first live bundle, shipped 07:19 on 13-Sep-2026, was opened and read. It
carried `root/portal/portal_config.py` (token seed, SSO secret, an auth token,
PIN hash and salt as literals), `root/att_config.py` (a dashboard password,
an SMTP password, a secret key) and `root/finance/freshness.conf` (a live
ntfy topic). Standing hold: secrets never go to cloud storage.

v1.1 added the filename walls and a content scan of its own -- a blunt
pattern that, live, excluded `finance_app.py`, `purchase_app.py`,
`finance_patient_match.py`, `clinic_sso.py` and `portal_console.py` on
constants like `TOKEN_HEADER = "X-Finance-Marg"`; the FATAL guard fired and
the installer rolled back as designed. v1.2 replaces that scan with the
gate's own heuristic and names the two config files outright. Proven against
the captured live tree: the five files are IN, the two config files are OUT
(see EVIDENCE_S243.txt). The 07:19 revision on Drive should be treated as
exposed until the owner overwrites it (the next `run`) and rotates what it
held.

## Install (one line, on the VPS, after PUBLISH + deploy pull)

```
bash /root/deploy/repo/deploy_kits/S243_CODE_BUNDLE/install_S243_CODE_BUNDLE.sh
```

Gates from inside the folder, copies as `.new`, md5-verifies, moves into place,
`py_compile`, runs `build` as the smoke (no network) and prints its summary,
backs the crontab up to `/root/crontab.bak_S243`, adds the tagged cron line only
if absent. Any failure removes the file and restores the crontab. Nothing is
restarted.

## Verify (one line)

```
/root/wa/venv/bin/python3 /root/state_backup/code_bundle.py list
```

Lists the Drive folder, says whether the slot `code_nightly.tar.gz` is present
and how many revisions it holds, and the age of the local copy.

## The slot -- DONE at S243 (13-Sep-2026 01:06 IST)

`code_nightly.tar.gz` was created by the assistant through the owner's Drive
connector (owner `drmka.ortho`, 219-byte placeholder) in the same folder as
`finance_nightly.db.gz`. `list` should now show it PRESENT; the first `run`
overwrites it. If `list` ever says MISSING again, re-create it the same way.

## Files

| file | role |
|---|---|
| `code_bundle.py` | the whole job: `build` / `run` / `list` |
| `selftest_code_bundle_s243.py` | `build` against a mock tree with forty-six decoys (name and content); asserts every decoy absent, every wanted file present, the manifest verifies, the refusal without `finance_app.py` |
| `install_S243_CODE_BUNDLE.sh` | the installer; honours `ROOT` and `PY` for tests |
| `EVIDENCE_S243.txt` | selftest and mock-installer transcripts from the build container |
| `KIT_ID.txt` | kit name and payload md5 (F-88) |
| `SUMS.md5` | the gate -- verify from INSIDE this folder: `md5sum -c SUMS.md5` |

## Restore, in words

Fetch `code_nightly.tar.gz` (Drive, or the local copy), `tar -tzf` to look,
`md5sum -c MANIFEST.md5` after extracting into a scratch directory, then copy
the file you need. Members are rooted at `/` (`root/finance/finance_app.py`).

## Known limits, stated plainly

- The bundle is not encrypted. It carries code, not patient data and (from
  v1.1) not configuration secrets; the same trust domain as the S213 db.gz.
- The content scan is the publish gate's, no looser and no tighter. Its
  known blind spot: a credential under a name the gate does not consider
  secret-shaped (`SMTP_PASS`, `DASHBOARD_PASSWORD` is caught, `SMTP_PASS` is
  not) -- that is why `att_config.py` is named outright. Its known edge: a
  mixed-case literal of 16+ characters under a secret-shaped name is a hit
  even when it is a header name; the live one is 14 characters. Read the
  summary after every live run; a false exclusion is repaired by renaming
  the variable or shortening the constant, never by loosening the scan.
- Drive's revision window (~30 days) is Google's behaviour, not a contract.
  The local copy is overwritten nightly; there is no on-box history by design
  (the repository is the history of intent, the bundle is the history of fact).
- `lib/` under `marg_ingest` is walked recursively; every other source is one
  level, as its pattern says.
