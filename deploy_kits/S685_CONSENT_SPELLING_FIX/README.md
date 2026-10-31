# S685_CONSENT_SPELLING_FIX — the parent, session S371, 31-Oct-2026

**What the owner found (09:28 IST).** In the consent's *Hindi spelling* box (S385, 24-Sep) he corrected the address and pressed *Apply everywhere*; the address in the consent did not change.

**Why.** The consent prints a name or an address tidied — no space before a comma, no double space (and, in Hindi print, no English in brackets). The box looked for the spelling as typed, found it nowhere, still showed *"✔ Address: 0 places"* and changed only the page header. Reproduced with made-up addresses ("Civil Lines , Bareilly", "Gaon  Rampur Bareilly"); the same held for the relative's name.

**The fix (one file).** `/root/wa/casepack/casepack_page.html` ff713e36 (S684's TO) → the kit's page: the box looks for the spelling as printed; a correction that finds no place changes nothing (header included) and says so in words. No restart.

**Proof.** `walk_s685.py` in Chromium, made-up names, both print languages: **10 of 10**; control on ff713e36 **7 red · 0 older red**; four mutants each caught; `walk_s684.py` still **45 of 45** on the new page. Independent cold review SAFE TO INSTALL, its one correction (the *हिंदी + English* print tidies less than the Hindi print) built and walked. Installer rehearsed on a made-up root: DRY · install · ALREADY · red after placing restores · a changed live page refused.

```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s685kit && cp -rp /root/deploy/repo/deploy_kits/S685_CONSENT_SPELLING_FIX /tmp/s685kit && bash /tmp/s685kit/install_S685_CONSENT_SPELLING_FIX.sh
```
