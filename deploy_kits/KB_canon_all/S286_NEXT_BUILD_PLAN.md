# S286 → NEXT BUILD PLAN — A · B · C (agreed with the owner, 30-Sep / 01-Oct-2026)

*Written in the S286 chat (the parent) for the fresh chat that builds it. Nothing below is built. The owner
agreed every flow here in his own words; technical choices are the assistant's. Open the fresh chat with:*
**"Read claude/S286_NEXT_BUILD_PLAN.md and build it."**

## 0 · BEFORE ANY CODE

- **Claim on the System Board first** (`board/_numbers`, version-pinned): session number, kits, D/F.
  The board's `claims` already carries a PLANNED line for the files below (S286, 01-Oct). Re-read it:
  if the Sanjeevni chat has claimed any of these files since, stop and settle with the owner before
  touching that file.
- **Read every file live** from the newest nightly bundle on manojz
  (`D:\Downloads\_kbtools\vps_code\code_nightly.tar.gz`), never from an older scratch copy.
  - Hashes at 01-Oct 01:35 IST: `/root/assetapp/asset_register.py` **0deaa531** (moved by Sanjeevni S440);
    `scanner_widget.js` unchanged since S219.
  - `slip_log.py` and `owner_sheets.py` are unchanged since 30-Sep.
- **Build offline, walk on copies of the live DBs, then hand the owner one install line per group.**
- **Model:** Opus. The Fable weekly limit is used up; that changes nothing in the method.

## A · SCAN APP + RATE PAGE  (one kit; parent-owned files)

### A·1 Scan flow — staff never wait, never answer questions (owner, 01-Oct)

**Staff side:**
1. The "kind of bill" drop-down stays, as now, opening on each person's default lane.
2. Every photo becomes a page by itself (the auto-detected outline). There is no "Add this page" tap, and
   each thumbnail has a small Retake.
   - A 2–3 page bill is 2–3 photos, then one Save.
   - A one-page bill is photo + Save.
   - Only the bill intake config changes; the widget's other callers stay as they are.
3. The stamp number shows at once, big. Staff write it on the paper; the camera reopens.
4. A slow upload retries by itself, so nobody re-scans out of doubt. Double scans most likely start there.
5. "Choose file" (a PDF bill from WhatsApp or email) stays: one bill, one stamp, no paper.

**Server side, after the fact:**
- **A forgotten page** is joined to its bill automatically: same person, within a few minutes, same bill
  number or no bill header. Both stamps resolve to the bill.
- **A sure double scan is set aside automatically.** Sure means: same supplier, the same bill-number digit
  tail, and the amount within 2%.
  - Reuse S439's rule: `purchase_app._bill_tails_s439` and its supplier similarity.
  - The bill is kept, never deleted, and left out of counts and packs.
- **A near match or a likely wrong lane** (e.g. a known pharmacy supplier in the clinic lane) goes to BOTH
  Shavez's list and reception's list.
  - Owner, 01-Oct: double scans go "to all — Shavez and the reception staff".
  - The first answer settles it; who answered is shown.
- **Use the existing "Scan ka kaam" list** (Sanjeevni S440 in porders) for anything that needs a person.
  Never put a question on the scanning person.

**The shared "Reception" login:**
- Facts:
  - 65 of 102 scans so far were under the shared "Reception" login (61 of them on 29-Sep), so who scanned is
    unknown.
  - The reception login is not in `porders.senders`, so it cannot send purchase orders.
- Build:
  1. When the shared login opens Scan or Purchase orders, it asks once "Kaun kaam kar raha hai?" with big
     name buttons: Shivani, Alisha, Darpan, Sukhveer, Shavez.
  2. The name is remembered until 30 minutes idle or "Badlo".
  3. Every stamp, order sent and arrival marked carries that name.
  4. Add reception to the order senders on that basis.
  5. Staff on their own logins are never asked.
- The owner chose this over disabling scanning on that phone: its WhatsApp is the order-sending one.

### A·2 X-ray & procedure rate page  `/finance/clinic/sheets` (owner_sheets.py)

- **Compact layout:** one short line per item (name · price · side). Tap a line to edit; consumables stay
  folded.
- **Saves happen in place** (fetch), with no reload and no jump to the top.
- **The fault:** `_back()` drops `?kind=xray`, so every X-ray save lands on the procedures view. Fix it.
- The owner prefers collapsible sections and no long scroll (preference of 28-Sep).

## B · PARCHI (SLIP) LOG  (one kit; slip_log.py + clinic_money.py read side)

### B·1 Discount and free, with maker–checker

- Any X-ray or procedure line can take "Chhoot ₹___" or "Free" (free = full discount).
  - The reason is a pick: staff/family · poor patient · repeat/redo · doctor's instruction · other.
  - Today only procedures have a discount box (S379), and 0 of 126 slip lines have ever used it.
- **Who:** reception (and Shavez, Bhati) enter; Shavez or the owner approve; Dr Bhawna also approves (already
  a slips checker). Nobody approves their own entry.
- **The patient never waits.** Approval comes later in the day; a rejected discount goes to the night report.
- Staff still apply the discount in Docterz; our entry is the record and the approval.
- **The night check:** Docterz below the rate with no approved discount → flag "discount not written" to the
  biller.
  - Measured 19–29 Sep: X-ray below the rate on 9 of 53 visits, procedure on 2.
- **The owner's page:** a monthly total of discounts and free items — who asked and who approved.

### B·2 Cancelled after billing (Docterz cannot cancel)

- "Radd" on a parchi asks for the clinic ID and one choice: money returned / money never taken. It is
  approved like a discount.
- That Docterz line then leaves the expected cash/UPI and shows under "Cancelled after billing".
- **The case:** Tehzida Begum, 29-Sep, Docterz consult ₹600 cash.
  - OPD parchi 19517 was marked cancelled at 20:12 with NO clinic ID.
  - After install, staff add her ID in one tap. Do not guess it.

### B·3 Late parchis

- The 7-day late entry exists (S401). The fault is that the day stays on "Aaj".
- **The fix:** the screen proposes the day itself when the ID is in yesterday's Docterz and not today's, or
  the parchi number is below today's first number. One tap accepts.
- **Data:** move OPD 19493–19509 (17 parchis, entered 29-Sep 08:47–09:02) from 29-Sep to 28-Sep, audited.
  - 28-Sep had 21 Docterz consult patients and 5 slips.
  - 29-Sep had 30 slips and 12 patients.

## C · DOCTERZ PICKUP + FOLLOW-UP TRACKER TO THE VPS  (one kit + one reception setting)

### C·1 Docterz export from the reception PC

- Chrome on the reception PC saves downloads into a new clinic-Drive folder, "Docterz exports". This is the
  same road as the X-ray inbox: Drive for Desktop (clinic account) is already on that PC.
  - The one human step is staff exporting the two reports.
  - The Chrome setting is a one-minute step at reception; give exact staff words.
- **The server reads the folder every ~15 minutes** with the read-only service account (as docterz_ingest
  already does).
  - Identify files by content, never by name.
  - A day is replaced, never appended; the newest export wins.
  - A newer file with fewer rows is quarantined and shouted (S223 spec §3).
- **Alarm:** no export for yesterday by 10:00 → red line on the owner's page, self-healing.
- **Check one real export first** for the per-patient cash/UPI/card split.
  - Exports sit on manojz `D:\Downloads\consultation_report_*.csv` and `followup_logs (n).csv` since 10-Sep.

### C·2 Follow-up tracker → VPS (a relocation, not a rebuild)

- **Where it lives now:** the tracker is Flask/Python on the owner's PC: `app.py` 2,150 lines, `processor.py`
  3,506, `revenue.py` 751.
  - Path: `C:\followup_tracker_local_test_kit\local_test_kit\followup_tracker`. This is NOT a connected
    folder; the owner's one action is the folder-access approval.
  - It is still running daily. Staff_Action_Today in Drive appeared 28-Sep 23:10 · 29-Sep 21:10 ·
    01-Oct 05:01 IST, each a few minutes after his export.
- **Move the same code onto the VPS behind clinic SSO as a portal tile.** Inputs come from the server-side
  exports; outputs go straight into the server.
  - The push watcher (`watch_and_push_followups.py` → :8100) becomes unnecessary.
  - Still write Staff_Action_Today so every downstream reader is unchanged.
  - Use the server's own credentials; never read the PC's `.env` (F-31).
- **Proof:** no side-by-side week (the owner ruled it out). Run the VPS copy over every saved export since
  10-Sep and compare row for row with the PC tracker's outputs for the same days before install. After
  that, only the next-day check.
- **The PC copy stays** as the fallback, untouched.
- **Size:** one session plus the next-day check, unless reading it whole shows a surprise — say so before
  going on.

## NOT IN THIS BUILD

- The Callback Tracker (Google Sheets): held by the owner, 01-Oct ("working reasonably well").
- The bank-SMS door: DONE by Sanjeevni S439, 30-Sep.
- **Noticed by S439, open for the owner, not this build:**
  - The SMS travels in the URL, so the web log holds bank SMS text. One macro change moves it into the body.
  - Macro 2 forwards every Yes Bank SMS, including two other account tails.
- **The mini PC:** the owner is deciding. Clear benefits only: a nightly backup that does not depend on
  manojz being on, and a home for local jobs. No local server is needed.

## DELIVERY

One build session; three install lines (A, B, C), so a fault in one never holds the others. Each kit
follows the standard shape: gates · FROM md5 · walk on DB copies · backups · place · restart · probes ·
journal · live report. The publish is the owner's double-click:
`D:\dr-manoj-git\drmanoj-clinic-automation\PUBLISH_ALL.bat`.
