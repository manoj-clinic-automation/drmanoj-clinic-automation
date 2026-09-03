# S222_STAFF_ENGLISH — the staff console in English

**Session 222 · 03-Sep-2026**

> *"remove words jodna, vidaai, with proper english ones"* — then, plainer:
> *"make it all englsh flow"*

## The line this draws, and it is not new

**D366 already says it:** the owner's consoles are English; staff-facing pages stay Hindi.
`/finance/staff` is **his** page — checker-only, the desk where he adds and removes people. It
had simply never been translated when that ruling landed.

So the split this kit makes is exact:

| what | language | why |
|---|---|---|
| the console at `/finance/staff` | **English** | he reads it |
| the WhatsApp message a new joiner receives | **Hindi**, untouched | *the joiner* reads it |

That second row is the one worth being careful about. It is composed by the server
(`joiner_app.api_message`) and this kit does not go near it. Translating it would have been the
easy mistake — one file, all Hindi gone, and a new counter man handed his login in a language he
does not read.

## Why a whole-file swap

Forty-seven strings change. An anchor patcher with forty-seven anchors is forty-seven ways to
refuse on a live file, for no benefit — and the repository holds the **exact bytes** that are
live, so there is nothing to reconstruct. The installer instead:

1. refuses unless the English file beside it hashes to what this kit shipped
2. refuses unless the live page is the `S222_JOINER_ALLRECS` result
3. copies the live page aside
4. writes, re-hashes, and **restores the backup** if the result is not byte-exact

**Words only.** No id, class, route, function, or line of logic moves — the English file was
produced by replacing whole quoted strings in the live file and nothing else.

## What it is proven by

`RENDER GREEN 23/23` — headless chromium re-running every flow on the English page: the pending
list, **All records** finding a completed record, opening it, the tested password line in all
three of its states, the missing-login warning, the role picker, and the search. Plus two checks
that only make sense for this kit:

- **no romanised Hindi is left** anywhere in the file — checked against a word list, not by eye
- the page **declares `lang="en"`**

A translation is the kind of change that looks obviously safe and quietly breaks a selector, a
handler name, or a status string another screen matches on. So it was walked, not eyeballed.
