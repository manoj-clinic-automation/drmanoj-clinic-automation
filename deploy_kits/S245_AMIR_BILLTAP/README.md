# S245_AMIR_BILLTAP — step 5: one tap per bill, reasons only when they are needed

Built 13-Sep-2026 (S245) to the owner's ruling of the same day:

> bill check kariye — make it user friendly, all collapsed default shd be bill ok / not ok — if
> not ok tapped then ask only ask options, its very cumbersome right now

## Why

A normal day is 5–8 bills, and every bill carried **five radio buttons, all open**. Forty choices
on one phone screen, when the answer to almost every bill is the same one word.

## What changes — one file, `/root/finance/amir_day.py`, replaced whole

| before | now |
|---|---|
| five options open on every bill | **two taps: `Theek hai` · `Theek nahi`** |
| *kam maal aaya · deal nahi mili · discount kam · aur koi baat* always on screen | the four reasons sit **inside `Theek nahi`, shut**, and open only when he taps it |
| 8 bills → 40 visible choices | 8 bills → 16 taps, and he touches one per bill |
| the Save button at the bottom of a long scroll | a **sticky save bar**, always reachable |
| no count | *"3 bill. Har bill par ek tap. Kuch gadbad ho to hi \"Theek nahi\" kholiye."* |

It is still **one radio group per bill** — picking a reason un-picks *theek hai* by itself — so
**the form the server reads is unchanged, field for field**: `k_<i>`, `r_<i>`, `n`. `_save_bills()`
is not touched.

Folding is a `<details>` element, so the page still carries **no JavaScript** and no event
handler of any kind (walked).

## The one thing that had to go, on purpose

`required` is gone from the radios. A `required` control **inside a shut `<details>` cannot be
focused**, and the browser then refuses the whole submit without saying why — a hidden dead end on
a phone. The forcing was never the browser's job: an unanswered bill is simply **not written** and
comes straight back on the list, which is the stronger guarantee and is walked here again.

## What deliberately does not change

- `GATE_STEPS = (2, 4, 5, 6)`; the day does not close while a bill is untapped.
- The five answers and the four that raise a claim: unchanged.
- He still types no bill number — the key travels in the hidden field.
- One claim per deficient bill, never a second on re-answering.
- The S244 report band still rides above the bills.
- No schema change, no new route, no cron, no service file, no other file.

## Proof

`EVIDENCE_S245.txt`, verbatim. Two live-shape walks — a real Flask app, a real sqlite database
with the real column shapes, driven over WSGI the way his phone drives it:

- **`walk_amir_billtap_s245.py` — 40 checks, 40 ok, 0 failed.** The shape of the screen (one tap
  per bill · the `<details>` shut by default · the four reasons present but folded · **no
  `required` anywhere** · one hidden key per bill · five choices in one radio group · the count ·
  the sticky save bar · a `<script>` supplier escaped · rupees readable) and the behaviour
  (*theek hai* written and no claim · a reason written and **exactly one** claim · an unanswered
  bill **not** written and returning alone · a garbage reason value refused · no second claim on
  re-answering · yesterday's leftover as *pichhla baaki* · the close refused and **writing
  nothing**, then closing once every bill is tapped · **no ten-digit phone-shaped number on any
  screen** (F-185) · **no `onclick`/`onchange` introduced**).
- **`walk_amir_processing_s244.py` — 62 checks, 62 ok, 0 failed**, re-run unchanged as a
  regression suite: everything S244 proved about step 3 and step 4 still holds.
- **Negative control:** the S245 walk against the live S244 file fails at A1–A4. A walk that
  passes on the unchanged file proves nothing (S208).
- `patch(live S244 bytes) == the kit file, byte for byte` — 4 asserted single-match edits.
- Mock install: installs · re-run says ALREADY INSTALLED · a live file that is not the pin is
  refused with the file left byte-identical.
- F-185 gate over every kit file: clean. All files LF (F-294).

## Install — ONE line on the VPS, after the owner's publish

```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S245_AMIR_BILLTAP/install_S245_AMIR_BILLTAP.sh
```

Refuses unless `/root/finance/amir_day.py` is **exactly** `aad400fa9c4b7804229c9f175c86533b`
(the S244 pin). Gates: `SUMS.md5` + `KIT_ID` → the live pin → the patcher's selftest on the live
bytes → **both walks on the box** → `amir_day.py.bak_S245_aad400fa` → place → `py_compile` →
import smoke under the unit's environment → restart → healthz 200 within 20 s. Any red after
placing: the file is restored and the service restarted. Re-run → `ALREADY INSTALLED`.

**Predicted to-pin:** `amir_day.py` → `79eb701f2df14e58c77e130a77b972ba`.

Rollback by hand:

```
\cp -f /root/finance/amir_day.py.bak_S245_aad400fa /root/finance/amir_day.py && systemctl restart clinic-finance
```
