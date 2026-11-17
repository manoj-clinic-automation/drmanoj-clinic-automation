# S846_SLIPS_NOT_IN_DOCTERZ — his list of slips not in Docterz (the parent, S471 → S474, 17-Nov-2026) — D994, A-D63

**His word.** 16-Nov-2026, 07:34–11:01 IST: he enters missed patients in Docterz back-dated himself; his list shows the FULL
mobiles; a few may stay outside Docterz; "go".

**The change — one NEW file and four patched; clinic-finance is restarted.**
- NEW `/root/finance/not_in_docterz.py` — his page `https://followup.dr-manoj.in/finance/clinic/not-in-docterz` (the console's
  gate, unit `packs`): every slip since 23-Sep (setting `nid.since` overrides) whose patient Docterz does not carry that day —
  OPD at the usual fee, X-ray / procedure net of discount (a rejected discount puts the full rate back), free lines out — only
  for days whose Docterz export has been read. Each row: date, what, amount, name, ID, the FULL mobile (the Call Console's
  mirror, read-only, his page only) and four taps: **Entered in Docterz · Not entering in Docterz · Free / staff / home ·
  Wrong slip**, each undoable. A row leaves by itself when Docterz carries it. One table `nid_mark`, created by his page's first
  request or tap (the readers never create it); one live answer per row (a unique index).
- `day_check.py` — a slip he answered Free / Wrong becomes a note; Entered / Outside place the money against the counter's
  room and become a note — with NO room the card stays (the counter does not hold the money). A part-billed line is never his.
- `clinic_money.py` — counter − Docterz equal to his Entered + Outside sum is explained; a bank UPI of an answered slip's amount
  is explained only for a slip not marked paid in cash, each once, never more than the counter's UPI over Docterz's.
- `owner_console.py` — "N slips not in Docterz — yours to enter back-dated" in Needs-you; the day's "Slips outside Docterz".
- `parchi_desk.py` (S844's 32f08523) — the patient lookup answers `old`: the patient's earlier slips not in Docterz; the desk
  shows one line "earlier slip (dd/mm · OPD) is not in Docterz — enter this visit in Docterz today".

**Install (one line on the server):**
`cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s846kit && cp -rp /root/deploy/repo/deploy_kits/S846_SLIPS_NOT_IN_DOCTERZ /tmp/s846kit && bash /tmp/s846kit/install_S846_SLIPS_NOT_IN_DOCTERZ.sh`
Undo: `bash /tmp/s846kit/install_S846_SLIPS_NOT_IN_DOCTERZ.sh --undo`. `DRY=1` before `bash`: every gate, nothing written.

**Proof.** `walk_s846.py` on a MADE-UP root (42 checks; the live files go red as the control; the first build went red on the
cold review's six cases); `shape_s846.py` on a copy of the live database — 14 days, no answer marked, the day check and the money
match exactly as the live files'; `walk_s844.py` 31/31 and `walk_s840.py` 25/25 on the new desk. The installer runs all of them
on a copy of the live database before placing anything.
