> ## ⚠ SUPERSEDED — DO NOT ACT ON THIS DOCUMENT
> **Superseded on 26-Aug-2026 — the fault it reports is CLOSED.** Successor:
> **`Fault_Action_Register_v2_41.md`** (md5 `4883e3bdf08cba92da7597448e00f2da`), which carries
> **F-179** in full and closed; the symptom row is in
> `MARG_AND_MEDICAL_PC_MASTER_REFERENCE_v3.md` §7 (md5 `579ea885e440e76af73de3ecc4542d71`), and
> the narrative is in `KB_History_Archive_v1_49_S202.md` §S201 (md5 `06c6670a8a1155959e4f0961ad58e7c5`).
> **The Fault Register is the only register of record for fault status.** A finding document is not
> a place to check whether something is still broken.
> Label added at S203, 26-Aug-2026. **Retained, not deleted (F-23).**

# S201 — FINDING: the Marg `_outbox` queue has no sender. Nothing has reached the clinic server since 22-Aug.

**Raised:** 25-Aug-2026, ~09:15 IST · owner report: *"made a Marg sale report this morning, saw it
being pushed from a cmd window, but it is not on the approvals page and I can't find it in margsync."*

**Verdict: the report is SAFE and CORRECT. It was never sent.** Capture, verification, archive and
offsite all worked. The upload leg does not exist.

---

## 1 · What actually happened this morning

| Time (IST) | Event | Evidence |
|---|---|---|
| 08:16 | Marg export #1 run on medical PC | `_captured\20260825-081605__REPORT_1__25c1ff95.XLS` |
| 08:20 | manojz pull → routed → **VERIFIED** → archived + Drive offsite | `index.csv` row, `uploaded=queued` |
| 08:27 | Marg export #2 run (owner re-ran with the correct single date) | `_captured\20260825-082716__REPORT_1__3b456d9c.XLS` |
| 08:30 | manojz pull → routed → **VERIFIED** → archived + Drive offsite | `index.csv` row, `uploaded=queued` |
| — | **push to `followup.dr-manoj.in` — NEVER HAPPENED** | `send_log.txt` last entry **22-08-2026 09:39** |

**The cmd window you saw was the capture/pull, not a push.** `PULL_FROM_MEDICAL.bat` runs every 10
minutes on manojz and prints *"Pulling Marg reports from the medical PC…"*. It looks exactly like
success. It is not the sender.

## 2 · Where the file is (both copies, verified by content)

```
D:\Downloads\margsync\MargArchive\SALE_BILLWISE\2026-08\
   SALE_BILLWISE_DETAIL__2026-08-24__20260825-082715__3b456d9c.XLS   <-- USE THIS ONE
   SALE_BILLWISE_DETAIL__2026-08-23_to_2026-08-24__20260825-081605__25c1ff95.XLS
```
Also mirrored to `MargArchive\_outbox\` and offsite to
`H:\My Drive\Clinic Data Archive\MargArchive\`.

You could not find it because **the router renames every file by the business date inside it and
files it into a type/month subfolder** — it is never called `REPORT_1.XLS` again and never sits at
the top of `margsync`.

### The two files hold identical data
Both parse clean: **SANJEEVNI MEDICOS · 24-08-2026 · 22 bills · gross 13,881.15 · discount 916.35 ·
NET ₹12,964.00 · cash ₹10,462.00 · non-cash ₹2,502.00.** One day section only; `DAY TOTAL` and
`GRAND TOTAL` agree. 23-Aug was a **Sunday** and correctly carries no bills.

The only difference is the report title —
`…FROM 23-08-2026 TO 24-08-2026` vs `…AS ON 24-08-2026` — which changed the md5 and produced two
archive entries for one day's trade. **No data was lost or duplicated.**

## 3 · Root cause — a queue built with no consumer

`marg_router.py` line 314–318:

```python
if verdict == "VERIFIED" and sig and sig.get("uploadable"):
    shutil.copy2(path, os.path.join(cfg["outbox"], name))
    res["uploaded"] = "queued"
    out("            -> queued for upload in Outbox")
```

**Nothing on any machine reads `_outbox`.** Grep of manojz *and* the whole repo for an outbox
sender returns nothing. Every VERIFIED sale report since 17-Aug is still sitting there — 8 files,
none sent from that path.

The only real sender is `SEND_TO_CLINIC.bat` → `POST /finance/api/marg-push`, which lives on the
**medical PC** and is fired by a human double-clicking `GUARD_AND_SEND.bat`. Scheduling it was left
open as S195 backlog item #2 ("Task Scheduler unattended run — schedule time TBD"). It has not been
double-clicked since 22-Aug.

**So the S195 watcher work quietly replaced the human's reason to click the sender.** Before S195,
the operator ran GUARD_AND_SEND and the report went. After S195, the export is captured
automatically, a cmd window flashes, everything *looks* handled — and the one manual step nobody
removed stopped being done. The automation did not break the push; it hid it.

### Aggravating factor: the word `queued` is a lie
`uploaded=queued` in `index.csv` and *"queued for upload in Outbox"* on screen both assert a
pending send. There is no queue-runner. Any future reader of that index would conclude these
reports were on their way to the server.

## 4 · Days now missing from the books

Nothing has been accepted by the server since **18-Aug** (id 6, the corrected 25,176 day).
Reports exist locally and verified for **21, 22, 23(Sun), 24 Aug** — check the approvals page
against the archive before assuming only 24-Aug is outstanding.

## 5 · The health check should have caught this

`GET /finance/health` carries a **"Marg push freshness"** check built at S195 for exactly this
failure, and last accepted push is now **3 days** old. Either it is red and the warning was not
seen, or it has died into its `except` the way both A4 cards did at S196 (F-162). **This needs
verifying from the box** — a freshness check that stays green through a three-day outage is worse
than no check at all.

## 6 · Fix

**Immediate (today, no code, no secrets in chat):** on manojz, drag
`SALE_BILLWISE_DETAIL__2026-08-24__20260825-082715__3b456d9c.XLS`
onto `D:\Downloads\margsync\SendToClinic\SEND_TO_CLINIC.bat`. That sender accepts a dragged file and
already holds its own `token.txt`. Expect *ACCEPTED — report clinic server pahunch gayi hai*.
If it answers **401**, the token was rotated after 20-Aug; send from the medical PC's
`GUARD_AND_SEND.bat` instead and treat the manojz token as stale.

**Permanent (proposed, awaiting owner OK):** write the missing outbox sender on manojz — post each
queued file to `/finance/api/marg-push`, dedup by md5 against `sent_hashes.txt`, write the real
outcome back into `index.csv` (`sent` / `HTTP nnn`), and call it from the last line of
`PULL_FROM_MEDICAL.bat` so the existing 10-minute task drains the queue. This finishes a design
already 90% built, puts the sender on the machine that is reliably on, and **removes the human
click entirely** — which is the actual defect. It also retires S195 backlog item #2.

## 7 · Faults to mint

- **F-a (this one):** `_outbox` queue with no consumer; `uploaded=queued` asserts a send that
  cannot occur. Sale reports stranded 3 days, silently.
- **F-b:** the router names a file by the **title's requested range** rather than the dates actually
  present in the data. `…2026-08-23_to_2026-08-24` contains 24-Aug only. A future reader could take
  that name as evidence 23-Aug traded zero, when 23-Aug was simply a Sunday out of scope.
- **F-c (pending verification):** Marg-push freshness health check apparently green through a
  3-day outage. Confirm from the box.

---
*S201 · Diagnosed from the manojz mirror and archive only. Nothing was written, sent or changed on
any machine. No patient identifiers reproduced; no tokens read or printed.*
