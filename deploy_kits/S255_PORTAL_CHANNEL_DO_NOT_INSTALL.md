# S255_PORTAL_CHANNEL — DO NOT INSTALL

**Status: published, immutable (F-460), and REFUTED. It was installed on 13-Sep-2026 and rolled back
the same hour. Its installer will still run — it is pinned to the live from-hashes, which the
rollback restored. Do not run it.**

The kit splits Docterz online money into "portal" and "ICICI" by the **mode label** (Wallet /
Patient APP / Net Banking = portal). Live evidence taken the same day shows that premise is false:

- the one payment with a Razorpay receipt in hand (29-Aug, ₹600) is recorded as **"Online Payment"**;
- a "Wallet" payment (12-Sep, ₹600) **paired to the ICICI MPR** at 18:25:38;
- the owner's personal-phone UPI is also recorded as **"Online Payment"**.

It also reintroduced an **F-459** contradiction: `finance_clinic_day._mpr_card` kept pairing an entry
that `clinic_money` had removed as portal, so two screens read the same ₹600 two different ways.

**D510:** an online payment's channel comes from which independent record holds it — the ICICI MPR,
the counter sheet's *Paid to another UPI* box, or the Docterz payment-completed email — never from
the Docterz mode field.

Full account: `D:\Downloads\ClaudeCowork\03_WORKING_PAPERS\S255\S255_PORTAL_PREMISE_REFUTED.md`
(faults F-467, F-468).

*Any future attempt must build step 2 of D507 — the payment record — before touching the reconciler.*
