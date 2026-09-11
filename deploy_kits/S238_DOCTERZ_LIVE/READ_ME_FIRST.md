# S238_DOCTERZ_LIVE — the Day Revenue screen updates itself again

**The owner, 11-Sep-2026:** "The Docterz revenue system is not getting updated since we set it up on
3rd Sept. Make it live again."

**Why it stopped:** the clinic PC still sends each morning's day sheet to Drive. The sheets for 4, 5, 7,
8, 10 and 11 Sep are all there. But the VPS reader that loads them into the Day Revenue screen
(`/root/finance/docterz_ingest.py`) was only ever run by hand. Its daily schedule was an optional step at
setup (S223) that was never added; the S230 freshness notes say so ("run by hand today").

**This kit** changes no code. It:
1. checks that the live reader is exactly the one built at S223 (md5 80bf760d…) and refuses otherwise;
2. backs up finance.db;
3. runs the reader once to catch up every day since 03-Sep, printing the day count before and after;
4. adds one schedule line so it runs itself daily at 09:40, 13:40 and 19:40. The morning sheet usually
   lands between 06:30 and 09:30; the later runs catch a late one. It is safe to run repeatedly:
   unchanged sheets are skipped, and a re-exported day is replaced, never doubled.

If the catch-up run reports a failure, nothing is scheduled and the backup is kept.

**Proven offline** (installer walk): green; a re-run adds no duplicate line; a reader failure leaves
nothing scheduled; a wrong reader file is refused before anything is touched; a tampered kit is refused.

```
bash /root/deploy/vps_deploy.sh S238_DOCTERZ_LIVE
```
