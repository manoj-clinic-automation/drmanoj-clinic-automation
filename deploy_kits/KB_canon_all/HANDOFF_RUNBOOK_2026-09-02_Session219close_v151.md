# HANDOFF RUNBOOK — v151 · Session 219 close · 02 September 2026 IST

**Tier 0.** §0 what happened · §1 mental models · §2 the live backlog · §3 install discipline ·
§4 the boundary. **§2 is the close-time snapshot; `OWNER_TODO_LIVE.md` is the always-current truth.**

---

## §0 — WHAT HAPPENED AT S219

**The Marg session. FIVE INSTALLS ON THE LIVE BOX, every one predicted offline and read back
identical.** It opened by paying the S217/218 close debt (Archive v1.64 · Register v5.66 · Fault
v2.48 · pins) and then ran the owner's Marg-first plan in his order.

| what | pin before → after |
|---|---|
| **M1 · Marg auto-apply** | `finance_app.py` `80c2323a…` → `b42b1f08…` |
| **M2 · router signatures** | `signatures.json` `6111889d…` → `99a7214c…` (8 → 11); `marg_router.py` **byte-identical** |
| **Scanner v2, seven surfaces** | `scanner_widget.js` `4fe8c89…` → `bd5f481d…` → v2.3 `4ae2d29a…` |
| **The pharmacy lane** | `asset_register.py` `0cd8fc3b…` → `e7a68a13…` → `958c7fb7…` |
| **M7 · the returns line** | four files → `200e4d1c…` · `f4161c7d…` · `a57980c2…` · `735c7958…` |

**M1 was half already built** (S194's auto-replay, F-155) — found by searching before building, the
third session running that this has paid. **M2 changed no code at all**: three report types were
data, and all 101 archived spreadsheets were re-routed offline before the file moved
(`_UNKNOWN` is now empty). **Scanner v2 had been staged unused since S207**; finalising it exposed
two defects five green gates had missed, one of which hid a sub-44px control on every production
screen. The owner supplied the verification this project cannot perform itself — a real A5 bill, on
his phone, snapping to its borders unaided.

### The measurement that reframed M7

He exported `SALE RETURN LIST 01-04-2026 → 02-09-2026`: **197 credit notes, ₹68,099, no gaps.**

- **0 of 197 lack a name.** The "unnamed returns" population five sessions of documents had been
  designing remedies for **does not exist** (F-279).
- **127 lack an ID** — ₹36,535, **53.6% of all return money.**
- **The break is dated.** No clinic ID was captured before July 2026 (0 of 43 in April, 0 of 36 in
  May; 31 of 39 in July). So 109 of the 127 are **a missing system, not a missing answer.**
- The real lapses are 18; 8 carry a mobile the system resolves unaided. **The human worklist is 10
  returns and 5 identity disputes** — one sitting.

### Two corrections owed, and one of them is still live

**F-276 — three-digit clinic IDs are REAL.** This session first called `104` and `523` "cut or
mistyped", inferred from 68 four-digit examples out of 70, master never opened. The owner: *"3 digit
clinic id exist, check patient master."* Docterz has *Chetna* for `104`. **The file that proved it
was built at S217/218 and had been sitting on his own disk the whole time.**

**F-277 — and it is worse than the fault this session set out to fix.** 5 of 43 August returns
(**12%**) carry an ID belonging to someone else. `finance_ingest.resolve_patient()` says so in its
own docstring — *"Clinic ID first, name only as a hint"* — and never compares the two. A stranger is
attached **silently**, and every audit afterwards judges her returns against his purchases with full
confidence. **STILL LIVE. The owner ruled it the first build of S220.**

---

## §1 — MENTAL MODELS EARNED HERE

1. **A claim about the SHAPE of data is checked against the master that defines it** — never against
   the frequency of its own examples. And **search this project's own prior work before asserting
   anything about a population**: the answer was already on his disk (F-276).
2. **Disagreement between two identifiers is a finding, not a tiebreak.** A verdict may be delivered
   only on an identity that has agreed with itself (F-277).
3. **In any value-to-appearance map, the default branch is the one to DESIGN.** A ladder whose final
   else is red will alarm on every future value (F-278).
4. **Count the population in the source of record before designing the remedy.** A wrong *name* for
   a problem outlives a wrong *number*, because nobody re-measures a word (F-279).
5. **Burying history is not deleting it.** D361 keeps every row, every verdict and every rupee — it
   stops the *work*, not the data, because that history is the only baseline a detector can be
   calibrated against.
6. **A green selftest proves the kit; run it ON THE BOX against the live sources and it proves the
   join.** M7's suite copies the live files, runs the kit's own patchers over them, and tests what
   comes out — 55/55, on the VPS, before anything was installed.
7. **Predict the pin offline, then read it from the box.** Five installs, ten predictions, ten
   matches. A prediction that is checked is worth more than a hash that is merely recorded.

---

## §2 — THE LIVE BACKLOG (close-time snapshot)

**⭐0 owner:** the publish · Darpan's sheet (`D:\Downloads\Darpan_Returns_Jaankari_Jul-Sep2026.html`,
10 names + 5 disputes) · the August staff close (Surendra ₹516.08 UNEXPLAINED first) · Pravesh's
₹569 · the bank trip (₹2,74,000+ unbanked, 34+ days) · rulings on the S214/S215/S216 candidate sets
and F-244 · the delete lists · token rotation · the first stock count push.

**⭐1 build, in the owner's order:**

1. **THE INGEST NAME-CHECK (F-277)** — *"the next session as the first thing, so as to polish out
   and complete the entire marg system."* Compare the bill's name against the master's at
   `resolve_patient`; a disagreement becomes **"identity disputed"** — amber, to Darpan — never a
   money verdict. Money-path change: needs his OK on the shape before it ships.
2. **The scanner A5 vertical resize** — his report: *"the a5 button doesn't do vertical resize."*
   Diagnosed: `fitAspect` covers the content box in BOTH directions, so a too-tall box keeps its
   height and widens instead.
3. Then: M3 finance-side purchase tables (**build yes, feed no** — August purchase is provisional)
   · M4 Phase B · M5 purchase orders/reorder · M6 alternative leg + task-health shouts · the F-269
   route patch · the fourth Marg layout (`SALE RETURN LIST`) taught to the router · Docterz feed
   Phase 1.

**🛑 STANDING HOLDS.** August purchase is provisional until he says otherwise (marker files in
`MargArchive\`). **NEFT portal WAITS.** The hub's SHAPE is not reopened without a ruling.

---

## §3 — INSTALL DISCIPLINE

Unchanged, plus three earned here:

- **Slice every OLD anchor verbatim from the live bytes** (A0). Anchors must be line-terminated: a
  substring anchor matched a drifted line with a trailing comment this session.
- **`\cp` and an unquoted wildcard.** A quoted multi-file `scp` list failed twice in one session.
- **`bind 'set enable-bracketed-paste off'`** — `[200~git: command not found` was the third distinct
  paste-failure mode this project has met.

---

## §4 — THE BOUNDARY

Nothing live is rebuilt without his OK. The publish is his double-click. F-277 is diagnosed,
measured and **deliberately not built** — it changes the money path, and that is his call to open.

---
*HANDOFF_RUNBOOK v151 · S219 close · 02-Sep-2026. Next free: D362 · F-280 · Session 220.*
