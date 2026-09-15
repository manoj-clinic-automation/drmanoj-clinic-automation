# S273_BACKUP_GAP — the six files that would not have come back

## What S258 measured

The nightly code bundle was brought within a session's reach for the first time
(kit S272). With the box's own bytes in hand, every live pin in
`live_pins_S257close.txt` was held against them: **109 matched, 0 mismatched.**

Seventeen pinned files were not in the bundle. Each was then held against GitHub
**and** against the encrypted state bundle's `SRC_FILES` and `SRC_DIRS`.
**Six have no byte-exact copy in any store:**

| file | what it is |
|---|---|
| `/root/deploy/repo/deploy_kits/S229_ITEM_SPINE/marg_spine.py` | **the live item spine** — one row per product, every spelling, every fact. The repository's copy is a different file. |
| `/root/assetapp/asset_register.py` | **the live asset register application** — `assets.dr-manoj.in`. Its *data* has been backed up since S230; its *code* was in no store. |
| `/root/finance/freshness_legs.json` | **the health page's leg configuration.** Its own pin note: *"Configuration, not code: a window is widened or a leg retired HERE, never in `freshness.py`."* |
| `/root/deploy/email_agent.py` | the read-only email query agent |
| `/root/deploy/gen_live_pins.py` + `verify_live_pins.py` | **the tools that generate and check the pin list itself** |
| `/root/deploy/sweep_baseline.txt` | the sweep baseline |

**No single store is wrong.** `code_bundle.py` excludes `/root/deploy`, every
`.conf`, every `*config*.py` and every key json because v1.0's first bundle
shipped literal passwords (F-456). Those walls are correct and **this kit moves
none of them.** The gap lives *between* three backups, and nothing was
positioned to see it until the bundle and the pin list could be read together.

*(A seventh, `/root/staff_master.csv`, was written up as a gap and **retracted**:
it is the fifth line of `clinic_state_backup.py`'s `SRC_FILES`, backed up nightly
and encrypted. The first check read `SRC_DIRS` and stopped. Recorded, not tidied.)*

## What changes — one file, three edits

`/root/state_backup/code_bundle.py`, **v1.2 → v1.3**, `27e42d0d…` → `ed5b483f…`.

1. **Three new source directories** appended after the existing list:
   `root/assetapp`, `root/shared`, `root/deploy`, plus the one folder under
   `/root/deploy` the item spine is actually run from.
2. **A second `root/finance` entry carrying `"*.json"` only**, with its own
   secret-shaped-name guard. The existing `root/finance` entry is **not edited** —
   a second entry is added beside it, so no file carried today can stop being
   carried by this change.
3. **`DEPLOY_ALLOW`** — a named list of the only six paths permitted to survive
   the existing `deploy` wall. `EXCLUDE_DIRS` itself is untouched; the deploy
   clone stays excluded apart from the two spine files.

**Unchanged:** every `HARD_EXCLUDE`, every `BASENAME_EXCLUDE`, `EXCLUDE_DIRS`,
the credential content scan, the Drive half, the manifest, the tar, the crontab
capture, every FATAL guard. Every new file is still read and scanned by the
repository's own publish gate before it is carried, exactly as every existing
file is.

## The proof

**`walk_s273.py` — 21 checks, all passing.** It is not a unit test: it builds a
mock `ROOT` out of **the box's own nightly bundle** — the real tree, the real
names, the real bytes — adds the six files and eight decoys, then runs the
**live** tool and the **patched** tool over that same tree and compares what each
one carries.

- **Nothing is lost** — every file the live tool carries, the patched tool still
  carries. This is the v1.1 regression that matters, asserted directly.
- **The six are in** — each is carried after and by neither before.
- **No wall moved** — a key json, a `config.py`, a secret-named json, a database,
  a file under `uploads/`, a `.conf`, and a file inside the deploy clone that is
  not on `DEPLOY_ALLOW` are carried by **neither** tool.

Result over the real tree: **+12 files, −0 files.**

**Installer rehearsal on a mock box, all four paths:** a clean install (exit 0);
a second run (`ALREADY INSTALLED`, exit 0); a wrong pin (`REFUSING`, exit 2); and
a deliberately failed assertion — which **rolled back byte-identically to
`27e42d0d…`** and exited 1.

## Installing

The installer proves the change **on the box** before keeping it: it runs the
live tool first and records what it carries, patches, runs the patched tool over
the same real tree, and asserts nothing was lost and the six arrived. On any
failure it restores the backup and verifies the restore.

No service is restarted. No page changes. The 01:35 cron ships the wider bundle
tonight, unchanged in every other way.
