# S222_JOINER_FORMS — the form, and the picker

**Session 222 · 03-Sep-2026**

> *"Clicking on new joiner and exit buttons opens a small prompt. It is not contextual. The new
> joiner should open a form where we do the entries contextually as it is a rare occurrence and
> not a day to day procedure… the exit lever should open the page where we can select from the
> staff and then proceed."*

## It was not a complaint about the UI

`/api/open` has **always** accepted the employment type, the list of authorities and a chosen
username. They are in its signature, they are in its validation, and `AUTHORITIES` is a
documented eight-item list of what a person may be given — stock count, expiry check, purchase
orders, purchase entry, returns, salt fixes, reception, and their own attendance.

A `prompt()` can only ask one thing at a time. So the page asked for a name and a job, and sent
nothing else.

**Every join since S208 was filed as `FULLTIME` with no authorities at all.** Employment drives
salary — Amir is biweekly — and the authority list is the nearest thing this system has to *"what
is this person allowed to do"*. The register was built to capture both at `DECIDED`. The screen in
front of it dropped them, silently, for fourteen sessions.

The owner saw a clumsy dialog. Underneath it was a contract the page had never honoured.

## The two shapes are opposite, and that is the point

**Joining is rare and consequential**, so it gets a form: name, job, employment, the portal login
(derived from the first name as you type, editable), what he may do, and who is opening it. One
screen, filled once.

The employment options and the authority list are **read from the register** — `/api/authorities`
— never written into the page. A page that invents an authority gets it silently dropped by
`/api/open`'s own filter; a page that reads the list cannot. *(The same rule the role picker
already follows, for the same reason.)*

**Leaving is the opposite: there is nothing to type**, because the person already exists. The
exit button opens a list of real people — every portal login, plus everyone the register knows —
and you tap one. Anyone with an exit already open shows as *in progress* and cannot be started a
second time.

That is not convenience. **Free-typing a leaver's name is the straightest road to one person
becoming two records**, in attendance and in salary, which is the exact failure this register was
built to prevent. The page was asking the owner to do by hand the thing the register exists to
stop.

## What the browser proved

`RENDER GREEN 30/30`, and two of those checks matter more than the rest:

- the form was filled with **BIWEEKLY** and three authorities ticked, and then **the database was
  read back**: `employment=BIWEEKLY`, `authorities=purchase_order,self,stock_count`. The values
  the prompts had always lost now land.
- the exit screen offered five real people and **has no text box on it at all** — asserted, not
  assumed. One exit was started, and the second attempt was gone.

Plus: no dialog is raised anywhere in either flow, and no JavaScript error at any point.

## One bug this gate caught, and it is worth naming

The first build put the person's name straight into an `onclick=""` attribute via
`JSON.stringify`. Its double quotes closed the attribute, and every *start exit* button died with
*"Unexpected end of input"* — silently, because a broken attribute renders as an ordinary button
that does nothing. **A person's name is content, and content does not belong in an attribute that
is also code.** Names now travel in `data-person` and the handler is attached after render.

Three times in one session a check that could not run offline was the one that lied, and this is
the fourth thing a real browser found that no amount of reading would have. The page tests earn
their keep.

## Still a prompt, on purpose

The Emp Code at the biometric step, the one-line detail on dues and items at an exit, and the
reason on a password reset. Each is a **single value asked at the moment it is needed** — which is
the one thing a prompt is actually good for.
