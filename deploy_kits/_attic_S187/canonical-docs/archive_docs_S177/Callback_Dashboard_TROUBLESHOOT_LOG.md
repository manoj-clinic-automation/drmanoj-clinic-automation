# Clinic Callback Tracker — Troubleshoot Log (running incident record)
**Companion to:** `Callback_Dashboard_KB_v1.md` (how it works) and `Callback_Dashboard_TROUBLESHOOTER_v1.md` (decision tree).
**Purpose of THIS file:** a dated diary of real problems hit on the dashboard, what the symptom looked like, what the actual cause was, and exactly what fixed it. Read newest-first. When a new problem is solved, add an entry at the top.

---

## INCIDENT #1 — Empty dropdowns, KPI tiles fine  ·  RESOLVED 29 Jun 2026 (Session 16)

### Symptom (what was seen)
- Top KPI tiles (Awaiting Callback, Incoming Missed, Total Calls, WhatsApp) all showed correct numbers.
- BUT every expandable section below — **NEEDS A CALLBACK NOW, RESOLVED CALLBACKS, TODAY'S FOLLOW-UP CALLS** — rendered **empty**, even though the tile above said "8".
- No error visible on the page itself. Nothing looked broken at a glance.

### False trails (what did NOT work — do not repeat these)
- ❌ Rolling the deployment back to earlier versions — no effect.
- ❌ Replacing the page with a fresh dark-theme HTML — no effect.
- ❌ Chasing the `rebuildCallFeed` trigger (it had last run 28 Jun 21:23) — **irrelevant.** That trigger only writes the Call_Feed tab; the live dashboard fetches the API directly and never reads Call_Feed. (See KB §2, the two-data-path rule.)

### How it was actually diagnosed (the path that worked)
1. **`probeApi`** (Run menu) → returned **5 live records**, token length 32, fields mapped → proved the **API + token are healthy**. So data coming IN is fine.
2. **Read-only server probe** (`probeDashboardData_`, called via a plain-named wrapper `RUN_DASH_PROBE`) → returned `pending:7 resolved:3 recentWA:12`, full patient detail. → proved the **server is computing and returning correct data**. So data going OUT of the server is fine.
3. Therefore the fault is **after** the server — in the browser render. Opened **F12 → Console → Ctrl+Shift+R**. The console showed the exact crash:
   `Uncaught … 'Error in protected function: i is not defined', ReferenceError: i is not defined, at <anonymous>:248:50, at Array.map`

### Root cause (the one line)
In `Dashboard.html`, the **pending-callbacks renderer** opened its map callback **without the `i` parameter**:
```
box.innerHTML = p.map(function(e){      // ← BROKEN: no i
   ...
   var inId = 'in_' + esc(String(e.number)) + '_' + i;   // ← but i is used here
```
The `i` was undefined → `ReferenceError` thrown **inside** `Array.map` → JavaScript aborted the **entire** render run. Tiles survived only because they are drawn earlier, before the crash point. Every section after it stayed blank.
Sibling renderers were already correct (`function(e,i)` for resolved, `function(m,i)` for WhatsApp), which is why ONLY the pending list's bug took everything down with it.

### The fix
One character. Add the missing parameter:
```
box.innerHTML = p.map(function(e,i){    // ← FIXED
```

### Why the fix "didn't work" at first (the second, separate problem)
After pasting + saving the fix, the live page **still threw the identical error at the identical line 248:50.** That was a **deployment** problem, not a code problem:
- Editing `Dashboard.html` in the editor does **NOT** change what the `/exec` URL serves.
- The web app keeps serving the **published version** until you explicitly publish a new one.
- **Resolution:** Deploy → Manage deployments → ✏️ Edit → Version dropdown → **"New version"** → Deploy. Then open `/exec?k=…` in a **fresh** browser tab.
- Confirmation that this was the issue: once a New version was published, the console error vanished and "NEEDS A CALLBACK NOW" filled with all 8 callbacks.

### Final verified state
- `Dashboard.html` line 689: `box.innerHTML=p.map(function(e,i){` ✅
- Inline `<script>` passes `node --check` ✅
- Live page: all dropdowns populated, console clean. ✅
- This corrected project (11 files) is the authoritative export, captured 29 Jun 2026.

### Lessons banked (added to KB)
1. **Empty sections + correct tiles + good server data = a client-side render crash.** Go straight to F12 Console; don't touch triggers or deployments yet.
2. **Two probes, in order:** `probeApi` (is data coming in?) → `probeDashboardData_` via a plain-named wrapper (is the server returning it?). If both pass, it's the browser.
3. **A single throw inside `Array.map` blanks every section drawn after it** — one list's bug can look like "the whole dashboard is broken."
4. **Saving an Apps Script HTML edit ≠ publishing it.** A persistent *identical* error at the *same line:column* after a fix means the OLD version is still deployed — publish a New version.
5. **The Run dropdown hides/caches `_`-suffixed functions** — wrap them in a plain-named function to run them.

---

## INCIDENT TEMPLATE (copy this block for the next problem)

## INCIDENT #N — <one-line symptom>  ·  <RESOLVED/OPEN> <date> (Session NN)
### Symptom
### False trails (what did NOT work)
### How it was diagnosed
### Root cause
### The fix
### Final verified state
### Lessons banked
