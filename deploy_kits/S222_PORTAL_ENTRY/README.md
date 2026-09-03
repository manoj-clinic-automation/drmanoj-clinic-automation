# S222_PORTAL_ENTRY — the flow starts where he starts

**Session 222 · 03-Sep-2026**

> *"This should be a part of the manage users, not a separate system. We open… I go to the
> portal. I click upon manage users. Then I see all the users. There, the option should be there,
> add new joiner, exit leaver. And from there, it should flow."*

## What was in the way, and why it is worth writing down

`/root/portal/portal.py` gates **every login in the clinic**, and the repository's copy of it is
stale — `d74aa3f9` against a live `16bfd590`. Editing a file that important from a stale copy is
precisely the mistake this session refused to make on `darpan_corrections.html` this morning, and
refusing was right: the Register's own pin table turned out to be wrong about that file.

So the live bytes were **reproduced before anything was touched**:

```
S204_VPS_LIVE/root__portal__portal.py            24ea2c0b…
  + S218_PORTAL_TILE/patch_portal_vaapsi_tile.py
  = 16bfd590e2e422bb81bb8b6ad6e84eae                        ← the pin the box printed
```

Byte-exact. That is the whole live file, offline, and the patch was written against it — so the
new pin is a prediction, not a hope.

**And it settles a question that was open this morning:** `portal.py` *is* reconstructible from
the repository. `darpan_app.py` still is not — three divergent copies, fourteen patchers, nothing
that reproduces `c98f0c24`. Two files, same shape of problem, and now they are known to be
different problems.

## What it adds

One card at the top of Manage Users, above *Add a login*:

```
Joining and leaving
A login is only one of six steps. The register walks the whole thing — roster row,
login, credentials, first sign-in, biometric and Emp Code, staff master — and refuses
a step taken out of order.

  ➕ Add a new joiner      🚪 Exit a leaver      📋 All staff records
```

Those links carry `?flow=join` and `?flow=exit`, and the staff page reads them — so the owner
**lands on the form**, not on a screen with a button that opens the form. One click from the tile
to the work.

That sentence in the card is doing real work too. *Add a login* has always looked like the whole
job of adding a person, and it never was — it is one of six, and the one that S221 proved can be
done while the other five quietly lag.

**Nothing is removed.** The user table, the add-a-login form, role, password, active and delete
are untouched.

## What it is proven by

- the patched `USERS_HTML` **re-rendered through Jinja** with a real user row: all three links
  present, *Add a login* and the table intact, three cards where there were two
- chromium on both entry URLs: `?flow=join` lands on the form with its eight authorities;
  `?flow=exit` lands on the picker with real people and **no text box**; no flag is still the
  ordinary home screen
- the full joiner-forms gate re-run on the same page — **30/30, unchanged**

## The restart

Step 4 restarts `clinic-portal`. Existing sessions survive it: the SSO token is signed rather
than held in memory, and the user store is a file read per request. The patcher writes a
byte-for-byte backup beside `portal.py` before touching it, and restores it itself if the result
will not compile.
