# S391_LAB_NO_ID — lab reports mailed without a clinic ID

**What went wrong on 24-Sep.** Sukhveer mailed the pending reports at ~4:30 pm and tapped *Mail kar diya*. The reports
reached the clinic mailbox within minutes — but eight of the lab's e-mails had **no clinic ID in the subject**
(`Your Report  MRS. <name>` instead of `… ( 8118)`). Both mailbox runs read the ID only from the subject, so they
skipped those e-mails silently: Report baaki never heard of them and the PDFs were not filed on the patients.

**The fix.**
1. The mailbox now asks the clinic server about an ID-less report (`POST /finance/slips/api/lab-noid`, same token as
   lab-report). The report joins the **one** open blood test with the same name — a mailed one wins a tie, a re-send
   follows the first, a name with no usable word matches nobody. Its line clears at once and the PDF is filed.
2. Anything not certain appears on **Report baaki → Report aayi, ID nahi likha** with *Yahi hai* (pick the patient or
   type the ID) and *Hamara nahi*. Nothing is guessed.
3. The blood tab reminds the desk: write the ID after the name in the lab's mail.
4. What arrived by name is marked *naam se juda* under *Aa gayi*; the doctors' counts gain `no_id`.

**Proof.** `walk_s391.py` 38/38 on a scratch copy of the live database, replaying 24-Sep's shape with invented names
(12 ID-less e-mails incl. re-sends → all placed; same-name ties; no-word names; order written after its report; the
desk's taps; token refusals). The S383 walk's 35 functional checks also pass on the new file. The live S384 file is
the negative control. `slip_log.py` 30d799e1 → 00038e76. Restarts clinic-finance only.
Mailbox half: `VPS_Lab_Files.gs` S391 (sha256 2cd99234…) — placed in Apps Script by the assistant.
