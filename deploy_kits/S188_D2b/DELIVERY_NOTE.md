# S188_D2b — F-129: a checker's look must not arm the maker's badge

**Session 188 · 18 Aug 2026 · built on the bytes D2a installed an hour earlier, rehearsed offline.**

## The finding

D2a recorded the mirror reveal against the **day**, whoever opened it. So this sequence misfired:

1. Darpan files a day.
2. **You** open it to look — the badge arms.
3. Darpan corrects a figure.
4. He is stamped **"changed after the check"** — for a check he was never shown.

The flag would still have been *literally* true: the figures did move after the day was
cross-checked. It would simply have been **about the wrong person**. A badge that the checker can
trigger by looking is not the badge described in the contract, and it would have quietly
undermined the one thing D2 exists to protect — the independence of his declaration.

> **F-129 — a marker that records "this was shown" must record WHO it was shown to, or it will
> speak about somebody else.**

This is a near relative of **F-118** ("a record asserting something about another component is a
claim, not a fact"): the reveal row asserted something about the maker's sequence that it had not
actually observed.

## The fix

The reveal is armed **only when the caller is acting as a maker** — `maker` in their roles and
`checker` not. The endpoint now also reports which kind of look just happened:

```
armed_by_this_look : true | false
looking_as_maker   : true | false
```

and the page renders a row when it is false:

> **You are looking as the doctor** — this is not Darpan's check; nothing has been armed, and he
> will not be badged for anything he changes next.  ✓ read-only

**One assumption, stated so it is a claim and not a secret:** a caller holding *both* roles is
treated as the checker and does not arm the badge. On medical no such person exists — the checker
is the doctor alone (S179). If that ever changes, the comment in `api_day_mirror` names the line
to revisit.

The flag's own wording now names whose sequence it describes, rather than leaving it to be
inferred.

## Proven, with the real roles

```
doctor's look   -> looking_as_maker=False  armed_by_this_look=False
Darpan corrects -> EDITED_AFTER_REVEAL flags = 0     (before F-129 this was 1)
Darpan's look   -> looking_as_maker=True   armed_by_this_look=True
Darpan corrects -> EDITED_AFTER_REVEAL flags = 1, reveal attributed to 'darpan'
```

The mechanism still fires exactly when it should. It simply no longer fires for the wrong reason.

## Evidence

**Smoke:** 451/453 → **462/464**. **+11 checks, zero new failures** (the same two seeded-data
artefacts). The eleven are the F-129 sequence asserted end to end, including the negative case —
*the maker is NOT stamped for a check he was never shown* — which is the finding itself, in one
assertion. Live projection: **464/464**.

The three role-refusal tests run as `smoke_no_seat`, with no checker rights riding along (F-106).

**F-87 differential — `F87_DIFFERENTIAL.txt`, verdict CLEAN:** 28/28 ids, 6/6 API paths, 8/8
selectors, 15/15 field classes, 11/11 payload keys, 54/54 markup ids. **Nothing was removed at
all** — this kit only adds.

**Installer:** the D2a installer, which was rehearsed green and red on a throwaway box, with four
hashes and the wording changed. `bash -n` clean. Currency gate demands
`finance_app.py 5a7fea4f…` and `finance_entry.html a114ebc4…` — the bytes D2a installed.

## Install

```
bash /root/deploy/vps_deploy.sh S188_D2b
```

Then pin from the box (D321(d)):

- `finance_app.py` → `3a7086f851720dd161bc43c3c1fd45dd`
- `finance_ui/finance_entry.html` → `2c23b461bdae5a4ed6a4c4ed4708b4f9`

**After this lands you can open any day — draft or not — without arming anything.**

## Still owed to the record

**F-127** (the ungated unit position), **F-128** (the seeded checker row that made eight
role-refusal assertions pass by accident), **F-129** (this), and the two live pins from each kit.
I am writing those into the Register and Fault Register next.
