# S344_WA_REPORTS

Records step 4 (owner, S271_BUILD_BRIEF §2.3). Photos and PDFs patients send on the clinic WhatsApp are swept from the receiver's own logs (read-only), saved into Google Drive → **Clinic Records → WhatsApp** by the mailbox script, and put in **Check karein**: reception opens the file, confirms the patient (the ones on that mobile are suggested, never chosen) and the kind — Blood / X-ray / MRI-CT / Other — or "Report nahi hai". Only then is it filed on the patient's record. The server keeps the sender only as the salted fingerprint and the last four digits. Walk: 150 checks.

```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S344_WA_REPORTS/install_S344_WA_REPORTS.sh
```

After the install, `VPS_Lab_Files.gs` (S344 build, this kit) replaces the S333 build in Apps Script project UPIReconciliation — done by the assistant in the owner's signed-in browser.

Pins: `records.py` `0f3e48ca…` → `04af860fc146d47e49344c67e025cf8c` · `finance_app.py` `7866b1ee…` checked, unchanged.
