# Debate 05 — K7/K8 versus FMEA

2026-10-12. Participants: independent specialists 08 and 14. Both read the other's completed memo and exchanged explicit challenges and replies. **Outcome: PROTOTYPE FIRST for isolated ≤1 mA signal fixtures; vehicle integration NO.** These are accepted analytical corrections, not physical results.

## Accepted corrections

- FMEA's “K7/K8 cross-coupling can propagate source shorts” applies to BOTH/contact-bridge faults. Healthy 01/10 states connect both COMs to one source without directly bridging J4-8/J4-9. The fixture sees increased source loading. A real COM-to-COM endpoint can conduct current between sources in 00/11; the graph omits endpoint impedance. Therefore “no graph short” proves neither negligible current nor safe response (`08-k7-k8.md`; `tests/test_passive_bypass_model.py:363–394`).
- Pairing controls or using one DPDT can restrict intentionally commanded settled states **if requirements justify pairing**. Neither guarantees simultaneous physical transfer or removes stuck-pole, open, bounce or release-skew states. Preserve independent controls while endpoint function and tolerated states remain unknown.
- FMEA's proposed “pre-arm physical driver/coil check” needs correction: with healthy Q5 withholding power, a shorted Q1/Q3/Q4 can still show zero coil current and NC contacts. ZERO_REQ observes command nets; the first zero-command ARM/permission transition can energize a faulty driver. The existing Q1 counterexample covers RLY1; Q3/Q4 analogues create a K7/K8 mixed state (`tests/test_passive_bypass_model.py:176–183`; `passive_bypass.net:998–1016`). Offline transistor continuity supports assembly screening, not universal runtime diagnosis.
- Q6 drain-source short grounds P_GATE and turns healthy Q5 on despite withdrawn permission (`passive_bypass.net:1018–1025,1123–1127`). Treat Q6, Q5 and stuck-HIGH permission faults separately within one automatic cutoff chain. Physical series feed removal retains authority only under its intact-wiring/sole-feed assumptions.

## Disposition and resolving experiments

Neither reviewer requires immediate circuit redesign for a deliberately contained fixture intended to expose faults. Both reject automatic single-fault recovery or endpoint-safe-state claims. Future requirements may demand a different architecture; reviewer agreement is not diagnostic coverage.

Add separate V20 cases: short Q1, Q3, then Q4 before qualification/ARM with all requests LOW; capture first permission transition, coil current and COM changes. Next emulate Q6 short with requests asserted, withdraw automatic permission, then open physical feed. Record both sources/COMs, differential voltage, currents, gate voltage and contacts through release/bounce. Repeat V22 four states and delayed/stuck poles; use simulator loads only.

Stop for fixture current breach, unexplained transfer, lost physical-feed authority or mapping mismatch. Expected injected failures are documented vulnerabilities, never successful mitigation; any zero-command ARM transfer during ordinary assembly acceptance fails that check and requires physical-feed removal. **Remaining uncertainty, no dissent:** endpoint identity, electrical envelope, default/mixed-state meaning and allowed exposure times need authoritative wiring plus measured/HIL evidence before integration.
