# HANDOFF RUNBOOK — v188 — written at the S266 post-close, 18-Sep-2026, 05:1x IST

*Supersedes v187 (the S266 close, 17-Sep). The Sanjeevni project; the parent's S267 was still open when this was written. v188 changes one thing of substance — §3, the health-probe rule that F-525 bought — and brings §0 up to the box as it now stands.*

---

## §0 — WHAT IS OWED, AND TO WHOM

**To the owner, one thing only: the eighteen answers on step 2, *Try to match*.**

```
https://followup.dr-manoj.in/finance/stock/page/hub?count=1
```

Nothing below step 2 moves until they are answered: Darpan's list cannot be cut (his own ruling — the list only after the swaps are settled), the loss totals cannot be computed, the claim queue has nothing to queue. Each *Yes* raises its two Marg corrections the same second.

**To the next session, nothing that this post-close has not already written.** The canon is current with the box. There is no publish outstanding: `cdb2a32` and `a8c6c8c` both landed and were verified. The only publish left is the one that carries *this* post-close's own files.

---

## §1 — THE BOX, AS IT STANDS

Live and pinned in Register **v5.107** (which is what `live_pins_S266postclose.txt` is generated from):

- **The stock check** — one page, all seven steps, behind the Stock Check tile: `stock_app.py` `a8f98cda` · `stock_hub.html` `936677b8` · `stock_desk.html` `485720fd` · `stock_amir.html` `14024b8d` · `pad_receipt.py` `f06daf16`. A confirmed swap raises STOCK ISSUE on the short item and STOCK RECEIVE on the extra at once; the vouchers freeze into rounds of at most six lines, one round one Marg voucher, recorded as entered with Marg's own number; step 7 proves the count from the two reference days.
- **The Marg lane** — `marg_ingest.py` `7f6b4dc2` · `marg_router.py` `318086e3` · `signatures.json` `b2dcb211` (the last two byte-identical on manojz). The daily *Bill wise sales statement* files itself; PHI is deleted at the door.
- **Amir's day** — `amir_day.py` `00c443cb`: the wrong-supplier warning (S285), plus twins and return wording (S311).
- **The watch** — `export_watch.py` `f6845ec5`: the missed-export alarm reads the door's own evidence, not the PC's word.

---

## §2 — THE FOUR RULES OF 17-SEP, CARRIED FORWARD

1. **F-509 — the board is the lock.** Claim your session number in `board/_claude_status` as your first act, and **read the key immediately before writing it**. Two sessions run at once, one per project.
2. **F-510 — a clock time is read, never estimated.** A date command, a commit stamp, a file mtime, a line a program printed.
3. **F-511 — no git command in `device_bash` against a connected folder.** Read `.git/logs/HEAD` and the refs, or clone in the cloud workspace.
4. **F-512 — a kit folder that could have been published is frozen.** A change is a new kit number. *(This post-close is the rule's cleanest case: S307 was published and broken, so the repair became S311 rather than an edit.)*

**And the rule F-523 added:** a file committed to the PC is **read back by md5 on the PC before it is used**.

---

## §3 — NEW AT v188: WHAT AN INSTALLER'S HEALTH GATE MAY TEST (F-525)

An installer's post-restart health check **either**:

- hits a route that is in `finance_app.py`'s `PUBLIC_PATHS` — today `/finance/healthz` and `/finance/purchase/api/healthz` — and **requires 200**; **or**
- hits a gated page and **accepts 200, 302 and 401 alike**, because 302 and 401 are the login gate answering correctly.

**A probe that cannot tell "the app is down" from "the app asked me to log in" is not a health check.** S307 made exactly that mistake and rolled back a correct patch; `S308_PURSUE_EVIDENCE` and `S311_SUPPLIER_CHECK_2B` show the right shape:

```
c1=$(curl -s -o /dev/null -m 8 -w '%{http_code}' http://127.0.0.1:8106/finance/healthz)
c2=$(curl -s -o /dev/null -m 8 -w '%{http_code}' http://127.0.0.1:8106/finance/amir/step/4)
echo "health : finance $c1 · Amir's day $c2 (302/401 = the login gate, expected)"
[ "$c1" = 200 ] || restore
case "$c2" in 200|302|401) : ;; *) restore ;; esac
```

**Corollary, from the same fault:** a line copied out of an older installer must be re-read for what it *does* there. S285 **printed** that code and tested nothing; the copy turned a harmless print into a trap.

---

## §4 — AND ONE ABOUT WHAT "LIVE" MEANS (from §2 of the Archive's post-close)

A kit is live when **the box** says so. A close that writes *published, not installed* must name the evidence, and the cheapest evidence is free: an installer run a second time answers **ALREADY INSTALLED (every live md5 == its to-pin)**, because every installer in this estate compares the live md5 against its to-pin before it does anything. When in doubt, ask the kit.

---

## §5 — THE SWITCHES

```
bash /root/finance/sanjeevni_switch.sh status
```

VPS `/root/finance/_off/ALL_OFF` (spine, attribution, export watch, salts refresh) · VPS `/root/marg_ingest/OFF` (collector, shadow) · manojz `D:\Downloads\margsync\_off\ALL_OFF.txt` · medical PC `D:\SendToClinic\_off\ALL_OFF.txt`, which does **not** stop capture, by design: Marg reuses one file name for every export.

---

*HANDOFF RUNBOOK v188 · written at the S266 post-close · supersedes v187 in full.*
