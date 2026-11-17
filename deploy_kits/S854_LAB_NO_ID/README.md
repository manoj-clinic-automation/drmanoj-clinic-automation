# S854_LAB_NO_ID — lab reports with no clinic ID: suggested patients (D979/D980; S450 study item 10)

*The parent · S477 · 17-Nov-2026 · built from the live bytes of slip_log.py (231aebde) and check_screens.py (ac0e890a).*

## What changes
- **Reception's "Report aayi, ID nahi likha" (Report baaki → Blood):** each report the lab mailed with no clinic ID now shows the likely patients **best first, one tap each**, every one with its reason — an open blood slip in the lab's 7 days ("sabse pakka" only when it is the ONLY open slip with the name; two open → "isi naam ki 2 parchi khuli — ID dekh kar chunein"), a closed slip 0–3 days before, a clinic visit in the 7 days before, the patient list by exactly the same name; more words of the name shared rank higher. Enter in the ID box files the typed ID, never a suggestion; a suggestion tapped with a different ID typed is refused. The ID box and "Hamara nahi" stay. **Every** unplaced report is listed, not only the last week's (4 older ones had dropped off every screen).
- **His Check karein → "Filed by themselves":** the lab reports that filed themselves by name (S391's rule) — and the ones reception picked — are listed with the report and **"Wrong patient? Move"** (doctors only): the file, the report line and the mail's row all move, with a note; the Drive copy keeps its first name.
- **The automatic rule is unchanged** (S391): one open blood slip with the name files the report by itself.

## Checked against the real record first (F-1442; the 17-Nov copy, counts only)
- 31 ID-less reports since 21-Sep: 25 filed themselves — the new ranking puts the same patient first and strong on 23, the other 2 among its suggestions; 6 never placed — now 1 has a slip patient first (its slip's report had already come, so it is offered, not filed), 4 a visitor first, 1 nobody ("Hamara nahi").

## Files
| file | pin |
|---|---|
| finance/slip_log.py | 231aebde → (TO_PINS.md5) |
| finance/check_screens.py | ac0e890a → (TO_PINS.md5) |

## Proof
- `walk_s854.py` — made-up patients and mails on a copy, a 2027 clock: **WALK OK 28/28**; control on the live files **red 18 of 28**.
- Cold review (a fresh reader): NOT SAFE on the first look — 2 MUST (Enter in the ID box would have submitted the top suggestion; 'sabse pakka' shown where a second open slip had the name), 5 SHOULD (a posted ID checked to be a known numeric patient; name strength in the order; the card's row wraps on a phone; reception's picks movable from his list; the older walks' results pinned, not only compared), LOW 8–10 — all built in, each with a walk case. Second look: one more MUST (a two-word report name could hide OPEN one-word slips) — fixed exactly as it prescribed, walk case B4b.
- `walk_s834.py` (S834, slip_log) — 34 green on both, pinned in the installer; `walk_s836.py` (S836, check_screens) — exactly 'BAD E1 E4 E6, WALK RED 3 of 40' on both, pinned (its 3 wording checks were superseded by S839's "Free X-ray").
- `shape_s854.py` on a copy of the database: S391's answer the same for every past report; every report the old list showed still shown; the X-ray part of "Filed by themselves" unchanged.

## Install (his one server line)
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s854kit && cp -rp /root/deploy/repo/deploy_kits/S854_LAB_NO_ID /tmp/s854kit && bash /tmp/s854kit/install_S854_LAB_NO_ID.sh
```
