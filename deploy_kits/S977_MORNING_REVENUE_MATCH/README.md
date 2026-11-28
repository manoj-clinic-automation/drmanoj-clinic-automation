# S977_MORNING_REVENUE_MATCH — the morning as a revenue match (K2a)

*The parent, S544, 28-Nov-2026. D1099 · D1100 (S537_MORNING_CHECK_FINAL_BUILD_PLAN §3, K2.1 · K2.2 · K2.3 · K2.5 · K2.6). His word 14:03: "build K2 today". F-1732 rides along.*

**What changes for the staff and for him.** The morning day check matches money against money only: the register total against Docterz's total (net of refunds and radd).
- No payment-mode card of any kind (mode · modeany · swap · regupi · bank). The per-tender figures and the bank part stay on his page as information.
- No Docterz edit is asked the next morning: a slip Docterz lacks whose money the register holds is counted *kept outside Docterz* by itself (a note; nothing written). A slip line neither billed nor in the register is a note.
- The three slip shapes the widened evening check (S972) names (a line twice · parchi short · parchi over) make no morning card **only when that evening's push actually told reception about that slip and kind** (an evening row 'missing', sent, its shapes column naming them).
- Register MORE, unexplained → ONE card naming the day's patients with no paid bill — *whose was it?* — with *Make the parchi* (the slip then settles by itself, S970).
- Register LESS by exactly one bill of one head (the other heads agreeing) → reception's card: *Register galat tha* (the register page) or *Paise nahi diye* (a pick from that head's patients writes slip_adjust's own *money never taken* radd on that patient's one slip, pending his approval). Anything else → his line, and **his push** (his devices only, once per line).
- The clean push carries the day's sum: *Register ₹X = Docterz ₹Y + parchi bahar ₹Z − wapas ₹W · N mareez mile*.
- F-1732: an empty consultation report after the day's good one is superseded, not "set aside" — no false "export again" line.

**Switches.** `DAYCHK_REVENUE=0` → the day check exactly as S970 left it (proven equal on 49 days). `REGPUSH_OWNER=0` → his push alone off. A full return without an undo needs both.

**Files.** `/root/finance/day_check.py` 946f0408 → 5843d3d5 · `register_push.py` 9b1fbc29 → 2ba0d63b (+ column `register_push.owner_sent`, additive) · `docterz_pickup.py` 8ffb93aa → cf42181e.

**Install** (one server line, any hour; it waits for a quiet minute between the 5-minute push runs, then records the past week quietly so nobody is pushed about an old day):
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s977kit && \cp -rp /root/deploy/repo/deploy_kits/S977_MORNING_REVENUE_MATCH /tmp/s977kit && bash /tmp/s977kit/install_S977_MORNING_REVENUE_MATCH.sh
```
**Undo:** `bash /tmp/s977kit/install_S977_MORNING_REVENUE_MATCH.sh --undo`

**Proof.** walk_s977 (made-up data) green on the TO, red on the FROM (the control), three mutants red; S962/S968/S970 walks green with the switch off (S962's differs, with the switch on, only where the morning was meant to change); the live shape (the 28-Nov copy, 49 days, counts only): cards 89 → 60 (mode 13 → 0, by hand 20 → 3, Docterz-edit 4 → 0, one-consultation cards 3), clean days 10 → 16, errors 0, the day's sum holds every day; rehearsal on a made-up root.

**Not in this kit (K2b, next):** the late slip made from the patient tap (`slip_log`), the register one-tap fix with the drawer guard (`clinic_register`), *Pata nahi* → his push, *Sab ho gaya*, the Day check link in the Docterz group, the register opening on yesterday.

**Cold review (NOT SAFE, 4 MUST — all built in):** his push could repeat after a staff line rewrote the day's row (owner_sent read before the write now); a seeded old day reached him on the next sweep (recorded as told now); the evening rule dropped cards nobody was told about (only shapes the evening's sent push named, by slip and kind); "Paise nahi diye" could cancel the wrong line (the radd is tried first and refused unless it takes out exactly that one bill). SHOULDs built in: the old code re-seeds the week after any put-back or undo; told only when a device took the push; his lines kept by their lasting names; the nf key carries no tender; no re-export prompt from a Found-it tick on a money-only day; the probe checks the card's figure against the page's line; a line in an unknown mode is no candidate.
**Second look (NOT SAFE, 1 MUST — built in):** an evening push that reached nobody ("sent 0, failed 2") counted as told — now only a push that reached somebody, read as the day's LAST export left it (a later clean / cleared export, or a push to nobody, brings the morning card back). SHOULDs built in: his push skipped when the owner_sent column cannot be read; an old "Found it" tick (the key with a tender) still counts; the installer's quiet sweep no longer silences yesterday's or today's unexplained gap for him; the lessnp trial runs against the day's own radds. **Re-look: SAFE** (0 MUST; its two SHOULDs built in: Undo clears an old-key tick; his push reads the judge's own clock).
