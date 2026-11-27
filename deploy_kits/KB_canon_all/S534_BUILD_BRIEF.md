# S534 BUILD BRIEF — the Sanjeevni chat, 27-Nov-2026 (for Dr Manoj)

**Nothing changed on your screens today.** At your word, the plan from yesterday's session was checked against the real code and the real database before anything was built — and it holds.

- **What the check found:** every rule in the plan has its data in the system already; the two faults the plan names (KT ROS DT reading "not in Marg", the item ledger without Darpan's counts) were traced to their exact cause in the code; the PANTAVIN 40 batch-number note turned out to be Marg's own printing, not an error of ours. One thing the plan had forgotten: Amir already gets wrong-batch corrections on his card every night from the Expiry watch — 11 are open with him now.
- **Your decision:** those night-time batch asks stay as they are. The new page will not raise batch-only differences a second time.
- **The build, by Opus, in this order:** first the one Stock check page you approved, read-only — every row opening in place with its steps, its voucher lines and its item ledger (now with Darpan's counts), the old corrections re-judged, KT ROS DT reading "waiting" again. Second, the Write off / Pursue buttons on that page. Third, Amir's card by itself and the inquiry for a voucher nobody asked for. Fourth, printed stock vouchers scanned only when needed.
- **Two things you will notice:** a count Darpan makes after 5 pm shows its buttons the next morning (it waits for the day's sales first); Pursue sends the item for a recount — if the recount agrees with Marg the row closes by itself, if it is still short it comes back to you with both counts.

**Next:** publish today's records, then open a fresh Sanjeevni chat with Opus and type `start` (session 535).

**Publish today's records:**
```
D:\dr-manoj-git\drmanoj-clinic-automation\PUBLISH_ALL.bat
```
on manojz — nothing follows it.
