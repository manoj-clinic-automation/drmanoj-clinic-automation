# S211_PATIENTJOIN — H1 · the patient join, the foundation of D355

**What it does.** Puts the patient master and the visit history onto the VPS, so a
pharmacy bill can be matched to a real patient **by lookup** instead of by a
generated confidence score. Everything in Club H stands on this.

**What it does NOT do.** It touches no money. It writes only to `patient_ref`,
`patient_visit` and `patient_id_collision` — never `day_entry`, `sale_item` or
`ingest_batch`. It never deletes a patient. It changes nothing a person sees yet;
the daily list is H2.

---

## The two halves

| half | file | goes to |
|---|---|---|
| clinic PC | `push_patient_join.py` | the follow-up tracker folder, beside `push_to_vps.py` |
| VPS | `finance_patient_sync.py` | `/root/finance/` |

It reuses the door that already exists — `push_to_vps.py` → `POST /fu-upload` →
`followup_receiver.py` → `/root/wa/followup-inbox`. **No new endpoint, no new
secret for transport, no new service.**

## A full mobile number never leaves the clinic PC

Each number becomes a **salted one-way fingerprint** plus its last four digits.
The fingerprint matches exactly; the number cannot be recovered from it.

The salt is not decoration. A ten-digit number has only ten billion possibilities,
so an *unsalted* hash of a phone number is reversible by brute force in seconds.
**If the salt is missing, the PC script refuses to run** — it never falls back to an
unsalted hash, because a fallback that quietly weakens a privacy guarantee is worse
than a stop.

**Why a fingerprint when `patient_ref` already has `phone_last4`:** measured on the
real master, **1,506 of 4,903 last-four values are shared by more than one number**.
Last-four cannot identify anybody. This is stronger matching *and* less patient data
at rest.

## Proven on the real data, not on a fixture

`REHEARSAL_patientjoin.py` runs the whole loop against the live tracker folder and a
throwaway database carrying the real `patient_ref` schema. **11/11 pass:**

- 7,830 patients and 1,815 visits built and ingested;
- **no real mobile number reaches the VPS** — every ten-digit run in both workbooks
  checked against all 6,833 real numbers, zero matches;
- **shared-mobile ambiguity survives**: 716 shared numbers in the source, 716 in the
  database. F-34's family-mobile case cannot be collapsed;
- **single-digit clinic IDs survive** — nine of them, which the old `\d{2,8}` pattern
  could never have matched;
- a second run changes nothing.

Unit gates: `push_patient_join.py --selftest` **14/14**;
`finance_patient_sync.py --selftest` **16/16**.

### What the walk found that no fixture would have

**Seventeen clinic IDs in the real master name more than one patient.** The clinic ID
is meant to be the strongest identifier there is. The sync now **records every
collision** in `patient_id_collision` and says so loudly, instead of keeping the first
and dropping the rest in silence. **D355 matching must treat such an ID as AMBIGUOUS,
not as a clean match** — that is a design consequence, not a footnote.

The privacy check is also deliberately *not* "no ten-digit run appears". A 32-character
hex fingerprint throws those up by chance — 409 of them here. That check would have
been red forever, and a gate that is always red is a gate everyone learns to ignore.
It asserts the real thing: no run that **is** one of the real numbers.

## Install

### Step 1 — the salt. Double-click, and read nothing.

    D:\dr-manoj-git\drmanoj-clinic-automation\deploy_kits\S211_PATIENTJOIN\SETUP_SALT.bat

It creates the salt, saves it to `patient_fp.env` beside the script (hidden, and the
only copy — back it up with your other credentials), and **puts the single VPS line
straight onto your clipboard.** Open Termius, press Ctrl+V, Enter. You should see
`SALT_INSTALLED`.

**The salt is never printed, never logged, and never passes through a chat.** Run the
script as often as you like: it will **never replace a salt that already exists**,
because changing it would orphan every fingerprint already on the VPS. Proven: two
consecutive runs, salt unchanged, and the value absent from all output.

The VPS keeps it at `/root/finance/patient_fp.env`, mode 0600 — a file rather than a
systemd `Environment=` line, so installing it needs no unit edit, no daemon-reload and
no restart of the money application for a value that is only ever read.

### Step 2 — copy the two scripts into place

`push_patient_join.py`, `setup_salt.py` and `SETUP_SALT.bat` go in the follow-up tracker
folder beside `push_to_vps.py`. `finance_patient_sync.py` goes in `/root/finance/`.

### Step 3 — preview, then push

The preview writes nothing and uploads nothing:

    python push_patient_join.py
    python push_patient_join.py --push

Then on the VPS:

    /root/wa/venv/bin/python3 /root/finance/finance_patient_sync.py --dry-run
    /root/wa/venv/bin/python3 /root/finance/finance_patient_sync.py

`--dry-run` reports exactly what would change, and rolls back.

## What travels beyond identity: the sanctioned entitlements

The workbook also carries what each patient is **sanctioned** for, so compliance can be
checked rather than assumed — read from the diagnosis sheet where the admin codes already
live:

| column | meaning | on the real data |
|---|---|---|
| `admin_cc_p` | sanctioned consultation charge, in paise | 155 patients; **82 of them free** |
| `admin_pd_pct` | pharmacy discount the counter must apply | 272 patients (10% x232, 15% x24, 20% x14, 5% x2) |
| `admin_bid_pct` | pathology discount percentage | 182 patients (30% x75, 50% x74, 40% x24, and **9 unusually low: 4% x8, 5% x1**) |
| `is_vip`, `concession_scheme` | context | 80 VIPs; 33 named schemes |

**"No rule" and "free" must never look alike.** A patient with no CC code stores `NULL`;
a patient sanctioned free stores `0`. Had both been blank, 82 free-consultation patients
would have silently become "no rule".

**The nine low BID values are carried through as written and flagged, not corrected.**
Reading 4 as 40 would be inventing a correction nobody sanctioned.

## Rollback

Nothing to roll back on the PC — it only reads. On the VPS the sync only ever adds:
the added columns are additive, and no patient row is ever deleted. To undo the data
itself, `DELETE FROM patient_visit` and `DELETE FROM patient_id_collision`; the
`patient_ref` rows are the ones `sale_item` will point at, so they stay.
