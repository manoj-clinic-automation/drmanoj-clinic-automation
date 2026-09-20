# S277 BUILD BRIEF — the X-ray test page reads your staff's real naming (0 → 8 of 9); the drift check has a living copy; and the next three blocks of work are settled in your words

*Session 277 · the parent project · 20-Sep-2026 · written at the close. The one document for the next session.*

---

## 1 · WHAT WENT LIVE TODAY (each from your one line)

| kit | what it does now | proof |
|---|---|---|
| **S351_XRAY_NAMES** (~13:33) | The X-ray test page reads the clinic ID **wherever** the staff put it in the name — they write `NAME 1234.jpg`, the second view `NAME 1234 ..jpg`; a file with no number takes its sister's ID and says so; two numbers go to a person. | page read live: **6 of 9 matched** (was 0 of 9); the X-ray PC clock agrees with the slips (median −5 min) |
| **S352_GAS_REPO_COPY** (13:33) | The Sunday check of the three Google Apps Script projects compares against a **living copy** in the repository (`GAS_CURRENT`) instead of the frozen 7-Sep photograph. It had been behind on two projects, not one, and its report went to a log nobody reads. | the read-only diff in your paste showed exactly the two expected findings; both clear at next Sunday's 02:20 export |
| **S353_XRAY_FILMS** (~14:3x) | Your ruling: one film per study; **Knee studies is the exception, two films** (both-knee AP standing, both-knee lateral). The page counts films. | page read live: **8 of 9 matched**; Phool Wati's two photos named *AP standing* and *Lateral*, slip 1143 |

```
https://followup.dr-manoj.in/finance/records/xray-test
```

The one file still in the check folder has no number in its name at all. **The live filing waits on 2–3 days of staff files** (there were 1½ today); 21-Sep and 22-Sep should give them.

## 2 · NEXT — the three blocks, in your order (D586 · D587)

**Ahead of everything:** the live X-ray filing, the day the test folder holds 2–3 days (`S273_BUILD_BRIEF §2`).

**Block B — the mail flood.** Measure first: every automated mail of the last 30 days in both inboxes, by project — the vehicle tracker, the UPI-received chain, the old Google-Form daily-payments system (Sanjeevni · Marg · doctors · Labmate · NK Pathology), and the Callback Tracker's own digests, summaries and morning report — with the Sheet each fills, the tile each holds and the VPS screen that now does the job. What stays without asking: the bank-statement relay, UPI Reconciliation, the Daily Clinic Report, **the system-health mail** (your word). Then one page you tick, KEEP · RETIRE; retirement is triggers switched off in your signed-in browser, restorable in one click, nothing deleted; then a quiet week and the count measured again.

**Block C — the Callback Tracker, kept and de-frictioned.** In build order: **sign in once through the Clinic app, no second login** (Shavez's days of being signed out end here) → the **caller tile** on the staff phone when a call comes in (clinic ID, name, last visit; the finalised design read back from the record; first proven that the incoming-call event reaches the server, and the delay measured on a real call) → **why it loads slowly**, measured, then fixed → the **WhatsApp call and reply buttons for every staff member**, not only you → the **WhatsApp-message ntfy alert with the sender's number** (your ruling). The Gist and Call Console improvements go on the same page you tick.

**Block A — the PWA tiles, last.** The new layout drafted as a page you open on your phone — your own screen first, then each staff member's — you tick or correct it, then one kit. The tile system itself stays.

Your part across all three: ticks on two pages, one look at the drafted layout, and the VPS lines.

## 3 · PINS

| file | pin |
|---|---|
| `/root/finance/records.py` | `07ec9b41cb5bbded215dcd1b1916e3d0` (S353, over S351 `4c2f38b9`) |
| `/root/state_backup/clinic_state_backup.conf` | one line added: `GAS_REPO_COPY=/root/deploy/repo/deploy_kits/GAS_CURRENT` (S352) |
| `deploy_kits/GAS_CURRENT/` | living folder, 13-row `SUMS.md5`; every Apps Script change updates it (D583) |
| `/root/finance/finance_app.py` | `29819879dec3f057b7690e004e4e87cb` — unchanged |

## 4 · THE LESSON (F-593 · F-594)

A rule about how people name or photograph things is measured on their own files before it is written. The brief imagined `1234 NAME.jpg`; the staff wrote `NAME 1234.jpg`, and one question to you settled how many photographs a study makes. Both fixes were one line each — once the real thing had been looked at.

*S277 · 20-Sep-2026. Decisions D583–D587, findings F-593–F-596.*
