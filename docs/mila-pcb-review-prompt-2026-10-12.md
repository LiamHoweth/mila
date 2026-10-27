# MiLa PCB redesign review prompt

Perform a rigorous, independent multi-agent engineering review of my MiLa PCB redesign before I commit more development time, order a new revision, or consider vehicle integration. Challenge the design and recommend the smallest useful next step. Review electrical behavior, physical faults, implementation, verification, cost and research value rather than mobile-app commercial metrics.

## Design under review

MiLa is a Nissan LEAF autonomous-vehicle research project with an ESP32 drive-by-wire interface, two MCP4728 DACs, CAN diagnostics and possible comma 4/openpilot integration. My immediate PCB goal is to replace the large eight-relay module with a smaller arrangement while preserving the required connections and power-loss behavior.

Use the current unmodified October 7 passive-bypass Rev A carrier plus supervisor as the ORIGINAL concept for scoring. Compare it with an IMPROVED engineering proposal developed by the reviewers. Also evaluate the earlier SN3257 semiconductor replacement as an alternative; do not silently treat that superseded proposal as the current design. Score the improved proposal as a proposal, without awarding it evidence from tests that have not happened.

The working baseline is:

- Six used paths, K3 through K8, with three independent control domains: K3–K6 together, K7 separately and K8 separately.
- Four nonlatching OMRON G6K-2P-Y DC5 DPDT packages. Two use both poles for K3–K6; the other two each use one pole for K7/K8.
- Healthy deenergized contacts restore the documented NC connectivity after finite coil decay, release and bounce. That does not prove uninterrupted signals, safe vehicle behavior or tolerance of welded contacts.
- K7/K8 cross-connect J4-8 and J4-9. Their default state and mixed states have no established vehicle safety meaning. Do not infer a motor, brake or sensor rating from a net name.
- AO3400A individual coil drivers, AO3401A common high-side cutoff, local flyback diodes and a physical series enable/deadman.
- A separate TPS3430-Q1 watchdog/TPS3808 rail-monitor supervisor with two heartbeat qualification stages, a fresh ARM edge with requests inactive, and a lightly loaded 3.3 V LVC permission output.
- Carrier 5 V feedback returns through JCTRL1-6 to supervisor J5-7. Local feedback loopback defeats that detection. Brief connector chatter and individual conductor reconnection can escape detection.
- The carrier and supervisor are isolated bench designs for 0–5 V, at most 1 mA per signal path. They are not automotive-power, actuator, ECU or vehicle-harness interfaces.
- The controller is described as a 38-pin ESP32-WROOM-32D development board. Its physical revision, USB/V5 power paths and header-to-GPIO mapping need verification.
- The supplied automatic-sweep firmware is reference evidence only. It can start automatically, does not implement this supervisor contract and has unresolved PCB/DAC/pin mapping conflicts.
- The guarded comma CAN diagnostic is a separate project: bench ID 0x5A5, 2 Hz, physical GPIO27 jumper plus serial ARM, 30-second timeout. It is not DBW actuation firmware.
- Previously recorded host tests and native CAD checks support particular software/connectivity claims. They do not prove physical operation. Recheck important claims against actual files and fresh read-only checks.

## Project sources and boundaries

Root: `/Users/howeth/Desktop/codex/Hardware/MiLa`. `/Users/howeth/Desktop/MiLa` is an alias; verify that before assuming two different projects.

Read `AGENTS.md` if present, `AGENT_NOTES.md`, `PROJECT_CONTEXT.md`, and relevant parts of `MILA_CONTEXT.md`. Then inspect:

- `docs/dbw-switch-redesign-review.md`
- `docs/passive-bypass-design.md`
- `docs/passive-bypass-fmea.md`
- `docs/passive-bypass-validation.csv`
- `docs/passive-bypass-review-log.md`
- `docs/six_relay_mapping.csv`
- Original PCB 2.0 schematic, board and relay footprint under `capstone_Oscar_Zheng_Jared_05032026/PCB_2.0/PCBGerberFiles/`
- `hardware/passive_bypass_rev_a/` and `hardware/passive_bypass_supervisor_rev_a/`, including schematic, routed board, local libraries, BOMs, connector maps and exported netlists
- `hardware/review_evidence/`, including final JSON reports and original-source hashes
- `tools/passive_bypass_model.py`, design generators/checkers and `tests/`
- Relevant firmware and CAN documentation for compatibility and authority boundaries

Preserve original sources and existing generated designs. This request authorizes a review and documentation, not a circuit redesign, firmware flash, fabrication purchase or physical actuation. Agents may write only their review artifacts in assigned files. The coordinator runs shared validation once and labels every result with its date and scope. Do not regenerate routing or fabrication files during review.

Use current primary sources for component properties, qualification, lifecycle, supported vehicle models, openpilot/panda behavior and standards where relevant. Give direct URLs and datasheet sections/pages. Distributor prices may support pricing only; record date, quantity and exact suffix. Never fabricate stock, quotes, reliability, diagnostic coverage, ASIL classification or certification.

## Independent specialists

Use 18 specialists when resources allow, with a coordinator and a separate final engineering committee. Specialists must finish their first analysis before seeing one another's conclusions. Assign distinct questions and evidence paths:

1. REQUIREMENTS AND RESEARCH VALUE: Define the problem, success measures, missing interface requirements and whether the redesign is worthwhile compared with keeping the original module.
2. LEGACY NET AND HARNESS ANALYST: Reconstruct all COM/NC/NO paths and control groups from raw CAD. Resolve pin naming and original-versus-new mapping without trusting the prose.
3. MECHANICAL RELAY SPECIALIST: Check exact relay suffix, pinout, footprint, minimum load, contact behavior, lifetime, coil characteristics and qualification limits.
4. SEMICONDUCTOR ALTERNATIVES SPECIALIST: Compare SN3257, Form-B PhotoMOS, hybrids and latching choices. Test whether each actually provides passive continuity at zero power and during transitions.
5. SUPERVISOR LOGIC SPECIALIST: Inspect watchdog windows, startup, rail thresholds, heartbeat qualification, asynchronous clear, setup/hold, manual rearm and missed faults.
6. POWER AND PARTIAL POWER SPECIALIST: Analyze USB/V5, diode OR, brownout, slow ramps, backfeed, I/O powering, cutoff body diode and stored coil energy.
7. ANALOG AND DAC SPECIALIST: Analyze voltage error, impedance, leakage, bandwidth, references, correlated channels, DAC startup/retention, stale-but-valid outputs and output collapse.
8. K7 K8 FUNCTION AND TRANSFER SPECIALIST: Analyze all four logical states and physical skew/bounce. Identify exactly what measurement is needed before assigning safety meaning or combining controls.
9. PCB AND FABRICATION SPECIALIST: Inspect actual routed boards, net parity, clearances, return paths, connector orientation, libraries, footprint geometry, testability and release provenance.
10. CONNECTORS AND HUMAN FACTORS SPECIALIST: Check interboard cable orders, ground routing, returned sense, removal bypass, strain relief, ARM/deadman usability and foreseeable assembly errors.
11. EMBEDDED FIRMWARE SPECIALIST: Compare real source behavior with the supervisor contract, GPIO strapping/header mapping, DAC routing, command freshness and heartbeat semantics.
12. CAN AND OPENPILOT SPECIALIST: Determine whether analog substitution is needed, distinguish a bus node from a gateway, preserve panda authority, and verify current support assumptions without vehicle transmission.
13. PHYSICAL VALIDATION AND HIL SPECIALIST: Assess the pending matrix, fixture, scope channels, loads, fault injection, pass criteria, repeatability and evidence needed to advance.
14. FMEA AND FAULT COVERAGE SPECIALIST: Examine opens, shorts, welded contacts, common cause, bypass loss and recovery. Separate fault detection from actual physical mitigation.
15. EMC AND VEHICLE ENVIRONMENT SPECIALIST: Identify the gap between a regulated bench fixture and automotive transients, grounding, temperature, vibration, ESD and service life. Do not invent target levels.
16. SOURCING AND ECONOMICS SPECIALIST: Estimate board/assembly/fixture/rework effort and current component availability from exact parts. Compare total effort of alternatives; no invented precise budget.
17. CODEX AND EVIDENCE AUDITOR: Assess source hashes, tests, generators, Boolean-model blind spots, parallel ownership, reproducibility and which work requires a person and instruments.
18. ADVERSARIAL REVIEWER: Argue against proceeding. Seek concrete counterexamples, unsupported claims and cheaper ways to answer the engineering question. Evidence outranks optimism.

## Review phases

Phase 1: Each specialist independently submits a concise memo with its verdict, three to six ranked findings, exact evidence, uncertainties, proposed changes, required measurements and stop criteria. A finding must state trigger, consequence and evidence; avoid generic checklists.

Phase 2: Gather primary-source evidence and perform bounded read-only verification. Distinguish CONFIRMED SOURCE, FRESH AUTOMATED RESULT, ANALYTICAL INFERENCE, PROPOSED CHANGE, PHYSICAL RESULT and UNKNOWN. A simulator prediction is never a physical result.

Phase 3: Conduct explicit challenge exchanges after the independent memos are complete:

- Requirements versus Adversarial
- Mechanical relays versus Semiconductor alternatives
- Supervisor logic versus Power and partial power
- Analog/DAC versus Firmware
- K7/K8 versus FMEA
- PCB/fabrication versus Connectors/human factors
- CAN/openpilot versus EMC/vehicle environment
- Physical validation versus Codex/evidence audit
- Economics versus Requirements and research value

Require an accepted correction or a documented disagreement with an experiment that could resolve it. Do not manufacture consensus. Count duplicate findings once; overlapping expert opinion is not independent physical evidence.

Phase 4: Form the improved proposal from the strongest supported findings. Prefer a smaller experiment that removes a major uncertainty over adding features or replacing tested structure without evidence.

Phase 5: Give the independent memos, debate outcomes, fresh checks, dissent and revised proposal to a separate final engineering committee. It makes the go/no-go recommendation and audits scores and prerequisites.

## Scoring

Score ORIGINAL and IMPROVED from 1 to 10, with reasons and confidence, using these weights:

| Criterion | Weight |
|---|---:|
| Requirements clarity and research value | 10 |
| Six-path and three-domain fidelity | 10 |
| Power-loss and transfer behavior | 12 |
| Fault detection and mitigation | 12 |
| Analog integrity and DAC compatibility | 10 |
| Power sequencing and electrical margins | 8 |
| Firmware and control authority compatibility | 8 |
| CAD integrity and reproducibility | 8 |
| Manufacturability and maintainability | 6 |
| Validation completeness and testability | 8 |
| Codex buildability and evidence discipline | 4 |
| Scope efficiency and cost of learning | 4 |

Overall /100 = sum(score × weight) / 10. Scores express engineering judgment, not failure probability, certification or permission to connect a vehicle. Use UNKNOWN for factual inputs that are missing; if a judgment score is still assigned, show its uncertainty. An improved test plan may improve testability but cannot improve completed physical-validation status before tests run.

Hard gates override the weighted score. Vehicle advancement requires identified vehicle/harness/functions, measured electrical envelope, application-specific safe states and response limits, physical fault/transfer evidence, a validated controller and separate qualified engineering acceptance. Bench prototype approval is a different gate with its own pre-power assembly, wiring and current-limit checks.

## Final output

1. EXECUTIVE VERDICT: PROTOTYPE FIRST, BUILD WITH CHANGES, KEEP EXISTING HARDWARE, MAJOR PIVOT or DO NOT BUILD. State exactly which stage is allowed.
2. Original and improved /100 scores with full weighted rubric and evidence limitations.
3. What the current redesign solves and the strongest reasons it could work.
4. Ranked ways it could fail, with path/component/net evidence and scope.
5. Alternatives comparison covering original relays, compact Form-C, SN3257, Form-B PhotoMOS/hybrids and native CAN where actually supported.
6. The better version, keeping changes proportionate to unresolved risks.
7. System sequence: boot in bypass → validate outputs/rails → qualify heartbeat → explicit ARM at zero requests → bounded request → fault/disable → measured NC return → manual requalification. Identify who verifies each step.
8. Failure and recovery behavior, including stuck-valid outputs, lost power, missing connector, welded contact and individual-wire reconnection.
9. Electrical/BOM/cost assessment with verified specifications, quoted prices versus planning estimates and open requirements.
10. Minimum useful bench prototype and precise exclusions.
11. Technical plan for carrier, supervisor, harness, firmware and documentation.
12. Proposed Codex ownership with exclusive files, one CAD integrator and one person coordinating physical tests.
13. First 30 days in four weeks, with dependencies and exit criteria rather than guaranteed completion dates.
14. Fastest decisive validation experiment, including fixture, signals to observe, fault stimulus, provisional screening criteria versus application limits, and stop conditions.
15. Measurable kill/pivot criteria and required revision gates.
16. Unresolved questions ranked by impact, with a measurement or source that can answer each.
17. Specialist verdicts, actual debate outcomes and remaining dissent.
18. Final answer: If this were your time and money, would you continue? YES or NO for the bench investigation, and a separate decision for vehicle integration. Explain in at most five paragraphs.

Do not praise the idea because it is mine. Keep safety claims narrower than the evidence. Do not equate automotive-qualified parts, valid CAD, passing Python tests or an NC label with a vehicle-safe system. Preserve original PCB files. Do not buy, flash, actuate or transmit as part of this review. Produce a concrete decision, evidence trail and next experiment.
