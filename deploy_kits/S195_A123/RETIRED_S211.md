# RETIRED — 31-Aug-2026, on the owner's ruling

> *"Your tech flaw — shouldn't have been there at all. Must be retired safely."*

This kit held a copy of **`finance_app.py`, the clinic's money application, whose bytes nobody can
account for.** Three different fingerprints existed for one file:

| what | md5 |
|---|---|
| this kit's own checksum row demanded | `6617ec6fac43d8b342b7970492cbd899` |
| the file actually in this folder | `e1791014cf0d311137f319d6b391aa6b` |
| the live VPS file (owner's paste, S208 close) | `8427c82e…` |

**Neither of the first two appears anywhere in the KB Register or the History Archive.** The row
cited a hash nothing ever pinned; the folder held a third the record never pinned either.

## What was done, and what was deliberately NOT done

**Retired in place. Nothing deleted** — the bytes remain, so the record of what was found remains:

- `finance_app.py` → renamed to carry its own fingerprint, then **MOVED OUT OF THE
  REPOSITORY ENTIRELY** to `D:\dr-manoj-git\_retired_out_of_repo_S195_A123\` — see the
  amendment at the end of this note. The bytes are preserved; they are no longer public.
- `install_s195_a123.sh` → **`install_s195_a123.sh.RETIRED_S211`** — nothing here can run.
  (Verified first: no other script in the repository references this kit.)
- `SUMS.md5` → **`SUMS.md5.RETIRED_S211`**, kept **verbatim**, so the hash it demanded stays on
  the record.

**The checksum row was NOT repaired to match the file.** That would have certified bytes nobody
can account for — the one thing the S209 note explicitly forbade. The gate is not made green; the
gate is removed along with the thing it was guarding, and this note replaces it.

## Why the ruling is right

`finance_app.py` is the money application. A folder holding an unidentified copy of it can only
ever be used by mistake, and identifying the bytes would not change what we would do — nobody is
going to install a 22-August copy over live financial code either way. **D188 stands: a filename
is not provenance.**

## Provenance of this retirement

The measurement and the reasoning are in `DO_NOT_INSTALL_S209.md`, kept beside this file
unchanged. Fault **F-244**, ruled by the owner 31-Aug-2026 and minted at the S211 close.


## AMENDED THE SAME DAY — the bytes left the repository altogether

Renaming was not enough, and the publish gate said so.

`NO_PHONE_NUMBERS.py` refused the publish: **that file carries real phone numbers** (two of
them, at lines 6089 and 6093). They had been in the repository since S195 — part of the F-185
backlog, grandfathered because the gate only ever scans what is being staged NOW. Renaming the
file made git stage it as new, so for the first time the gate actually looked at it, and refused.

**The gate was right, and the fix is the one it prescribes for data: move it out of the
repository.** The payload now lives at

    D:\dr-manoj-git\_retired_out_of_repo_S195_A123\finance_app.py.UNIDENTIFIED_e1791014_RETIRED_S211

outside git, where the bytes are still preserved for the record but are no longer published.
This note, the original S209 measurement, the retired installer and the retired checksum file
stay here, and none of them contains a number.

**Two things worth keeping.** A rename can turn a grandfathered file into a staged one and put
it in front of a gate for the first time — that is the gate working, not misfiring. And the
F-185 position is now strictly better: an unidentified copy of the money application, carrying
real numbers, is no longer in a public repository at all.
