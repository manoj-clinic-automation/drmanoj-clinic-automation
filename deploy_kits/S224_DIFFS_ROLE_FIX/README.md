# S224_DIFFS_ROLE_FIX — the diffs page draws only the buttons your login may use

**Owner's words (04-Sep-2026):** *"diffs page cause button fix to make it proper."* Found by the S224 all-staff
sweep (`S224_STOCK_ANCHOR_FIX` §6 item 2): `stock_diffs.html` showed the eight cause buttons to every login, while
`/api/diff/<id>/cause` is checker-only, so Darpan, Amir and the desk girls tapped a cause and got "not_permitted".
A control that refuses is a trap (S222 ruling). The finding page already did it right (`F.you.may_decide`).

## What changes

| file | live pin | after | what |
|---|---|---|---|
| `/root/finance/stock_app.py` | 4e929d0b | a61af74a | `/api/open` gains `you` {user, may_cause, may_answer}, `reasons`, and per line `answer` + `cause_label` (ADDITIVE — every S213 field stays). `_has_role()` looks in `roles` and `role`; `_may_decide()` uses it. A comment on `page_diffs`. |
| `/root/finance/stock_diffs.html` | 3f6a87b2 | fb372655 | replaced whole. Checker: cause buttons + note (as S213) and the staff's reason as text. Maker: the S221 staff-reason buttons → `/api/diff/<id>/answer`, the cause as text. Viewer: text only — zero buttons, zero inputs. English throughout (the owner's ruling today). |

**No server gate moved.** `/cause`, `/decision`, `/rate` still `_require("checker")`; `/answer` still checker/maker/viewer;
the page is the courtesy, the server is the rule. The RENDER test asks the server directly to prove it.

**The second defect this closes.** `_may_decide` read `u["role"]` — the broker's clinic-wide role (`doctor` for the
owner) — and never `u["roles"]`, where `finance_app.require` puts the unit roles. So `/api/finding` told the live owner
`may_decide=false` and the finding page would offer him the staff's reason buttons, not write off / recover / no loss.
`stock_finding.html` has never been read back live (pin row BLIND). One line, same file, same defect class.

## Provenance (F-299)
`stock_app.py` is the S213 base 83b0a1b0 walked through the four S221 patchers — ed2f76ef → c627e440 → 74825031 →
**4e929d0b** (== the S223-close live pin) — and then `patch_diffs_role_s224.py`. `selftest_diffs_role_s224.py` reproduces
that byte-for-byte and proves the patcher refuses any other base.

## Proof, offline
* `EVIDENCE_render_s224.txt` — **RENDER GREEN 55/55**: jsdom runs the page's own JS as manoj / darpan / amir / alisha with
  the LIVE login shape (role=doctor|staff, roles=[…]) over a temp finance.db with three differences; counts buttons and
  inputs per role, taps a cause as the owner and a reason as Darpan, reads both back from the rows and from the other
  logins' screens; asserts the server's 403s unchanged and no 10-digit run anywhere.
* `EVIDENCE_selftest_s224.txt` — **11/11**: provenance, idempotency, refusal on a wrong base, gates unchanged.
* `EVIDENCE_walks_rerun_s224.txt` — the standing walks on the NEW file: S213 27/27 · S221 prices 63/63 ·
  purchase_due 75/75 · amir_access 29/29 · finding 51/52 (the one failure is pre-existing, identical on the unpatched
  live bytes; that walk predates TWO_PRICES which fills the cost column it expects empty).

## Install
`INSTALL.txt` — one line, guards both pins, dated backups, `\cp`, compile, restart, is-active, md5, self-rollback.
Then the LIVE-SHAPE walk that no offline test replaces: open the page as yourself, as Darpan, as Amir.
