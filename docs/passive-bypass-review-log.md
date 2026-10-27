# Passive-bypass design review log

2026-10-07. Scope: complete isolated bench reference, not a vehicle release.

The supplied multi-agent prompt contained a blank idea field and commercial-app
roles. The user asked for a complete solution to the MiLa power-off issue; the
review process was applied to that circuit with twelve engineering specialists.

## Round 1 — independent evidence

| Specialist | Independent finding incorporated |
|---|---|
| Requirements | NC restoration depends on healthy contacts and retained harness; continuity alone is insufficient |
| Raw-net audit | Schematic and PCB agree; used K3–K8 and three domains confirmed; NC/NO names remain inferred |
| Signal relays | Nonlatching G6K selected for simulator; library NC row wrong by 0.2 mm |
| Power relays | Automotive power-relay minimum loads are unsuitable for sensor fallback; K7/K8 could drive a motor when unpowered |
| Semiconductor bypass | True zero-drive NC semiconductor exists; paired NC/NO nonoverlap is the difficult guarantee |
| Hybrid | Parallel NC bridge around SN3257 leaves off-voltage exposure and source-contention counterexamples |
| Supervisor | Independent rail/window-watchdog clear plus manual edge arm; heartbeat qualification needed after READY |
| Drivers | Gate defaults, loaded VOH and high-side orientation need explicit bounds; flyback lengthens restoration |
| PCB | Compact block cannot occupy all original 133 mm interface pad positions; separate wired simulator board chosen |
| Validation | Model OPEN/bounce/skew/stuck cases; finite dead-DAC interval is a required physical test |
| FMEA | NO weld/COM open/common faults defeat broad fail-safe claim; separate cutoff handles individual driver short |
| Firmware integration | Legacy sweep has no matching guard contract; GPIO15→J4-4 does not demonstrate J4-23 control |

## Round 2 — competing architectures

The semiconductor and hybrid reviews challenged the assumption that passive
semiconductor bypass is impossible. It is possible with Form-B isolated parts
or depletion devices. The direct relay baseline was retained because it supplies
changeover and zero-power default with fewer independently timed elements.
This is a scope/guarantee decision, not a claim that mechanical contacts solve
all single faults or that solid-state bypass cannot work.

The raw-net and power-load reviews challenged pairing K7/K8. The reference
preserves both independent controls. Mixed states are characterized rather than
called intrinsically forbidden; paired mechanical poles still have timing skew.

Requirements and FMEA challenged an overly broad definition of bypass. The
claim was narrowed to eventual NC restoration with healthy nonlatching
contacts, intact wiring and no downstream coil-energy source. A separate
simulator bypass plug covers removal of the carrier.

## Round 3 — concrete implementation corrections

- Four identical G6K-2P-Y DC5 packages preserve the three domains. Two spare
  poles remain physically unconnected.
- Corrected footprint longitudinal positions: 0 / 3.2 / 5.4 / 7.6 mm, opposing
  columns 5.08 mm. The original generic library's 3.0 mm NC row is not reused.
- Gate biases tightened from 100 kΩ to 10 kΩ. Series gates changed to 330 Ω;
  loaded request HIGH ≥2.60 V gives ≥2.517 V gate voltage.
- A 5 V AHCT permission buffer meets the load-driving requirement without
  assuming an unlisted 3.3 V LVC VOH guarantee.
- Heartbeat qualification requires two falling edges after READY and health
  qualification, not just a static level or a pre-READY heartbeat.
- Faults clear the arm latch; held ARM does not re-arm on recovery.
- Replaced self-powered G50 with G01 divided-SENSE monitor: diode-OR supply
  from both rails keeps PG5 observation alive when only controller 3.3 V
  remains, while avoiding an out-of-range SENSE/VDD partial-power condition.
- Increased the final AHCT output series resistor to 1 kΩ to bound capacitive
  gate charging; the calculated loaded carrier gate still exceeds 3.07 V.
- Source containment changed to 10 kΩ per simulator source, with 100 kΩ loads;
  the earlier 1 kΩ suggestion did not satisfy the ≤1 mA fixture fault envelope.
- No bulk capacitor or external energy source is placed downstream of the
  coil cutoff. Its single P-FET does not claim reverse-current blocking.
- Plain flyback diodes are an explicit first-test choice. Release/bounce timing
  remains a measurement, not the relay's unsuppressed catalogue value.

## Round 4 — integrated challenge and validation

Independent specialists reviewed the assembled design and exported CAD.
The root agent reconciled the findings, ran model and CAD checks, and inspected
the final drawings. The accepted results are recorded below.

This round found and corrected an actual rail-observation gap: a G50 powered
from the failing 5 V rail could leave RESET undefined at zero supply while
3.3 V remained live. A G01 divider monitor supplied through an isolated
diode-OR from both rails preserves observation of that fault and respects
SENSE/VDD ordering. Arming now explicitly requires at least 4.95 V; the
carrier 4.75 V lower operating limit does not guarantee monitor recovery.

The supervisor flip-flop pipeline also received a small Schmitt-buffered
1 kΩ / 100 pF delay to give stage-two D positive hold margin, rather than
assuming minimum clock-to-Q exactly equal to minimum hold establishes margin.
Valid clock/reset pulse widths and asynchronous-clear recovery/removal still
require actual timing verification.

Closure criterion: no remaining correctable mapping, schematic, footprint,
logic-contract or CAD consistency issue within the stated bench scope. Missing
physical requirements remain visible measurement gates; a passing ideal model
or ERC/DRC is not substituted for hardware evidence.

## Round 5 — reconnect and brownout counterexamples

FMEA identified a real reconnect counterexample: while the upstream supervisor
remained powered and armed, removal/reinsertion of a carrier connector could
restore the previous request without a new ARM edge. The final interface adds
returned carrier `5V_RAW` through JCTRL1-6 to supervisor J5-7. PG5 now senses
that returned post-physical-enable feed instead of merely upstream 5 V.
Sustained loss of either complete carrier connector therefore clears the latch.
The filter/detector response must be measured; brief chatter and individual
request/permission-wire interruptions with feedback intact remain outside
universal reconnect inhibition.

The driver reviewer also challenged the AHCT output's defined-voltage range:
below 4.5 V its output is unspecified even if the relay can still remain held.
The final permission stage returns to 3.3 V LVC logic, with 82 kΩ header/gate
pulldowns keeping static load below the manufacturer's 100 µA VOH condition.
This preserves permission control when monitored 5 V falls while 3.3 V stays
healthy. All four request-driver pulldowns remain 10 kΩ. Whole-rail sequencing,
leakage and coil release are still measured acceptance gates.

External held-enable and ARM switches now have exact manufacturer selections,
terminal maps and an off-board BOM. No assumed generic switch pinout is used.

## Final closure — 2026-10-07

The twelve specialist reviews and five review rounds are closed for the
isolated simulator scope. No remaining correctable circuit, mapping, footprint,
logic-contract or CAD consistency issue was identified in that scope.

- Carrier: 60 × 50 mm, two layers, four nonlatching relay packages. Native
  ERC, DRC, unconnected-item and schematic-parity results are all zero.
- Supervisor: 80 × 60 mm, two layers, 64 circuit parts plus four mounts.
  Native ERC, DRC, unconnected-item and schematic-parity results are all zero.
- All recorded fabrication/export commands completed successfully. The
  supervisor's accepted routing is retained separately from exploratory
  routing-search failures; native connectivity is the acceptance criterion.
- The root host run passed 60 tests: 41 ideal behavior/counterexample tests,
  three retained-source/carrier CAD tests, twelve independent supervisor XML
  tests and four existing CAN payload tests. The XML tests evaluate 512
  settled Boolean combinations and the final loaded permission-drive bounds.
- The original eighteen contact terminals match the authored carrier mapping.
  SHA-256 checks confirm ten original KiCad source/library files are unchanged.
- Final schematic, top/bottom copper and assembly previews were inspected.
  Exact switches, interboard feedback, current-limited fixture sources and
  assembly/first-power-up instructions are documented.

`hardware/review_evidence/` holds the root checks and preservation manifest;
each board also retains its own native reports, command record and fabrication
files. CAD checks use the projects' recorded rules, with no individual ERC/DRC
exclusions. They do not establish physical operation or component-fault coverage.

The 34 main physical procedures remain NOT_RUN, and the supervisor's 33 focused
probes remain PENDING. These overlap; they are not 67 measured results. Actual
coil cutoff, permission leakage/partial rails, relay release/bounce, long dwell,
asynchronous edges, contact faults, reconnect timing and source plausibility
remain acceptance gates. K7/K8 physical function and the Nissan-specific
required response remain unresolved. This is a complete bench reference and
fabrication package, not a vehicle installation release.
