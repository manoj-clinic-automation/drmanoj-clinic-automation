# S680_IPD_CASES_RECORD — IPD cases, kit 1 of 6: the record and the list (FINAL)

The parent · built S368 (29-Oct-2026, D801), rebuilt S370 (30-Oct-2026) to the owner's review of the screens (D804) and his word of
30-Oct 12:49 / 13:07 ("NEED FULL PHONE NUMBERS" · calling from the case through the MyOperator IVR · "Do it whatever seems best to you").
Kit S680 v3 (S368) was never published or installed; this kit keeps its number, its PLANNED line and its four files.

**What Dr Manoj and Shavez will see** (the screens were shown first, rendered from this module with made-up patients:
`D:\Downloads\ClaudeCowork\03_WORKING_PAPERS\S370\IPD_cases_real_screens_preview.html`)
1. *Surgery cases* is **IPD cases** — the tile, its folder face, every page, the Case Pack's link (which now also carries the patient's UID, so the full mobile is filled in). Addresses stay `/finance/surgery…`.
2. **The list** — compact rows: name, case no., UHID, IPD no., the **full mobile(s)**, source · type, payer and its TPA, admitted →
   discharged, diagnosis · operation, **three status chips** (patient · hospital money · implant payment) and the **next step**.
   Filters for each status, payer, source, type, old/new; a search by name, clinic ID, case no., IPD no., UHID or **full mobile** (the
   case's own and the console's patients mirror, read only). On a phone: a search box, tap chips (All · Admitted · Money pending ·
   Implant pending · Old) and *More filters*.
3. **Tap a patient** — the case opens below its row, on the same page; every entry is made there and comes back to the list with the
   case open. One yellow **Next** line; sections 1 Admission · 2 Surgery, implant, assistants · 3 Discharge & papers · 4 Hospital bill ·
   5 Payment & what remains · 6 Implant settlement · 7 Follow-up · 8 What happened — the current one open, the rest folded. 4, 6 and 7
   say which later kit fills them (3, 4, 6); assistants, thumbnails and the new paper kinds come with kit 2.
4. **📞 Call (IVR)** beside each mobile on an opened case: the caller's own phone rings first, then MyOperator joins the patient (the same
   call service as *Call ke baad* and the inbox). The number is the one stored on the case, never one from the page; one call per case a
   minute; each call is kept (who, when, the last 4 digits) in section 8. A login not on the IVR call list sees the button greyed.
5. **New case** — compact (several fields a line on a PC, one on a phone): Find (name / mobile / clinic ID) fills the name, the full
   mobile and the clinic ID and lists that patient's own Case Pack cases to pick from; clinic ID optional; UHID beside the IPD no.; type,
   source (+ a new one), medicolegal and payer as tap chips; TPA / scheme a drop-down with *+ add a name*. A patient who already has a
   case says so, with a link to open it.
6. **Old cases** (backfill, from 1-Apr-2025) — the same form plus the implant, its vendor and both payment statuses; only the name and
   the payer are compulsory; they sit in the same list marked *old case*.
7. **Settings** (Dr Manoj only) — admission ₹1,200, nursing ₹500 a day, his share % (not set), the sources, the TPA / scheme names.
8. **Who sees what** — Shavez sees everything on a case, the hospital money included, except the implant's actual cost (*you only*)
   and Dr Manoj's money pages; the amount due, Settings, the TPA list and removing a case are Dr Manoj's.

**Data** — additive only: twelve columns on `surg_case` (type, source, payer kind, admission, IPD no., diagnosis, MLC, backfill, UHID,
mobile, implant status, money status), tables `surg_source`, `surg_tpa` (seeded from the names already on cases), `surg_call`; the old
`payer` column stays the vendor ledger's class, so every ledger, cheque and receipt rule reads as before. The live database holds only
the two removed test cases of 18-Oct. Read only, never written: `/root/wa/console.db`, `/root/wa/casepack/case_ledger.csv`,
`/root/portal/ring_agents.json`, `/root/wa/.env` (the call key, never shown). **No phone number is ever put in a page address** (the searches post), so none reaches the web server's log; a call is kept with its last 4 digits only.
Old cases stay out of the vendors' balances and the awaiting-cheque list until kit 4 settles them on the vendor's page (their implant status says where each stands).

## Install (on the server, after the publish)
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s680kit && cp -rp /root/deploy/repo/deploy_kits/S680_IPD_CASES_RECORD /tmp/s680kit && bash /tmp/s680kit/install_S680_IPD_CASES_RECORD.sh
```
Gates → the four pins (surgery_cases 7effc05e · portal 1e0c6548 · grants 83828b81 · Case Pack 2dfe4221) → compile on both pythons →
**the walk** (205 checks: S581's and S680 v3's carried — the 13 that D804 changes are marked [D804] and rewritten — section Y for D804,
section Z for the IVR call against a stand-in call service (MyOperator is never reached), section R for the independent review's findings) on a made-up database and on a copy of the
live one, and its control on the live module → **the portal walk** (every login × role × PC: the same homes but the one name; the Case
Pack link) and its control → **the probe** through the real finance app as manoj, shavez, bhawna, darpan (15 checks, the posted search and an IVR call ending at a dead
port included), and its control → health →
backups and the database copy → place and read back → restart clinic-finance and clinic-portal → health → the portal walk and the probe
on the placed files. A red after placing puts all four files back. A second run says ALREADY INSTALLED.

**Proven before placing:** the walk 205/205 on a made-up database and on a copy of the 30-Oct database; 31 broken versions of the module
(two rounds) each turn it red (one — the discharged filter without its old-case mark — is harmless by construction: an old case's stage is always
kept *discharged*); the real screens rendered and read by an independent reviewer twice (two blockers on the phone fixed; a nested
Find form — which would have submitted the case — found and fixed); an independent cold read of the code, two rounds (round 1 NOT SAFE: phone numbers in page addresses, a call double-tap
race, old cases inflating the vendors' balances and five corrections — all fixed, each with a walk check; round 2 SAFE TO INSTALL, its
corrections built in); the installer rehearsed on a
made-up server (DRY · install · ALREADY INSTALLED · a red after placing restores).

## Undo
```
cp -p /root/finance/surgery_cases.py.bak_S680_7effc05e /root/finance/surgery_cases.py && cp -p /root/portal/portal.py.bak_S680_1e0c6548 /root/portal/portal.py && cp -p /root/portal/tile_grants.json.bak_S680_83828b81 /root/portal/tile_grants.json && cp -p /root/wa/casepack/casepack_page.html.bak_S680_2dfe4221 /root/wa/casepack/casepack_page.html && systemctl restart clinic-finance && systemctl restart clinic-portal
```
(The added columns and tables are harmless to the old files.)
