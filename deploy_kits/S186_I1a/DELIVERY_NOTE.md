# Kit S186_I1a — F-114 fixed, and Marg uploads through the portal

**Session 186 · replaces two live modules · gated on both · backed up · self-restoring**

## 1. F-114 — the review queue that could only grow

`marg_report.py` warned *"10 of 33 bills carry no clinic ID and will attribute to WALK-IN."*
`finance_ingest.py`'s own docstring said *"a line with no ID lands on WALK-IN."*
**Neither was true.** On 14–15 Aug: WALK-IN **0**, review **10**.

A gate three lines above `resolve_patient` diverted the line before that function was ever reached:

```python
if ln["confidence"] < min_conf or (not ln["clinic_id"] and not ln["patient_name"]):
    -> sale_item_review
```

So a bill with neither ID nor name was parked in a queue **with nothing in it a human could
resolve** — no name to look up, no ID to match. 2,062 rows by S186, ~10 more every clinic day.

**Two records described behaviour the running code did not have, and nobody checked.** The same
shape as F-97, F-107, F-112, and the S184 SQL narration *"tracked in salary system."*

**The fix, narrow by design:**

| line | goes to |
|---|---|
| read cleanly, has ID or name | its own patient (unchanged) |
| read cleanly, **anonymous**, from a **structured export** | **WALK-IN** |
| **low confidence** | review — a human *can* fix that |
| anonymous **from OCR** | review — an unreadable scan looks exactly like an anonymous one |

Reversible with no code change: `ingest.anonymous_to_walkin = 0`.
Diff: **one line replaced, 17 added.**

## 2. Marg uploads through the portal

Until now an export reached the books by being copied to the VPS by hand — which is why it had to
live on the box at all, and then be deleted again for PHI hygiene.

Now: **Workbench → Marg item-wise report → Check first / Load into the books.**

The file is parsed, surveyed, ingested and **deleted inside the same request**. It never persists on
the server, in any code path — the delete sits in a `finally`.

It keeps every guard the command-line driver has, each bought with a fault:

- refuses an export with **no item detail** (a mis-export)
- refuses a **column map that does not match** the parser (the silent-zero trap)
- **aborts the day** if the adapter reads a different row count than the file holds — never half-loads

And it adds the one the driver lacks — **F-113**: a day skipped because it is **NOT FILED** now
writes a `data_flag`. *"not filed (refused, harmlessly)"* is true at that instant and false the moment
the day is filed. A console line does not survive the run; a flag does.

**Check first** writes nothing and shows every day in the file, whether it is filed, and what would be
replaced.

## Proven before shipping — the F-87 differential

| | passed | failures |
|---|---|---|
| unmodified live bytes | 303 / 314 | 11 |
| **this build** | **340 / 351** | **11** |

**37 checks added, ZERO failures added.**

Three of the new checks failed on the way here, twice for the same reason: they asserted the *suite's
state* rather than behaviour. An earlier step in the suite rewrites the marg column map, so both
"assume the shipped map" and "read the current map" made the test a test of ordering. It now **owns
its map and puts it back**. That is F-106, caught in our own tests — for the second time today, which
is itself the argument for running the differential rather than trusting a green.

## Safety

- Gated on **both** live md5s: `finance_app.py` `31642789bc…` and `finance_ingest.py` `2cd0f264fb…`
- Backups: `finance_app.py.bak_S186I1a` · `finance_ingest.py.bak_S186I1a` · `finance.db.bak_S186I1a`
- Selftest runs on a copy of the real store **before** the service returns; any red restores all three

## Install, then W1a

```
bash /root/deploy/vps_deploy.sh S186_I1a
```

Then run **S186_W1a**. Order matters: the ingest stops refilling the queue first, then the reclass
empties it once — instead of clearing 2,072 rows and watching them come back tomorrow.
