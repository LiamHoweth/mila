# Independent engineering investment committee

2026-10-12. Reviewed all 18 independent memos, ten challenge outcomes, the revised proposal and fresh validation; checked the disputed source passages directly. No circuit, firmware or physical action was performed.

**Executive verdict: PROTOTYPE FIRST for a bounded isolated bench investigation. Vehicle integration: NO.** Retain existing hardware and freeze Rev A. Inventory first; use an inspected existing assembly if available, otherwise the exact relay/driver/cutoff/flyback coupon. This is an investment recommendation, not authorization to purchase, energize or connect a vehicle. Confidence is high in the stage decision, low in eventual vehicle suitability.

## Independent weighted assessment

Original = unmodified October 7 carrier plus supervisor. Improved = proposed investigation plan using unchanged circuitry. Scores assess engineering readiness against the stated redesign objective; they are not reliability or certification measures. Missing physical facts remain **UNKNOWN**. Confidence concerns the score judgment, not physical performance.

| Exact criterion | Weight | Original /10 | Improved /10 | Reason; confidence |
|---|---:|---:|---:|---|
| Requirements clarity and research value | 10 | 4 | 6 | Defined bench question improves; named unmet lab function/endpoints absent. Medium. |
| Six-path and three-domain fidelity | 10 | 8 | 8 | 18 terminal nets preserved; physical legacy NC/NO oracle pending. High source, medium overall. |
| Power-loss and transfer behavior | 12 | 4 | 4 | Healthy settled NC plausible; no measured decay/gap/bounce/skew bound. Medium. |
| Fault detection and mitigation | 12 | 4 | 4 | Recognized-fault latch useful; stuck drivers/permission, contacts and reconnection defeat broad claims. High. |
| Analog integrity and DAC compatibility | 10 | 3 | 3 | Output/reference/correlation and physical channel mapping unknown; DAC-only loss invisible to PG5. Medium. |
| Power sequencing and electrical margins | 8 | 4 | 4 | Conditional calculations useful; partial-power and backfeed unmeasured. Medium. |
| Firmware and control authority compatibility | 8 | 2 | 2 | No compatible guarded controller implemented; proposed contract earns no implementation credit. High. |
| CAD integrity and reproducibility | 8 | 8 | 8 | Fresh native/connectivity checks pass; future capture/report binding remains weak. High. |
| Manufacturability and maintainability | 6 | 5 | 5 | 93-part pair, exposed-pad assembly, unkeyed headers, incomplete purchasing/export specification. Medium. |
| Validation completeness and testability | 8 | 3 | 5 | Better discriminating fixture plan; completed physical acceptance remains zero. Medium. |
| Codex buildability and evidence discipline | 4 | 7 | 7 | Good retained evidence; asserted guards and proposed repairs still unchanged. High. |
| Scope efficiency and cost of learning | 4 | 4 | 7 | Inventory/coupon branch avoids premature full-board expenditure. Medium. |

Weights sum to 100. Original = **456/10 = 45.6/100**; improved = **504/10 = 50.4/100**. The entire 4.8-point gain comes from requirements, testability and scope—not improved electrical performance or completed tests. Hard gates override both totals.

## Evidence and challenged claims

`validation/fresh-validation.json` supports 60 passing host tests, 18 contact terminals, 207 populated supervisor pins/9 unused pins, four clean native checks and 69 preserved source/design files. The derived carrier audit was rewritten byte-identically; calling the entire validation strictly read-only would be inaccurate. The 34 procedures and 33 overlapping probes remain pending, not 67 completed experiments.

The committee independently rejects these broader interpretations: settled NC equals uninterrupted delivery; healthy K7/K8 mixed states inherently short both sources; every reconnect requires ARM; zero pre-arm current detects a shorted driver; optimized-assert weakness invalidates today's matched CAD. Raw source and tests support the narrower debate corrections. There is **no measured transfer bound**, and injected-fault observations must not be scored as successful mitigation.

The 7,800 mm² summed new boards versus 6,929 mm² legacy F.SilkS rectangle compares unequal functionality and excludes installed clearances. It proves neither system growth nor compactness. Equal-function installed size remains **UNKNOWN**.

[TI SN3257-Q1](https://www.ti.com/lit/ds/symlink/sn3257-q1.pdf), §§6.3/8.3.4, excludes an SN3257-only passive bypass. [Panasonic Form-B](https://mediap.industry.panasonic.eu/assets/download-files/import/semi_eng_cc1b_aqy4c_p.pdf), pp.1–4, establishes a legitimate zero-drive continuity alternative, but no selected complementary pair proves collapse nonoverlap. Preserve that conditional dissent; do not dismiss all semiconductors or spend on them before a measured mechanical shortfall.

## Five priorities and remaining proposal omissions

1. Establish the physical COM/NC/NO oracle and canonical GPIO→DAC→terminal manifest. Name the research function; keep vehicle endpoints, K7/K8 meaning and application limits UNKNOWN until identified.
2. Issue one executable fixture sheet: isolated returns/probes, exact assembly/lot, current limits, declared dwell duration, uncertainty and numerical provisional error/observation thresholds. The proposal lists variables but does not yet specify these screening bounds. They cannot substitute for vehicle limits.
3. Capture paired COMs, actual generated-output power and coil current for request-off, high-side-off, physical-feed-off and supply collapse. Retain failed trials and first-after-dwell traces; compare the old module under identical containment.
4. Separate fault-free acceptance from injected Q5/Q6 shorts, stuck permission and pre-ARM driver shorts. Include DAC-only loss, independent rail ramps and single-wire reconnection. A person coordinates physical tests; synthetic WDI/operator READY precede any new controller.
5. Set cash/hour caps after inventory; bind future reports to input hashes, replace assertion-only rejection guards and complete the purchasing/manufacturing manifest before release. These are proposed, unimplemented changes.

The [exact watchdog listing](https://www.digikey.com/en/products/detail/texas-instruments/TPS3430WQDRCRQ1/9597846), rechecked October 12, displays zero stock and November 11 expected; availability is not guaranteed. The $150–350/30–66-hour assumptions exclude instruments and full-matrix completion. No guaranteed four-week supervisor acceptance follows. The coupon avoids this dependency but earns no supervisor-validation credit.

Stop immediately for containment/rating violations, mismatched mapping, unexplained pickup or lost physical-feed authority. Freeze further integration if no unmet research need or equal-function packaging benefit exists. Pivot if required recovery includes welded/open contacts, every reconnection or actuator currents; unchanged Rev A cannot meet those demands. Vehicle advancement requires identified interfaces, measured envelopes/response limits, controller validation, physical/environmental evidence and separate qualified acceptance.

**My time and money: YES for the capped isolated investigation; NO for vehicle integration or another speculative full-board spin.** The adversarial KEEP EXISTING HARDWARE position survives as a spending constraint, not a declaration that legacy hardware is vehicle-approved. One reproducible comparative waveform is worth more now than another schematic.
