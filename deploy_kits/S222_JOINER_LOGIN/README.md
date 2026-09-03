# S222_JOINER_LOGIN — the login that was never created

**Session 222 · ⭐1-3 · F-295 · 03-Sep-2026**

## What the page was doing

For every new person, unconditionally:

```
login: amir · pehla password: amir1234 (pehli login par badalna hoga)
```

Both halves **invented in the browser** from the first name. `/api/message` composed the same
thing into a WhatsApp text, and its docstring called it a virtue:

> *"The password is DERIVED, not stored — nothing in this database holds it."*

That reads like good hygiene. What it actually meant is that **the account did not exist**.
Nothing in the joiner flow ever called the portal's user store. The register ticked
ACCOUNT_CREATED, the owner read the credentials out to a new man, and the portal refused him —
which is exactly what happened to Amir, in front of the owner, at S221.

`/api/reset_password` has the same shape: it records a `PASSWORD_RESET` event and returns a
password with the words *"Set the portal password to this, then read it out"* — an instruction
to a human, in the return value of a route that sounds like it did the work. **Left alone here
on purpose:** one live file, one behaviour, one walk. It is the obvious next step.

## The fix, in the order that matters

**First stop lying. Then offer to act.**

| route | who | what |
|---|---|---|
| `GET /finance/staff/api/portal_user` | any desk role | **read only** — does this login exist, is it active, what role, and what roles does the store even have |
| `POST /finance/staff/api/portal_user/create` | **checker only** | creates it — and proves it |

The page's login line now says one of four true things instead of one false one:

```
✅ login amir ban chuka hai (manager) · pehla password amir1234 — pehli login par badalna hoga
⚠️ login amir hai lekin BAND hai — portal se chaalu kijiye
⚠️ Yeh login abhi bana NAHIN hai. amir se koi login nahin kar sakta.   [🔑 login banao]
   login: amir · portal ka user store padha nahin ja saka
```

## The seven guards on the write

The owner ruled at S222 that the finance service may write the portal's login store. That store
is the one file gating **every** login in the clinic, which is why the route does all of this:

1. refuses unless the store is readable and lists roles
2. refuses a role that is not in **that store's own list** — the list is read, never guessed
3. refuses if the user already exists
4. **copies the store beside itself** before touching it
5. calls the portal's **own** `clinic_users.add_user` — the same call `/portal/users/add` makes;
   the write is atomic (`tmp` + `os.replace`) inside that module
6. **then signs in as him** — `verify_password()` against the printed password. *A login is not
   created until it has been used once.*
7. if that sign-in fails, the backup is restored and the route reports failure

## And the message finally has somewhere to go

The WhatsApp text was composed and displayed with **no send button**. It now has one:
`https://wa.me/?text=…` — **no number in it**. WhatsApp opens with the message already typed and
the owner picks the person from his own contacts. The owner's ruling, and the F-185-safe shape:
no number is written into this page, this database, this repository, or the box.

## What it is proven by

`RENDER GREEN 22/22` — headless chromium, on the exact live bytes:

1. a joiner with no login — the page **warns** instead of printing credentials, and the old
   *"pehla password"* claim is gone from the screen entirely
2. tap **login banao** — the choices offered are the store's real roles (`doctor / manager /
   staff`), read from the store, not written into this page
3. choose one — the line flips to *ban chuka hai (manager)*
4. **the proof F-295 never had**: `clinic_users.verify_password(store, "zahir", "zahir1234")`
   returns `manager`. The login the page just printed **actually signs in**. A backup of the
   store sits beside it
5. the WhatsApp button renders a `wa.me` link carrying the message and **no digits before
   `?text=`**
6. a *disabled* login reads as **BAND**, not as a green tick

## One thing the gate caught, and it is worth keeping

The first version of the render test mounted `joiner_app` **without** `staff_pages.joiner_require`
— the adapter that converts finance_app's user dict into the plain name the register binds
straight into SQL. The create route crashed with `type 'dict' is not supported`… which is the
**same crash, in the same file, for the same reason** that S208's own selftest caught when this
register was first wired up. The code was right; the test was not wired the way the box is.

That is the second time in one session that a check which could not be run offline was the one
that lied. The rule stands: **a test that does not wire the app the way the box wires it is not a
test of the box.**
