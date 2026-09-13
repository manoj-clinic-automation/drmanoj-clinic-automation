# S246_AMIR_LIST_REOPEN — what the bill list holds, and a day that can be opened again

Built 13-Sep-2026 (S246) on the file that is **live now** (`79eb701f`, the one-tap bill screen
installed earlier today), to two owner rulings:

> show only purchase bills from 1sept onwards all previous are settled, and only not ok marked
> bills shd appear till they are corrected and you get ok for them

> din band kar diya / then there is no way to open the flow again

**This kit supersedes the `S245_AMIR_BILLTAP` folder.** That folder was rebuilt after it had
already been installed, so its installer now refuses on the pin — correctly, and without touching
anything. Everything it carried is in here, rebuilt against the live file.

## 1 · What the list holds

- **`BILLS_FROM = 2026-09-01`.** Bills dated before it are settled and are never shown again.
  `AMIR_BILLS_FROM` in the environment moves the line at the next settlement — no kit needed.
- **A flagged bill stays**, in its own band — *Flag kiye hue bill* — carrying what he wrote and
  when (*"Aapne likha tha: Kam maal aaya · 13-09 09:40"*). It leaves **only** when he marks it
  *Theek hai*.
- **A flag never holds the day open.** A supplier's credit note can take a fortnight. Step 5 is
  done when every *untapped* bill has been answered; the flags are a count on the close screen.
- **Marking a flagged bill Theek hai settles the claim** Darpan was chasing — `state=settled`,
  `settled_outcome=amir_ok`, with who and when.

### The duplicate-rows fix that had to come with it

A bill rides in **every** cumulative 1st-to-date export after the one that first carried it, and
`_bills()` joined bill to export **without grouping**. With more than one BILLWISE export, one
unanswered bill was listed — and **counted, in the gate that decides whether a day can close** —
once per export it appears in. It has barely shown yet because step 4 could not verify before
S243 (F-455). Now grouped by the bill, with `seen_day` = the **earliest** export that carried it,
which is what makes *pichhla baaki* mean anything. The old rolling 45-day cutoff is gone: a
rolling window would have hidden an unresolved flag once it aged out.

## 2 · DIN BAND is no longer a dead end

| | |
|---|---|
| **the 1→7 banner** | every step is now a **link**, on every screen. That alone is the way back in from anywhere. |
| **the closed screen** | names the three places he comes back for — *Bill dekhiye* (with the flag count), *Salt aur naam*, *Report ki jaanch* — and says **"N naya bill aa gaya hai"** when one has arrived since the close |
| **opening the day again** | **Din phir se kholiye**. The close is undone, everything already done stays done, and he lands on whatever is actually unfinished |
| **the record** | `reopened_at` and `reopened_by` are written. The owner's page reads *"CLOSED at 18:40 (reopened 17:05 by amir)"* and the visit-summary JSON carries both. A reopen is never silent |
| **a plain post** | does **not** reopen — only the explicit button does (walked) |

Two columns are **added** to `amir_day` (`reopened_at`, `reopened_by`), lazily and idempotently,
under the table that is already live. Nothing existing is altered or dropped; a four-column table
with rows in it is grown in place and keeps its data (walked).

## 3 · What deliberately does not change

`GATE_STEPS = (2, 4, 5, 6)` · the five answers and the four that raise a claim · he types no bill
number · one claim per deficient bill, never a second on re-answering · the S244 report band ·
still **no JavaScript**, no event handler, no `<script>` · the owner's page stays English.

## Proof — `EVIDENCE_S246.txt`, verbatim. **156 checks, 156 ok, 0 failed.**

- **`walk_amir_reopen_s246.py` — 41 checks.** The schema grown under a live four-column table and
  its rows kept · idempotent on a third run · all seven banner steps are links on every screen ·
  the closed screen naming the ways back and the flag count · a new bill after the close
  announced · a plain post **not** reopening · the reopen clearing the close, recording who and
  when, dropping the step-7 tick, landing him where the work is, **leaving every other tick and
  every disposition untouched** and the flag standing · re-closing and saying it had been opened
  again · the owner's page and the JSON carrying it, in English · healthz naming the kit.
- **`walk_amir_billtap_s245.py` — 53 checks**, the list rules and the one-tap screen.
- **`walk_amir_processing_s244.py` — 62 checks**, step 3 and step 4 regression.
- All three run **on the box** before the installer places anything.
- **Negative control:** the S246 walk against the live file fails at A2 and B1.
- `patch(live bytes) == the kit file, byte for byte` — 20 asserted single-match edits.
- Mock install from a frozen copy: installs · ALREADY INSTALLED on re-run · a live file that is
  not the pin refused with the file **byte-identical**.
- F-185 gate over every kit file: clean. All LF (F-294).

## Install — ONE line on the VPS, after the owner's publish

```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S246_AMIR_LIST_REOPEN/install_S246_AMIR_LIST_REOPEN.sh
```

Refuses unless `/root/finance/amir_day.py` is **exactly** `79eb701f2df14e58c77e130a77b972ba`.
Gates: `SUMS.md5` + `KIT_ID` → the live pin → the patcher's selftest on the live bytes → **all
three walks on the box** → `amir_day.py.bak_S246_79eb701f` → place → `py_compile` → import smoke
under the unit's environment (routes, `GATE_STEPS`, the five answers, a valid `BILLS_FROM`, and
the two columns actually appearing on a four-column table) → restart → healthz 200 within 20 s.
Any red after placing: the file is restored and the service restarted. Re-run → `ALREADY
INSTALLED`.

**Predicted to-pin:** `amir_day.py` → `a9f2062267ebac59e02fdb0f88e775de`.

Rollback by hand (the added columns are harmless to the old code — it never selects them):

```
\cp -f /root/finance/amir_day.py.bak_S246_79eb701f /root/finance/amir_day.py && systemctl restart clinic-finance
```

To move the settlement line later, without a kit:

```
systemctl set-environment AMIR_BILLS_FROM=2026-10-01 && systemctl restart clinic-finance
```
