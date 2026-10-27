# 02 — Legacy nets and harness

Independent phase-1 memo, 2026-10-12. **Verdict: PROTOTYPE FIRST, isolated simulator only.** Terminal connectivity and three-domain structure are preserved in the carrier's raw pad nets. Physical NC/NO identity, functional signal identity and controller mapping remain open; no vehicle or drop-in replacement approval follows.

Evidence abbreviations: **OLD** = `capstone_Oscar_Zheng_Jared_05032026/PCB_2.0/PCBGerberFiles/PCB1.2.kicad_pcb`; **NEW** = `hardware/passive_bypass_rev_a/mila_passive_bypass_bench_rev_a.kicad_pcb`. This read-only reconstruction parsed raw footprint/pad nets, then compared the retained mapping documentation; it did not run the coordinator's shared validation.

## Reconstructed routes

CONFIRMED SOURCE terminal equality; NC/NO names below remain conditional on the original module's photographed terminal order. Entries are original connector terminals, not GPIO numbers.

| Path | COM | Assumed NC | Assumed NO | New package/pole |
|---|---|---|---|---|
| K3 | J4-14 | J4-13 | J5-10 | RLY1 3/2/4 |
| K4 | J4-15 | J4-12 | J5-11 | RLY1 6/7/5 |
| K5 | J4-16 | J4-11 | J6-8 | RLY2 3/2/4 |
| K6 | J4-17 | J4-10 | J6-9 | RLY2 6/7/5 |
| K7 | J4-18 | J4-9 | J4-8 | RLY3 3/2/4 |
| K8 | J4-19 | J4-8 | J4-9 | RLY4 3/2/4 |

OLD:676–873 directly provides all 18 used terminal assignments; NEW:7258–7310, 3707–3759, 1134–1159, 2587–2612 reproduce them. No terminal-net mismatch found. OLD:951–1016 ties IN1–IN6 to J4-23; OLD:1017–1038 and 2502–2523 ties IN7 to J3-25 and IN8 to J3-26. NEW:6773–6788/6257–6272 shares REQ_GROUP for RLY1/2, while 1477–1492/5229–5244 keeps REQ_K7/K8 separate. OLD:874–939 leaves K1/K2 contacts unused; NEW:1161–1186/2614–2639 leaves the spare poles unused.

## Ranked findings

1. **Physical contact oracle missing.** A reversed original NC/NO assumption would preserve copper-terminal equality while reversing intended bypass/injection semantics. OLD uses generic `Pin_n` names, not a relay contact symbol (403–455, 676–873); `docs/dbw-switch-redesign-review.md:31–40` explicitly calls terminal order inferred and input polarity undocumented. Required measurement: six original unpowered COM/NC continuities, then six energized COM/NO continuities on an isolated fixture. Stop if any differs; revise the oracle before wiring a replacement.

2. **Header numbers cannot become firmware GPIOs.** Treating J3-25/26 as GPIO25/26 could actuate the wrong conductors. OLD:2139–2181 defines J3 as a generic counter-clockwise connector; 2502–2523 supplies positions/nets only. GPIO identity is UNKNOWN. Photograph board orientation/revision and continuity-map each controller header to its labeled GPIO before issuing any request.

3. **Not a drop-in harness/control replacement.** NEW:4473–4579 repacks J4 terminals; NEW:5456–5490 combines two DAC headers; NEW:4129–4181 adds active-high requests/permit and returned 5V_RAW. Connecting by equal pin numbers swaps signals; reusing legacy polarity can reverse requests. `hardware/passive_bypass_rev_a/README.md:12–27` agrees. Require a terminal-to-terminal adapter worksheet and 100% disconnected-cable continuity; stop on ambiguity, reversal or powered feedback-to-GPIO wiring.

4. **Cross-connection is confirmed; safety meaning is UNKNOWN.** OLD:676–741 and NEW:1134–1159/2587–2612 imply mixed K7/K8 states connect both COMs to J4-8 or both to J4-9. Simultaneous commands cannot remove physical skew/bounce. Characterize four steady states and transitions using distinct current-limited simulator sources; identify actual loads before selecting limits or combining controls.

5. **Net labels do not identify vehicle functions or DAC channels.** OLD confirms J5/J6 terminals, not exact breakout suffix, calibration, ECU destinations or load ratings. `docs/six_relay_mapping.csv:2–19` labels functions provisional. Maintain canonical terminal names until physical tracing establishes every source/load and the DAC-channel worksheet. Stop vehicle advancement if those identities remain unresolved.

Proposed change is documentation/fixture qualification, not new circuitry. Kill the replacement direction if original unpowered continuity cannot be reproduced within subsequently measured application limits; pivot to preserving the existing module until requirements are known. No physical result is claimed.
