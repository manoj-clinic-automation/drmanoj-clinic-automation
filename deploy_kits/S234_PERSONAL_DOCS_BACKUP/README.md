# S234_PERSONAL_DOCS_BACKUP — the third personal book joins the nightly

**Session 234 · 08-Sep-2026 · detour item 2 of D432.**

---

## What it is

`PERSONAL_DOCS_ID` — the **Personal Documents** sheet the Janitor's `Code.gs`
updates, holding identity-document rows with expiry and lead-time columns.
`PERSONAL_GOOGLE_PLANE_v1_S233` §4 named it and said what was wrong with it:

> *"It has no backup, it is not in the S233 pull, and no census, brief or
> register had ever named it."*

This kit adds it to the `SHEETS=` list that `sheets_pull.py` already reads, so
it rides the 01:45 pull and the 01:50 AES-256 bundle with the other four books.

**No new job. No new key. No new mechanism.** Not one line of `sheets_pull.py`
or `clinic_state_backup.py` changes. The install is a single line added to one
settings file, and everything else in the kit exists to prove that line is safe
and to put it back if it is not.

## Why this is a real second copy

S233's second lesson was *a copy in the same account is not a second copy.*
This passes that test: the book lives in the owner's **personal** Google
account, and the encrypted bundle lands in the **clinic** account's Drive.
Different account, different credential, AES-256 in between.

## Where the numbers end up

Said plainly, because these are identity documents:

- **plaintext CSV** at `/root/state_backup/sheets/personal_docs/` on the VPS —
  inside **D429**, the owner's ruling that the VPS is a safe place for his data,
  on a box only he holds credentials for;
- **inside the encrypted bundle** on the clinic Drive, never plaintext there;
- **nowhere else.** **D431 stands** — the personal exports and their books never
  enter the repository, and this kit carries no row of that book. What it does
  carry is the book's id, in `BOOK_ID.txt`, which is the same thing S233 put in
  git for the other four books.

## The safety property, and it is the whole design

**Any failure puts the settings file back byte for byte.** The conf is copied
aside before it is touched; every `stop` restores it; and the walk asserts a
byte-identical conf after each of the four failure paths. A failed run leaves
tonight's pull running exactly as last night's.

The failure most likely to happen is the ordinary one: **the sheet has not been
shared with the backup's service account yet.** The installer stops at
preflight, restores the conf, and prints the service-account address **read off
the box** — never hardcoded, so it is always the right one. Share, re-run, done.

## Proof taken before handover

| gate | result |
|---|---|
| `bash -n install.sh` | clean |
| `WALK_pd_install.py` | **24 checks, 0 failures** |

The walk drives `install.sh` against stand-in pull and bundle scripts and
covers: the ordinary run · a second run being a no-op · **the sheet not shared**
· the pull failing after the edit · **the bundle shipping without the new book**
· a missing `BOOK_ID.txt` · a conf carrying two `SHEETS=` lines. Four of those
seven assert the conf comes back byte-identical, and two assert the book's id is
**never printed** to the screen.

## Files

| file | what it is |
|---|---|
| `install.sh` | nine stages; restores the conf on any failure |
| `BOOK_ID.txt` | the book's spreadsheet id, and nothing else |
| `WALK_pd_install.py` | drives the installer in a sandbox, every failure path |
| `INSTALL_ONE_PASTE.txt` | the two lines, and the one thing that may ask something of him |

---
*S234_PERSONAL_DOCS_BACKUP · Session 234 · built offline, walked, installed by
the owner from two lines.*
