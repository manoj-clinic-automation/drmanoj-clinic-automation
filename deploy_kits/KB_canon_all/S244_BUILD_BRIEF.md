# S244 BUILD BRIEF — the day Amir's screen stopped lying, the ledger learned to reach back, and the clinic's money got one channel each

*13-Sep-2026, one Sunday, two chats. One brief instead of eleven kit READMEs and seven build documents: the
shortest complete path into what S244 did. Next session: S255 (F-463 — the kit counter had run ahead).*

## The session in one line

Amir's four screens fixed from his own morning → the ledger given the one control it lacked → two salaries
raised from August → the staff register's door opened to the three who fill it (second chat) → the owner's
money brief built whole, refused once by the gate, re-issued, live by 13:27, then reshaped three times within
the hour from his own readings — every install his one line, every pin printed by the box.

## What changed, in the order it landed

| # | kit | what it did | pins |
|---|---|---|---|
| 1 | `S244_AMIR_PROCESSING` | step 4: processing → done → what is left; never blocks him (D497) | `amir_day.py` bf7d9826 → aad400fa |
| 2 | `S245_AMIR_BILLTAP` | one tap per bill (D498); **then rebuilt in place — F-460; installer refused the rebuild** | → 79eb701f |
| 3 | `S246_AMIR_LIST_REOPEN` | bills from 1-Sep, flags stay (D499); *Din band* reopenable (D500); F-461 fixed | → a9f20622 **predicted — re-hash** |
| 4 | `S247_LEDGER_LATE_COLLECT` | collect an advance against a closed month, from the ledger card (D501) | `staff_ledger.py` 49b13f42 → eacd7154 |
| 5 | `S248_SALARY_RAISE` | Awdhesh 10,500 · Sandip 8,000 from August (D502); July a test case (D503) | `staff_master.csv` → e48ae0b0 **SHORT** |
| 6 | `S250_STAFF_REGISTER_TILE` *(second chat)* | `Staff Register` unmasked for shivani / alisha / shavez (D496) | `tile_grants.json` v14 → v15 932f7bd0 |
| 7 | `S249_CLINIC_MONEY` | built on v14; **refused at the currency gate (F-462); never installed** | — |
| 8 | `S251_CLINIC_MONEY` | the reconciler, the match card, the owner's line, other UPI, the float, physiotherapy, Bhati (D504 · D505 · D507; F-459 fixed) | `finance_clinic_day.py` → b2b7ff7d · `clinic_register.py` → 92136a97 · `finance_app.py` → 1fc62335 (patched on the box) · NEW `clinic_money.py` 08c57466 · `portal.py` → d0f126a3 · grants v16 d7edf850 |
| 9 | `S252_FLOAT_FLOW` | zero taps on a normal day; one *Given* tap; one monitoring line (D506) | `clinic_money.py` → 9cc6bb7a |
| 10 | `S253_MATCH_PLAIN` | one plain sentence; flags in words; ₹50 blood sugar head move (D508) | → da9122e0 |
| 11 | `S254_SHEET_PHONE` | each head its own row, three boxes beneath, four folds (D509) | `clinic_register.py` → eaaea278 · `clinic_money.py` → d5c3a845 |

## The three things worth knowing next time

**1 · The clinic's money has one rule.** Every rupee has one channel, and each channel says whether an
independent record exists: counter cash (the drawer count) · ICICI UPI (the MPR) · card · portal/Razorpay
(**no record here yet — the plan below**) · another UPI (the box on the sheet, the owner's *settled* tick) ·
physiotherapy (its own table). The reconciler is pure — it changes no figure and invents no adjustment; the
sheet, the MPR and the explanation layer are the only inputs. The checker is a setting, not code.

**2 · Two refusals, both correct, both the assistant's to prevent.** A kit rebuilt after publish (F-460) and a
kit built on a pin another chat had moved (F-462). Freeze published kits; name the shared file before a second
chat builds.

**3 · The owner's readings are the spec, within the hour.** *Friction* → S252; *your mathematics* → S253;
*boxes too small, long scroll* → S254. None needed a design conversation; each needed a walk and one line.

## The plan written and not built — the Razorpay / Yes Bank channel (D507)

Docterz's *Wallet*, *Patient APP* and *Net Banking* rows are Razorpay payments: the receipt lands in the owner's
**personal Gmail**, the money settles to the **Yes Bank clinic current account**, and neither is in the ICICI file
the reconciler reads. Three steps, in order: **(1)** the reconciler stops expecting channel 4 in the ICICI MPR and
lists it as *portal — awaiting the Razorpay record* rather than *not in bank*; **(2)** a payment-email relay —
Apps Script on his Gmail, read-only, forwarding each Razorpay receipt's amount, id, time and last-4 of the payer
to a `portal_payment` table through a machine door, so the reconciler pairs a Docterz Wallet line to a receipt
the same way it pairs UPI to the MPR; **(3)** Yes Bank settlement recognition through the existing 07:00
statement relay, marking each `portal_payment` *settled* when its batch lands (T+1/T+2). Nothing of this touches
Docterz or Razorpay's own dashboard.

## Owed

The Razorpay / Yes Bank channel · re-hash `amir_day.py` and `staff_master.csv` on the box · Bhati's login (his,
parked) · reception's first pass on Saturday 12-Sep · Bhati's itemising · the learning step · the physiotherapy
system · the S243 carry-overs (F-456 rotation · D493 phase 2 · F-458 gate · pin rows · F-451 cron).
