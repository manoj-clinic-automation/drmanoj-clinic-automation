# S216_CP11_TONE — CP-1.1 step 4: flow, tone, and the language switch

**Page only.** `casepack_portal.py` unchanged and NOT installed.
**This kit changes consent wording.**

## Provenance — where every word came from

`D:\Downloads\CONSENT_TONE_S216_FOR_YOUR_PEN.txt`, md5 `21cf41e9…`, the owner's
own returned file:

| part | his ruling |
|---|---|
| A — the polio paragraphs | returned unedited, then **approved in chat: "polio excellent work"**. Held until he said so — silence is never DONE. |
| B — the 34 bracketed glosses | **"none needed"** — all may disappear in Hindi-only mode |
| C — the loose English words | 1: *एक्सरे और एमआरआई जांच* (his wording) · 2: *नई लिगामेंट बनाकर* · 3: *घुटने की लिगामेंट (ACL)* unchanged |
| D — the switch | **starts on हिंदी every time; does not remember** |

**Two words were missed in the owner's Part C and are recorded here, not hidden:**
the draft said three loose English words remained; a re-measurement before
building found **five** — `implant` twice in the hip templates and a second
`graft` in the ACL risk line. Both were put to the owner with a proposal and
follow his existing house style (`इम्प्लांट` is already how the
implant-removal template spells it).

## What changed

- The polio module prints as **flowing prose under a Hindi lead line**. The
  bold heading is gone; `h` is now empty and the generator prints a module's
  paragraphs as ordinary `<p>`s.
- A **हिंदी | हिंदी + English** switch above the consent. In Hindi mode a
  bracketed group containing Latin letters is dropped from the printed
  paragraphs.
- It is applied **only inside the paragraph loop**, so the attestation line —
  which carries the owner's `(M.S. Ortho)` — is untouched *by construction*
  rather than by a protected list that could rot.
- **The stored template is never edited.** The switch changes only what prints,
  so toggling can never lose a word. `TONE_WALK` asserts the English is still
  in the store after a Hindi-only print.

## Measured result

**No English words remain in the consent body at all** — only "Dr. Manoj
Agarwal" and "(M.S. Ortho)", which are his and deliberate. That is the
measurable form of the complaint that started CP-1.1.

## Proof

| gate | result |
|---|---|
| `TONE_WALK.py` (new) | **16/16** |
| selftest · render · guard · contrast · naming · back · smart | 32/32 · 18/18 · 19/19 · 9/9 · 14/14 · 12/12 · 21/21 |

Two older suites asserted the polio wording the owner had removed. They were
updated to assert the **new prose and that the heading is gone** — the change
itself, not merely a green light.

## Install

    cd /root/deploy/repo && git pull && bash deploy_kits/S216_CP11_TONE/install_tone.sh

Base `62d472fd…` → new `63b2cba4…`.
