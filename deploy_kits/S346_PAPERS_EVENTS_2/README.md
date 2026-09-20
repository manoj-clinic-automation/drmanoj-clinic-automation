# S346_PAPERS_EVENTS_2

Records step 5 (owner, S271_BUILD_BRIEF §2.3). **Outside MRI/CT reports, discharge papers and outside reports**: reception or the chamber add a photo or PDF with the clinic ID picked (Check karein → *Kagaz jodein*), or the doctor adds one on the patient page (*Add a paper*). **Hospital admissions and surgeries**: *Add event* on the patient page — date, hospital, what was done, note, and the paper if there is one. Each file waits on the server only until the mailbox script carries it to Google Drive (Clinic Records → Scans / Papers / Blood outside / X-ray outside); then it is filed on the patient and the server's copy is deleted. Walk: 174 checks. **S346 = S345 unchanged except the walk**, which S345 failed on the box because the live queue already held a real WhatsApp photo; every queue check now looks only at the walk's own rows.

```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S346_PAPERS_EVENTS_2/install_S346_PAPERS_EVENTS_2.sh
```

After the install, `VPS_Lab_Files.gs` (S345 build) replaces the S344 build in Apps Script project UPIReconciliation — done by the assistant in the owner's signed-in browser.

Pins: `records.py` `04af860f…` → `8cdd334f2f1329899afd8fc09df145fd` · `finance_app.py` `7866b1ee…` checked, unchanged.
