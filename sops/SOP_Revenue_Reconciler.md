# SOP — Revenue Reconciler  ⚠️ STUB (status unconfirmed)
## Advanced Orthopaedic Surgery Centre, Bareilly
**Drafted: Session 63 · 04 Jul 2026 · Owner: Dr. Manoj Agarwal · Maintained with: Claude**

> **This is a deliberate STUB, not a finished SOP.**
> The Maintenance & SOP spec lists `SOP_Revenue_Reconciler.md` (ingest, match ladder,
> held-bills review) as one of the seven SOPs. However, the **current** Master KB (v1.30)
> and Runbook (Session 62) do **not** describe the revenue reconciler as a confirmed live
> component, nor its current parameters. Writing a full "here's how it works and how to fix
> it" SOP from memory would risk documenting a system as live when its live state can't be
> verified — which violates the KB-wins discipline.
>
> So this file exists only as a placeholder so the SOP library is complete-by-name, and to
> record exactly what needs confirming before it can be written properly.

---

## What to confirm before writing the real SOP

1. **Is the revenue reconciler currently live?** (The surveillance register reserves
   `REVENUE_STALE`, "last run within 7 days" — implying it was planned/built, but the KB §12
   live-state does not list it among running components.)
2. **Where does it run?** (VPS service? Apps Script? Scheduled job? Which port/timer?)
3. **What are its inputs and the match ladder?** (Ingest source, matching rules, held-bills
   review flow.)
4. **Who is the single writer of its output tab?** (One-writer-per-table invariant.)
5. **What does "healthy" look like, and what's the manual fallback?**

Once those are answered in a build session (or read from live), replace this stub with a full
SOP in the same shape as the others (VPS Services / Dashboard / etc.).

---

*Placeholder only. Do not treat as operational guidance. Keep in the SOP folder so the
library is name-complete; upgrade to a full SOP when the reconciler's live state is confirmed.*
