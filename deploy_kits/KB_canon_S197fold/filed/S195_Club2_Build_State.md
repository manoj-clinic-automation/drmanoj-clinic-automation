# S195 CLUB 2 — built unattended, ready to install

**Kit:** `deploy_kits/S195_CLUB2.tar.gz` (`fa691670a7d49db45be0ee01c963c3f4`)
Built 22-Aug-2026. **Not yet installed.**

| file | live now (gate) | this kit |
|---|---|---|
| `/root/finance/finance_app.py` | `3e2f707b83994b69019a99b8f9621c0c` | `af617bf043a2bdda562f88fc6893e906` |
| `/root/portal/portal.py` | `bd4ed0a3b89659676e7e193998eeb1a9` | `ff08980737c107c3babb78b0c5c169c2` |
| `/root/deploy/email_agent.py` | `2c191082c27cb9a4acc52bb0e068aa2b` | `e535c4f8116abd2fe60b7fda334f33ec` |

All three gates are checked **before anything is touched**. One red hash stops the whole
install with nothing changed — rehearsed against a fake estate, exit 1, all three reported.

```bash
R=$(find /root -maxdepth 4 -type d -name deploy_kits 2>/dev/null | head -1)
cd "$R/.." && git pull --ff-only && \
cd /root/finance && tar -xzf "$R/S195_CLUB2.tar.gz" --overwrite && \
bash S195_CLUB2/install_s195_club2.sh
```

---

## 2.1 · Darpan's accuracy on his portal tile

`api_my_day_summary` has returned an `accuracy` block since S195_SHARE; `portal.py` simply
did not render it. His Daily Sale tile now reads, beside *today: filed*:

- `✔ cash/UPI matched 26/26` when every day the bank could witness matched, or
- `⚠ 1 cash/UPI day to fix` when one did not.

It says **nothing** when the bank could witness no day at all — there is nothing to claim
then, and a reassuring line drawn from no evidence is worse than no line.

Verified by **executing the tile's own JavaScript** against six data shapes (all matched /
one differing / three differing / bank saw nothing / no `accuracy` key at all / API not ok),
not by reading it. The existing S187_P2a portal gate still passes **26/26**, four of those
checks new — including one that deliberately **fails against the baseline**, because an
assertion that also passes on the old file is not testing the change (F-106).

## 2.2 · The email agent's lost commands

**The first diagnosis was wrong, and the test caught it.** I assumed Gmail RFC2047-encoded
long subjects. It does not: a long *ASCII* subject is **folded**, so a space in the middle
of the command becomes `"\n "`, and the SQL reaching `dr_query` carried an embedded newline.

Separately and genuinely: **one** non-ASCII character — a rupee sign is enough — makes Gmail
encode that run in place, so the middle of the command arrives as `=?utf-8?q?=E2=82=B9=27?=`
and goes to the query as literal gibberish.

Fix: **unfold, then decode**, in that order (an encoded word can itself be split across a
fold). Measured against five subject shapes built and re-parsed through a real serialisation:

| subject | folded | encoded | old intact | new intact |
|---|---|---|---|---|
| short | no | no | yes | yes |
| long ASCII | **yes** | no | **no** | yes |
| very long | **yes** | no | **no** | yes |
| one non-ASCII char | **yes** | **yes** | **no** | yes |
| long + non-ASCII | **yes** | **yes** | **no** | yes |

All five now recover **byte-identically**. An undecodable header falls back to the literal;
an absent subject gives `""`.

Also: a trusted sender whose subject is not recognised is now **logged**. Silence is what let
this survive — nobody could see commands being ignored.

## 2.3 / 2.4 · The month, and the days that never arrived

A1 compares one day against its own Marg report and cannot, by construction, see a day that
never arrived at all.

- **`GET /finance/api/marg-month`** (`?m=YYYY-MM`) — books vs Marg for the month, totalled
  **only over days both sides have**, so the number means something. Days each side is
  missing are named separately: `days_no_marg` (filed, no export yet) and `days_not_filed`
  (Marg had bills, no day was filed, the export was skipped).
- The Marg side is rebuilt from `sale_item` rows on a `marg_export` batch with returns
  **signed back to negative** — `finance_ingest` stores a credit note as a magnitude plus a
  `_return` service because `sale_item` forbids negatives, and summing without that turns a
  refund into a sale.
- **The health page carries both.** That is the real fix for *"three `MARG_DAY_NOT_FILED`
  flags nobody has looked at"* — the flag was already well-worded and already self-clearing
  (it drops off the moment that day has a Marg batch), it was simply only ever shown on the
  workbench, not where he looks.

11 new selftests. One of them I wrote **wrong first** — `status_code == 999` is never true,
so it passed unconditionally and proved nothing. Replaced with a real invariant: the
not-filed set and the compared set must never intersect, which is exactly what the
self-clearing SQL claims.

## 2.5 · The pre-flight sweep, extended

`py_compile`, `pyflakes` and `check_late_locals` now run over `portal.py` and
`email_agent.py` as well as `finance_app.py`. All clean. (`check_row_keys` is specific to the
correction-row contract and does not apply to the other two.)

## What the rehearsal caught

Running the installer against a fake estate found a hazard worth recording: the portal gate
imports `clinic_users` / `clinic_sso` / `portal_config` from the **live** portal directory,
and offline development uses **stubs of exactly those names**. A stub shipped in the kit
folder would shadow the real module — the gate would pass while testing a fake.

The installer now **refuses to run** if any of those three files is present in the kit, as a
kit-integrity check before the currency gates. Proved by putting one there and watching it
stop.
