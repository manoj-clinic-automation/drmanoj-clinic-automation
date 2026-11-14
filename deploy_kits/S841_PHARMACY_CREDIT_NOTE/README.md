# S841_PHARMACY_CREDIT_NOTE — a credit note scanned on the pharmacy lane comes in as a credit note (F-1419, F-1422)

**Board:** `_numbers` v1526 → v1527 (kit S841). Built in the Scan App chat, session 466, 14-Nov-2026. This project's files only.

**The fault (F-1419).** The pharmacy reader (`claude_reader.read_pharmacy`) had no credit-note kind, so a dealer's credit note
scanned straight on the pharmacy lane landed as kind `Pharmacy` — and every Sanjeevni reader of the scan app selects
`kind='Pharmacy'` (`scan_register.py`: `WHERE kind='Pharmacy' AND status='captured'`), so it could be paired with a Marg bill as if
it were one. **F-1422** (found while reading): the bill's edit page kept only a list of lane kinds; `Pharmacy credit note` was not in
it, so an edit dropped the kind to the form's choice (Consumable / Pharmacy).

**What changes**
- `claude_reader.py` e2338b8b → 5b27b226: the S841 block re-binds `PHARMACY_PROMPT` and the long-bill fallback
  (`_S783_PROMPT_BEFORE`) with S835's kind list and a pharmacy-worded rule (a "Credit Invoice / Cash-Credit / Credit Sale" is a
  BILL). `clean()` (S835) already keeps `credit_note` and `against_no`. `PROMPT` (the desk's reader) is unchanged.
- `asset_register.py` 63eba920 → b668771c: (1)(2) the edit page and its Save keep `Pharmacy credit note`; (3) the S841 block —
  after the pharmacy reading, before the row is filled, a credit note is marked kind `Pharmacy credit note`, doc_kind
  `credit_note` (the kind the sorting desk gives, A-D52); healed after every POST, every reading and at start (a paper with
  doc_kind `credit_note` back on the pharmacy lane as `Pharmacy`; or one that came in on the lane and stayed, whose reading says
  credit note, incl. a clinic credit note a person moved onto the lane); a person's answer stands (the desk saving it as a bill; a
  person's re-lane off and back AFTER this kit marked it — the way back from a wrong recognition, as S754's); the papers page's
  history rule never moves a pharmacy credit note. Audited `kind` (who: `server (S841 …)`). Cold review: SAFE TO INSTALL; its five
  points (a person-moved credit note, the way back, the bare "CN" in the prompt, E1's proof, the installer's log check) fixed.
- No staff screen changes. It opens on the sorting desk with S835's credit note box (the owner; Shavez once `desk.cn` is on).

**Proof:** walk on the REAL app (every part mounted, made-up rows, the reader's answer made up in the process) **20/0**; the
control on the live files **11 of 11 red** (the 9 that must stay green stayed green); rehearsal on a made-up root **7/7** (dry,
install, again, a moved FROM refused, the lock, red health → restored byte-identically, a moved read-only file refused).

**Install** (his publish, then one line on the server):

    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S841_PHARMACY_CREDIT_NOTE/install_s841.sh

**The way back:** settings `read.pharmacy_cn` = `off` (no paper is marked; the reading still says so) — or the installer's
printed `\cp …bak_S841_…` lines and `systemctl restart assetapp`. Papers already marked keep their kind.
