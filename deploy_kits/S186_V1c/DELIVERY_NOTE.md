# S186_V1c — the corrected live-pin list (S186 post-close)

**No code. One file: `/root/deploy/live_pins.txt`.**

## Why

`S186_V1b` installed cleanly and its check went **RED on one file**:

```
DRIFT  /root/finance/finance_ui/finance_workbench.html
       record says : 45cb85b353ba8675114ca23eaa6afa90
       box is  now : 18c71e63e5f1790c07d7fa3df53cd24e
```

**The box was right.** `finance_workbench.html` shipped twice at S186 — in `S186_R2a` (`45cb85b3…`),
then a newer build inside `S186_I1a` (`18c71e63…`), which is what installed last and passed 351/351.
At the close, the duplicate-path guard fired because one path was pinned twice; the conflict was
resolved by deleting a row, and the row deleted was the current one — settled from the documents
instead of from the box, the inverse of D321(d). That is **F-118**, and it is the first RED in this
project caused by the record rather than the box.

This kit carries the list generated from the corrected **KB Register v5.12**.

It also repairs what V1b's header *claimed*. V1b attested `manifest_md5: 04eff42c…` — a hash **no file
anywhere carries**, because the manifest was re-pinned twice after that list was built. The checker
printed `VERIFIED against the manifest … (md5 04eff42c…)` without ever comparing it (**F-117**). This
list is generated with `--manifest` against the rebuilt manifest `78881ddd…`, so the attestation is
true *and* checkable.

## Expect

```
match 42   drift 0   missing 0   untracked 76   unverifiable 11
VERDICT: GREEN
```

The 76 untracked and 11 unverifiable are unchanged and are **not** failures — they are the honest
blind spots the tool refuses to hide (F-97 part 2 is the work of listing or excluding them).

## Still owed — do not mistake this GREEN for a complete one

`verify_live_pins.py` **prints** the manifest md5 it was handed and never hashes the file. Until that
is fixed, the `source : VERIFIED against the manifest` line is an unproved claim. The fix is about
three lines and sits at the head of **Runbook v121 §2 as item 0**.

## Install

```
bash /root/deploy/vps_deploy.sh S186_V1c
```

The installer refuses unless: the kit's own SUMS pass · `KIT_ID` matches the list's md5 · the header
reads `register_pin_verified: yes` · the source is Register v5.12 `1da5b0c4…` · **and the F-118
correction is physically present in the list.** It keeps the previous list as
`live_pins.txt.bak_S186_V1c` before replacing it.
