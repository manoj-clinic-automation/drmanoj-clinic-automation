# S504 BUILD BRIEF — the Sanjeevni chat (Fable), 22 → 23-Nov-2026 (for Dr Manoj)

**What changed (one kit, S933, in four versions through the night — live 07:0x Monday)**

- **One stock record, read everywhere.** Your Stock check page and the item ledger no longer work out stock each in its own way: the system writes one record per medicine — Marg's newest closing report (a morning report is the end of yesterday, no waiting), plus the bills Amir keyed after Shavez printed it (his purchase export tells which and when), plus the sales since; the shelf (the last count carried forward); the deliveries waiting for Marg; the gap — and every page reads that record. It is rebuilt every ten minutes and whenever a report, a tap, a scan or a count moves it. Kit 2 puts Darpan's count judgments, the Hub's count lines, the Expiry watch and the ordering engine on the same record.
- **The 53 "need a look" were mostly not real.** About 13 of them, including every large one (MEG QCS, PATOPAN DSR, FERONES HD, FLUXIC P, PRETOL 8 …), were bills Amir keyed after Saturday's print: on the shelf side, not yet on Marg's. They now agree. The page shows 39, and the ones left are questions, not bills.
- **The rows now say why.** TRAMATEE P: *"counted 9:4 on 21-11; Marg holds bill 502 (Mannat, 20-11: 40:0) — was that delivery on the shelf when he counted? count again."* TYRO BR and others with a count older than three weeks: *"the shelf figure is an estimate; count again."* A Marg figure that would go below zero is shown as "behind a bill", never as a number; the clinic's consumables sit apart and are never a shop difference.
- **Deliveries tied properly.** The "bill over the tap" rule from Saturday was silent whenever reception tapped before the bill was scanned (41 of 99 cases). It speaks on every delivery now — the page showed 0 waiting on Sunday night, every arrival in Marg.

**What moves this page** (your question, 07:13): purchases — by timing only, until both sides have the bill; Darpan's counts — the only thing that sets the shelf. After those, a gap is either real shelf loss / surplus, or a Marg entry with no record (the Marg watch's line). Sales never make a gap; they come off both sides.

**Checked before and after:** 37 offline checks on a made-up spine (two prints, bills keyed before / on / after the print, a return keyed late, a tap before its scan, a below-zero count, an old count, a fresh count below Marg); the old files go red on the same checks; a cold reviewer who had not seen the build caught two faults before anything was installed (a purchase return's sign; a crontab rewrite that could have wiped the nightly jobs); the installer rehearsed on a made-up server including an unreadable crontab and a forced failure; each version read live after your line.

**What waits on you**
- Nothing to install. Monday morning Darpan counts TYRO BR; his line reaches your Needs-you. If he can count TRAMATEE P too, that settles Mannat's 40.
- The publish of today's records (below).
- One tap: "Yes — same medicine" on VFER 500 — on the flow page or in Needs-you.
- Ram Singh: the Stock Register report in Shavez's Marg login, then Shavez's switch on.
- The packs page: the 25 card shops; the card and ICICI passwords.

**Your Stock check page:**
```
https://followup.dr-manoj.in/finance/stockcheck/
```
**Publish:**
```
D:\dr-manoj-git\drmanoj-clinic-automation\PUBLISH_ALL.bat
```
on manojz — nothing follows it.
