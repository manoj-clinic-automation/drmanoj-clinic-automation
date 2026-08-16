# S182_P1a — portal tiles for the clinic finance module

**One file changes on the VPS: `/root/portal/portal.py`. No database, no migration,
no other app touched. Medical is untouched and proven so by the gate.**

---

## What you will see after it installs

| Who | New tile | Opens |
|---|---|---|
| Shavez, Alisha, Shivani | **Daily Collection** | `/finance/clinic/entry` |
| You, Dr Bhawna, **and Shavez** | **Clinic** | `/finance/clinic/review` |

Both sit in the **Money & Accounts** group, beside Daily Sale and Sanjeevni Medicos.

**Shavez gets both tiles on purpose.** The C2a migration seeded him a clinic *maker*
seat and the middle-approver *checker* seat — he files the day and he verifies it
before you give final approval. With only the entry tile he would have had no route
to the verify screen. Self-verify stays barred in code (D272), so he still cannot
approve his own entry.

**The legacy "Daily Collections" tile is retired**, per your ruling. That tile pointed
at the old Google Sheet. The sheet itself is untouched and still reachable by its
bookmark — only the tile is gone. Say the word and it comes back in one line.

**Tile wording is not hardcoded.** The labels come from the `clinic.tile.*` settings
your migration already seeded, fetched by the browser from
`/finance/clinic/api/tile-meta`. Change the setting, the tile follows. If the finance
app is down, or a person has no clinic seat, the tile keeps the text baked into the
page and nothing breaks — the same pattern the Staff Register and Clinic Gist tiles
already use. One honest limit: `tile-meta` answers for one seat per person and the
checker seat wins, so Shavez's *Daily Collection* tile keeps its static label. Cosmetic
only; his tile still works.

---

## Why this kit refuses to install on the wrong file

This kit carries a **live-file currency gate**. It checks that
`/root/portal/portal.py` is exactly `34f038a765…` — the file it was built on — and
**refuses, touching nothing**, if it is not.

That gate exists because of what S182 found. The live `portal.py` had drifted from
both git and its KB Register pin for two sessions: it carried the S179 finance tiles,
which existed nowhere else. The Register said `da417709…` (S176) and the repo agreed
with it byte-for-byte — so the stale record looked *verified*. Building the obvious
way would have deleted Daily Sale and Sanjeevni Medicos from your medical unit, and
every check would have passed on the way out. Logged as **F-97**.

---

## The gate

`smoke_portal_S182.py` runs **before anything live is touched** — no migration and no
database here, so there is no reason to swap first. **42 checks**, each printing what
it saw. It imports both the candidate and your live file and asks the real objects,
rather than grepping for text.

The block that matters is **REGRESSION**: every tile present on the live box must
still be present afterwards. It was proven by deliberately deleting Sanjeevni Medicos
from a copy — the gate caught it and named it. It was also run against the unmodified
live file, where 16 checks correctly failed. A gate that passes everything is not a
gate.

Also asserted: the two S179 medical tiles and their URLs, no tile pointing at the old
sheet, both new tiles grant-only (`roles: []`), exact visibility for all six named
people, no leakage to any ungranted user of any role, Bhawna still masked from
Sanjeevni Medicos, Darpan unchanged and seeing neither clinic tile.

---

## To install

On the PC: double-click `deploy\push_kit.bat`.
Then on the VPS, one line:

```
bash /root/deploy/vps_deploy.sh S182_P1a
```

Rollback if you ever want it: `/root/portal/portal.py.bak_S182P1` is written before
the swap, and a red install restores it automatically, restarts the service and
re-checks health before it reports.

---

*Kit built S182 · gate 42/42 offline · candidate `410388da…` · built on live `34f038a765…`*
