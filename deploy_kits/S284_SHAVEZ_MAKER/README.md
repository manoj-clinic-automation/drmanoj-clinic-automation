# S284_SHAVEZ_MAKER — Shavez may write the cheque register (D524)

**Session 262 (Sanjeevni project) · 17-Sep-2026 · closes D524. Installs on top of S282_LINE_OWNER.**

## The ruling, and its scope

Board line F5, 15-Sep, the owner: **"make him maker."** The Register carries it as *Shavez as maker
**on the cheque register***, and the S262 note says of the same person: *"If he is ever made a maker in
the medical unit, that is the line to reconsider."*

A `unit_role` row `maker` on the medical unit would be one line — and it would also let Shavez file
the day (Darpan's role), give verdicts on purchase bills, type carry-forwards on the payment sheet and
read the vendor phone book as of right. None of that was asked for. So the grant is the pattern this
file already uses twice (`purchase.phonebook_users`, `purchase.salt_users`): **a named list in the
`setting` table, `purchase.cheque_users`, read fail-closed.** A maker or checker writes exactly as
before; a viewer writes only if named. Everything else Shavez sees stays read-only.

## What he can now do

Log a cheque from the payment sheet's cheque card · mark it handed over · void it with a reason. Both
cheque APIs and both places the form is rendered (the register page, the sheet's card) ask the same
question, `_cheque_writer_s284(u, con)`. The sheet's own `editable` (carry-forward, verification), the
month lock and the phone book keep their own gates — the selftest checks they are untouched.

## The change

Four anchored edits in `purchase_app.py` — the two cheque routes admit any medical login and then
refuse a non-writer; the register page and the sheet's cheque card render the forms for a writer — plus
`CHEQUE_USERS_KEY` and the helper appended. Then one setting row: `shavez`.

## The proof

- **26 offline checks, 0 failed** (`selftest_s284.py`, on a copy of the live bytes brought first to
  the S282 state): all four anchors match once, wrong pin refused with nothing written, compiles, the
  helper is used at four sites and defined once, the old anchors are gone, the sheet's editable flag and
  the phone-book gate are byte-untouched, ALREADY PATCHED on a second run; and the helper lifted out of
  the patched file with the real `_is_viewer_only` and `_who`: maker writes · checker writes · a named
  viewer writes · an unnamed viewer does not · no row admits nobody · no table admits nobody (not a
  crash) · case and spacing ignored · empty login refused · the undo takes it away again.
- **The installer rehearsed against a fake root:** refuses on the pre-S282 file with the reason; chains
  S282 → S284; the second run stops at ALREADY INSTALLED and leaves the list as it is.
- **Not proven offline:** the rendered pages themselves (they need the Flask app and the real login
  broker). The installer restarts the service and reads the purchase health endpoint; the first real
  read is the owner opening the register signed in as himself, then Shavez logging September's one
  cheque — that log entry is the live proof.

## Install — one line on the VPS, after S282

```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S284_SHAVEZ_MAKER/install_S284_SHAVEZ_MAKER.sh
```

| pin | from | to |
|---|---|---|
| `/root/finance/purchase_app.py` | `216a0cd95afad73eecbc484683892ca3` (S282) | `d1476f80836e8b68fae2da1855c7105f` (predicted; refused if the read-back differs) |
| `setting purchase.cheque_users` | — | `shavez` |

## The undo — the grant without the code change

```
/root/wa/venv/bin/python3 -B /root/deploy/repo/deploy_kits/S284_SHAVEZ_MAKER/seed_setting_s284.py --db /root/finance/finance.db --value ""
```

Takes effect on the next request; no restart. The code then behaves exactly as S270/S271 did. A
second name is one more word on that line (`--value "shavez,amir"`).

| file | what |
|---|---|
| `patch_cheque_writer_s284.py` | the four anchored edits + helper; refuses on any surprise |
| `seed_setting_s284.py` | writes / shows / clears the list; prints old and new |
| `selftest_s284.py` | the 26 checks |
| `install_S284_SHAVEZ_MAKER.sh` | pins, backup, patch, setting, restart, roll back |
