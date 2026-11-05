# S707_GMB_ENGINE — the GMB Review Assist wording engine · the parent · session 385 · 05-Nov-2026

**For the owner, in two lines.** The GMB Review Assist page now writes drafts the way your patients actually write: short, a story in order, your name once, no fixed closing, patients' own words for the trouble, and never a sentence already posted on your listing. A fourth language button, **हिंदी + English**, writes Hindi words in Hindi and English words in English.

## Why
D826 (the owner, 05:18 IST 05-Nov): the page is assistance only — the patient reads the draft and posts it himself; most accept it as it is, so it must read human, with no repeated phrases and no fixed closing. The final plan, `claude/S385_GMB_PLAN.md`, his OK 14:58 IST 05-Nov (Part A of three; B — drafts and edits saved — and C — local ortho listings watched — are later kits). The research behind it: 337 public Google reviews (170 of other Bareilly doctors, all 167 on his own listing), `D:\Downloads\ClaudeCowork\03_WORKING_PAPERS\S385\GMB_RESEARCH.md`.

## File
| live file | FROM | TO | what |
|---|---|---|---|
| `/root/portal/gmb.html` | e33aa612 | d9aad642 | the whole file replaced. The wording engine (the phrase tables and the composer behind *Generate* and *Fresh variation*) rebuilt; a fourth language button; "4 languages"; the size hints *one or two lines · up to 20 words · up to 50 · up to 90*. The tick lists, buttons, Copy, WhatsApp, Restore and the layout are byte-identical to the live page. The portal reads the page from disk on every request: no restart. |

## What the engine does (the plan's rules, each measured)
Real sizes — a short draft is one or two lines (8–20 words: what happened, one result, a brief thanks with the name); medium up to 50 words; long up to 90 and always longer than medium. A long draft reaches 60–90 words when enough is ticked; it never fills the gap with things nobody ticked. A story in order: what happened → came to the doctor → what he did → how it is now → (sometimes) one line about him → (sometimes) a close; the optional pieces drawn fresh at every press. ("Tried other doctors first" and "someone told us about him" were dropped at the cold review: no tick says them.) The name once at most, then *sir / doctor sahab / he*; the clinic's full name never; *Bareilly* in about one draft in five. Six closing kinds with many wordings, one draft in four with none; no "go and see him" line. Patients' words (घिसाव, gathiya, kamar dard, kalai, plaster, Ayushman); never "osteoarthritis". Nothing claimed that was not ticked — no fall, no "24 hours", no joined bone unless a fracture is ticked; an operation and "no operation" never in the same draft, and "recovery after the operation" only beside the operation. The only clinical number: **6 weeks of plaster for a wrist fracture** (the owner's figure, 05-Nov), and only when plaster and a fracture are ticked. Gender-neutral first person in Hindi and Hinglish. Typed, not typeset: about two drafts in five end without a full stop, 🙏 in a few thank-yous, Roman-Hindi spelling varied one way per draft. Each press is redrawn (up to 25 times) until its three drafts share no sentence and no long draft repeats more than three content words.

## Cold review (independent agent, S385)
R1 **NOT SAFE** — 2 blockers, both built: (1) English pronouns after the first mention — "Along with medicines, him gave…", "Thanks, him." in 16.5 % of English presses → now *he* as a subject, *him* after to/with/about/in, *doctor* when addressed; its own test: **0 of 3,000**; (2) "…and me was walking" in the hip-replacement lines (103 of 123) → "…and had me walking"; **0 of 126**. Its should-fix all built: trimming by importance (the operation is never cut while its recovery line stays); after an operation only a plain "a plaster was put on as well"; "the bone joined" only with a fracture ticked; no fall; no 24-hour figure; बाईं / दाहिनी with कलाई, कोहनी, पसली, जाँघ, रीढ़; one word for hand/fingers; "Self" went to the doctor (not "took him"); Mixed keeps Hindi words in Devanagari and one kind of full stop per draft; no doubled "की तकलीफ"; the hints say "up to"; Long always longer than Medium; neutral verbs for Self. Its notes on the installer: no fault. The walk now checks every one of these.
R2 **SAFE TO INSTALL** — no blocker, no should-fix (its harness: 0 of 3,000 English presses broken; 10,000 targeted drafts clean on every R1 item). Its three wording notes taken as well: *her / my* left wrist (not *the*); no subject-less "The hip bone broke." for Self; the "life is normal now" kind of closing only when relief or walking is ticked.

## Proven (S385, the cloud workspace, node 22 + headless Chromium)
- `walk_s707.js` — 8,400 drafts across every language, relation, problem and tick, checked against the 910 sentences of the 337 posted reviews: **WALK OK, every rule green** (0 broken, 0 English pronoun faults, 0 falls, 0 untold numbers, 0 slashes, 0 mixed full stops, 0 name twice, 0 without the name, 0 shared sentences, 0 sentences already posted, 0 over size, long shorter than medium and long drafts with more than 3 repeats each under 1 %). **Control:** the live page — WALK RED (name twice in all 1,200 presses, 1,414 sentences already posted, every short over size); S382's draft — WALK RED.
- `browser_walk_s707.js` — the page in Chromium at PC and phone width, clicked the way the owner uses it (relation, language, problem, bone, side, knee plan, good points, qualities, Generate, Fresh variation ×2, an edit and Restore), four cases × three presses: **BROWSER OK 162/162**, no script error, no sideways scroll at 390 px. **Control:** the live page stops (it has no fourth language button); S382's draft RED 72 of 162.
- 4,500 drafts with surgery, plaster and "no surgery" all ticked at once: 0 say "no operation".
- The installer rehearsed on a made-up server: dry run writes nothing; install places and reads back; run again → ALREADY INSTALLED; a changed live file, a config pointing elsewhere, a tampered kit and a held lock each STOP with nothing changed; a health failure after placing puts the live page back byte-identically and frees the lock.
- The posted-review files the walk reads hold patients' public texts and stay out of the repository: `D:\Downloads\ClaudeCowork\03_WORKING_PAPERS\S385\`.

## Install (on the server, after the publish; window 04:00–23:30 IST)
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s707kit && cp -rp /root/deploy/repo/deploy_kits/S707_GMB_ENGINE /tmp/s707kit && bash /tmp/s707kit/install_S707_GMB_ENGINE.sh
```
## Undo
```
\cp -p /root/portal/gmb.html.bak_S707 /root/portal/gmb.html
```
