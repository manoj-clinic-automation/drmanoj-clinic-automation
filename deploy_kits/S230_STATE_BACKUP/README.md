# S230_STATE_BACKUP — everything on the VPS that has no off-box copy · v1

**Built at Session 230, 07-Sep-2026. Not installed by the builder — the owner installs it.**

## The gap this closes

S230 measured the box. Exactly one thing on the VPS has a daily off-box copy:
`finance.db`, shipped by `S213_FINDB_DRIVE` at 01:40. **Everything else has
none.** If the VPS is lost tonight, the call console, the asset index, the
attendance punches, the staff register and the staff ledger are gone — and so
is the *shape* of the machine: which units run, what cron fires, how the vhosts
are wired. Code survives in GitHub and the OS survives in the provider snapshot.
Nothing holds the rest. This kit is the second off-box leg.

## What it backs up

**The data — the things with no other copy:**

| source | how it is taken |
|---|---|
| `/root/wa/console.db` | sqlite **online-backup api** (`.backup`), never a file copy |
| `/root/assetapp/assets.db` | sqlite online-backup api — the **index only** |
| `/root/punches.csv`, `/root/punches_raw.log` | byte copy |
| `/root/staff_register/` | data files **discovered at runtime** (`*.db`, `*.csv`); sqlite files through `.backup` |
| `/root/staff_ledger/` | same |
| `/root/staff_master.csv` | byte copy |

A live database copied byte-wise while a writer holds it is a torn database
that verifies today and fails in a year. Hence `.backup`, always.

**The shape of the machine — small, and it turns a rebuild from archaeology
into an afternoon:**

- `crontab -l` output
- the **clinic** systemd unit files from `/etc/systemd/system` (`*.service`,
  `*.timer`), matched by name at runtime — never a hard-coded list. The
  personal-cluster units (`fitlog`, `gutlog`, `rxguard`) are a different trust
  class and are deliberately not collected; neither are OS units.
- the OpenLiteSpeed vhost configs whose domain matches the clinic's
- a **schema-only dump** (`.schema`) of every sqlite database found, so a
  corrupt file can still be read structurally
- `INVENTORY.txt` — every file included, with its path, size and mtime

## What it deliberately does NOT back up, and why

- **Application code.** GitHub is its backup. Backing it up twice is not safety,
  it is confusion about which copy is canonical.
- **The OS and the packages.** The provider snapshot covers them.
- **`/root/assetapp/uploads/`.** 198 MB of scanned images, re-scannable, and it
  would turn a two-minute nightly job into a bandwidth problem. The asset
  *index* is backed up; the images are not.
- **Every secret.** Any `.env`, `*key*.json`, `token*`, `credentials*`, `*.pem`,
  `*.key`, `id_rsa*`, `*secret*` is skipped by pattern before it is ever read.
  The script logs **how many** it skipped and never their names or contents. A
  backup that carries the keys to the estate is a second copy of the breach.

## 🔴 Encryption, and the one thing that can never be undone

`console.db` holds patient call records. The staff register and the staff
ledger hold staff-financial data. The estate's golden rule (F-31) is that
**patient data and staff-financial data never reach cloud, chat or GitHub.**
They therefore may not go to Drive in the clear, and they do not.

The bundle is encrypted **on the box, before it leaves**, with
`openssl enc -aes-256-cbc -pbkdf2 -iter 200000 -salt`, using a key file whose
path is named in the conf and whose contents never leave the VPS. openssl is
already present on the box and needs no new dependency; if it is ever missing,
`preflight` and `run` refuse loudly (exit 14) rather than shipping in the clear.
The key file must be mode 600 — the script refuses a key the whole box can read.

> ## **A BACKUP WHOSE KEY IS LOST IS UNRECOVERABLE.**
> **There is no reset, no recovery link and no support desk. If the VPS dies and
> the key died with it, every file in Drive is permanently unreadable noise.**
>
> **The key is generated once, on the VPS, by the installer. Copy it, that same
> hour, to BOTH of these:**
>
> 1. **`F:\ClinicBackup\S230_STATE_BACKUP\`** — download the key file with
>    WinSCP into that folder.
> 2. **Dr Manoj's own credentials store** — paste the key's single line in as a
>    secure note.
>
> **That copy is the one manual action this design requires. Nothing else in the
> kit can be done wrong in a way that cannot be fixed later; this can.**

## The two Drive slot files the owner must create first

A Google **service account has zero Drive storage quota** — proven on this
estate's live box on 31-Aug-2026, HTTP 403 *"Service Accounts do not have
storage quota."* It cannot create a file. What it *can* do is write new
**content** into a file the **owner** already owns; those bytes bill the owner.

So two files must already exist in the Drive folder, **created from the owner's
own account**, and they are then overwritten:

| slot file | role |
|---|---|
| `clinic_state_nightly.tar.gz.enc` | overwritten every night. Drive's own revision history keeps previous versions ~30 days, so this one file is about a month of restore points. |
| `clinic_state_monthly.tar.gz.enc` | overwritten on the first verified run of each month, and **that revision is pinned `keepForever`** — one immortal copy per month. Drive caps pins at 200 per file; the job warns at 180. |

If either is ever deleted, the job stops with **exit 13 and names it**.
Recreate it from the owner's account — the service account cannot.

The simplest route is to put both slot files in the folder the S213 job already
uses, which is already shared to the service account as Editor. A separate
folder works equally well; then its id goes in the conf by hand.

## Conf keys

`/root/state_backup/clinic_state_backup.conf`, `KEY=VALUE`, chmod 600. Every
id, path and key lives here and never in the repository (F-185). **The script
refuses rather than guesses** — there is no search list and no default for
anything that identifies this estate.

| key | required | meaning |
|---|---|---|
| `SA_JSON` | yes | full path to the Drive service-account json already on the box |
| `FOLDER_ID` | yes | id of the Drive folder holding the two slot files |
| `ENC_KEY_FILE` | yes | full path to the AES key file (mode 600) |
| `WORK_DIR` | no | staging directory; default `<conf dir>/work` |
| `STATE_FILE` | no | freshness state json; default `<conf dir>/clinic_state_backup.state.json` |
| `SUMMARY_FILE` | no | one-line-per-run summary; default `<conf dir>/clinic_state_backup.summary.log` |
| `SYSTEMD_DIR` | no | where the unit files live; default `/etc/systemd/system` |
| `VHOST_DIR` | no | where the OpenLiteSpeed vhost folders live; default the CyberPanel location |
| `UNIT_MATCH` | no | comma list of systemd name fragments to collect |
| `VHOST_MATCH` | no | comma list of vhost domain fragments to collect |
| `MAX_FILE_MB` | no | a single file larger than this is skipped and said so; default 64 |

## Freshness — the part that matters most

**A backup that cannot state its own age has not been taken.** Every successful
run writes a small json state file recording `last_success_iso`, `bytes`,
`md5`, `files_included` and `secrets_skipped` (plus the source list and whether
the monthly was written). A later freshness page reads that file and can say,
without asking anyone, how old the newest good backup is. `list` mode prints
the same thing and calls it **STALE** past 30 hours.

A failed run does **not** advance the state file. Silence is never DONE.

## Refusals — nothing leaves the box on a bad day

| exit | refusal |
|---|---|
| 40 | any sqlite database fails `integrity_check` — **before any network call** |
| 41 | a source file present on the last successful run is missing now |
| 42 | the encrypt → decrypt → compare round trip fails on the real bundle |
| 30 | the read-back md5 from Drive differs — **and the monthly is not touched**; the previous good version still stands in the nightly file's revision history |
| 13 | a slot file is missing (named) |
| 14 | openssl is unavailable — it will not ship in the clear |
| 15 | the key file is missing, too short, or not mode 600 |
| 10 / 11 | the conf is missing, or a required key is unset |

## What `preflight` proves

Everything, without shipping anything and without changing a byte on Drive:

1. the conf exists and every required key is set
2. openssl is usable, and its version is printed
3. the key file exists, is long enough, and is mode 600
4. **the encryption round trip** — a fixture is encrypted, decrypted and
   compared by md5, and the ciphertext is checked to carry a real salt header
5. every source's presence, and every database's `integrity_check`
6. the count of files that would be included and secrets that would be skipped
7. the age of the last success, if there has ever been one
8. Drive is reachable as the service account, the folder is a folder, and both
   slot files exist
9. **write access** — proven by a metadata-only description touch on the
   nightly slot. Content is not changed and no revision is created.

## Files

| file | role |
|---|---|
| `clinic_state_backup.py` | the whole job: `preflight` / `run` / `list` |
| `WALK_clinic_state.py` | the live-shape walk: a fixture estate in a temp dir, a fake Drive with per-file revision history, **86 checks across 17 paths** — every refusal, the secret-skipping, the encryption round trip, and a full decrypt-and-untar of the bytes actually shipped. No network, no real path. |
| `INSTALL_ONE_PASTE.txt` | the owner's steps, one line per command, full paths |
| `KIT_ID.txt` | the kit's name |
| `SUMS.md5` | the gate — verify from **inside** this folder: `md5sum -c SUMS.md5` |

## The cron line

```
50 1 * * * /root/wa/venv/bin/python3 /root/state_backup/clinic_state_backup.py run >> /root/state_backup/clinic_state_backup.log 2>&1
```

01:50 — after the 01:05 local finance backup and the 01:40 finance Drive leg,
and before the 02:00 recordings archive.

## Rollback

One line. Remove the cron entry:

```
crontab -l | grep -v clinic_state_backup | crontab -
```

Nothing else is touched. The script writes only inside its own directory and
its own two Drive slot files; no existing file, service or job is modified by
installing it or by removing it.

## Known limits, stated plainly

- Drive's ~30-day revision window is Google's behaviour, not a contract. The
  pinned monthly is the guaranteed tier; the nightly revisions are convenience.
- The bundle is a full copy every night, not an incremental. At the measured
  sizes (console 8.5 MB, assets index, punches, register and ledger — well
  under 20 MB compressed) that is the right trade: a full copy needs no chain
  and no previous night to restore.
- `MAX_FILE_MB` guards against a store quietly growing into a bandwidth
  problem. If a file is skipped for size, the run still succeeds and says so —
  that is a signal to re-scope, not a failure.
- Restoring is deliberately manual: decrypt with the key, untar, read
  `INVENTORY.txt`, put files back. It is a disaster procedure, not a routine.
