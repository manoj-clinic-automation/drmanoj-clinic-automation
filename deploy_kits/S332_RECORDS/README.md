# S332_RECORDS

The 360° patient record, step 1 (owner, 19/20-Sep-2026 · S271_BUILD_BRIEF §2). A doctors-only page — patients of the day on top, one click to a patient's visits (Docterz), X-rays taken, blood reports, Sanjeevni bills with returns shown against the bill (only bills the system is sure of), procedures. Blood-report PDFs are saved by the clinic mailbox into Google Drive → **Clinic Records / Blood / <Mon YYYY> / <DD-Mon>** and opened from there through the server's read-only reader account; never a public link; every open logged. Walk: 79 checks.

```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S332_RECORDS/install_S332_RECORDS.sh
```

One-time, in the Apps Script project **UPIReconciliation** (drmka.ortho@gmail.com): add a file `VPS_Lab_Files`, paste `VPS_Lab_Files.gs`, Save, run `setupLabFiles`. It prints the check, including the Drive space.

```
https://followup.dr-manoj.in/finance/records
```

Pins: `/root/finance/records.py` NEW → `b312a4d13c9eb9324cfb34abea5dc3ed` · `/root/finance/finance_app.py` `41e0ffb4…` → `3a871f53b5208edf8f218baeaa6c2882` (patched on the box).
