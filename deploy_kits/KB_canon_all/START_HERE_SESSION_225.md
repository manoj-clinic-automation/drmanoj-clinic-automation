# START HERE — SESSION 225

*Generated at the S224 close, 04-Sep-2026. Supersedes `START_HERE_SESSION_224`.*

---

## §0 · THE STANDING OWNER RULINGS — read first, every session

1. **Publishing is HIS double-click.** Name one file, full path. Never drive the desktop for it.
2. **FULL PATHS ALWAYS — including URLs**, each in its own copy block. Never a bare `/finance/...`.
3. **ONE line per command.** Multi-line pastes have twice been cut in transit. Use `\cp`.
4. **Token-lean working — never at the cost of verification.**
5. **Plain language. One step at a time. Full-file replacements. ALL-CAPS = urgent.**
6. **Mask patient numbers (last 4) and never print secrets or tokens.**
7. **Nothing live is rebuilt without his OK; the manual path stays as fallback.**
8. **Sub-agents read screens** — screenshots never enter the main conversation.
9. **Do not hand him diagnostics, investigations or A/B tests.** Do the background work; ask for the
   one action nobody else can do — a GUI step, a credential, a decision — in one line.
10. **When a screen is wrong, read the screen's own code FIRST.** The server is the last suspect.
11. **Do not put technical or architectural choices to him.** *"for your technical questions,
    seriously, I don't grasp these and cannot answer them the way you expect."* Make the call, state
    it in one line, proceed. He rules on what he can SEE: a screen, a wording, a workflow, a priority.
12. **He wants to be part of the PWA build** — the product and the flow, never the implementation.
13. **Keep chat SHORT.** *"less for me to read, its your turf."* Long write-ups go in project docs.
14. **English to him, always.** Hindi is staff-side only.
15. **Supplier-wise is FINAL for month-end; Marg's purchase returns are normal** (D368). A return is
    labelled and counted, never asked about, never blocks a month. *"Avoid such confusing lines."*
16. **Staff pages may be all-English** (D369). *"This much English should be OK."* The Vaapsi desk
    stays Hindi as it is.
17. ***"And such lines also"*** — no per-type counts, held/live tallies or export bookkeeping on a
    card he reads. Three plain lines, or nothing.

---

## PHASE 0 — CONNECTIONS, then verification, then work

**1 · CHECK THE CONNECTIONS AND PROMPT HIM BY NAME. Before anything else, every time.**

| needed | what breaks without it |
|---|---|
| **`D:\Downloads`** | no Marg archive, no `_config`, **no ClaudeCowork** — the KB extension |
| **`D:\dr-manoj-git`** | no repository, no kits, no publish |
| **`F:\ClinicBackup`** (1 TB SSD) | the close cannot mirror or take a cold kit |
| **a browser** | no live-page reads, no portal verification |

⚠ **`F:` may not mount in the device shell — that does NOT mean unreachable.** The file-transfer
tools read and write it. Try before declaring. ⚠ **The device bridge dropped mid-close at S224** and
stayed down for a stretch; if it drops, wait and retry — never work around it in the cloud on his files.

**2 ·** Open **`CANONICAL_MANIFEST.md`** (Tier 0 · the linchpin).

**3 · Verify every row by md5 — from INSIDE `KB_canon_all`:**

```
cd $HOME/mnt/dr-manoj-git/drmanoj-clinic-automation/deploy_kits/KB_canon_all && md5sum -c MD5SUMS_ALL.txt --quiet && echo ALL OK
```

A mismatching row halts work (D172/D188). *A row absent from one store is not a failed row — halt on
hash mismatch only.* **Verify a kit gate from INSIDE its folder.**

**4 · Read only Tier 0:** manifest · `START_HERE_PROMPT` (evergreen) · **`KB_Register_v5_72_S224`** ·
**`HANDOFF_RUNBOOK_2026-09-04_Session224close_v156`** · `OWNER_TODO_LIVE.md` · any open incident.

**5 ·** Open **`D:\Downloads\ClaudeCowork\00_INDEX.md`** and the latest brief —
**`D:\Downloads\ClaudeCowork\03_WORKING_PAPERS\S224\S224_BUILD_BRIEF.md`** — one document in place of
eleven papers.

**6 ·** Then confirm, and ask which backlog item to start.

---

## ⭐ FIRST ACTION AT S225 — before any build

**The pin-capture paste, owed since S223.** Four S223 files are still DECLARED-PENDING (`tile_grants.json`
was read back at S224 as v7 and is a pass), and five S221 8-char prefixes have been carried
through three closes (`push_snapshot.py` was promoted at S224 by a manojz hash). **They are not passes.** Ask for this ONE line on the VPS:

```
md5sum /root/finance/finance_clinic_day.py /root/finance/docterz_day.py /root/finance/docterz_ingest.py /root/finance/clinic_upi_check.py /root/finance/finance_ingest.py /root/finance/darpan_card.html /root/finance/stock_finding.html /root/finance/stock_drift.html /root/finance/cards_registry.json
```

Record every value in the Register's pin table as READ BACK, regenerate `live_pins`, and only then
build the bank-MPR line on the Day Revenue page (`S224_BANK_MPR_STATUS` §5 — two lines,
anchor-guarded, on `finance_clinic_day.py`).

**Then the drawer count** — `clinic_register.py` **`93a31e68234df066776b7b80ef65ffbd`**, 89/89 green,
committed to `S223_REGISTER_CARD`, still not published and not installed (the one line is in
`OWNER_TODO_LIVE` ⭐0 step 3).

**Then begin S225 ⭐1-1: the staff order page** — `S224_PURCHASE_ORDER_STAFF_FLOW_SPEC` §1, §2 and
§5: Item · Stock now · Order qty; rounded to 10 strips then multiples of 10; WhatsApp one-tap per
stockist; `tel:`; the A4 PDF. Read the spec's §8 for the order of the rest.

---

## THE BACKLOG POINTER

**`HANDOFF_RUNBOOK_2026-09-04_Session224close_v156.md` §2** — ⭐0 the pin paste, the drawer, the
finding page's buttons read back once · ⭐1 the staff purchase-order flow in its §8 order, then the
S223 dawn specifications · ⭐2 owed technical work (stock snapshot on capture · the tracker-side
parser · the F-235 wording VPS-side · the S182 tiles) · ⭐3 rulings owed, including
**`darpan_app.py`, awaiting his ruling since S210 and load-bearing**.

**Tonight, 05-Sep 22:30:** OUR first computed stock figure reaches the drift page — the first sale
export after the 03-09 baseline. If it does not, `PUSH_STOCK_NIGHTLY.bat`'s log names the step.

---

## NEXT FREE NUMBERS

**D371 · F-320 · Session 225.**

---

## THE FIVE STORES, AND THE ONE RULE

project knowledge = canon · GitHub = code + `deploy_kits/KB_canon_all/` (**no numbers, F-185**) ·
`D:\Downloads\ClaudeCowork\` = everything canon excludes · `F:\ClinicBackup\` = frozen mirrors
and cold kits, one folder per project · Google Drive = the only phone-readable route, still not set up.

**NO DOCUMENT MAY BE LIVE AND EDITABLE IN TWO STORES** (D202 · F-201). Dated frozen snapshots are
exempt. **No canonical document is a delta.** **The manifest WINS on what is current.**

---
*START_HERE_SESSION_225 · generated at the S224 close, 04-Sep-2026.*
