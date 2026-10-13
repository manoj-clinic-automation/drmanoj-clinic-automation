# S548_PACK_BHAWNA_FILE — Dr Bhawna's expense file in the accountants' pack (D721)

*Scan App project, S314, 13-Oct-2026. The owner, 14:13 IST: "KEEP DR BHAWNA IN HER EXPENSE FILE, IN ACCOUNTANT PACK".
**The file is the parent's** (`/root/finance/packs.py`, S541's TO, live since 08:05 IST) — built under a PLANNED line on the
System Board (v397; D646). Built by BUILD_NORM_v1 (D704).*

## What the kit does
The scan app's personal expenses (S544) carry whose they are (`bills.pe_who`: `bhawna`, or empty = Dr MK). The pack now
makes **three** scanned-bill files instead of two:

| item | file | carries |
|---|---|---|
| 8.1 | Dr Bhawna's lab-purchase bills | the NK Pathology lane — unchanged |
| 8.2 | Dr Manoj's expense-file bills | the personal expenses **not** marked Dr Bhawna |
| **8.3** | **Dr Bhawna's expense-file bills** | the personal expenses marked Dr Bhawna (new) |

Each is the same numbered bundle with its index page as before (late bills, the month rule and the rejected-paper rule
unchanged). The column is read only when it exists: **before S544 is installed the pack is exactly as today** and 8.3
reads *not ready — no personal expense is marked Dr Bhawna yet*.

## Files
| file | FROM (pinned) | TO |
|---|---|---|
| `/root/finance/packs.py` | `ada0860a` (S541) | `PIN_TO_packs.txt` — backup `.bak_S548_ada0860a` |

`make_s548.py` (five counted edits: the person in `build_bundle`, its query, two sets of words, the third file in item 8)
· `install_s548.sh` · `walk_s548.py`.

## Proven
- **The walk: 8 of 8** — `build_bundle` on a made-up scan database: 8.2 carries Dr MK's two, 8.3 Dr Bhawna's one (a rejected
  one left out), 8.1 untouched, 8.3 builds as a PDF; on a database without the column (before S544) 8.2 carries every
  expense as today and 8.3 is simply not ready. **The control** on the live file: 5 red.
- **The installer**, rehearsed on a made-up root five ways: DONE · ALREADY INSTALLED · health red → restored · a wrong
  FROM → refused · another build holding the lock → refused, the lock left to its owner.

## Install (the owner's one line, after the publish; any order with S544 and S545)
`cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S548_PACK_BHAWNA_FILE/install_s548.sh`

Order: gates → the estate's build lock → pin → rebuild on the box → walk + control → backup → place → restart
`clinic-finance` only → health (red → restored by itself) → words. On DONE the PLANNED line is RELEASED: the parent
builds on `packs.py` only from the new byte.

## Undo (one line)
`cp -p /root/finance/packs.py.bak_S548_ada0860a /root/finance/packs.py && systemctl restart clinic-finance`
