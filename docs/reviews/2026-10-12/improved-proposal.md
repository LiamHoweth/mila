# MiLa revised bench investigation proposal

Continue a bounded physical investigation of the current passive-bypass concept, preserve the old module for comparison, and freeze Rev A circuit structure until measurements identify a specific change. The research question is whether the actual compact nonlatching relay, cutoff and flyback arrangement provides useful low-current transfer behavior under supply loss. A successful fixture measurement does not establish Nissan acceptance.

## Original baseline and revised scope

The original scored concept is the current unmodified four-relay carrier plus hardware supervisor, not the superseded two-SN3257 proposal. The revised proposal changes sequencing, fixture acceptance and evidence discipline. It does not claim better completed physical validation or implemented fault coverage.

Inventory actual assemblies, instruments and exact parts first. If an assembled Rev A pair exists, inspect it and use it after pre-power acceptance. If none exists, characterize one exact two-pole G6K relay with AO3400A low-side drive, AO3401A/Q6 high-side cutoff, physical series interruption and the installed diode suppression. Do not assemble the 93-part pair merely to learn relay-transfer physics. The coupon does not test supervisor startup, window timing, interboard wiring or full six-path faults.

Define a named lab experiment and six-path interface worksheet before investing in a vehicle revision. Identify functions, connector destinations, GPIO/DAC channels, voltage/current/impedance/reference, permitted states, correlation and response limits. Keep missing values UNKNOWN. Measure a complete installed envelope against an equal-function baseline; carrier area alone does not prove system compactness. The old module's 133.25 by 52 mm rectangle is silkscreen, not a measured enclosure or courtyard.

## First experiment and assembly gates

Keep all endpoints isolated simulators: 0–5 V and at most 1 mA per signal/fault path, regulated fixture rails, documented room-temperature scope. Independently maintain default sources and interrupt actual generated-output power. Verify original NC/NO contact order, relay suffix/orientation, every adapter endpoint, both grounds and returned carrier feedback before powering.

Use distinct source levels through measured 10 kΩ resistors and 100 kΩ COM loads. Account for additional loads, probe resistance/capacitance and hidden USB/scope returns. Within the ≤1 mA fixture, characterize low-current path error and repeatability; do not claim equivalence to the manufacturer's 10 mA/1 V contact-resistance method. Observe first transfer after dwell before higher-energy contact conditioning.

Capture both COMs, actual DAC rail and coil current together. Use digital channels for requests, permission, health and ARM on integrated tests. Test request-off, high-side inhibit, physical feed removal and supply collapse separately; add DAC-only collapse and independent rail ramps. Record interruption, invalid selected-output interval, bounce, skew and stable NC return. Thirty phase-varied trials per case are proposed screening, not demonstrated reliability. Retain all raw traces and failed trials.

Then test the integrated supervisor with synthetic compliant WDI and externally verified/operator-controlled READY. Require valid levels at the watchdog pin and its documented 30 ms cadence; a 100 Hz loop or the CAN diagnostic's 2 Hz frames are not equivalent heartbeat service. Valid-protocol startup/rearm is tested before malformed pulse/race boundaries. Test individual-wire reconnect separately from recognized whole-bundle loss and measure ENABLE pole sequencing.

## Explicit faults and controller boundary

Add separate contained fault cases for Q6 drain-source short, permission stuck HIGH, and an individual driver short before the first zero-request ARM. A shorted driver can be hidden while the coil rail is inhibited; zero requests and zero pre-arm coil current do not prove driver health. Observe the first permit transition. For intentionally injected faults, characterize the expected residual and prove physical-feed authority; unexplained pickup during fault-free operation is a stop condition.

Do not retrofit the automatic-sweep sketch. A later separate bench controller must default LOW/BYPASS, validate initialization and each completed iteration, enforce command freshness, lower READY/requests on the first failure, cease WDI and require manual requalification. ACK, register readback, EEPROM programming status, actual output volts and authorized intent remain distinct checks. External measurement is sufficient for the first supervised fixture study; it is not continuous autonomous output protection. PG5 does not diagnose a separately powered DAC-only failure.

Keep CAN diagnostics isolated. The current diagnostic starts in Normal mode and may ACK/error-participate before ARM; STOP halts new queue submissions but has no verified last-frame bound. A later passive capture needs independently verified silent mode. Supported native Nissan steering could reduce analog scope only after exact vehicle/harness/objective identification; it does not supply independent longitudinal actuation.

## Evidence and advancement

Fresh October 12 evidence: 60 host tests, 18 contact-terminal audit, 207 populated supervisor pins/9 unused pins, and both native ERC/DRC/parity runs pass. Sixty-nine tracked source/design files match the earlier checkpoint. The carrier checker refreshes a derived audit whose bytes match the retained release archive. All 34 main physical procedures and 33 overlapping supervisor probes remain pending.

Before a future routing capture or release, replace assertion-only rejection guards and bind fresh native reports to exact input/output hashes. Complete the manufacturing payload manifest and exact purchasing BOM. These weaknesses do not invalidate the currently matched Rev A files or require an immediate circuit redesign.

Advance only against evidence: useful coupon result → full fixture acceptance → scoped guarded-controller validation → identified endpoint/ECU simulator requirements → a separate vehicle-specific interface and environmental review. No current score overrides an unknown safe state or missing physical acceptance. If the research function needs automatic single-fault recovery from welded/open contacts, every reconnection, or real actuator currents, this unchanged signal-selector architecture is inadequate.

## Decision and budget

The tentative combined recommendation is PROTOTYPE FIRST for the isolated investigation, with the original module retained. The adversarial KEEP EXISTING HARDWARE position is compatible with a coupon or an already available inspected Rev A assembly; it defers further integration spending. Form-B PhotoMOS remains a conditional alternative if measured mechanical contact behavior or installed size fails the objective, and an exact complementary pair's timing/loading can be substantiated.

The sourcing specialist's $150–350 and 30–66 operator-hour ranges are assumptions for an initial pair/fixture and scoped acceptance using existing instruments, not a quote or full-matrix completion estimate. A displayed zero-stock exact watchdog threatens a new supervisor's schedule. The inventory-first coupon branch avoids that dependency while providing no supervisor-validation credit. Set a concrete cash/time cap after inventory rather than approving an open-ended redesign.
