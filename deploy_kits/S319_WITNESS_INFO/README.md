# S319_WITNESS_INFO

**One line on the VPS:**

```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S319_WITNESS_INFO/install_S319_WITNESS_INFO.sh
```

## Why

The health page's never-fired witness exists to catch a check whose **red branch cannot be reached** —
AF-2 was born dead at S195 and stayed green for five sessions. Reading the code at S269 (D525) showed
that two of the seven keys it names have no red branch **on purpose**:

| key | lines | states it can ever take |
|---|---|---|
| `flags` | 11885–11897 | `ok` ("none raised") or `info` — "Notes, not failures" |
| `margqueue` | 11874–11880 | `info` only, by the S195 ruling quoted above it |

Left in, they are named every single day, and a list that never changes is a list nobody reads — the
alert fatigue that ruling was written to prevent.

## What it does

Declares `HEALTH_INFO_ONLY = ("flags", "margqueue")` with the reasoning beside it, excludes those keys
from the witness's eligibility, and makes the card **say so in its own hint**, naming them, so nobody
has to read the code to know why the number fell from seven to five.

The two rows are **still tracked** — the `INSERT OR IGNORE` and the non-ok counter above the filter are
untouched, so if either ever gains a red branch its history is already there. Nothing else on the page
changes, and no other check is excluded: `backup`, `outbox`, `drawer`, `renewals` and `watcher` all
stay in. (At S269 `watcher` was the real finding for the opposite reason — its red branch is nearly
unreachable in practice. That needs the owner's ruling, not this patch.)

## Proof

`walk_s319.py` does not reimplement the witness: it **lifts the witness's own list comprehension out
of the file by text**, from the unpatched copy and the patched one, and executes both against a
scratch `health_check_seen` table in /tmp. No copy can drift from the file when the file's own line is
what runs. **16 checks**: before, the expression names four including the two informational rows;
after, it names only the two real guards; a check too young (5 days), a check that has fired, and a
stored key that is no longer a card are all correctly still unnamed; the insert and the counter are
byte-identical in both files; the declaration appears exactly once; and nothing else in the 686 KB
file selects on `nonok_count=0`.

**Negative control:** the same patched expression run with `HEALTH_INFO_ONLY` empty names the two rows
again — so the exclusion, not the fixture, is what removes them.

The installer runs that walk against a copy of the **live** file before it touches anything, restores
its own backup and restarts on any red, and ends by printing every tracked row with its age and
non-ok count, read-only from `finance.db`.
