# S757_XRAY_LAB_CHECK — the X-ray photo and lab-report check screens

**The owner, 09-Nov-2026 06:39 IST (D875):** his FINAL on mock-up `YBLGcgEAGi18QB9PL1bRL4` (v9) — *"Plan is final … build in a fresh session"*.

**Why (F-1205, F-1206).** 52 X-ray pictures sit parked in Drive's *X-ray check* folder waiting for a person, and Check karein showed
staff only a file name — nothing to look at. 42 lab-report days since 19-Sep have no blood slip that week (40 of those patients came
to the clinic that day or the day before), and *Report baaki* never knew of them.

**What changes.**

| who | where | what they see and do |
|---|---|---|
| Alisha, Shivani, reception | Check karein (phone or PC) | each parked picture **with the photo**, why it was parked, and that day's patients from every slip and Docterz line (the likely one on top: *ID milta hai / Ek ank alag / Naam milta hai*); tap the patient → **Haan, daalein**. *Inmein nahi? Clinic ID likhiye* · *Yeh X-ray nahi hai* · *Baad mein*. A patient with no X-ray slip: a warning. |
| Shavez | Check karein on his PC | **one queue** — X-ray photos and lab reports, newest first by month, chips *Sab / X-ray photo / Lab report*. A lab report with no blood slip: the report inline; **Blood parchi bana di** opens the Parchi desk with the patient filled and writes the slip on the visit day, then comes back; *Seedha lab gaye the*; a likely wrong ID → *Haan, ID … hai* (the report moves) / *Nahi*. |
| the owner | `/finance/records/xray-check` (from Patient records and his console) | four tiles — filed by themselves since 8-Nov · waiting for staff · X-ray taken, no X-ray slip · lab report came, no blood slip — each list by month, newest first, the photo or report inline, every staff button his too; *Wrong patient? Move*; *Charged elsewhere* / *Missed — tell Shavez* (the X-ray goes on Shavez's list until the slip is made). |
| ways in | Shavez's *Aaj ka kaam* (morning) · a strip on the Parchi desk · the Check karein tile as it is | |
| F-1185 | his portal home | the **Marg Purchases** tile shows (tile_grants v44). |

**Strict filing stands (F-1203):** nothing is filed or moved without a person's tap. A picture is filed the S373 way (the next
mailbox run files it; the mailbox script stays the only Drive writer). The other Check karein items (blood test with no report, lab
ID, WhatsApp, X-ray file not come) are under *Aur sawaal*, exactly as before; `/finance/checks?list=1` is the old list.
September shows on these two queues, as on his mock (the other items keep the 01-Oct floor).

**Who sees what (F-1179):** shared work queues — every permitted login sees the same list. Photos: any Check karein login, only while
the picture is waiting. Lab reports and X-rays to bill: Shavez and the doctors only, only while open. His page: the doctors.

**The cold review (S413) — R1 NOT SAFE, all built:** a correct report could be offered for a move to a namesake who visited
(now only when the ID's own name is not the lab's); a move could carry a second report nobody saw (now only one report, the one
shown); Enter on another button could file a picture (now only from the page or *Haan*); the desk let any slips login reach a lab
item (now Shavez and the doctors); a slip could land on a day the patient was not seen (now the visit day); the installer now
proves the doors are on after the restart, and *--undo* refuses if a later kit changed a file.

**Proof on last night's database (09-Nov copy, counts only):** 52 pictures waiting (Nov 4 · Oct 24 · Sep 24); a likely patient on top
for 39 of 52. 42 lab reports with no blood slip (Nov 1 · Oct 20 · Sep 21): 28 came the same day, 11 the day before, 1 earlier that
week, 1 a likely wrong ID (offered only when the ID's own registered name is not the lab's, for a single report), 1 with no visit. 48 filed by themselves since 8-Nov. The installer re-runs this on the live database.

**Install** (after the publish), one line on the server:
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s757kit && cp -rp /root/deploy/repo/deploy_kits/S757_XRAY_LAB_CHECK /tmp/s757kit && bash /tmp/s757kit/install_S757_XRAY_LAB_CHECK.sh
```
Undo: `bash /tmp/s757kit/install_S757_XRAY_LAB_CHECK.sh --undo`
