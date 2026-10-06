# S294 BUILD BRIEF — 06-Oct-2026 (the parent)

Session 294, one chat across two nights (04-Oct 15:56 → 06-Oct before dawn). Six kits — S476, S477, S478, S479, S481, S487 — four live on the server, two on your PC. Numbers from `board/_numbers` (v260 → v292): D679, D680; F-741 … F-752.

## What you asked for, and where each stands
| what you asked | where it stands |
|---|---|
| "Do what all is possible for you in your list" (04-Oct) | **Done, six things.** A watch on the bank-statement road — the health page now says when a statement last reached the shelf, and turns amber if a month's statements stop coming. The hand-over photos, the login store and the order sheets are in the nightly encrypted backup. The setup kits for your PC and the Medical PC were tested on a real Windows by the nightly job itself (all 46 checks green) — **both buttons on *Clinic PCs & phones* are safe to press now.** The reception PC's agent is updated and reports how current its Windows is. |
| The Yes Bank statement that would not read (the one mailed monthly) | **Done.** It reads now. September shows **13 of 15** statements; the two missing are NK Pathology's and the Clinic's current accounts — they wait on your passwords. The pack also hands the accountants the opened copy, not the bank's locked file. |
| A tile at the top of your app, leading to a "command console" | **Done — live since 05-Oct evening.** The *Today* tile on your Clinic app, and behind it one page: what needs you, the money, today's work person by person, attendance, Sanjeevni, scans and papers, the system. Every line opens the page it belongs to. It only reads; approving is still done on each page. |
| "Start staff lists build now, dont populate old stale data, use from current month only, and the leftovers of September" | **Done — live, and switched OFF until you turn it on.** Each person has one Hinglish screen, *Aaj ka kaam*, of what is theirs to do. Nothing before 01-Sep-2026 is shown or counted — on their lists and on your console. Jobs the system cannot see have a *Ho gaya* button; who tapped and when is kept. |

## What needs you
1. **Look at each person's list, then turn the lists on.** Open your console, open *Today's work*, tap **List** beside each name. Tell me any wording to change. When you are happy, **Turn on** is on the *Staff lists* line in the same section. Until then the staff see nothing new.

```
https://followup.dr-manoj.in/finance/console
```

2. **One double-click — the publish.** It carries only this record; no server line follows.

```
D:\dr-manoj-git\drmanoj-clinic-automation\PUBLISH_ALL.bat
```

3. **The two Yes Bank passwords still missing** (NK Pathology current, the Clinic current), on the packs page › *Statement passwords* › *Set*. Then the September pack can be sent.

```
https://followup.dr-manoj.in/finance/packs
```

## Good to know when you look at the lists
- **"late"** means the allowed days for that job are used up — the same rule on the staff's list and on your console.
- **Weekly and monthly *Ho gaya* lines** show in your preview; for the staff each begins with the first full week or month after you turn the lists on, so nobody is shown a week that was already running.
- **Alisha and Shivani share one list** (the reception desk's). The shared Reception login sees the desk's lines only.
- If a person's list ever cannot be read fully, it says so on their screen and never says *Sab ho gaya*.

## Built with you on 05-Oct and NOT yet made — the next kits, in this order
1. The morning step each person must answer before their other tiles open, starting from their punch.
2. Stand-ins when someone is away.
3. The lock until the Docterz reports of the previous day are exported.
4. The attendance month-end sheet (reception prints, staff tick and sign, Shavez checks, you approve changed days only).
5. Later: approving from inside your console.

## What went wrong on my side, and what it cost you
- The console's first install stopped itself at its own test and installed nothing — a fault in my test, not in the console. One extra publish and one extra paste.
- The staff lists' first publish was refused — I had not listed the kit's one `.json` file in the repository's allow list. One extra double-click.
- For a few seconds a test copy of the clinic database sat in my evidence folder on your PC. I emptied it at once. The two empty files are now in one small folder for you to delete whenever you are at the PC (I cannot delete on your PC): `D:\Downloads\_to_delete_S294\`.

## Yours, when you are ready — nothing waits on it
- Electrical and plumbing bills: the clinic / MK split, when you settle it.
- The reception PC: the LAN cable · "Connect automatically" for the clinic Wi-Fi · its Windows.

## Waiting on your word (you said "later")
The follow-up tracker on the server · the contacts workbook · the mail flood · the portal tiles.
