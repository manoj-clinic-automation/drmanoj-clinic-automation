# S308_PURSUE_EVIDENCE — step 8 asks Darpan with the evidence already gathered

**Session 266 (Sanjeevni project) · 17-Sep-2026**, on the owner's "GO".

## What it adds

When the owner marks a line **to pursue**, Darpan is asked whether it was sold without a bill. Until now the question
went to him bare. The server already holds the sale lines and the purchase lines, so step 8 of the Stock Check hub now
carries, for each pursued line:

- what sold in the **30 days before the count**, and on how many bills (returns netted off);
- when it **last sold**;
- what has sold **since the count**;
- when it was **last bought**, and how much;
- the item's own open **question for Marg's ledger**, if it has one.

An item that never sells is a different question from one that sells every day, and the line says which it is:

> **NOT SOLD ONCE in the 30 days before the count — a shortage here is not a counter sale**

Worst first, ten on the page. It only reads: no table, no decision. His answer is still evidence, and the owner's tap
still decides.

## The proof

**`selftest_s308.py`: 25 checks, 0 failed.** It covers the file (pin, anchors, refusal, idempotence, backup, compile,
the hub script) and the evidence itself:

- a selling item's units, bills and last sale, with a return netted off;
- sales since the count and the last purchase, in words;
- an item that never sold in the window says so;
- only lines marked to pursue get a card, worst first;
- an item with no sale lines, a count with no day, and a database with no tables each give an empty card and never
  raise;
- the item's Marg question rides along, at most two lines of it.

**Rehearsed on the office PC** against the 17-Sep nightly database (`rehearsal_s308.txt`). Nothing is marked to pursue
today, so the four biggest open shortages were marked on the copy:

| line | what the card says |
|---|---|
| **TYRO BR**, short 23 strips | sold 287 strips on 170 bills in the 30 days before the count (last 05-09); 85 strips since; last bought 09-09 (50 strips); and its Marg question — *which voucher took 40 strips out between 27-08 and 03-09?* |
| **ROSIKA FORTE**, short 17 strips | sold 139 strips 7 tabs on 63 bills before the count; 28 strips 8 tabs since; last bought 01-09 (60 strips) |
| **ETOZOX 90**, short 46 strips 9 tabs | **not sold once** in the 30 days before the count; nothing since |
| **HYORTH XL**, short 1 pc | **not sold once**; nothing since; last bought 15-06 |

**On the box, before anything is placed,** `walk_s308.py` builds the hub on a scratch copy of the live database, checks
every pursued line has a card, marks one more line on the copy and checks it gets its evidence.

## Install — one line on the VPS, after the publish

```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S308_PURSUE_EVIDENCE/install_S308_PURSUE_EVIDENCE.sh
```

It restarts clinic-finance. **Rollback:** put the two `.bak_S308_*` files back beside the originals and run
`systemctl restart clinic-finance`.
