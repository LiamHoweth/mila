# 04 — Semiconductor alternatives

Independent Phase 1 memo, 2026-10-12. Manufacturer sources checked live; no physical results obtained.

**Verdict: PROTOTYPE FIRST.** Keep four nonlatching Form-C packages as the bench comparison baseline. Reject SN3257-only and latching replacements for the present zero-power-default requirement. A Form-B semiconductor investigation is technically legitimate, but is a separate experiment rather than a justified carrier substitution.

## Ranked findings

1. **SN3257 fails the default connection requirement, even with three packages.** On total board-power loss, its signal pins become high impedance rather than connecting COM to NC. A surviving 5 V source also exceeds its 3.6 V recommended powered-off signal range. More packages fix shared-control grouping, not this failure. **CONFIRMED SOURCE:** [TI Rev. D](https://www.ti.com/lit/ds/symlink/sn3257-q1.pdf), §§5, 6.3, 8.3.4, pp.3–4,20. Project grouping: `docs/six_relay_mapping.csv:2–19`; carrier netlist `hardware/passive_bypass_rev_a/passive_bypass.net:516–621` identifies four single-side-stable relays.

2. **True zero-input-power semiconductor continuity exists.** Panasonic AQY4C2PX is normally closed and capacitively isolated; dismissing it because older photorelays have high resistance would be incorrect. Its 8 Ω maximum is specified at 25°C, zero input, maximum load, within one second. At 1 mA that implies a calculated 8 mV path drop under those conditions, not a temperature-wide guarantee. Recommended load voltage is 30 V, despite a 60 V absolute rating. **CONFIRMED SOURCE / ANALYTICAL INFERENCE:** [Panasonic catalog ASCTB453E](https://mediap.industry.panasonic.eu/assets/download-files/import/semi_eng_cc1b_aqy4c_p.pdf), printed pp.1–4; [current exact-suffix page](https://industry.panasonic.com/ap/en/products/control/relay/photomos/number/aqy4c2px). Automotive applicability requires manufacturer consultation.

3. **A complementary pair lacks a guaranteed passive transfer interlock.** Six Form-B branches plus six Form-A branches preserve six changeovers in principle. On abrupt simultaneous drive loss, stock can reconnect before generated-source isolation completes. AQY4C2P publishes 1.5 ms maximum reverse-ON time at 25°C under its fixture, but no minimum restoration delay that can establish worst-case nonoverlap against another part. Firmware sequencing does not control a dead supply. **ANALYTICAL INFERENCE:** Panasonic catalog printed p.3; project `docs/passive-bypass-fmea.md:192–199`. A matching Form-A part and bounded collapse behavior remain **UNKNOWN**.

4. **Parallel NC bridging around SN3257 retains two problems.** A stuck-closed bridge plus commanded generated branch creates source contention; opening switch supply still exposes its attached pins to surviving signals. A Form-C stage that fully disconnects the semiconductor can remove exposure, but consumes poles and adds transfer validation. **ANALYTICAL INFERENCE:** TI §§6.3,8.3.4; `docs/passive-bypass-design.md:349–350`. No reviewed hybrid schematic establishes these conditions.

5. **Latching saves coil energy by retaining the selected state.** Loss of power while generated input is selected therefore does not restore bypass. Stored-energy reset introduces another powered recovery dependency. **CONFIRMED SOURCE / INFERENCE:** [OMRON G6K](https://omronfs.omron.com/en_US/ecb/products/pdf/en-g6k.pdf), model legend p.1 and latching set/reset ratings p.3. It does not meet this baseline requirement.

## Best alternative and decisive measurement

Retain compact Form-C for the first simulator run. If size remains decisive, compare one AQY4C2P/Form-A channel separately. Use two distinguishable 0–5 V sources through resistors sized for ≤1 mA, a known load, and measure both branch currents, COM voltage and actual input-drive collapse. Test normal transfer, abrupt unplug, slow ramps, individual drive loss and stuck-conducting branches. Determine output capacitance separately: catalog Ciso describes input/output isolation capacitance, not open-branch capacitance.

**Kill criteria:** reject the tested variant on any unbounded overlap, missing zero-drive continuity, excessive measured error against a predeclared simulator budget, or need to merge K7/K8 controls. Any unresolved application limits prevent vehicle advancement regardless of successful bench screening.
