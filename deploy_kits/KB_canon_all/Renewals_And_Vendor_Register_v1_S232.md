# RENEWALS AND VENDOR REGISTER — v1 · S232 · 08-Sep-2026

**The live register.** It supersedes §2 and §3 of `claude/S230_RENEWALS_AND_VENDOR_REGISTER.md`,
which was a read-only assessment and correctly said so. §1 of that document — *the register silently
forgets, permanently* — is unfixed and restated here as §5.

**No policy, licence, account or document number is reproduced anywhere in this file.** Those live
only in the Janitor's own source on the personal account, and D421 sends them to Bitwarden.

---

## 1 · WHAT D422 CLOSED

The owner's ruling, 07-Sep-2026: **`dr-manoj.in` is renewed to 2027. `drmanojagarwal.in` is
deliberately NOT renewed** — of no further use, the public-facing site being `drmanojagarwal.com`.
The JustDial → Hostinger transfer question is moot.

**Both S230 clocks are therefore closed by ruling, not chased.** What remains is tidiness, and one
measured fact that D422 could not have known:

> ⚠ **`drmanojagarwal.in` resolves TODAY to `93.127.195.49` — the clinic VPS itself.** The domain
> being allowed to lapse currently points at the live server. Nothing appears to depend on it and
> nothing should be built on it; recorded so that when it stops resolving, nobody spends an hour
> wondering what broke. **Measured 08-Sep-2026 by DNS lookup.**

## 2 · THE NAME ESTATE — measured, not listed from memory

**Measured 08-Sep-2026 by DNS lookup of every name that appears in the repository.** The S230
assessment said *"the eight `*.dr-manoj.in` subdomains"*. That figure is wrong in both directions:
**fifteen distinct names appear in the repository, fourteen resolve, and they split cleanly in two.**

**SIX ARE THE ESTATE** — all on the VPS, `93.127.195.49`. These are the clinic's own applications and
a lapse of `dr-manoj.in` takes every one of them down at once:

| name | what it serves |
|---|---|
| `attendance.dr-manoj.in` | the staff register — 974 references, the most-used name in the estate |
| `followup.dr-manoj.in` | the follow-up tracker, finance, stock, ledger, purchases — 672 |
| `assets.dr-manoj.in` | the asset register and scanner — 417 |
| `fit.dr-manoj.in` | 182 |
| `health.dr-manoj.in` | 104 |
| `rx.dr-manoj.in` | 99 |

**EIGHT ARE SHORT LINKS / FORWARDING** — on AWS-range addresses, i.e. registrar forwarding, not the
VPS: `save` · `map` · `contact` · `web` · `ios` · `book` · `app` · `www`. *(These correspond to the
`GoDaddy_Short_URL_Master` sheet already in the project.)*

**AND ONE IS DEAD:** **`alt.dr-manoj.in` does not resolve** and is referenced twice in the
repository. Harmless; recorded so it is not mistaken for an outage later.

The apex **`dr-manoj.in` itself → `76.223.105.230`** (forwarding, not the VPS) ·
**`drmanojagarwal.com` and `www` → `93.127.195.49`** (the VPS) ·
**`nkpathology.com` and `www` → `62.72.56.226`** — a **different host**, and the only piece of the
estate not on the clinic VPS.

## 3 · THE REGISTER AS IT STANDS

*Dates as recorded in the Janitor array. Identifiers deliberately omitted.*

| when | item | cycle | note |
|---|---|---|---|
| ~~PAST 12-Aug~~ | ~~transfer `drmanojagarwal.in`~~ | — | **CLOSED by D422 — moot, not renewing** |
| ~~PAST 29-Aug~~ | ~~GoDaddy `dr-manoj.in`~~ | 12 mo | **CLOSED by D422 — renewed to 2027.** The array entry still says 29-Aug-2026 and will drop out ~13-Oct; §5 |
| 03-Dec-2026 | **Marg ERP licence** | 12 mo | Sanjeevni Medicos pharmacy ERP — **feeds the whole revenue pipeline**. The nearest clinic-critical date. |
| 28-Feb-2027 | KIA Carnival insurance | 12 mo | |
| 03-Mar-2027 | VW Vento insurance | 12 mo | |
| 01-Apr-2027 | **Biomedical waste authorisation ×2** (Clinic + NK Pathology) | 12 mo | UPPCB; both valid 1-Apr → 31-Mar; **renew BEFORE 1 April** |
| 01-Apr-2027 | Fire extinguisher refill | 12 mo | |
| 27-Apr-2027 | Professional indemnity — Dr Manoj | 12 mo | |
| 27-Apr-2027 | Professional indemnity — Dr Bhawna | 12 mo | |
| 01-Jun-2027 | `drmanojagarwal.in` domain | — | **retire this entry — D422** |
| 15-Jul-2027 | Family health insurance | 12 mo | |
| **03-Sep-2027** | **MyOperator (IVR + WABA)** | 15 mo | **₹2,12,400 incl GST — the largest recurring cost.** The entry says *negotiate before renewal*. |
| 25-Sep-2027 | **Docterz EMR, 5-year plan** | 60 mo | ₹29,500; the entry says *strategic: renew vs migrate* |
| 10-May-2028 | ⚠ **CHECK: Webuzo auto-renew is OFF** | 24 mo | parked upsell — **must NOT renew on 10-Jun-2028** |
| 10-Jun-2028 | **Hostinger KVM2 VPS, 2-year** | 24 mo | ₹28,776 / 2 yr; confirm Webuzo is not re-added |
| 10-Jun-2029 | `drmanojagarwal.com` domain | 12 mo | the public site |
| 31-Mar-2030 | Clinic registration CMO/UPMC | 60 mo | valid to 31-Mar-2030; start Jan-2030 |

Four **personal identity documents** ride in the same array. They are personal, not clinic; no
numbers here. **One had an action date of 27-Sep-2026 — nineteen days away, and the only item in the
whole register due inside a month.**

## 4 · THE EIGHT TECHNICAL VENDORS — added here for the first time

**This is the half the register never had, and it is the dangerous half: a lapsed key or a lapsed
domain takes this system down more surely than any bug in it.** Ordered by what a lapse costs.

**Nothing below is invented.** Where a date or an account is not known, it says so and names the one
question that settles it. **An empty cell is the finding, not a gap to be filled by guesswork.**

| # | vendor | what it does | what a lapse costs | known | the one question owed |
|---|---|---|---|---|---|
| **1** | **Tailscale** | the only link between the medical PC and manojz | 🔴 **the entire Marg lane stops** — no exports, no sale data, no purchase data, no stock. And **node keys expire on a schedule**, so this can lapse without anyone cancelling anything. | free/personal tier is the presumption; two nodes | **Which account owns the tailnet, and is key expiry DISABLED on both nodes?** That second half is the whole risk. |
| **2** | **The registrar accounts** | who holds the login for `dr-manoj.in`, `drmanojagarwal.com`, `nkpathology.com` | 🔴 a domain nobody can renew is a domain that lapses | GoDaddy holds at least `dr-manoj.in` (forwarding is theirs); Hostinger holds the VPS | **Which registrar holds each of the three, and where does each login live?** → Bitwarden, D421. |
| **3** | **Google account `drmka.ortho@gmail.com`** | Drive archive · every Apps Script · the live Sheets · the VPS database backup destination | 🔴 the entire Google plane, including the only off-box copy of the finance database | storage plan unknown | **Is it a paid Workspace or a free account, and how full is the storage?** A full Drive stops the backup silently. |
| **4** | **Sarvam AI** | call transcription (03:00 nightly) + bill OCR | transcripts and bill auto-fill stop; the verdict layer starves | key is on the VPS, not in the repository | **Prepaid credit or subscription, and what is the balance?** |
| **5** | **Anthropic API** | the call verdict layer (03:40 nightly) | verdicts stop | key is on the VPS | **Prepaid credit or invoiced, and what is the balance?** |
| **6** | **MyOperator sub-services** | the WABA number itself, IVR minutes | patient messaging stops | main contract 03-Sep-2027, ₹2,12,400 | **Is the WABA number billed separately from the ₹2,12,400, and on what date?** Ask alongside the token-overlap question already with Ms. Khushi Jain. |
| **7** | **`nkpathology.com`** | the lab's public site — **the one thing not on the clinic VPS** (`62.72.56.226`) | the lab site goes dark; nothing clinical depends on it | resolves; registrar and expiry unrecorded | **Registrar and expiry date?** |
| **8** | **SSL certificates** | every `https://` in the estate | — | **`acme.sh --cron` renews them at 00:07 daily. Automatic.** | **None. Recorded so nobody adds a reminder for something that renews itself** — a nag for a solved problem is how nags get ignored. |

> **Why item 1 is first and not the most expensive one.** MyOperator at ₹2,12,400 is the biggest
> cheque; **Tailscale is the biggest hole.** It costs nothing, nobody sends an invoice for it, and
> a node key quietly reaching its expiry date stops the Marg lane with no bill, no email and no
> error anyone reads. **Cost is not risk. The register had been sorted by cost.**

## 5 · THE REGISTER STILL FORGETS — unfixed, and it is a live-script change

`nagRenewals` computes `days = dateISO − today` and then `if (days > 30 || days < −45) return;`.
**Nothing rolls `dateISO` forward by `cycleMonths`.** `cycleMonths` is recorded on every entry and
used by nothing. So the life of an entry is:

> quiet → nagged from 21 days out → nagged daily inside 7 days → **OVERDUE for 45 days** →
> **silently dropped, and never mentioned again.**

**`dr-manoj.in`'s entry still reads 29-Aug-2026 and will fall out of the register around 13-Oct.**
D422 renewed the domain; it did not update the array. **The domain every screen in this estate runs
on would then have no watcher at all** — and the register decays to empty by design, not by neglect.

**The fix is small and safe** — roll `dateISO` forward by `cycleMonths` when an item passes N days
overdue, or record a `lastDoneISO` and compute the next date from it. **It is not done, for one
reason: it changes a live Apps Script on the personal account, and Apps Script work is PARKED by the
owner** until Phases 1 and 2 are complete. It is built and shown when that hold lifts, never
installed unasked.

## 6 · WHAT WOULD ACTUALLY CLOSE THIS

1. **Nine answers** — the eight questions in §4 plus the new expiry for `dr-manoj.in`. Most are one
   line each and several are a single look at a vendor page.
2. **Then the array carries all of it**, technical vendors included, so there is one register and not
   two.
3. **Then the register goes behind a screen with its age on it** — *"26 items · nearest in N days ·
   nothing overdue"* — rather than an email. **A list you can look at beats a mail you can miss**,
   and it is the rule this whole estate keeps arriving at: everything that runs says how old it is.
4. **And Tailscale key expiry gets disabled before any of that**, because it is the only item on this
   page that can bite without anybody being billed.

---
*Renewals and Vendor Register v1 · S232 · 08-Sep-2026. Supersedes §2–§3 of
`claude/S230_RENEWALS_AND_VENDOR_REGISTER.md`. DNS measured 08-Sep-2026. No identifiers reproduced.*
