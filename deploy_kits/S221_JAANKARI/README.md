# S221_JAANKARI — Darpan's Hindi list (⭐1-1)

**Two live files move:** `/root/finance/returns_desk.py` (`afc8b0d0` → **`1dc1fd62`**) and
`/root/finance/returns_desk.html` (`32c4b8cc` → **`6d98e1b0`**). Both predicted offline before
install. No other file moves.

## The ruling this is built to, and what it changed

> *"send identity questions, go soft on answers from him … first get him to do sales return,
> stock check, drawer management for some time, and reassess … right now only internal match is
> sufficient"* — the owner, 03-Sep-2026

So the questions **do** reach him, and **nothing he answers is allowed to act.**

`S220_RETURNS_INTENT_DESIGN` Layer C said *a row unanswered for two days escalates by itself*, and
G6 set him a two-working-day clearance target. **Both are superseded by that ruling: silence costs
him nothing.** There is no timer anywhere in this kit. Recorded here rather than quietly dropped.

## "Soft", as a property of the database rather than a choice of words

This whole feature is **read-only except for one INSERT into one new table**, `jaankari_answer`.
It does not move money. It does not re-attach a patient. It does not close an `identity_dispute`.
It does not mark a `stock_spot_check` done — the owner still taps *counted* on his own card.

The walk measures exactly that: every table in the database is fingerprinted before and after he
answers, and **exactly one is allowed to differ.**

An answered row leaves **his** list, so the list can shrink, and stays **open** for the owner,
now carrying what he said. If he changes his mind, both answers are kept — the table is
append-only, and that is what evidence means.

## What he sees

One card on the desk he already uses, under the day's slips. **It hides itself completely when
there is nothing to ask** — an empty list must never look like a task. Under the heading, in his
own language: *answering changes no money; it only tells the doctor; if you don't know, leave it.*

| list | the question | the answer |
|---|---|---|
| नाम मेल नहीं खा रहा | the bill says one name, the ID says another — which is right? | यह सही है · बिल ढूँढ़ो · पता नहीं |
| किसकी वापसी थी | a return with no name or ID attached | the same three |
| गिनती करनी है | count this medicine on the shelf | **a number** — a count is a number |

The **full mobile** shows beside the name (D363 — a counter screen). No number is written into any
file here; it is read from the master at request time and falls back to the last four.

He never sees a score, a verdict, a ratio or a flag. The walk and the render test both assert it.

## Two defects a real browser caught that no server check could

The standing rule for this page since S214 v6 — *headless chromium opens it and clicks the flow, or
it does not ship* — earned its keep twice in one build:

1. **The heading rendered as the Hindi letter "ग".** I had written the wrong code point where an
   icon belonged. Invisible to every server assertion; obvious the moment a screen existed.
2. **The list opened with twenty-two rows stacked down a phone.** `returns.act_from` **does not
   exist as a setting**, so my default reached back to 18-June and put the entire backlog in front
   of him — against D361 and against the whole point of the ruling. **The default is now
   `2026-09-02`, the day the identity machinery went live**, and each group is capped at six with
   a *और दिखाएँ* button, so the page can never become a wall again.

*(Seen, not guessed. Both are in `EVIDENCE_render_s221.txt`'s lineage.)*

## Proofs

| | |
|---|---|
| **live-shape walk** | **31/31** — the REAL blueprint mounted on a COPY of the live db, driven through the real routes; the "exactly one table changed" measurement; a refused bad answer writes nothing; a re-answer keeps both rows; the untouched endpoints still answer; an empty list hides the card |
| **render test** | **26/26** — headless chromium at 390 px, **all three groups on screen and all three kinds of button actually tapped**, no JS error, every request 2xx, and the database checked afterwards: the dispute still open, the spot check still due |

The render test does **not** run on the box (the VPS has no browser). It ran offline against these
exact bytes; `EVIDENCE_render_s221.txt` is its output.

**Its screenshot is deliberately NOT in this kit.** It photographed real patient names out of the
database copy, and patient data does not enter the repository — the S207 lesson, applied before
anyone had to catch it.

## Files

| file | what |
|---|---|
| `patch_desk_jaankari_s221.py` | returns_desk.py — the table, the two routes (2 anchors) |
| `patch_deskpage_jaankari_s221.py` | returns_desk.html — the Hindi card (2 anchors, plus a script-tag balance check) |
| `walk_jaankari_s221.py` | the live-shape walk — 31 checks, runs on the box |
| `RENDER_TEST_jaankari_s221.py` | the browser gate — 26 checks, runs offline |
| `EVIDENCE_walk_s221.txt` · `EVIDENCE_render_s221.txt` | what those two printed against these bytes |

## The one setting, if the backlog should ever be worked

```
returns.act_from = 2026-06-18
```

That opens roughly twenty-two historical WALK-IN returns onto his list. **It is deliberately not
the default.** D361 says the past is accepted and raises no work.
