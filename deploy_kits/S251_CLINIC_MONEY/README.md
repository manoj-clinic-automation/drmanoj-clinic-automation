# S251_CLINIC_MONEY — the morning match · other UPI · the float · physiotherapy · F-459

**This is the S249 build, re-issued under the next number (F-458).** Between the S249 commit and its install, kit
`S250_STAFF_REGISTER_TILE` moved `/root/portal/tile_grants.json` v14 → v15 (`932f7bd0…`, the Staff Register
mask lifted for shavez, shivani, alisha). S249's installer correctly refused at the currency gate. Nothing
else differs: the grants file here is **v16 = the live v15 + the S249 grants**; every other file is byte-identical
to S249. S249_CLINIC_MONEY is superseded and must not be installed.

Built 13-Sep-2026 on the files that are live now (every pin reproduced byte-exact this session):
`finance_clinic_day.py 56fb7619` · `clinic_register.py c6b87682` · `finance_app.py 912398e9` ·
`portal.py 06f1b378` · `tile_grants.json v15 932f7bd0 (S250)`. Plan: `S249_CLINIC_MONEY_FINAL_PLAN`.

## The owner, 13-Sep-2026 — the rulings this kit carries

> cross match of both, and a human friendly analysis take away to do away the manual matching in
> morning, only your flags will be needed · reception staff do the morning first pass, shavez does
> the first pass when they are not available, and shavez is the checker when they do the first
> pass, i get minimum required flags, all flags stay in staff apps till reconciled · physiotherapy
> … add a backend physiotherapy revenue table … manoj Bhati also gets this, a new pwa member …
> he only views it … the data he gets is only and only of the physiotherapy part · icici upi not
> working – paid to other upi – box opens · reception staff want some loose currency … 2500 …
> at end of day put also what is the balance … so the cash flow and calculation stays stable and
> accurate

## What is in it — one rule: every rupee has one channel, and each channel says whether an independent record exists

| piece | where | what |
|---|---|---|
| **F-459** | `finance_clinic_day.py` | ONE "our online" figure (`our_online_p`: online bills + the online legs of split bills), read by the day card, the MPR page and the reconciler. The day card now also names money that went to another UPI and links the match. |
| **The reconciler** | `clinic_money.py` `match_day()` | four passes, cheapest first — the day's money · by head · by tender · transaction pairing against the MPR — then the explanation layer: other UPI, tender swap, head swap, rung as cash, not settled yet (one banking day), never in the MPR (two banking days → the owner), whole-fee hint, under ₹100 is a note. Pure: changes no figure, invents no adjustment. |
| **The staff card** | `/finance/clinic/match/<date>` | reception's first pass (answer every flag: a line, or *Cannot explain*), Shavez's second (agree → reconciled; disagree → Dr Manoj). Reception away → Shavez's pass closes the day **"one pass only"**. Flags live in `clinic_money_flag` until reconciled — never dismissed, never aged out; a corrected sheet marks a flag *cleared by the data*, never deletes it. |
| **The owner's line** | `/finance/clinic/money` | exactly four things: could not be explained · maker/checker disagree · money that never lands · a sheet unfilled after 14:00 the next day. Plus the month's channels with no independent record: other UPI (with the *settled* tick), physiotherapy, the float (short days, change requests), one-pass days. And the float's issue / top-up form. |
| **Other UPI** | on the counter sheet | *ICICI UPI not working? → Paid to another UPI*: the amount is the only compulsory field; phone and app remember themselves; bill optional; one reason per day, three taps; *+ add another*. Kept out of the bank match by the sheet's own three-records line and by the reconciler. |
| **The float** | on the counter sheet, issued from the owner's page | issued once (₹2,500: 5×200, 10×100, 10×50), counted at close on a denomination grid pre-labelled with the standing composition, a change request line, a shortfall that carries. **Never revenue:** `expected_handover_p = day's cash + float open − float kept`; on a normal day the float appears nowhere. |
| **Physiotherapy** | `/finance/physio` | the revenue table: current month open, earlier months folded, a year total. Reception writes it from the counter sheet (now with *handed to Dr Manoj / Dr Bhawna*); the doctors tap **received**; Bhati reads it in Hindi. |
| **Bhati's hard edge** | `seed_s249.py` + the gate | the schema allows only maker/checker/viewer, so "the physio role" is a NEW unit `physio`; Bhati is a viewer there and holds **no clinic row**, so the app's own front gate refuses him every `/finance/clinic/...` address (proven through the real gate, 15 addresses + the API). A stray clinic row for him is deactivated by the seed. |
| **Tiles** | `portal.py` + grants v16 | *Morning match* (shavez, shivani, alisha by name; the doctor lands on his line) · *Physiotherapy* (bhati, bhawna by name). Bhati masked from Attendance / Staff Register / Forms & Downloads / Scan Purchase, as Amir is. |

The checker is a **setting**, not code: `clinic_money.checker = shavez` (seeded). The three clinic
makers stay makers; the doctors, clinic checkers, get the owner view.

## Proof — `EVIDENCE_S249.txt`, verbatim

- `patch_s249.py --selftest`: **patch(live bytes) == kit file, byte for byte** for
  `finance_clinic_day.py`, `clinic_register.py` and `portal.py`; every anchor asserted to match
  exactly once; a second pass says *already*. **`finance_app.py` is not shipped** — F-185 keeps it
  out of the repository (its selftest fixtures carry number-shaped text, and the publish gate
  refuses it) — so the installer patches it **from the live bytes on the box** and refuses unless
  the result is exactly the predicted `1fc62335…` (the same two edits, proven offline).
- **`walk_s249.py` — 126 checks, 126 ok** — the REAL patched `finance_app.py` over a real sqlite
  built from the real schemas, every live sibling module beside it, requests through the app's own
  front gate; then the patched `portal.py` imported with grants v16 and asked who is shown what.
  It walks: the mount; the seed (twice, then a stray row); Bhati refused at 15 addresses and the
  API; **the 12-Sep shape** (₹2,050 to a personal phone against bill 2353's entry, a ₹100 rung as
  cash, a split bill) → *nothing to do*, both differences explained, the day card and the MPR page
  agreeing on one figure; the counter sheet saving physio *handed to*; the other-UPI box (blank
  amount refused, add, remember, add another, remove, audited); the S224 drawer loop closing
  other-UPI-aware; a day one ₹600 consultation ahead → one flag with the hint, answered, checked,
  closed on two passes, kept as the record after the sheet is corrected; the checker alone → one
  pass only; ₹500 that never reached the bank → a note the morning after, the owner's flag after
  two banking days; an unfilled sheet → staff flag, then the owner's after 14:00; a tender swap
  explained; ₹50 a note; the float issued, kept, short, topped up, and the handover arithmetic at
  each step; the physiotherapy table in Hindi for Bhati with nothing of the doctor's revenue on it;
  Dr Bhawna tapping received; the owner's page, settle and reconcile; who is shown which tile.
- **Mock install** from a frozen copy of the live tree: GREEN end to end; re-run → ALREADY
  INSTALLED; a wrong pin → LIVE CODE CURRENCY GATE, nothing installed; a red healthz after placing
  → every file restored to its pin.
- F-185 gate clean; every file LF; six pages screenshotted at phone width and read.

## Install — ONE line on the VPS, after the owner's publish

```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S251_CLINIC_MONEY/install_S251_CLINIC_MONEY.sh
```

Refuses unless all five live files are exactly their pins. Gates in order: kit SUMS + KIT_ID → pins →
the patcher's selftest on the box (and `finance_app.py` patched from the live bytes into `/tmp`,
md5 checked against the prediction) → py_compile → **the 126-check walk on the box** (scratch db,
nothing live touched) → `.bak_S251_CLINIC_MONEY_<stamp>` beside every file and the db → place →
seed → restart `clinic-finance` and `clinic-portal` → healthz 200, the four new addresses 302 behind
the login, the portal 200, the journal free of *NOT mounted*. Any red: every file restored, both
restarted. Re-run → ALREADY INSTALLED.

Predicted pins: `finance_clinic_day.py b2b7ff7d8ed654aa4cca067b1cfe5716` · `clinic_register.py
92136a97929d86b8458e62e1a9c8878f` · `finance_app.py 1fc62335f085b4cb4a634bbe9cca96c4` ·
`clinic_money.py 08c57466b44e417d93fc1e6117724fda` · `portal.py d0f126a3815a4c7e24960a15f1951857` ·
`tile_grants.json v16 d7edf850a977c033448d6e14076490b4`.

## Then — two things only the owner can do

1. **Bhati's login** at `https://followup.dr-manoj.in/portal/users` — add user `bhati`, role
   `staff`, a password. His unit rows and his tile are already in place; nothing else opens to him.
2. **Issue the float, once**, at `https://followup.dr-manoj.in/finance/clinic/money` — 5 × ₹200,
   10 × ₹100, 10 × ₹50, given to reception. Until it is issued the counter sheet shows no float
   block and nothing changes in the handover.

Rollback: the lines the installer prints (six files, both services). The seeded rows
(`business_unit physio`, six `unit_role` rows, one `setting`) are data and stay; they grant
nothing without the patched gate, and the db backup is beside the db.

## Later (the plan's §D and §E 8–10)

Bhati's optional itemising (clinic ID → name → mobile, lookup not browse), the learning step
(answered patterns become auto-explanations), and the physiotherapy system (home visits, a patient
not in Docterz, visits, sessions) — none built here; nothing here has to change for them.
