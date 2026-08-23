# S196_HLT3 — F-162 fix

The A4 month-vs-Marg health block was dead since S195 (`today()` shadowed by the local date — both its cards swallowed the error). One line fixed; one new smoke check refuses ANY health card whose detail is a swallowed exception. Pins: `6fc3becc…` → `388c8ac0fdfecdee6029c0033b9b0ef8` · smoke 667 → 668. Install: publish → `cd /root/deploy/repo && git pull && bash deploy_kits/S196_HLT3/INSTALL_S196_HLT3.sh`
