# S245_AMIR_BILLTAP — step 5: one tap per bill, and a list that holds only live work

Built 13-Sep-2026 (S245) to two owner rulings of the same day:

> bill check kariye — make it user friendly, all collapsed default shd be bill ok / not ok — if
> not ok tapped then ask only ask options, its very cumbersome right now

> show only purchase bills from 1sept onwards all previous are settled, and only not ok marked
> bills shd appear till they are corrected and you get ok for them

## 1 · The screen

| before | now |
|---|---|
| five radio options open on every bill | **two taps: `Theek hai` · `Theek nahi`** |
| the four reasons always on screen | inside `Theek nahi`, **shut**, opening only when he taps it |
| 5–8 bills → 25–40 visible choices | 5–8 bills → one touch each |
| Save at the bottom of a long scroll | a **sticky save bar** |
| no count | *"N bill. Har bill par ek tap. Kuch gadbad ho to hi 'Theek nahi' kholiye."* |

Still **one radio group per bill**, so **the form the server reads is unchanged, field for field**
(`k_<i>`, `r_<i>`, `n`). Folding is a `<details>`, so the page still carries **no JavaScript** and
no event handler (walked).

## 2 · What the list holds

- **`BILLS_FROM = 2026-09-01`.** Bills dated before it are settled and are never shown again.
  Env `AMIR_BILLS_FROM` moves the line the next time a period is settled — no kit needed.
- **A flagged bill stays.** Answer anything but *Theek hai* and the bill keeps its place, in its
  own band — **Flag kiye hue bill** — carrying what he wrote and when (*"Aapne likha tha: Kam maal
  aaya · 13-09 09:40"*). It leaves only when he marks it **Theek hai**.
- **A flag never holds the day open.** A supplier's credit note can take a fortnight; step 5 is
  done when every *untapped* bill has been answered. The flags are listed on the close screen as a
  count, not a blocker.
- **Marking a flagged bill Theek hai settles the claim** Darpan was chasing — `state=settled`,
  `settled_outcome=amir_ok`, with who and when. Nobody chases a bill that is already right.

## 3 · Found while building this — the duplicate bill rows

A bill rides in **every** cumulative 1st-to-date export after the one that first carried it, and
`_bills()` joined bill to export without grouping. The moment there is more than one BILLWISE
export, one unanswered bill is listed **once per export it appears in** — and the count the owner
sees, and the gate that decides whether a day can close, count it that many times too. It has not
bitten yet only because step 4 could never verify before S243, so the list has barely run.

Fixed here: the rows are grouped by the bill itself, and `seen_day` is the **earliest** export that
carried it — which is what makes *pichhla baaki* mean anything. The old rolling 45-day cutoff is
gone, replaced by `BILLS_FROM`; a rolling window would have hidden an unresolved flag once it aged
out, which is exactly what the owner asked against.

## 4 · The one deliberate removal

`required` is gone from the radios. A `required` control **inside a shut `<details>` cannot be
focused**, and the browser then refuses the whole submit without saying why — a dead end on a
phone. The forcing was never the browser's: an unanswered bill is **not written** and comes
straight back on the list.

## 5 · What deliberately does not change

`GATE_STEPS = (2, 4, 5, 6)` · the five answers and the four that raise a claim · he types no bill
number · one claim per deficient bill, never a second on re-answering · the S244 report band still
rides above the bills · no schema change, no new route, no cron, no service file.

## Proof — `EVIDENCE_S245.txt`, verbatim

- **`walk_amir_billtap_s245.py` — 53 checks, 53 ok, 0 failed.** The screen (one tap per bill · the
  `<details>` shut · reasons folded · **no `required` anywhere** · one hidden key per bill · five
  choices in one radio group · the count · the sticky bar · a `<script>` supplier escaped). The
  list (a pre-`BILLS_FROM` bill **never shown** · a bill riding in **three** exports listed
  **once** and counted once · *pichhla baaki* judged by the export that first carried it). The
  flag (stays, with what he wrote · does **not** hold the day open · clears **only** on *Theek
  hai* · **settles the claim**, named and attributed · the other claim untouched · no second claim
  on a changed reason). And the standing properties (a garbage reason refused · the close refused
  and **writing nothing**, then closing · **no ten-digit number on any screen**, F-185 · **no
  `onclick`/`onchange`/`<script>` introduced**).
- **`walk_amir_processing_s244.py` — 62 checks, 62 ok, 0 failed**, re-run unchanged as a
  regression suite. Both walks run **on the box** before the installer places anything.
- **Negative control:** the S245 walk cannot even start against the live S244 file — no
  `BILLS_FROM`. A walk that passes on the unchanged file proves nothing (S208).
- `patch(live S244 bytes) == the kit file, byte for byte` — 11 asserted single-match edits.
- Mock install from a frozen copy: installs · ALREADY INSTALLED on re-run · a live file that is
  not the pin refused with the file **byte-identical**.
- F-185 gate over every kit file: clean. All LF (F-294).

## Install — ONE line on the VPS, after the owner's publish

```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S245_AMIR_BILLTAP/install_S245_AMIR_BILLTAP.sh
```

Refuses unless `/root/finance/amir_day.py` is **exactly** `aad400fa9c4b7804229c9f175c86533b`
(the S244 pin). Gates: `SUMS.md5` + `KIT_ID` → the live pin → the patcher's selftest on the live
bytes → **both walks on the box** → `amir_day.py.bak_S245_aad400fa` → place → `py_compile` →
import smoke under the unit's environment (routes, `GATE_STEPS`, the five answers and a valid
`BILLS_FROM`) → restart → healthz 200 within 20 s. Any red after placing: the file is restored and
the service restarted. Re-run → `ALREADY INSTALLED`.

**Predicted to-pin:** `amir_day.py` → `d5d485dd85fefd80b41372ff8cf1082c`.

Rollback by hand:

```
\cp -f /root/finance/amir_day.py.bak_S245_aad400fa /root/finance/amir_day.py && systemctl restart clinic-finance
```

To move the settlement line later, without a kit:

```
systemctl set-environment AMIR_BILLS_FROM=2026-10-01 && systemctl restart clinic-finance
```
