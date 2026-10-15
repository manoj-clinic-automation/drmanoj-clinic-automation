# S565_DARPAN_SMS_AND_CLAUDE_BILLS — Darpan's day draws the bank's SMS; Claude vs Sarvam on the medicine bills

**Brief:** `claude_code_briefs/S565_DARPAN_SMS_AND_CLAUDE_BILLS.md` (the Sanjeevni chat, session 316, 15-Oct-2026, v2 after R1).
**Why:** REPORT_S562, "Outside the brief". Since S562 the bank's settlement SMS can stand in for the MPR mail, behind the owner's switch.
Darpan's *Kal ka hisaab* did not say so, and a day he had already posted was worked again only for a POS total. Part B is the owner's
ask: a sample of how well Claude reads the Sanjeevni medicine purchase bills, against Sarvam, by the same rules.

## Part A — what it does (for the owner)
- **Darpan's view** (Devanagari, as the page already is): with the SMS standing, the online row says *"बैंक SMS 07:02 से — bank की report बाकी"*,
  the same shape as the POS line, which stays exactly as it was. No SMS-vs-MPR figure is ever shown to him.
- **Your view** (English): the online row says *"provisional — bank SMS 07:02, MPR not in"*, or *"…, MPR never received"*. Under it:
  *"UPI total from the bank's settlement SMS of 07:02 — the MPR mail is not in yet."* An SMS that came on a later day reads like *"28-Apr 07:02"*.
- **A day Darpan already posted is worked again** when the SMS starts standing, and again when the MPR mail replaces it (the second already
  happened).

## Files — pins FROM → TO (built on the box by `make_s565.py`, counted anchored edits on the live bytes)
| file | FROM | TO | edits |
|---|---|---|---|
| `/root/finance/darpan_kal.html` | `f5e279eb26e7f24827f29b79f95b2769` | `75d5a5b51b017abd5ad3aa408609a1ff` | 4 |
| `/root/finance/darpan_kal.py` | `a8e11c31b9c80c1b01e63e948418d4a4` | `8128598f745fca48a08472905f47da97` | 1 |

The html edits: (1) the helper `smsAt` (the SMS time out of the stand-in's label), once; (2) Darpan's online row, the `"sms"` case first;
(3) the owner's note under *online* (`bank\'s`, escaped); (4) the owner's online row, the `"sms"` case first. The `"pos"` and Marg branches are
byte for byte. The py edit: `_refresh_if_needed`'s third condition `== "pos"` → `in ("pos", "sms")`, with an S565 comment.
Read only, must be at their pins: `bank_standin.py` `fd635862`, `bank_sms.py` `aa527840` (S564's TO; the brief's `053d4ccb` was moved by S564
at 16:45, its page fold only). **Data step:** none. **Restarts:** `clinic-finance` only.

## Install (on the server)
```
rm -rf /tmp/s565kit && cp -rp /root/deploy/repo/deploy_kits/S565_DARPAN_SMS_AND_CLAUDE_BILLS /tmp/s565kit && bash /tmp/s565kit/install_S565_DARPAN_SMS_AND_CLAUDE_BILLS.sh
```
`DRY=1` runs every gate and the walks and writes nothing. `bash rehearse_s565.sh` rehearses on a made-up root (red-after-placing restore,
green, ALREADY INSTALLED). The installer needs `jjs` (the box's Java JS engine, `/usr/bin/jjs`): the walk draws the page with it.

## The walk (`walk_s565.py`)
The real finance app on scratch copies (Flask's test client, the walk's own header session), made-up Sanjeevni days in April–May 2027 found by
date, made-up SMS / MPR / POS rows. The page draws itself in the browser and the box has no browser or node: the walk takes the page **as served**
and runs, in `jjs`, the exact expressions that draw the online rows (verbatim from the served page) on the day's JSON as the page receives it;
it lexes the whole `<script>` so a broken quote is red (and proves the lexer can fail). (1) an SMS day: Darpan's row, one rupee figure, no
difference; the owner's row and note, no Devanagari; (2) a posted day → the SMS → re-decided → the MPR → re-decided, no loop; (3) the POS rows
byte-identical to the old page's; an SMS two days late; a "never" day; (S) staff-eye for darpan and manoj (portal tiles, door markers, page
weight). `--expect-red` on the old files: every `C:` check red. A real headless-Chrome render of the same made-up days was done at kit time
(REPORT_S565).

## Part B (`claude_vs_sarvam_s565.py`) — read only, run once by hand, never by the installer
```
cp /root/deploy/repo/deploy_kits/S565_DARPAN_SMS_AND_CLAUDE_BILLS/claude_vs_sarvam_s565.py /tmp/ && cd /tmp && /usr/bin/python3 -B /tmp/claude_vs_sarvam_s565.py --csv /tmp/s565b_out/claude_vs_sarvam_detail.csv
```
Copies finance.db and assets.db (backup API) into `/tmp/s565b`, scores Sarvam's stored readings and Claude's readings with
`purchase_app._s446_compare_one` called as it is, prints the aggregates, writes a per-bill CSV with no phone or email column (10-digit runs
masked), removes `/tmp/s565b`. Claude's existing readings (`claude_reading ok=1`) are used as they are; `--fresh N` bills are read again only to
measure the cost per bill (spend capped by `--cap-usd`, default 12). Nothing is installed, scheduled or left running.

## Retired / left for later
Retired: nothing (no second copy of a figure or of words was added; the SMS label is built once, in darpan_kal.py, and the page only draws it).
Left for later: see REPORT_S565 "Charter".

## Undo
```
\cp -p /root/finance/darpan_kal.html.bak_S565_f5e279eb /root/finance/darpan_kal.html && \cp -p /root/finance/darpan_kal.py.bak_S565_a8e11c31 /root/finance/darpan_kal.py && systemctl restart clinic-finance
```
