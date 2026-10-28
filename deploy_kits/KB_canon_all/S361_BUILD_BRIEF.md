# S361 BUILD BRIEF — the Sanjeevni chat, 28-Oct-2026 — the procedure bill of 27-Oct; procedure bills now counted the moment the sale report lands

*For the owner. The next Sanjeevni chat is session 362 (reserved). The same text is in project knowledge, `D:\Downloads\ClaudeCowork\03_WORKING_PAPERS\S361\` and `F:\ClinicBackup\DrManojClinic_Automation\03_BUILD_BRIEFS\`.*

**What you found.** Procedure bill 4474 of 27-Oct (₹98, one Loftypred 80 injection) was not taken off the day's cash.

**Why.** The system read the bill correctly. But the procedure deduction was made by a job that runs every half hour, and only on a day not yet approved. Your export reached the server at about 08:31, just after the 08:30 run. The day was approved before 09:00, and that job never changes an approved day, so the bill stayed in the cash. Your 08:42 handover entry therefore showed ₹97 short.

**Live now (09:59, read on the server after install).**
- **A home or procedure-medicine bill is taken off the day's cash the moment the sale report arrives**, in the same step that reads it. No day can be seen or approved without it. The half-hourly job stays as a backstop.
- **27-Oct is corrected:** procedure medicine ₹98, expected cash ₹8,379. Dr Bhawna received ₹8,380, so the day is **settled**.
- Every earlier approved day since 1 September was checked; none had this gap.

**It took three tries.** The server refused the first two at their own safety check, before changing anything. The first time, my test looked on the server for the export file, which the server deletes after reading (no patient phone numbers are kept there). The second time, my test didn't expect your 08:42 handover. Both were faults in my tests, not in the fix. Each refusal changed nothing.

**Yours:**
- the publish of this close, one double-click;
- still from before: **Bhejo** on the two September payment messages (A.A. Pharmaceuticals, Deepam), **Dealer badliye** on scan B-0167, **before 1-Nov** REEBORN D and RIFAVAX 550, Shivani's Marg login.
