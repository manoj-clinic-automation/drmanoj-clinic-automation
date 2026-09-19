# S330_BLOOD_TEST

Blood tests in the slip tile: the chamber logs the order (two taps); the lab report e-mail (clinic ID in the subject) reaches the server through `VPS_Push_Lab.gs` in the clinic mailbox and joins reception's Docterz-upload list; at upload time only, an order with no report is answered once (not tested / lab did not e-mail). The report lists both for follow-up. Walk: 125 checks.

```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S330_BLOOD_TEST/install_S330_BLOOD_TEST.sh
```

One-time, in the Apps Script project **UPIReconciliation** (drmka.ortho@gmail.com): add a file `VPS_Push_Lab`, paste `VPS_Push_Lab.gs`, Save, run `setupLabPush`.
