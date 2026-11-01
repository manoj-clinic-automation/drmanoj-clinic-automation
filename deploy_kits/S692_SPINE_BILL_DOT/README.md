# S692_SPINE_BILL_DOT — the spine's reader reads a bill number typed with a stray dot

*Sanjeevni session 375 · 01-Nov-2026 · the parent's note parent_S371_1 (the owner's ntfy shout of 31-Oct 08:05: "Marg spine gate — newest build FAILED").*

## For the owner
The pharmacy's Marg records (the spine) failed to rebuild on every attempt from 29-Oct 09:40 to 1-Nov. The cause: Shivaaz's purchase
bill of 26-Oct (number 3920) was typed in Marg as **"3920."** — a dot after the number. Marg then prints that bill number as text, the
reader refused that one line (OSTOVAXL DM, Rs 4,907.40), and every October purchase report since then did not add up to its own total,
so the gate refused the whole build. The last good records stayed in place; no staff screen showed a wrong figure.
After this kit the reader takes "3920." as 3920 (bill numbers only), re-reads the purchase reports, and rebuilds the records once. Amir's batch fixes of this morning can then be confirmed. **Nothing in Marg needs changing** — the dot can stay.

## What changes — one file
`/root/finance/spine/marg_read.py` **b47a1d62 → 55efcbf7** (`make_s692.py`, five anchored edits):
1. `READER_VERSION` S524.1 → S692.1 (every reading records which reader read it).
2. `billno(v)`: a bill number with a stray trailing dot is read as its digits (`3920.` → `3920`, `SF-123.` → `SF-123`); anything else
   exactly as `textno` gives it. **Bill numbers only** — a batch keeps every character (`textno`, untouched).
3. The purchase-line row rule accepts the dotted shape.
4. The purchase-line reader stores `billno(...)`.
5. The purchase bill-wise reader stores `billno(...)` — both sides of the line-to-bill tie read the same number.

Untouched: the sale readers (a sale bill is `A` + digits; a dot is still refused), the closing and list readers, every witness check, the
gate itself, the readings' shape, every staff and owner screen.

## The proof
- **In the device VM, on the 1-Nov bundle, the archive on manojz and a copy of the 1-Nov database:** the live reader → **GATE FAILED
  12/13** (the box's exact failure, `spine_state.json`); the kit's reader → **13/13, SPINE BUILT**, 630 of 630 purchase bills re-add.
- `walk_s692.py`: 22 checks on made-up rows only (a made-up supplier, made-up items, year 2099): the number rule (dot, `.0`, letters,
  leading zeros, `..`, a real decimal, a dotted batch kept), the purchase-line reader and the bill-wise reader on a clean report and a
  dotted one (the dotted bill reads, is stored as its digits, the totals re-add; a row that is no bill is still refused), the sale rule
  untouched — **22 of 22 green**; the control on the live file **6 S692 check(s) red · 8 green**.
- The spine's own `selftest_spine.py` (71 checks, every reader made to fail on purpose) on the kit's reader: **SELFTEST OK**.
- **The installer's gate on the box:** the purchase readings of the older reader (88) set aside in scratch, the archive re-read by the
  kit's reader, the spine built on a copy of the database — must say SPINE BUILT, or nothing is placed. After placing, the live readings
  are re-read and the live spine rebuilt once under the spine lock (`/tmp/spine.lock`, the cron's own lock) — the gate must pass.
- Rehearsed on a made-up root (the VM): DRY · install (gate 13/13, last good 07:35) · ALREADY INSTALLED · a forced red at [8/8] (the file
  back at b47a1d62, the set-aside readings put back, finance restarted) · a changed live file refused at [2/8] · a corrupt kit refused.

## Install (the server)
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s692kit && cp -rp /root/deploy/repo/deploy_kits/S692_SPINE_BILL_DOT /tmp/s692kit && bash /tmp/s692kit/install_S692_SPINE_BILL_DOT.sh
```
Gates → pin b47a1d62 → rebuild from the box's bytes → compile on both pythons → walk + control + selftest → THE PROOF on copies → backup
`marg_read.py.bak_S692_b47a1d62` → place → md5 read-back → the live re-read and rebuild under the spine lock (gate must pass) → restart
clinic-finance (the reports tile imports the reader) → healthz 200 → journal clean → walk on the placed file → lock released.
About two minutes (the 88 purchase reports come back from Drive). Window 04:00–23:30 IST.

**Undo:** `\cp -p /root/finance/spine/marg_read.py.bak_S692_b47a1d62 /root/finance/spine/marg_read.py && systemctl restart clinic-finance`
(the readings re-read by the kit stay, so the spine built by the kit stays and the cron keeps passing until a NEW purchase export carrying a
dotted bill is read by the old reader; the installer's own restore on a red is different — it puts the older readings back from scratch, and the older
readings are also kept in `/root/finance/spine/readings_pre_S692/` after a green install. A reading whose export Drive no longer lists is
never dropped: the older reading is put back and named on the install line.)

## Named, not done
- The reports tile (`reports_tile.py`) showed the staff the reader's refusal of the purchase item report for three days as a file problem;
  with the kit's reader that report reads clean. The fault — a typing slip in Marg stalled the spine for three days with only an ntfy
  shout to the owner, and no line on any staff screen named the bill — is minted at the close.
- Marg's own record still carries "3920."; the scan matcher (`purchase_app.py`) compares digit runs, so the scan of bill 3920 pairs.
- `selftest_spine.py` has no dotted-bill fixture; the walk carries it.
