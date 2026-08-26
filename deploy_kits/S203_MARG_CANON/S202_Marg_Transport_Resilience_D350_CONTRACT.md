# D350 — THE MARG TRANSPORT HAS NO SINGLE POINT OF FAILURE

**Session 202 · 26-Aug-2026 · DESIGN CONTRACT, for the owner's signature · NOT YET BUILT**

> **Every rupee of Sanjeevni pharmacy revenue reaches the books through two Windows PCs and the
> link between them.** On 26-Aug that link failed silently for eight hours and forty minutes. This
> contract exists so that cannot happen again without somebody being told.

---

## 0 · THE FAULT THAT PRODUCED THIS

At **23:08 IST on 25-Aug** the pull stopped working. It was found at **07:33 the next morning**,
and only because the owner asked why a report had not arrived.

**Everything was healthy.** The medical PC was on — the owner was in an RDP session with it.
Tailscale was up and showed `medical` as `active; direct 192.168.1.37:41641`. The agent was
running, the watcher was alive, Marg was capturing, Drive was syncing.

**The single thing that failed** was Windows on manojz applying its default policy against
*unauthenticated guest access* to SMB shares. manojz had been reading `\\100.119.151.40\DDrive` as
an anonymous guest; a policy refresh closed that door.

**Three things made it expensive:**

1. **Nothing was watching that leg.** Reports piled up on the medical PC while the server showed
   nothing wrong, because every server-side check watches *arrival at the VPS*.
2. **The error message named the wrong causes.** *"Is it switched on and Tailscale connected?"* —
   both were true. It listed the two innocent causes and not the guilty one.
3. **A working alternative route was sitting idle.** Google Drive carried the heartbeat across the
   entire outage without interruption. The captures could have travelled the same way. Nothing was
   wired to try.

**The lesson this contract encodes: a system with two paths and no switch has one path.**

---

## 1 · TWO TRANSPORTS, ONE AUTOMATIC SWITCH

**Primary — Tailscale SMB.** manojz pulls from `\\<medical>\DDrive`. Fast, direct, unchanged.

**Fallback — Google Drive.** Already installed on both machines, already carrying the heartbeat,
the `ToMedical` kit channel and the offsite archive copy. **It is proven under exactly the failure
this contract addresses**, because it kept working throughout.

**The switch.**

- The medical agent copies each new capture into a Drive outbound folder as well as leaving it in
  `D:\SendToClinic\_captured`. Copies, never moves — the primary path must not be weakened to
  enable the fallback.
- When manojz's pull cannot reach the share, it takes that cycle's work from Drive instead.
- **The switch is automatic. Announcing it is not optional** — see §3.

**Deliberate limits.** Drive is slower and eventually-consistent; it is a fallback, not a peer. If
BOTH routes are unavailable, the medical PC's own `SEND_TO_CLINIC.bat` remains the manual path and
is never removed (D347). Three routes, in descending order of automation.

---

## 2 · VERIFICATION AT BOTH ENDS — MEASURED, NEVER INFERRED

**The rule this comes from: on 26-Aug both endpoints were healthy and the link between them was
dead.** Two green lights either side of a broken wire.

**The medical agent reports** (into the heartbeat, which travels by Drive and therefore survives a
Tailscale failure): Tailscale running / logged in / its current address · whether `DDrive` is still
shared · power and session state — boot time, sleep and wake gaps, who is logged in, since when,
and whether it is an RDP session · its own file hashes, as it already does.

**manojz reports** (into the B2 status): its own Tailscale state and address · **an actual
reachability test of the share, performed, not deduced** · which transport this cycle used ·
whether any credential for the medical host exists at all.

**A changed Tailscale address must be visible the moment it changes**, not eight hours later. The
address is currently hardcoded in `PULL_FROM_MEDICAL.bat`; the durable fix is the Tailscale
MagicDNS name, so the number can never be the fault again.

---

## 3 · WHAT B2 MUST SHOW — the owner's ruling, taken as written

Three new states on the health page, all owner-visible:

| state | shown as |
|---|---|
| **Tailscale, both ends** | address, up/down, and when each was last confirmed |
| **Which point is down** | not "the pipeline failed" but *"the PC answers, the share refuses — most likely credentials"* |
| **Running on the FALLBACK** | **`warn`, and it stays `warn` for as long as it is true** |

**Why the fallback is a warning and not an "ok".** A fallback nobody notices becomes the new
normal. If the system runs on Drive for three weeks and Drive then fails, there was no warning at
either step — the first failure was invisible and the second looked like the first. **Working by
the reserve route is a degraded state, and it must read as one.**

This extends B2. It does not replace it.

---

## 4 · THE REINSTALL KIT — the part that matters most

**Neither PC could be rebuilt today from anything written down.** Everything that carries pharmacy
revenue lives on two machines, and the knowledge of how to recreate them lives in session
transcripts.

One kit per machine, each stating: what to install and in what order · which files go where, with
their md5s · which credentials are needed and how to store them — **never the values, which are the
owner's alone** · the scheduled tasks and the account each must run as · **the checks that prove it
worked**, so a rebuild is verified rather than hoped.

**Medical:** Windows account and its password requirement · the `DDrive` share and its permissions ·
Tailscale · Drive for Desktop · portable Python · `marg_watch.py`, `medical_agent.py`,
`xlsx_stdlib.py` · the scoped token · the Startup entry.

**manojz:** Tailscale · Drive for Desktop · the `MargPull` folder · the stored credential for the
medical host · the scheduled task and its Run-As account · the `margsync` folder layout.

**It must be rehearsed, not merely written.** A recovery document nobody has followed is a guess.

---

## 5 · DOCUMENT CORRECTIONS OWED WITH THIS

**D347 says Tailscale is *"a read-only D:-only view and NOT load-bearing"*. That is wrong** — the
entire pull leg runs through it, and when it closed, the feed stopped. Corrected in the decision
record, `MARG_PIPELINE_REFERENCE_v1` §1 and §5, and `MARG_PIPELINE_MAINTENANCE_FLOW_v1`.

**Also owed:** the guest-access failure and its `cmdkey` remedy added to the maintenance flow by
SYMPTOM, since that is how it will next be met; and the fact that **credentials are stored per
Windows user**, so the scheduled task's Run-As account must be the one holding them.

---

## 6 · NOT IN SCOPE, DELIBERATELY

Replacing Tailscale · moving Marg itself · any change to what the server does with a report once it
arrives (D313 stands: the import never touches money) · automating the credential step, which needs
a password and stays the owner's.

---

## 7 · BUILD ORDER

1. **The document corrections (§5).** Free, and stops the record teaching the wrong thing.
2. **Verification at both ends (§2)** — extends the agent and `pipeline_status.py`.
3. **The B2 states (§3)** — the three checks.
4. **The reinstall kits (§4)**, written and then rehearsed.
5. **The Drive fallback and its switch (§1)** — last, because it is the only part that changes how
   reports actually travel, and it should be built once everything watching it already works.

**Rationale for that order:** every step before the last is observation. If the fallback is built
first and its switch is wrong, the failure it causes is invisible — which is the fault this whole
contract exists to end.

---

## 8 · A COUNTER-ARGUMENT, RECORDED

A reasonable objection: **this adds moving parts to something that worked for months**, and each
new part can itself fail — the Drive copy, the switch, three new checks. Complexity is not free,
and a fallback that misfires can corrupt the primary path.

The answer is the build order in §7: nothing that moves data changes until everything that watches
it is proven. And §1's rule that the agent **copies** rather than moves, so the primary path is
never weakened to serve the fallback.

But the objection is real, and if the owner would rather have only §2, §3 and §5 — verification,
visibility and correct documents, without a second transport — **that is a coherent position and a
much smaller change.** It would leave one path, watched properly, and a rebuild kit. Today's outage
would then have been caught in ten minutes instead of eight hours, without any new route existing.

---

*D350 · S202 · NOT YET BUILT. Awaiting the owner's signature, and his ruling on §8.*
