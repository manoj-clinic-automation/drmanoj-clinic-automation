# HANDOFF RUNBOOK — v190 — written at the S268 close, 18-Sep-2026

*Supersedes v189 (the parent's S267 close, 18-Sep 01:46) in full — **not v188**; see the note at the end of §0.*

*The Sanjeevni project. The Sanjeevni project. v189 changes §0 — what is owed — and adds §3, the one rule this session cost the most to learn.*

---

## §0 — WHAT IS OWED, AND TO WHOM

**To the next session, one body of work, and it is named in `START_HERE_SESSION_270.md` §1: the Marg report contract.** The owner's words, 18-Sep: *"I want you to work from the very thing that this system is built from. That is the various type of Marg exports you read. And then you populate the data here. Because my confidence in your work is shaken right now."*

It is shaken for a reason this session proved three times over. Read §3 before starting it.

**To the owner: nothing this session is entitled to ask him for.** His stock-check part is settled, it is his, and it is not to be raised — not as a prompt, not as a blocker, not as an opening line. He will say when it is done.

**Read F-537 before you write your first canon file.** This close appended to the versions it read at
its open and found, at the pins step, that the parent's S267 close had taken Register v5.108, Archive
v1.106, Fault v2.93, Runbook v189 and `START_HERE_SESSION_269` seven hours earlier. The two canon files
that carry **no session in their name** were not collided with but **destroyed**, and were recovered from
the published commit `5cfc938` by cloning in the cloud workspace. **List `KB_canon_all\` by `ls`, and read
the board, in the minute before you write your first canon file — not at your open.**

**Outstanding publish: none once the S268 close lands.** `S314_SECTION_SCOPE` is built, publish-ready and **not installed**; its one VPS line is in `START_HERE_SESSION_270.md` §2 and is the owner's to run when he chooses.

---

**Canon at this close:** Archive **v1.107** · Fault **v2.95** · Register **v5.109** · Runbook **v190**
(this file) · Sanjeevni Book **v1.4** · `live_pins_S268close.txt`. **Next free: D550 · F-539 · A-D25 ·
kit S315 · Session 270** — and the board wins if it is later.

---

## §1 — THE BOX, AS IT STANDS

Live and pinned in Register **v5.109** (which `live_pins_S268close.txt` is generated from). New since the parent's v189:

- **The claim queue** — `claim_queue.py` `a61744ee` NEW · `stock_app.py` `10be8a9e` · `darpan_app.py` `df3224c5` · `darpan_card.html` `8510c9cb` · `stock_hub.html` `c4f3280b`. A pursued line becomes a claim; Darpan carries it *open → contacted*, **the owner settles and only he does**. Hub step 8 can now reach DONE. The self-closing half is asleep behind a live capability test (**F-527**: no purchase return is stored anywhere on this box).
- **The section map** — `section_map.py` `b05b0f08` NEW · `stock_sections.html` `17e006cc` NEW. One stored answer to *"which section is this item in"*, seeded at 373 rows, corrected by the owner the same morning: seven items moved, Orthotics 68 → **69**. Read by nothing yet, on purpose. **D548: it decides SCOPE only, never whether a shortfall is a loss** — the consume / ortho / dead lanes keep their own word lists.
- **Unchanged and still live:** `marg_ingest.py` `7f6b4dc2` · `marg_router.py` `318086e3` · `signatures.json` `b2dcb211` · `amir_day.py` `00c443cb` · `export_watch.py` `f6845ec5` · `stock_desk.html` `485720fd` · `stock_amir.html` `14024b8d` · `pad_receipt.py` `f06daf16`.

---

## §2 — THE FOUR RULES OF 17-SEP, CARRIED FORWARD UNCHANGED

1. **F-509 — the board is the lock.** Claim your session number in `board/_claude_status` as your first act, reading the key immediately before writing it.
2. **F-510 — a clock time is read, never estimated.**
3. **F-511 — no git command in `device_bash` against a connected folder.** Read `.git/logs/HEAD` and the refs, or clone in the cloud workspace.
4. **F-512 — a kit folder that could have been published is frozen.** A change is a new kit number.

**And F-523:** a file committed to the PC is read back by md5 on the PC before it is used.

---

## §3 — NEW AT v190: A REPORT IS A SURFACE (F-535, F-536, and the rule they bought)

Three beliefs in this estate turned out to have been taken from a surface and never checked against a store. They were not three mistakes. They were one mistake in three coats.

- **F-535.** S236 recorded *"truncation is gone"* on 09-Sep. It was true of the **printed bill** and false of the **export we import**. The paper that said so told its successor to re-measure; nobody did, for nine sessions. Measured now, across April–September: **sale export 20 characters · purchase export 27 · Marg's own item master 29.**
- **F-536, the owner's catch.** The salt importer identified a salt heading *by exclusion*, so it read `SANJEEVNI MEDICOS` — **Marg's page-break header, printed every 64 rows** — as a salt. 19 of 373 items wrong. Worse: **one of the pairs waiting on the owner's step-2 answer was a pair our own reader had invented.**
- **The third** was the assistant's own counter-vocabulary figures, taken from a default in the code rather than the stored `setting`.

**The rule, now standing in the Fault Register:**

> **A report is a surface. Before any figure from it enters canon, the reader that produced it must be able to fail — and must have been made to fail on purpose at least once.**

In practice this means a reader classifies every row **positively** — advert, continued, page-number, shop-name, title, column-header, stray, item, heading, anomaly, in that order — never by exclusion, and it carries **an independent witness**. Marg gives one free: **every item row is numbered, and the numbering restarts at 1 under every group heading.** A reader that asserts the serial cannot silently mis-file a heading, because the very next item row disagrees with it.

`margparse.py` is that reader. It is at **`D:\Downloads\ClaudeCowork\03_WORKING_PAPERS\S268\reader\margparse.py`**, it is **not installed anywhere**, and `READ_ME.txt` beside it says so. Installing it is part of §1's work, not a prerequisite to it.

---

## §4 — WHAT "LIVE" MEANS (unchanged from v188 §4, carried through v189)

A kit is live when **the box** says so. A close that writes *published, not installed* must name the evidence, and the cheapest evidence is free: an installer run a second time answers **ALREADY INSTALLED (every live md5 == its to-pin)**. When in doubt, ask the kit.

---

## §5 — THE SWITCHES

```
bash /root/finance/sanjeevni_switch.sh status
```

VPS `/root/finance/_off/ALL_OFF` (spine, attribution, export watch, salts refresh) · VPS `/root/marg_ingest/OFF` (collector, shadow) · manojz `D:\Downloads\margsync\_off\ALL_OFF.txt` · medical PC `D:\SendToClinic\_off\ALL_OFF.txt`, which does **not** stop capture, by design: Marg reuses one file name for every export.

---

*HANDOFF RUNBOOK v190 · written at the S268 close · supersedes v189 (the parent's) in full.*
