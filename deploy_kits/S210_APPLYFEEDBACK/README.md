# S210_APPLYFEEDBACK — the Apply button says what it is doing

Owner, 30-Aug (after the first successful D354 apply): *"during processing a popup /
applying / processing would be informative, currently no idea what's happening in backend."*

He is right, and it is a safety matter, not cosmetics: a long multi-day apply ran in
SILENCE, which is what invited the second click that raced two workers into the
database-lock 500 earlier tonight.

**One page change** (base: the live S210_TRUTHFLOW page): on Apply the button disables and
reads "applying…", and a line appears — *"Report load ho rahi hai — ek minute tak lag
sakta hai. Dubara click mat kijiye; poora hone par popup aayega."* The completion popup is
unchanged; a network failure now also refreshes the list so buttons reset. js_gate PASS.

## Install — one paste after the publish (rides with any future publish; no urgency)

```
git -C /root/deploy/repo fetch --depth 1 origin main && git -C /root/deploy/repo reset --hard origin/main && \cp /root/finance/finance_ui/finance_approvals.html /root/finance/finance_ui/finance_approvals.html.bak_S210_AF && \cp /root/deploy/repo/deploy_kits/S210_APPLYFEEDBACK/finance_approvals.html /root/finance/finance_ui/finance_approvals.html && echo DONE
```

No restart — pages read from disk per request.
