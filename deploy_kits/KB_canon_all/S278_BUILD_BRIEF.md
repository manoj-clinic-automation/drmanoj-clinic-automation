# S278 BUILD BRIEF — the order is settled: the Callback Tracker's sign-in once, then the caller's name on the staff phone as it rings

*Session 278 · the parent project · 20-Sep-2026 · written at the close. The one document for the next session.*

---

## 1 · WHAT CHANGED TODAY (nothing for you to do)

| what | what it does now |
|---|---|
| **The nightly report of the 02:05 unattended run** | now also lands in Drive (`Clinic_Unattended_Reports`), and your PC's 03:10 nightly copies it into the ClaudeCowork folder — so it is backed up and on the SSD, and a lost night raises a warning by itself (D588, kit S354). The run reads the current start-up instructions (v10). |
| **Vitals & Plan** | found: the tile only shows on a browser marked as the clinic PC, and the tool was never moved to the VPS (F-598). To use it today on your PC: double-click `D:\clinic_writer\open_vitals.bat`, then open `https://followup.dr-manoj.in/portal/mark-pc` once. The move is on the list, last. |

## 2 · NEXT — in your order (D589)

**Ahead of everything, only if ready:** the live X-ray filing, the day the test folder holds 2–3 days of staff files (`S273_BUILD_BRIEF §2`).

1. **Callback Tracker — one sign-in through the Clinic app.** Staff open the Tracker from the Clinic app and are already signed in; no password fetched from the Apps Script project again. Starting point: the portal's sign-in token (`/root/portal/clinic_sso.py`, signed cookie on `dr-manoj.in`) cannot be read by a Google page, so the portal hands the Tracker a short-lived signed pass and the Tracker checks it with a shared secret kept in its Script Properties. The Tracker change is placed in your signed-in browser (D577) and `GAS_CURRENT` updated in the same breath (D583) — the Tracker becomes the fourth project in it.
2. **The caller's name on the staff phone as it rings (D590).** A second MyOperator webhook entry — *Dial Begin* and *Answered* only — to a new receiver on the VPS; the live call recording is not touched. The caller's number is looked up in the VPS's own patient table (`finance.db` `patient_ref` + `patient_visit`): a known patient shows name, clinic ID, last visit and open items; a family phone shows every name on it; an unknown number shows *New number*. The pop-up is sent by our server through the Clinic app (Web Push — free, no message limit; **not ntfy**) to the phone being rung, and changes to *answered by …* on the others. Each staff phone taps *Allow notifications* once; one real call proves it. The after-call tile in the Tracker stays as it is. About 6–8 hours.
3. **The rest of the Callback Tracker** — why it loads slowly, measured then fixed · the WhatsApp call and reply buttons for every staff member · the sender's number in the WhatsApp alert · the Gist and Call Console list on a page you tick.
4. **The mail flood** (D586) — measured, your ticks, switched off in your browser (restorable), a quiet week, counted again.
5. **The portal tiles** — the new layout as a page on your phone, your screen first; your ticks; one kit.
6. **Two small follow-ups** — the Sunday Apps Script report onto the health page (F-595); the nightly's checksum backups kept out of the canon folder for good (F-596).
7. **Vitals & Plan to the VPS** — every screen and all the readings kept, patient data on the VPS disk and not Drive, the PC copy kept as the fallback.

## 3 · PINS

| file | pin |
|---|---|
| `D:\Downloads\_kbtools\NIGHTLY.bat` | `f0a070f231f085e3e07949d9443e86d2` (S354, from `26b93fe6`) |
| `D:\Downloads\_kbtools\unattended_pull.py` | `b5560a3182327fd62194abfc3789cf25` (S354, new) |
| VPS | unchanged from S277 — `records.py` `07ec9b41`, `finance_app.py` `29819879`, `portal.py` `d9a9dc40`, `call_hook_capture.py` `b8a1a293` |

## 4 · THE LESSON (F-597)

The last brief told this session to read the caller design back from the record — and had itself misread it, so the first answer proposed a channel you knew could not carry the call volume. A decision is quoted, not paraphrased.

*S278 · 20-Sep-2026. Decisions D588–D590, findings F-597, F-598.*
