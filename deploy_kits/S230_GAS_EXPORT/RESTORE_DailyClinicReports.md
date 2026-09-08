# HOW TO RESTORE DailyClinicReports — without ever editing the live project

**Written 08-Sep-2026 (S232), after the owner asked for a restorable backup that needs no change in
Google. Nothing in the live project was read or altered to produce this.**

---

## The problem this solves

`DailyClinicReports/Code.gs` in this folder has four values masked as `«MASKED-S230»` and
`«MASKED-PHONE»`, on lines **587, 588, 589 and 590**. They are masked because this folder is in the
repository, and the repository may hold no credential and no phone number (F-185, and the S232
publish gate now refuses both). That made the copy safe to publish — and, as it stood, impossible to
restore.

## Why no code edit is needed

The project already reads Script Properties before its own literals:

```
var apiKey = props.getProperty('MYOP_API_KEY') || MYOP_DEFAULTS.API_KEY;
```

**Verified mechanically at S232, not assumed.** Every one of the four masked fields is read through
that pattern on the send path — lines 601, 602, 603 and 604. So a restored project that has the four
Script Properties set **never reads the masked literals at all**, and needs no edit.

**One exception, and it does not matter:** line 723, inside `showWhatsAppStatus()`, logs
`MYOP_DEFAULTS.WA_TO_NUMBERS` directly. That function is a manual diagnostic that writes to the
execution log; it is not on the send path and it cannot affect delivery. On a restored copy it would
simply log the mask string. *(Separately, that line writes a phone number into the execution log —
worth fixing whenever this project is next legitimately touched, and not a reason to touch it now.)*

## Where the four values live

```
D:\Downloads\margsync\_config\myop_defaults.json
```

**Off-repo by design** — the same place this project already keeps `stockist_phones.json` and
`escalation.json`. `D:\Downloads\` is not a git repository, so the publish gate never sees it and the
values cannot reach GitHub.

They were extracted on **08-Sep-2026** from a copy that already existed on manojz, machine to machine.
**No value was displayed, typed, or passed through a conversation**, and Google was not contacted.

⚠ **`MYOP_API_KEY` is superseded by the pending WABA token rotation.** Refresh that one entry when the
rotation is done; the other three do not change.

---

## The restore, if it is ever needed

1. Create a **new** Apps Script project. *(Do not paste into the live one.)*
2. Paste `DailyClinicReports/appsscript.json` and `DailyClinicReports/Code.gs` from this folder,
   **exactly as they are — masks and all.**
3. **Project Settings → Script Properties → Add**, once for each of the four keys in
   `myop_defaults.json` (`MYOP_API_KEY`, `MYOP_COMPANY_ID`, `MYOP_PHONE_NUMBER_ID`,
   `MYOP_WA_TO_NUMBERS`).
4. Set `MYOP_WA_ENABLED` to `YES` **only** if the WhatsApp leg is wanted. The code defaults it to `NO`,
   so a restored copy is silent until someone decides otherwise — which is the right default for a
   recovery.
5. Set the workbook properties the project expects (`SS_ID` and its siblings) to whichever workbook it
   should write to. **These are per-installation and are deliberately not stored here** — a restored
   project pointed at the live workbook by accident would write into it.

**Triggers are project settings and appear in no export.** A restored project is inert until someone
arms it, which is the safe behaviour and is why this is a recovery copy, not a deployment.

---
*S232 · 08-Sep-2026. The live Google project was not read, edited or re-exported to produce this.*
