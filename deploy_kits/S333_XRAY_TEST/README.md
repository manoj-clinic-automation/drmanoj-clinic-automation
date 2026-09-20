# S333_XRAY_TEST

Records step 2, the **read-only test run** (owner, S271_BUILD_BRIEF §2.7). Staff put the pen drive's X-ray files into Google Drive → **Clinic Records → X-ray test**. The doctors' page shows each file: original name → proposed name → matched or not; the date comes from the file's own time and the page says whether the X-ray PC's clock agrees with the slip. Several files for one patient pair with the slip's X-rays in time order; if the counts differ they are numbered "X-ray 1 / 2", never guessed; an ID not in that day's list goes to the check folder; the same picture twice is kept once. **Nothing is renamed or moved.** Walk: 92 checks (S332's 79 + the test run).

```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S333_XRAY_TEST/install_S333_XRAY_TEST.sh
```

The mailbox script `VPS_Lab_Files.gs` in this kit **supersedes S332's copy** (same lab filing, plus it makes the three X-ray folders and tells the server their ids). One-time, in Apps Script project **UPIReconciliation** (drmka.ortho@gmail.com): add a file `VPS_Lab_Files`, paste, Save, run `setupLabFiles`.

```
https://followup.dr-manoj.in/finance/records/xray-test
```

Pins: `/root/finance/records.py` `b312a4d1…` → `f284fd150d5b19ca949d2b88f95df9c7` · `finance_app.py` `3a871f53…` checked, unchanged.
