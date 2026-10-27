# MiLa PCB redesign review

October 12, 2026. **PROTOTYPE FIRST for an isolated bench investigation. Vehicle integration remains NO.** Preserve the original hardware, inspect actual inventory, and measure the compact relay's transfer behavior before another integrated PCB revision. Use an existing inspected Rev A assembly if available; otherwise start with one relay and its actual driver, cutoff, physical interruption and flyback circuit.

The review used 18 independent specialists, 10 subsequent challenge exchanges, a separate final engineering committee and a coordinator. The original concept is the unmodified October 7 four-relay carrier plus supervisor. The improved concept is a narrower investigation and evidence plan; no circuitry, firmware or physical fault coverage was improved during this review. The [adapted reusable prompt](/Users/howeth/Desktop/codex/Hardware/MiLa/docs/mila-pcb-review-prompt-2026-10-12.md) contains the MiLa-specific roles, phases and scoring rules.

## Original and improved scores

The committee scored the original **45.6/100** and improved proposal **50.4/100**. These are engineering readiness judgments about the stated redesign objective, not reliability, certification or permission to connect a vehicle. All physical acceptance remains pending in both versions. The gain comes entirely from requirements, testability and scope.

| Criterion | Weight | Original /10 | Improved /10 | Reason and confidence |
|---|---:|---:|---:|---|
| Requirements clarity and research value | 10 | 4 | 6 | Better bench question; named unmet lab function still absent. Medium. |
| Six-path and three-domain fidelity | 10 | 8 | 8 | CAD terminal fidelity; original physical contact oracle pending. High source confidence. |
| Power-loss and transfer behavior | 12 | 4 | 4 | No measured release, gap, bounce or skew bound. Medium. |
| Fault detection and mitigation | 12 | 4 | 4 | Useful recognized-fault control with explicit single-fault gaps. High. |
| Analog integrity and DAC compatibility | 10 | 3 | 3 | Endpoint, reference, routing and validity unknowns remain. Medium. |
| Power sequencing and electrical margins | 8 | 4 | 4 | Conditional calculations; no assembled partial-power evidence. Medium. |
| Firmware and control authority compatibility | 8 | 2 | 2 | Compatible controller proposed, not implemented. High. |
| CAD integrity and reproducibility | 8 | 8 | 8 | Fresh checks pass; future capture provenance remains weak. High. |
| Manufacturability and maintainability | 6 | 5 | 5 | Assembly/harness/purchasing specification work remains. Medium. |
| Validation completeness and testability | 8 | 3 | 5 | Improved discriminating plan; zero completed physical acceptance. Medium. |
| Codex buildability and evidence discipline | 4 | 7 | 7 | Strong retained evidence; proposed guard repairs unimplemented. High. |
| Scope efficiency and cost of learning | 4 | 4 | 7 | Inventory/coupon branch avoids premature integration expense. Medium. |

Weights total 100. Weighted sums are 456 and 504; dividing by ten gives 45.6 and 50.4. The [independent committee](/Users/howeth/Desktop/codex/Hardware/MiLa/docs/reviews/2026-10-12/committee.md) held every electrical, fault, firmware and CAD score unchanged. Unknown factual inputs remain UNKNOWN; neither score overrides the stage gates.

## What the redesign gets right

The carrier preserves all eighteen used contact terminals and three control domains in the authored CAD. Compact, nonlatching Form-C contacts address the earlier SN3257 power-loss issue: healthy contacts eventually restore their NC connection without controller power. SN3257 instead isolates its signal terminals when unpowered; three packages can preserve grouping but cannot supply passive bypass. [TI SN3257 Rev D, section 8.3.4](https://www.ti.com/lit/ds/symlink/sn3257-q1.pdf).

Separating the supervisor from the carrier makes the inhibit/rearm contract reviewable. The physical feed interruption, rail monitoring, window watchdog and fresh zero-request ARM are useful controls within their stated assumptions. The existing models deliberately expose several residual faults rather than claiming that all faults are covered. These features justify a measured bench investigation, with healthy contacts and verified wiring.

Fresh [automated evidence](/Users/howeth/Desktop/codex/Hardware/MiLa/docs/reviews/2026-10-12/validation/fresh-validation.json) confirms:

- All 60 host tests pass.
- The carrier audit matches 18 contact terminals; supervisor verification matches 207 populated pins and checks nine intentionally unused pins.
- Both boards pass native KiCad 10.0.6 ERC and DRC, with zero violations, unconnected items or schematic-parity findings under their saved rules.
- All 69 tracked source/design files match the October 7 checkpoint, including all ten original-source files.

The existing carrier checker refreshed its derived connectivity report; the bytes match the retained release archive. No CAD or manufacturing exports were regenerated. **The 34 main physical procedures and 33 overlapping supervisor probes remain unperformed.** Automated checks do not establish relay timing, assembled behavior or endpoint acceptance.

## Ranked ways the design can fail

| Priority | Trigger and consequence | Evidence and disposition |
|---|---|---|
| Blocking integration | Unknown endpoint function or limits make the selected topology/rating inappropriate, particularly for K7/K8. | [Legacy analysis](/Users/howeth/Desktop/codex/Hardware/MiLa/docs/reviews/2026-10-12/02-legacy-nets.md), [K7/K8 analysis](/Users/howeth/Desktop/codex/Hardware/MiLa/docs/reviews/2026-10-12/08-k7-k8.md). Identify destinations and measured electrical/diagnostic envelope before a vehicle revision. |
| Critical measurement | Generated output collapses while NO remains selected; gap, bounce and pair skew occur before stable NC return. | [Transfer review](/Users/howeth/Desktop/codex/Hardware/MiLa/docs/reviews/2026-10-12/13-validation.md). Capture COMs, actual DAC rail and coil current; settled continuity is insufficient. |
| Critical coverage gap | DAC-only failure, stale codes or wrong-but-correlated outputs coexist with valid READY/WDI. PG5 monitors carrier feed, not independently powered DAC outputs. | [Analog and firmware exchange](/Users/howeth/Desktop/codex/Hardware/MiLa/docs/reviews/2026-10-12/debate-04-analog-firmware.md). Separate transaction acknowledgment, measured output validity and fresh command authority. |
| Critical residual fault | An individual driver shorts before ARM. With requests LOW, the first permission transition can still energize its relay. Q6 short can also defeat healthy Q5 automatic cutoff. | [Fault exchange](/Users/howeth/Desktop/codex/Hardware/MiLa/docs/reviews/2026-10-12/debate-05-k7-k8-faults.md). Inject separately on contained simulators; physical feed removal remains conditional manual mitigation. |
| Critical residual fault | NO weld, broken NC/COM, trace or harness open prevents default restoration despite coil cutoff. | [FMEA review](/Users/howeth/Desktop/codex/Hardware/MiLa/docs/reviews/2026-10-12/14-fmea.md). This architecture does not repair contact faults or provide automatic single-fault recovery. |
| High | An asserted request/permit conductor reconnects while feedback remains valid; retained ARM permits renewed selection. Short bundle chatter can also escape recognition. | [Connector exchange](/Users/howeth/Desktop/codex/Hardware/MiLa/docs/reviews/2026-10-12/debate-06-pcb-connectors.md). Test individual wires separately; prohibit powered harness service in the fixture. |
| High | Mixed connector order, reversed insertion or mistaken GPIO/header identity puts a signal on the wrong terminal, potentially including 5 V on logic. | [Mapping exchange](/Users/howeth/Desktop/codex/Hardware/MiLa/docs/reviews/2026-10-12/debate-10-legacy-firmware.md). Require photographed physical mapping and disconnected-cable continuity. |
| High empirical uncertainty | Abrupt partial-power sequences or asynchronous heartbeat/ARM edges produce behavior outside the Boolean model. | [Supervisor and power exchange](/Users/howeth/Desktop/codex/Hardware/MiLa/docs/reviews/2026-10-12/debate-03-supervisor-power.md). Favorable slow-ramp monitor ordering is analytical support; measure actual permission, coil current and contacts. |
| High implementation gap | The auto-sweep reference uses incompatible active-low requests and lacks READY/WDI/error/freshness handling. | [Firmware review](/Users/howeth/Desktop/codex/Hardware/MiLa/docs/reviews/2026-10-12/11-firmware.md). Create a separate guarded bench controller after the physical pin manifest; do not adapt by polarity inversion alone. |
| Future release risk | Python optimization removes assertion guards; accepted-layout capture can consume clean reports not bound to the current board. | [Evidence audit](/Users/howeth/Desktop/codex/Hardware/MiLa/docs/reviews/2026-10-12/17-audit.md). Use explicit rejection and fresh report/hash binding before another capture/release. This finding does not invalidate today's matched CAD. |

The source-ground-plane observation was narrowed during debate: the carrier's routed ground is an unmeasured margin, not a demonstrated layout defect. Parallel returns and hidden USB/scope grounds are concrete fixture conditions to control.

## Alternatives and what would change the choice

| Approach | What it offers | Decision |
|---|---|---|
| Retain original module | Lowest redesign effort and a direct comparison baseline. Its physical condition/contact behavior still needs verification. | Preserve it; instrument it on the same bounded fixture. |
| Current compact Form-C design | Passive settled NC connectivity with healthy contacts; original control grouping retained. | First bench baseline. Transfer, dwell behavior and full installed size remain empirical. |
| Three SN3257 devices | Smaller selectors and compatible control grouping. | Reject as a stand-alone replacement requiring zero-power continuity. |
| Form-B PhotoMOS plus complementary Form-A | Genuine normally-closed semiconductor continuity can exist at zero input drive. | Conditional separate experiment. Choose exact parts and establish loading, leakage and worst-case complementary collapse behavior. |
| Hybrid bypass or latching relay | May solve selected packaging/power problems. | Added branches, poles or reset energy bring new fault/transition requirements. No demonstrated advantage warrants development now. |
| Supported native Nissan CAN steering | Could eliminate analog steering substitution for a matching research objective. | Conditional scope reduction after exact vehicle/harness identification; current upstream steering support does not supply independent acceleration/braking. |

The semiconductor reviewer corrected a blanket rejection: [Panasonic AQY4C2PX](https://industry.panasonic.com/ap/en/products/control/relay/photomos/number/aqy4c2px) is a legitimate zero-drive NC candidate. The unresolved issue is its complete complementary changeover, especially when both drives collapse. A maximum switching delay alone does not establish earliest-versus-latest nonoverlap. Mechanical contacts likewise need first-transfer-after-dwell measurements, rather than inferred low-load lifetime. [Switching debate](/Users/howeth/Desktop/codex/Hardware/MiLa/docs/reviews/2026-10-12/debate-02-switching.md).

Upstream lists LEAF 2018–23 with ProPILOT Assist. Exact target support remains UNKNOWN. The pinned [Nissan controller](https://github.com/commaai/opendbc/blob/390618eef8be4462aebdfddb534d289b23684a23/opendbc/car/nissan/carcontroller.py) covers steering, cancellation and HUD. Direct ESP CAN or analog substitution remains outside panda's CAN enforcement; a DBC does not grant authority. [Current upstream vehicle table](https://github.com/commaai/openpilot/blob/master/docs/CARS.md).

## The better version and system sequence

The better version is an inventory-first physical investigation of the existing design. Use available inspected hardware before building more. If there is no assembled Rev A pair, a two-pole coupon keeps the exact relay, low-side driver, high-side cutoff/Q6, physical feed interruption and flyback. It answers transfer physics without claiming full-supervisor acceptance. The [revised proposal](/Users/howeth/Desktop/codex/Hardware/MiLa/docs/reviews/2026-10-12/improved-proposal.md) defines both branches.

For the integrated fixture, the intended sequence is:

1. Boot in BYPASS with requests LOW. The operator verifies assembly, cable orientation, passive paths, supply limits and physical interruption.
2. Validate rail/source identity and measured outputs. The later controller checks transactions, deadlines and command freshness; externally controlled READY suffices only for the initial manually supervised fixture.
3. Qualify compliant WDI and a new physical ARM edge with all requests LOW. Use the documented 30 ms falling-edge cadence; feeding every 10 ms can violate the watchdog's 10.35 ms lower corner. The 2 Hz CAN diagnostic is also unsuitable.
4. Issue bounded requests, keeping all three domains explicit. A detected first-iteration error immediately lowers requests/READY and prevents further WDI; it does not wait for three cycles or a watchdog timeout.
5. Fault/disable removes permission or physical feed. Instruments measure the actual selected-output exposure, decay, release and bounce through stable NC.
6. Recognized faults require renewed qualification and a fresh ARM. Individual reconnection and undetected chatter are separate limitations.

Thirty milliseconds is heartbeat scheduling, not an output-return guarantee. READY, ARMED and coil permission are also not contact-position feedback. MCP4728 startup/reset can recall EEPROM settings; programming RDY/BSY does not mean analog readiness. [Microchip MCP4728, sections 3.5 and 4](https://ww1.microchip.com/downloads/en/DeviceDoc/22187E.pdf).

## Failure and recovery limits

Healthy contacts return to documented NC paths only while the carrier and relevant conductors remain intact. Removing the carrier requires a separately verified simulator bypass plug. Welds/opens are unrepaired; manual feed removal assumes intact switch wiring and no alternate downstream source. K7/K8 01/10 joins both outputs to one source, without inherently bridging the two sources; external load impedance can still change currents and endpoint behavior. Pairing commands cannot eliminate mechanical skew.

The separate CAN diagnostic deserves a narrower claim: it enters Normal mode before ARM and can electrically ACK/error-participate. STOP blocks new submissions; no physical last-frame bound is established. Use an independently verified silent configuration for future passive capture, and test last-frame timing only on an isolated CAN fixture. [CAN and environment exchange](/Users/howeth/Desktop/codex/Hardware/MiLa/docs/reviews/2026-10-12/debate-07-can-environment.md), [MCP2515 sections 10.3 and 10.5](https://ww1.microchip.com/downloads/aemDocuments/documents/APID/ProductDocuments/DataSheets/MCP2515-Family-Data-Sheet-DS20001801K.pdf).

## Electrical cost and packaging assessment

The bare carrier is 60 × 50 mm; the supervisor is 80 × 60 mm. Their summed area is 7,800 mm², versus the original module's 6,929 mm² silkscreen rectangle. The carrier alone is about 57% smaller; the sum is about 13% greater. These unequal-function rectangles establish neither installed growth nor successful compactness. Compare complete installed envelope, clearance, switches, cable and equivalent supervision. [Requirements and economics exchange](/Users/howeth/Desktop/codex/Hardware/MiLa/docs/reviews/2026-10-12/debate-09-economics-requirements.md).

The pair has 93 circuit placements before external items. Exact suffixes and generic passive/header purchasing details need a frozen orderable BOM. As observed October 12, four relays, two selected physical switches and the watchdog total about $58 at quantity-one pricing, excluding remaining parts and delivery. The exact watchdog showed zero DigiKey stock with November 11 expected; displayed stock/dates are not commitments. [Sourcing memo and direct listings](/Users/howeth/Desktop/codex/Hardware/MiLa/docs/reviews/2026-10-12/16-economics.md).

The specialist's **$150–350 excluding instruments and 30–66 operator hours** are planning assumptions for one initial pair/fixture and selected acceptance, not a quote, full matrix estimate or authorized purchase. Inventory existing tools/assemblies first, then set a cash/hour cap. Supervisor sourcing can delay integration; the coupon avoids that dependency by excluding supervisor validation.

## Minimum prototype and deferred work

The minimum useful prototype includes a verified original comparison module if available, the exact two-pole relay/cutoff coupon or inspected Rev A, independently bounded default and generated sources, actual generated-output power interruption, known loads, a mapped retained fixture and suitable simultaneous capture. Preserve every raw trace and configuration. Before energization, issue a fixture worksheet with fitted identity, every return/probe connection, declared cold-dwell duration, measurement uncertainty and numerical provisional error/observation thresholds. Those screening targets and the cash/hour cap remain to be set after actual inventory; they are not inferred Nissan limits. The committee identified these as prerequisites omitted from the proposal, rather than completed work.

For now defer another integrated PCB spin, automotive supply/interface design, onboard ADC architecture, hold-up supply, new CAN gateway, PID/sweeps, custom Nissan longitudinal messages, automatic resume, and semiconductor conversion. Each requires either a measured failing condition or a named research need. The original hardware remains intact.

## Technical plan and Codex ownership

Keep carrier contacts free of new semiconductor/loading branches until requirements support them. Use fixtures and breakout access rather than repeatedly probing tiny pads. Verify fitted part orientation and hidden-pad assembly quality. Freeze design, BOM, export and assembly identity together before future fabrication.

| Owner | Exclusive scope |
|---|---|
| Requirements and harness agent | A six-path physical interface manifest and fixture/cable drawings in a new revision folder. |
| CAD integrator | Carrier/supervisor CAD, local libraries, both board generators and manufacturing exports; serialize all writes and native validation. |
| Model and test agent | `tools/passive_bypass_model.py`, host/CAD tests and checker behavior; separate ideal topology from timing assumptions. |
| Firmware agent | A new bench-only controller folder; explicit state machine, pin manifest, transaction/deadline/freshness behavior and validated-cycle WDI. |
| Evidence agent | Dated command records, explicit hash guards, bound report/manifests and trace metadata; no shared CAD mutation. |
| CAN agent | Silent-capture/physical-stop investigation in the separate diagnostic track; no DBW command authority. |
| Human bench lead | Assembly, source containment, wiring, instruments, fault injection, trace review and advancement signoff. |

Codex can prepare implementations, analysis and reproducible records. It cannot substitute for actual instrument connections, contact behavior or endpoint acceptance. Future proposed guard changes need mutation/stale-report rejection checks in disposable copies; no such changes were implemented here.

## First thirty days

| Week | Work and exit condition |
|---|---|
| 1 | Inventory actual modules/parts/instruments; define the lab question, provisional fixture limits and cash/hour cap. Produce physical connector/GPIO/DAC manifest and original contact oracle. Exit with unambiguous wiring and a qualified bounded fixture. |
| 2 | Run paired-contact request-off, high-side-off, physical-feed-off and supply-collapse captures, including first transfer after dwell. Retain at least 30 proposed phase-varied trials per case and compare the old module where available. Exit with measured extrema and a specific correction or justified continuation. |
| 3 | If exact supervisor hardware is available, test compliant startup/rearm, rail ramps, switch sequencing, bundle/single-wire and explicit driver faults. Otherwise continue coupon characterization and sourcing; award no supervisor credit. Exit with an identified assembly and reproducible scoped results. |
| 4 | Implement only the justified guarded bench controller; test DAC-only loss, EEPROM reset, wrong-but-ACKed codes, freshness/replay and loop stall. Repair provenance before any new capture/release. Review packaging and unmet requirements. Exit with a decision on a measured revision, further bench work or stopping. |

This is a dependency plan, not a promised hardware-completion date. No ECU/HIL or vehicle work enters the schedule while its requirements remain unknown.

## Fastest decisive test

Use distinguishable 1–4 V simulator sources through measured 10 kΩ resistors and 100 kΩ COM loads. Keep each signal/fault source at or below 1 mA. Default sources stay alive while generated/DAC power collapses. Verify suffix, orientation and all power-off continuity before energizing. The existing envelope is 20–30°C, carrier feed 4.75–5.25 V, carrier-only current limit 150 mA; the shared carrier/supervisor supply starts at 200 mA and arming requires at least 4.95 V at the returned carrier input. These documented fixture values do not authorize direct vehicle power or unverified USB/V5 combinations.

Capture COM-A, COM-B, actual DAC rail and coil current simultaneously on four analog channels, with digital stimulus/permission/health/ARM where needed. Use at least 1 MS/s for mechanical captures and separate suitably fast, low-capacitance probing for logic-boundary tests. Account for probe loading: a 1 MΩ probe can change this nominal divider by about 41 mV; a 10 MΩ probe by about 4 mV. Those errors can dominate the inferred contact effect.

Measure selected-dead-source duration, gap, bounce, pole skew, source currents and stable NC restoration. Record every trial and every failure. Repeat normal shutdown, total loss, DAC-only loss and independent rail collapse; then full-bundle and individual-wire tests on the integrated assembly. Fault-injected pickup is a residual to characterize; unexplained pickup in ordinary acceptance is a failure requiring physical-feed removal.

Within this fixture, grade low-current path error with stated uncertainty. **Do not claim the relay's supplier contact-resistance limit:** its catalog method uses 10 mA/1 V, outside the ≤1 mA signal fixture. A separately scoped component test would be a different activity. Thirty trials and provisional screening budgets do not establish lifetime or Nissan diagnostic tolerance. [OMRON G6K characteristics footnote 1](https://omronfs.omron.com/en_US/ecb/products/pdf/en-g6k.pdf), [validation debate](/Users/howeth/Desktop/codex/Hardware/MiLa/docs/reviews/2026-10-12/debate-08-validation-audit.md).

Stop for source-current breach, mapping mismatch, unexpected connection or pickup, lost physical-feed authority, unexplained backfeed, or component-limit excursion. Preserve traces before investigating. An invented universal 3 ms or 30 ms deadline is not an acceptance criterion; determine endpoint-specific allowable error and interruption before application grading.

## Kill and pivot criteria

- Stop ordinary fixture acceptance if any path differs from its physical oracle, default restoration fails, or an unexplained zero-request ARM causes pickup.
- Revise the measured topology if its transfer/error/dwell behavior violates a predeclared fixture requirement. Block application advancement if it violates the independently established endpoint limits.
- Pivot away from this unchanged selector if actual paths require actuator current, incompatible default/mixed states, automatic recovery from contact weld/open, or automatic coverage of every single-wire reconnect.
- Reject the miniaturization investment if the measured equal-function installed envelope misses the sponsor's size target or required assembly/test effort exceeds its explicit cap.
- Stop further integration if supported native control already satisfies the named lab experiment and analog substitution adds no needed capability.
- Reject a future release/capture whose exact files and fresh validation cannot be bound to its assembly/export identity.

Unknown requirements are blockers for application acceptance. They do not automatically kill a safe, bounded characterization experiment.

## Questions that decide the next stage

| Rank | Unknown | Evidence needed |
|---|---|---|
| 1 | Named research task and required command authority | Lab objective plus exact supported native-control comparison. |
| 2 | Actual K3–K8 endpoints, including K7/K8 function/default meaning | Authoritative wiring, physical tracing, exact part identity and measured current/voltage/impedance. |
| 3 | Allowed error, pair correlation, interruption and fault-response times | Endpoint specification and qualified ECU-simulator/diagnostic evidence. |
| 4 | Old contact oracle and actual controller/DAC routing | Original-module continuity, photographed header map and one-channel-at-a-time fixture identification. |
| 5 | Actual transfer, dwell and partial-power behavior | Raw simultaneous source/COM/coil/rail traces from identified fitted parts. |
| 6 | Existing assembly/instrument inventory and complete compactness/cost benefit | Physical inventory, equal-function installation measurements and sponsor cash/hour limits. |
| 7 | Vehicle identity/harness and environmental profile | Model/year/market/ADAS/harness revision, mounting/use profile and measured interface envelope. |

## Team findings and remaining dissent

All 18 independent memos and 10 actual challenge outcomes are retained in the [review evidence index](/Users/howeth/Desktop/codex/Hardware/MiLa/docs/reviews/2026-10-12/README.md). Seventeen specialists selected PROTOTYPE FIRST; the adversarial specialist selected KEEP EXISTING HARDWARE with a bounded experiment. Debate reconciled these into retaining the comparison hardware and avoiding an unnecessary full-pair build. Hardware availability remains unknown.

The main accepted corrections were: unequal-function area is not installed-size proof; Form-B can supply genuine zero-drive continuity; static zero-current inspection can miss a shorted driver until ARM; a 30 ms watchdog cadence is not a return-time guarantee; mechanical ground-plane observations are not confirmed failures; and future provenance vulnerabilities do not invalidate freshly matched Rev A data.

Conditional dissent remains about the eventual switch technology: PhotoMOS could be preferable if measured contact behavior or the installed size target fails and an exact pair's electrical/transfer bounds are substantiated. Reviewer agreement closes interpretation, not physical unknowns. The [committee assessment](/Users/howeth/Desktop/codex/Hardware/MiLa/docs/reviews/2026-10-12/committee.md) independently evaluates the revised plan and scores.

## Decision on further work

**YES to spending a capped amount of time and money on the isolated transfer investigation.** It answers the most consequential physical question using current design structure and a preserved comparison. Inventory first; use existing assembled hardware if suitable, otherwise the exact-topology coupon. Spend on evidence before integration.

**NO to vehicle integration or a production redesign on the current evidence.** Actual endpoint functions, limits and behavior remain undefined, physical acceptance is absent, and the design has explicit contact, semantic-output and cutoff fault limitations. The next worthwhile milestone is measured transfer behavior and a concrete lab requirement, followed by a separate vehicle-specific engineering decision.
