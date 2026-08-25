# MARG INGESTION — THE REFERENCE

**v1 · 25-Aug-2026 (S201). The server-side half: what happens to a Marg export after it reaches the
VPS.** Companion to `MARG_PIPELINE_REFERENCE_v1.md`, which covers capture and transport up to the
POST.

Every statement here was verified against the **live bytes** (`finance_app.py 2c99b2c6` →
`d930b6b5`, `finance_ingest.py 6cb83302`, `marg_report.py 6411a57d`) and against the **live
database**, queried read-only on 25-Aug. Nothing is inferred from a doc.

---

## 0 · THE ONE RULE THAT EXPLAINS EVERYTHING

**The Marg import never touches the money.**

- **Money** = `day_line` — what the maker types when filing the day. `v_cash_ledger.revenue_p` is
  literally `SUM(day_line.amount_p)`.
- **Attribution** = `sale_item` — which patient bought what, populated from the Marg export.

`finance_ingest.py` **contains no reference to `day_line` at all.** It cannot change a rupee of
recorded revenue. This is D313, and it is the reason a half-attributed day is not a half-counted day.

Consequence: **a "books vs Marg" difference is never missing money.** It is the portion of the day
that has not yet been attributed to a patient.

*Verified live: 21-Aug books = ₹49,181.00 and 24-Aug books = ₹12,964.00 — each exactly the Marg
report's own total, because the maker types the day from that report.*

---

## 1 · THE CHAIN

```
POST /finance/api/marg-push          token-scoped, stage-only
   parse (marg_report) -> survey -> per-day replayable payload
   file DELETED inside the same request (S186) -- the VPS never keeps an export
   -> marg_push_staging (status pending)
   -> for any day with no day_entry: data_flag MARG_DAY_NOT_FILED (F-113)
          |
          |  nothing has entered the books yet
          v
APPLY  -- two doors, same guarded path
   a) checker presses Apply            /finance/api/marg-push/apply   require("checker")
   b) AUTO-REPLAY: the maker files a day that has a pending push (S194)
          |
          v
finance_ingest.ingest_day(con, unit, date, "marg_export", lines_csv, ...)
   supersede + delete any earlier batch for the day
   adapter_csv -> lines
   per line: the CONFIDENCE GATE  ->  sale_item   |   sale_item_review
   finance_returns.load_lines(items_csv) -> sale_line_item
   reconcile_day_attribution()
          |
          v
sale_item (attributed)      sale_item_review (parked, resolvable by a human)
```

---

## 2 · STAGE 1 — THE PUSH

```
POST https://followup.dr-manoj.in/finance/api/marg-push
Header: X-Finance-Marg: <FINANCE_MARG_TOKEN>
Body:   multipart/form-data, field "file", filename "REPORT_1.XLS"
```

| response | meaning |
|---|---|
| `200` `{"ok":true,"verdict":"ACCEPTED-FOR-REVIEW","days":[…],"bills":n,"item_lines":n,"id":n}` | staged; **nothing in the books** |
| `200` + already-received | same content already staged |
| `401` `{"error":"not_signed_in"}` | **the token did not match** — the request fell through to the session gate. This is what a stale token looks like; it never says "bad token" |
| `422` `column_map_mismatch` | the parser's columns do not match `ingest_column_map` |
| `503` | `FINANCE_MARG_TOKEN` absent server-side — fail-closed (F-84) |

**The endpoint does NOT dedupe by content across pushes.** Sending the same bytes twice stages
twice. Only client-side state prevents that (this is why `marg_gate.py` keeps `_outbox_state.json`).

**What is stored** — `marg_push_staging.parsed_json`, one entry per day:

```python
days_payload.append(dict(date=iso_d,
                         business_date=iso_d,     # added S201_A1FIX
                         net_p=d["net_p"],        # added S201_A1FIX
                         expect=nonzero.get(iso_d, 0),
                         lines_csv=…, items_csv=…))
```

`expect` is the count of bills with a non-zero net — the number of rows the replay must read back.

---

## 3 · STAGE 2 — APPLY, AND THE GUARDS

`api_marg_push_apply` reads only `date`, `expect`, `lines_csv`, `items_csv`. Every other key is
ignored (which is why S201_A1FIX was safe).

Per day:
- **no `day_entry` → skipped**, recorded in `still_not_filed`. The export is NOT consumed; it waits.
- `ingest_day(...)` → `rows_read`
- **`rows_read != expect` → `con.rollback()` and the whole day aborts.** A half-loaded day is never
  left behind.
- items CSV loaded into `sale_line_item`; `irows and n_lines == 0` → rollback as well.

**Auto-replay (S194):** filing a day that already has a pending push applies it immediately. Proven
live — 21-Aug was filed after its push and batch 127 exists. There is a selftest for this path.

---

## 4 · STAGE 3 — `ingest_day`, AND THE CONFIDENCE GATE

**Supersede first** (`finance_ingest.py` ~408-417): every earlier batch for the day has its
`sale_item` and `sale_item_review` rows **deleted** and is marked `superseded`. Re-applying a day is
therefore a clean replace, never an accumulation. *Verified live: 24-Aug batch 128 = `superseded`,
0 rows — one of the duplicate pushes, correctly discarded.*

**Then, per line, the gate:**

```python
cid  = clinic_id column (from marg_report)
name = patient_name column
conf = 0.99
if not cid and name:
    cid, name, conf = split_clinic_id(name)      # RE-PARSE the name field
...
low_conf   = conf < min_conf                     # ingest.min_confidence, default 0.70
anonymous  = not cid and not name
structured = adapter != "sarvam_ocr"             # marg_export -> True
if low_conf or (anonymous and not (anon_to_walkin and structured)):
    -> sale_item_review
else:
    -> sale_item, patient resolved (WALK-IN if no id)
```

`split_clinic_id()` scores **one text field**, and `phone_last4` never enters it:

| what the name field holds | confidence | outcome |
|---|---|---|
| marg_report supplied a clinic_id | **0.99** | attributed |
| an ID **and** a name | **0.95** | attributed |
| an ID, no name | **0.60** | **parked** |
| a name, no ID | **0.50** | **parked** |
| nothing at all (no id, no name) | **0.99** — the re-parse never runs | attributed to **WALK-IN** |

**Two consequences that surprise everyone:**

1. **A bill with a name is treated "worse" than a bill with nothing.** That is deliberate, not a
   bug. The S186/F-114 comment states the principle: *"A review queue is for lines a human can
   resolve."* A nameless bill has nothing to look up, so it goes to WALK-IN; a named bill is
   resolvable, so it waits.
2. **`marg_report` and `finance_ingest` both look for a clinic ID, by different rules.** A bill
   `marg_report` calls id-less can still be attributed when `split_clinic_id` finds an ID inside the
   name text. *Verified live: 18-Aug bill A003039 (₹190) is id-less to `marg_report` and was
   ingested.* This is why the approvals page's *"N bills carry no clinic ID and will attribute to
   WALK-IN"* **overstates what actually parks, and names the wrong destination** — they go to
   review, not WALK-IN.

**Also applied per line:** `home_med` tagging (S194 ⭐2, name matches `home\s*medi`), and mode-flip
detection writing `mode_change_log` (S194 ⭐3).

---

## 5 · BATCH STATUS — WHAT IT MEANS

| status | set when |
|---|---|
| `ok` | every line was attributed |
| `partial` | **any** line went to review (`if review:` → partial, whether or not anything was accepted) |
| `superseded` | a later batch replaced it; its rows were deleted |

`partial` is the system telling the truth: *some lines are parked.* It is **not** an error.

*Live on 25-Aug:* 18-Aug batch 126 `partial` 22 rows · 21-Aug batch 127 `partial` 21 rows ·
24-Aug batch 129 `partial` 17 rows, batch 128 `superseded` 0 rows.

---

## 6 · THE SIGNED NET — ONE EXPRESSION, EVERY READER

`sale_item.amount_p` has a **non-negative constraint**, so a credit note is stored as a *magnitude*
plus a `_return` service. A plain `SUM(amount_p)` therefore **adds** a refund.

```python
marg_net_sql(a) = SUM(CASE WHEN a.service LIKE '%return%' THEN -a.amount_p ELSE a.amount_p END)
```

This exists because on **18-08-2026** the day held one credit note of ₹1,640: the true net was
**20,599** and a second reader displayed **23,879** — out by exactly 2 × 1,640, and close enough to
the figure under dispute to send a real investigation down the wrong road for an hour.

*Verified live, same day, same two numbers: naive `SUM` = 23,879.00, `marg_net_sql` = 20,599.00.*

**Rule: never write a second way of summing Marg rows.**

---

## 7 · WHAT EACH SURFACE ACTUALLY MEASURES

| surface | compares | goes green when |
|---|---|---|
| **This month vs Marg** (health) | `v_cash_ledger.revenue_p` (whole day, typed) **vs** `marg_net_sql(sale_item)` (attributed only) | **never**, on any day with one parked line |
| **Day Page variance** | typed total vs Marg, threshold ₹2,000 | the maker's total matches |
| **`TOTAL_VS_MARG`** (A1, save-time) | typed total vs the staged report's `net_p` | dead until S201_A1FIX; live now |
| **`MARG_DAY_NOT_FILED`** | a push arrived for a day never filed | the day is filed and re-loaded |

**The month check therefore measures the review queue.** Confirmed to the rupee on every day:

| day | open review lines | review value | health difference |
|---|---|---|---|
| 17-Aug | 9 | 9,990.00 | 9,990.00 |
| 18-Aug | 8 | 4,577.00 | 4,577.00 |
| 19-Aug | 7 | 3,500.00 | 3,500.00 |
| 20-Aug | 4 | 1,331.00 | 1,331.00 |
| 21-Aug | 16 | 30,045.00 | 30,045.00 |
| 24-Aug | 5 | 2,425.00 | 2,425.00 |
| **total** | **49** | **51,868.00** | **51,868.00** |

---

## 8 · THE REVIEW QUEUE AND THE DOCTERZ PLAN

The queue exists so bills can later be matched to the **Docterz EMR patient master**, assigning
revenue to named patients. Until that master reaches the VPS (migration planned; the follow-up
tracker still runs on the owner's PC), **these lines stay parked by design.**

**The queue already holds exactly the right set.** Nameless bills — unmatchable by anything — are
absorbed into WALK-IN and never queued. Named-but-unidentified bills are parked. *Verified on
18-Aug: 8 of 8 parked bills carry a name; 5 of 8 also carry a phone; none have neither.*

**What a parked row preserves.** `sale_item_review` has no `bill_no` or `phone` column, but
`raw_text` holds the whole CSV row as JSON:

```
bill_date · bill_no · clinic_id · patient_name · phone_last4 · description · amount · mode · gross · disc
```

**The match key will be `bill_date + patient_name + phone_last4`.** The phone is stored as **last 4
digits only** (F-86 masked it deliberately) — so a full-number lookup against Docterz is not
possible. Worth designing for now rather than discovering later.

**A re-apply wipes and rebuilds the queue** for that day (`DELETE FROM sale_item_review WHERE
ingest_batch_id=?`). So resolutions must be recorded somewhere that survives a re-import, or a
re-load of an old day will discard them.

---

## 9 · FAULTS IN THIS HALF

1. **The month check compares incomparable things** → permanently red at `bad`, which drives the
   portal tile. Exactly the "wallpaper" condition the S195 flags-as-info ruling exists to prevent.
2. **`days_differing[:5]` truncates silently** — no "and N more", unlike the sibling line directly
   above it. 24-Aug was differing and was not shown; found by arithmetic before code.
3. **The approvals page's WALK-IN warning is wrong twice** — it uses `marg_report`'s id count (which
   `finance_ingest` may overrule) and names WALK-IN when the destination is review.
4. **Two parsers look for a clinic ID** (`marg_report` and `split_clinic_id`). The same class of
   fault `marg_net_sql` was created to end.
5. **`ingest.min_confidence` = 0.70 is tuned for OCR**, and applies unchanged to a *structured* Marg
   export where the only uncertainty is a missing ID. Whether 0.70 is right here is an owner
   decision, not a code one.

---
*MARG_INGESTION_REFERENCE v1 · S201 · verified against live bytes and the live database
(`?mode=ro`). No patient identifiers reproduced; no tokens read or printed.*
