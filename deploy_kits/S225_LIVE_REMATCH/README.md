# S225_LIVE_REMATCH — the cross-check goes live (rev 9)

**The owner:** the Sarvam-scan vs Marg-bill verification *"should run in background, to update the next purchase order"* — and,
ruled at S225, **"live, not nightly."** Also: *"received-but-not-yet-in-Marg quantities count as stock in transit for the reorder engine."*

- **On the event.** A purchase push that stores bills or lines re-matches scans to bills at once. The hub and the scan-links page
  re-match on opening **whenever the scans have changed** since the last match (a fingerprint of the scan store is kept; nothing
  moved, nothing done — the page stays fast). The *Re-match now* button remains for the impatient.
- **Stock in transit.** Goods marked *Arrived* on an order, for which Marg has not yet shown a purchase line from that stockist,
  are on the shelf but not in the stock snapshot yet — the engine now counts them as stock, and the line's reasons say so
  (*"N units received on order #K, not yet in Marg — counted as stock"*). Fourteen-day window.

**Proof:** `selftest_live_rematch.py` **311/311** — the fingerprint is remembered; no change → no re-match; a new scan → one
re-match on the next opening; a push re-matches with `who='push'`; in-transit quantities are counted and worded. Install per F-321.
