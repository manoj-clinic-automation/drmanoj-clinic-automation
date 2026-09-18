# HANDOFF RUNBOOK — v189 — written at the S267 close, 18-Sep-2026

*Supersedes v188 (the Sanjeevni chat's S266 post-close) in full. This is the parent project's close. v189 carries three new rules — the masked-unit pin, the canon-fork rule, and the pin that has two owners — and states the roadmap the owner finalised in conversation and asked to be carried whole.*

---

## §0 — WHAT IS OWED, AND TO WHOM

**To the owner, three things, none of them urgent and none of them mine to do:**

1. **The eighteen answers on step 2, *Try to match*** (the Sanjeevni side, unchanged since the 17th):

```
https://followup.dr-manoj.in/finance/stock/page/hub?count=1
```

2. **Two CSV exports of contacts** — one from `bocbareilly@gmail.com` (the reception phone's account) and one from the clinic Google account. The labels, the non-patient numbers and the merge plan (D545) are settled the moment those two files exist; nothing can be built before them.

3. **The procedure → consumables map** and the X-ray price list as he wants them to auto-populate (D546). One sheet, his words, whenever he has ten minutes.

**To the next session:** the build is agreed and written down — see §4. Nothing in it is blocked by canon.

---

## §1 — THE BOX, AS THIS CLOSE LEAVES IT

Live and pinned in Register **v5.108** (which is what `live_pins_S267close.txt` is generated from):

- **The staff desk** — `staff_register.py` `0a098cfa`: the attendance page as the owner amended it on the 17th (tappable Hinglish reasons, past days display-only showing absents and leaves alone, *Mark overtime* with *Told Dr Bhawna* / *Told Dr Manoj*, no *My month*), and the locked month showing **the sheet it paid** beside today's recompute. **F-519 is settled from the store:** the card is the paid figure; eight staff differ; the differences reconcile to exactly **−410**.
- **The petty book** — `petty_book.py` `88f28571`: Bhati's cash and loan each have an opening balance, set once by the checker and correctable, audited.
- **The nightly code bundle** — `code_bundle.py` `a70bf6e2` (v1.4): unit-file secrets masked before they leave the box, a guard that dies if a named secret survives, and the original md5 recorded in `BUNDLE_INFO`. **F-518 closed**, and proven the next morning from Drive and from the PC copy.
- **The health page** — `freshness_legs.json`, last read `0e56aa9e`: the Docterz leg watches a **50 h** window measured from the box's own quiet spells (24.0 h and 28.7 h observed), the asset-app leg 26 h, and petty photos off-box are watched for the first time.

---

## §2 — THE RULES CARRIED FORWARD, AND THE THREE THIS CLOSE ADDS

1. **F-509 — the board is the lock.** Claim the session number in `board/_claude_status` as the first act, reading the key immediately before writing it.
2. **F-510 — a clock time is read, never estimated.**
3. **F-511 / F-520 / F-532 — no git command in `device_bash` against a connected folder.** The third occurrence left a `maintenance.lock`. Read `.git/logs/HEAD` and the refs, or clone in the cloud workspace.
4. **F-512 — a kit folder that could have been published is frozen.** A change is a new kit number.
5. **F-523 — a file committed to the PC is read back by md5 on the PC before it is used.**
6. **NEW · F-531 / F-533 — a unit file is a pin like any other, and a masked file is held against `BUNDLE_INFO`'s `original_md5`, never against the masked copy.** From tonight `clinic-finance.service` diverges from its bundle copy for ever, correctly.
7. **NEW · F-534 — the canon folder is listed immediately before the first canon file of a close is written.** Not at the open. The parallel chat spent this session's whole reserved block (D541 … D543, F-521 … F-525, Archive v1.104 and v1.105, Fault v2.91 and v2.92, Register v5.106 and v5.107, Runbook v187 and v188) between this session's open and its close. Two files were rebuilt onto the current parents; nothing was published stale.
8. **NEW · a pin can have two owners.** `freshness_legs.json` moved four times in one evening between two chats. Before calling such a file drifted, read it — and read the other chat's close.

---

## §3 — THE FIVE KITS OF S267

| kit | what it did | evidence |
|---|---|---|
| `S300_ATTENDANCE_AND_OPENING` | D540 as amended + Bhati's opening balances | 103-check walk, installer read back `439d6790` / `88f28571` |
| `S303_SALARY_LOCKED_TABLE` | the locked month's own table; F-519 answered | 23 tests on the real `salary_policy.sheets34_html`, live-shape walk printed the −410 |
| `S306_BUNDLE_MASK` | the two machine tokens masked out of the nightly bundle | 22 tests; proven in production the next morning |
| `S309_FRESHNESS_DOCTERZ` | the Docterz window 200 h → 50 h, measured | 21 selftests; refuses to tighten onto stale data |
| `S310_FRESHNESS_LEGS_2` | asset-app 26 h + a new petty-photos leg | 25 selftests; re-runnable, answered ALREADY on the second run |

---

## §4 — THE ROADMAP THE OWNER FINALISED IN CONVERSATION (no code written yet, by his instruction)

**A · One contact book (D545).** The clinic Google account on both reception phones, contacts-only sync; `bocbareilly@gmail.com` exported, verified and then frozen as an archive; labels (patient, personal, unclassified, DTH, staff, vendor …) settled from the two CSV exports; **every patient contact carries name + clinic ID**. New patients stop being typed by hand: they arrive from the day's own data. **Waits on:** the two CSVs.

**B · The reception X-ray register.** Stays an Excel file in Drive as today; the system produces it rather than reception typing it. The Fuji X-ray laptop **stays off every network** — the pen drive stays, by the owner's ruling.

**C · The slip-number logging design (D546), as refined through the owner's corrections:**
- **Reception is not disturbed at all.** They keep working only in the Docterz EMR. The one thing they may add is *paid / not paid* — nothing else.
- **The slip travels, as it does today**, with the clinic ID already written on it, to the chamber.
- **A chamber order screen**: the assistant picks the clinic ID from the day's own list, chooses the X-ray or procedure from a short dropdown (ten or twelve items, price auto-populated), and types **the physical slip number**. That is the whole entry.
- **The X-ray/procedure room gets a list, not a live screen.** Awdhesh's phone stays in his pocket; after each session he works the batch.
- **A nightly three-way match** — the slip book, the chamber screen, the Docterz day lines — that **speaks only about exceptions**, so Shavez's morning matching stops being a sit-down job and his absence stops blinding the system.
- **The physical numbering remains the authority.** The system's number rides beside it, never instead of it. This is a convenience and a log, not a replacement.

**D · Held, deliberately:** the one-line lowercase fix for the portal login (**F-529**) — `portal.py` is being changed by the Sanjeevni chat; it goes in on the first parent kit that owns that file again.

---

## §5 — THE SWITCHES

```
bash /root/finance/sanjeevni_switch.sh status
```

VPS `/root/finance/_off/ALL_OFF` (spine, attribution, export watch, salts refresh) · VPS `/root/marg_ingest/OFF` (collector, shadow) · manojz `D:\Downloads\margsync\_off\ALL_OFF.txt` · medical PC `D:\SendToClinic\_off\ALL_OFF.txt`, which does **not** stop capture, by design.

---

*HANDOFF RUNBOOK v189 · written at the S267 close · supersedes v188 in full.*
