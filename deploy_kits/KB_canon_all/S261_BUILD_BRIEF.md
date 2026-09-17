# S261 BUILD BRIEF — 17-Sep-2026 · the one document written for the owner

**What this session was for:** moving the 35 Sanjeevni/Marg documents into their own project (D528, part 2).
**What it also did:** got your pharmacy PC talking to this one again, and caught a small counting tool reading
the wrong file.

## What is different now

| before S261 | after S261 |
|---|---|
| the 35 Sanjeevni documents lived in this project | **they live in "Sanjeevni — Pharmacy & Marg"**, proven there by hash, and are gone from here — project knowledge 1,593,475 → **1,475,742** (73.8 %), measured |
| the pull from the pharmacy PC had been failing every 10 minutes since 15-Sep 10:20 | **working again from 06:50** — your one `cmdkey` line after the password change; the 17-Sep stock export and two days of sales went through in the first clean pull |
| the paper shelf silently read a superseded Register | **fixed (F-506)**; 406 papers, 205 never referred to — 50.5 %, down from 51.5 % |
| the staging folder had no rows in the nightly's manifest | rowed, 2,945 → 3,061 |

## What was not a fault

Your 17-Sep morning stock export *had* been taken on time (05:13). It could not travel because this PC's
stored password for the pharmacy PC was stale. Nothing was lost; the pharmacy PC keeps every capture.

## What needs you — nothing new

Your list stands, deferred at your word. One export from the pharmacy PC at 16-Sep 23:55 was refused
because no known report matches it — the Sanjeevni session can tell you which report it was, if it matters.

## The publish

One file, when convenient:

```
D:\dr-manoj-git\drmanoj-clinic-automation\PUBLISH_ALL.bat
```

It carries the Fault Register v2.85, Archive v1.98, Register v5.101, Runbook v182, START_HERE_263, this
brief, the pin list, the manifest, `MD5SUMS_ALL.txt`, `KIT_ID.txt` and the small tool fix
(`S281_PAPERS_SORT`, already applied on this PC — nothing to run). Then, on the VPS:

```
git -C /root/deploy/repo fetch --depth 1 origin main && git -C /root/deploy/repo reset --hard origin/main
```

## Next session — S263, in THIS project

The remaining 75 Sanjeevni evidence papers leave this project a batch at a time; then the small server
items (the health checks that have never fired, the backup that names no log).
