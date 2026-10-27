# MiLa passive bypass — revision A design

Date: 2026-10-07. Status: **isolated, current-limited signal-simulator prototype**.
This is a complete reference circuit for investigating the power-loss bypass
problem. It is not a Nissan production design or vehicle installation release.

![Circuit and interboard overview](/Users/howeth/Desktop/codex/Hardware/MiLa/hardware/review_evidence/design_overview.png)

## Decision and scope

Replace the powered analog-switch proposal with nonlatching mechanical Form-C
contacts. With intact wiring and healthy contacts, loss of coil energy returns
COM to NC without MCU power, DAC power, a battery, or a working regulator.
The transition takes time; it is not an uninterrupted signal transfer.

Build two separate modules:

1. `hardware/passive_bypass_rev_a/`: compact passive contact carrier, four relay
   drivers and a separately controlled high-side coil cutoff.
2. `hardware/passive_bypass_supervisor_rev_a/`: rail supervision, hardware
   window watchdog, heartbeat-seen and manual-arm latches, and coil permission.

The contact carrier remains in the signal path when controller electronics are
unplugged. Removing the contact carrier itself opens the intercepted paths.
Use the explicit bypass plug below for that case.

The six contact paths are reproduced for **simulator characterization only**.
In particular, K7/K8 are default-path selectors of unknown physical function.
No claim is made that their NC state is stock bypass, motor-off, or safe braking.

## Prototype operating envelope

| Quantity | Revision A limit / contract |
|---|---|
| Contact sources | Independently current-limited 0–5.0 V simulators |
| Contact path current | At most 1 mA, including fixture faults |
| Initial source containment | 10 kΩ series at every source; 100 kΩ simulated loads |
| Coil input | Regulated 5.0 V nominal; carrier 4.75–5.25 V; no vehicle power |
| Supervisor arming supply | At least 4.95 V for threshold/hysteresis margin; 4.75 V may inhibit |
| Coil carrier supply limit | 150 mA, room-temperature prototype |
| Shared carrier + supervisor supply | Start at 200 mA; investigate unexpected limit activation |
| Test temperature | 20–30°C; purchased relay revision must be reconciled |
| Requests | Active-high; 0–5.25 V allowed; nominal 3.3 V, HIGH ≥2.60 V |
| Coil permission | Dedicated supervisor-generated 3.3 V logic |
| Signal references | Fixture references outside carrier; no signal-to-logic-ground clamp |

Series source resistors are fixture containment, not proposed vehicle sensor
impedance. Account for the 10 kΩ / 100 kΩ divider when assessing output voltage.
At a 5 V source feeding one 100 kΩ load, nominal output is 4.545 V.
In K7/K8 mixed states one source feeds two loads, giving 50 kΩ effective
load and 4.167 V nominal output. Account for that change rather than treating
it as relay resistance. A 5 V short through 10 kΩ is limited to 0.5 mA.
Near-zero signals do not establish contact wetting/lifetime.

## Exact contact architecture

Use **four G6K-2P-Y DC5**, not the latching G6KU variant. Two packages use both
poles and two use one pole each. The spare poles are unconnected. This retains
three independent control domains while using one consistent prototype part.

| New relay/pole | Existing path | COM | NC/default | NO/selected | Request |
|---|---|---|---|---|---|
| RLY1 A | K3 | J4-14 | J4-13 | J5-10, DAC VB | REQ_GROUP |
| RLY1 B | K4 | J4-15 | J4-12 | J5-11, DAC VA | REQ_GROUP |
| RLY2 A | K5 | J4-16 | J4-11 | J6-8, DAC VD | REQ_GROUP |
| RLY2 B | K6 | J4-17 | J4-10 | J6-9, DAC VC | REQ_GROUP |
| RLY3 A | K7 | J4-18 | J4-9 | J4-8 | REQ_K7 |
| RLY4 A | K8 | J4-19 | J4-8 | J4-9 | REQ_K8 |

The original relay-module COM/NC/NO names were inferred from its photographed
silkscreen. The original hardware must confirm them. The new relay pin map is
verified against the manufacturer's drawing:

| G6K pin | Function |
|---|---|
| 1 / 8 | Coil positive / negative |
| 3 / 2 / 4 | Pole A COM / NC / NO |
| 6 / 7 / 5 | Pole B COM / NC / NO |

The manufacturer specifies a nominal 237 Ω, 21.1 mA 5 V coil. Use the
project-local footprint checked against the drawing: longitudinal pin rows at
0, 3.2, 5.4 and 7.6 mm, opposing columns 5.08 mm apart. The installed generic
footprint's 3.0 mm NC row was corrected to 3.2 mm. These are bench part choices,
not automotive-control qualification. [G6K manufacturer datasheet](https://omronfs.omron.com/en_US/ecb/products/pdf/en-g6k.pdf)

Each passive route has only connector, copper, and mechanical contact:

```text
                          NC ─── original/default source
                          /
destination ─── COM ─── changeover
                          \
                          NO ─── generated/alternate source
```

Do not attach unpowered ADC inputs, mux pins, clamp diodes, or indicator LEDs
to these signal nets. Such branches could defeat the loading/back-powering
benefit even though the relay itself is isolated.

## K7/K8 truth table

| REQ_K7 | REQ_K8 | J4-18 source | J4-19 source |
|---:|---:|---|---|
| 0 | 0 | J4-9 | J4-8 |
| 0 | 1 | J4-9 | J4-9 |
| 1 | 0 | J4-8 | J4-8 |
| 1 | 1 | J4-8 | J4-9 |

Mixed states put both outputs on one source. They do not inherently short the
two sources together. If the sources are opposite motor supply rails, 00 and
11 apply opposite polarities and the mixed states may implement braking.
Therefore neither pairing nor prohibiting the mixed states is justified yet.
One DPDT relay would also have physical pole skew and bounce.

## Coil driver and independent cutoff

For each of four coils:

```text
COIL_5V ───────── relay coil ───────── AO3400A drain
          │                      │         source ─── LOGIC_GND
          └── 1N4148 flyback ─────┘
              cathode at COIL_5V

request ── 330 Ω ── gate
                       │
                     10 kΩ
                       │
                   LOGIC_GND
```

Each flyback diode is local to its coil. A plain diode was selected for the
first simulator prototype; its slower release is an explicit test variable.
No 3 ms all-condition release guarantee is claimed for the assembled circuit.

The separate coil feed is:

```text
5V supply ── physical series ENABLE contact ── AO3401A source
                                                    drain ── COIL_5V
                                                    gate
                                                      │
                                        10 kΩ to source
                                                      │
                                           AO3400A drain
                                           source ── GND
supervisor COIL_PERMIT ── 330 Ω ── gate
                                      └── 82 kΩ ── GND
```

An absent permission signal leaves the high-side P-FET off. A shorted
individual low-side driver can still be released by opening the high-side
cutoff or physical coil-feed contact. An upstream cutoff short is outside
that single mechanism; low-side requests still provide a separate normal
release path. Neither switch is contact-fault redundancy.

No supply connector or bulk capacitor is permitted on `COIL_5V`. Bulk supply
decoupling belongs upstream of the physical/circuit cutoff. The single P-FET
is not a reverse-current blocker: its body diode permits backfeed from an
externally energized downstream coil rail. Such a source is excluded.

At ≥2.60 V input, the nominal 330 Ω / 10 kΩ gate divider produces
≥2.517 V (about 2.515 V at the stated 1% resistor corners). AO3400A
has a specified 48 mΩ maximum at 2.5 V gate drive under its stated conditions.
AO3401A has 60 mΩ maximum at −4.5 V. At nominal four-coil current 84.4 mA,
the shared switch drop is approximately 5.1 mV; each low-side drop is about
1.0 mV. These are room-temperature design calculations, not measured losses.
[AO3400A](https://www.aosmd.com/sites/default/files/res/datasheets/AO3400A.pdf),
[AO3401A](https://www.aosmd.com/sites/default/files/res/datasheets/AO3401A.pdf)

At 5.25 V and 10% low coil resistance, four coils draw about
`4 × 5.25 / (237 × 0.9) = 98.5 mA` at the stated reference temperature.
The current limit includes margin and is not an automotive-temperature budget.
The combined supervisor/carrier loads a 3.3 V GROUP request by roughly
0.97 mA and each independent request by roughly 0.65 mA. Verify header HIGH
under this load. The carrier input tolerance does not authorize applying 5 V
to a connected ESP32 pin.

The permission output uses 82 kΩ pulldowns on the supervisor header and
carrier Q6 gate, with 1 kΩ output-series and 330 Ω gate-series resistors.
This keeps its settled load below the LVC gate's 100 µA VOH test condition.
It removes the earlier 5 V AHCT output's unspecified behavior below 4.5 V
while controller 3.3 V remains healthy. Permission gate voltage, leakage,
discharge time and partial-rail sequences remain assembled-board tests.
[TI LVC1G08-Q1](https://www.ti.com/lit/ds/symlink/sn74lvc1g08-q1.pdf)

## Supervisory contract

The separate supervisor implements a hardware fault-clearable arm latch:

```text
3V3 good ──┐
5V good ───┤
reset good ┤
window WD ─┼── qualified ── asynchronous clear of all three latches
READY ─────┤                              │
deadman ───┘                              ├── HB_ONE → HB_GOOD
                                          └── ARMED

two qualified falling WDI edges ── clock HB_ONE → HB_GOOD
physical ARM rising edge ── clock ARMED
ARMED D input = HB_GOOD AND all three requests inactive
COIL_PERMIT = ARMED AND qualified
```

The component-level schematic and exact connector map in the supervisor
directory are authoritative. The watchdog is TPS3430-Q1; rail monitors are
TPS3808G33-Q1 and TPS3808G01-Q1; digital latches provide two-edge heartbeat qualification and
explicit arm state. A lightly loaded 3.3 V LVC output drives the carrier
permission input independently of the monitored 5 V rail.
[TPS3430-Q1](https://www.ti.com/lit/ds/symlink/tps3430-q1.pdf),
[TPS3808](https://www.ti.com/lit/ds/symlink/tps3808.pdf)

Two falling WDI edges after health/READY qualification establish one full
watchdog cycle before ARM can be accepted. All health/READY/deadman/reset
failures clear both heartbeat qualification and arm. A held ARM button cannot
re-arm after a fault clears within the valid voltage/timing contract: a fresh clock edge is required. Requests must be
low at the arm event. Flip-flop setup/hold and asynchronous-clear recovery/removal must be checked
against actual clocks, fault edges and switch bounce; the Boolean model alone
does not establish these timing margins.

Watchdog timing is a bench configuration, not a derived
Nissan fault-response allowance. READY is an external assertion; this module
does not independently prove DAC voltage, command intent, or correlation.

The 5 V monitor uses a 100 kΩ / 9.53 kΩ divider into G01 SENSE and a
diode-OR supply from both rails. Its divider senses the carrier's actual
post-physical-enable input through a dedicated returned wire. This keeps the monitor alive when 5 V
disappears but USB/controller 3.3 V remains, while also respecting SENSE/VDD
ordering when only 5 V is present. See its exact diode, threshold-tolerance
and supply-sequencing contract in the supervisor README.

The heartbeat stages include a 1 kΩ / 100 pF delay followed by a Schmitt
buffer. This provides positive same-clock hold margin between the stages;
actual timing must include component tolerance and routed clock skew.

The physical enable must open the actual coil feed, not merely inform firmware.
An auxiliary contact informs the supervisor; its opening clears all three latches.
An MCU-generated READY or heartbeat can falsely remain valid after a semantic
software error. Only feed the watchdog after a complete validated control cycle.

## Transfer and power-loss behavior

| Event | Intended response | Remaining exposure |
|---|---|---|
| Cold boot / reset | Coils disabled; fresh heartbeat, READY and manual arm required | Actual partial-power behavior must be tested |
| Watchdog timeout / too-fast heartbeat | Hardware permission drops and arm clears | Does not detect incorrect commands with valid timing |
| Physical enable released | Coil energy feed physically interrupted | Coil decay, mechanical release and bounce remain |
| MCU rail fails | Supervisor inhibits permission | Backfeed and rail ordering need bench evidence |
| Total power loss | Healthy contacts settle on NC without any reserve supply | DAC may collapse while contacts still select NO |
| Power restored after a recognized supervisor fault | Remains disarmed until fresh qualification and ARM edge | Brief undetected chatter is outside this claim |
| Entire controller/carrier power or control connector removed | NC carrier remains inline; feedback/health loss clears arm after detection | Individual broken signal wires are not all detected; entire carrier removal requires bypass plug |

Total fault exposure is `detection + cutoff + coil decay + mechanical release
+ contact bounce`. Measure every term with the actual clamp and loads.
Power-off NC continuity alone does not pass the transition test.

A reserve supply for generated outputs could bridge measured transfer time,
but is not part of revision A and does not cover a failed DAC/regulator/ground.
It cannot be sized honestly until output load, decay and acceptable transition
are measured. Indefinite bypass comes from NC contacts, not retained energy.

## Module interconnection and removal bypass plug

These two boards have different connector orders; they are not plug-compatible.
Wire the following explicit cable, including both common-ground destinations:

| Supervisor J5 pin | Function | Carrier endpoint |
|---:|---|---|
| 1 | Logic ground | JPWR1-2 and JCTRL1-5 |
| 2 | 5 V after physical enable | JPWR1-1 |
| 3 | Coil permission, 3.3 V logic | JCTRL1-4 |
| 4 | GROUP request | JCTRL1-1 |
| 5 | K7 request | JCTRL1-2 |
| 6 | K8 request | JCTRL1-3 |
| 7 | Returned carrier input, 5 V sense | JCTRL1-6, tied to carrier 5V_RAW |

The fixture headers are exposed bench headers. Confirm pin 1/orientation and
all cable continuity before power, add strain relief, and do not describe them
as a keyed automotive harness interface.

Route feedback through the carrier control connector. Do not locally link
supervisor J5-7 to J5-2; that defeats connector-loss detection. It is a 5 V
sense conductor, never an ESP input. Complete connector loss must last long
enough for SENSE filtering and monitor recognition to clear the arm latch.
Start characterization with 100 ms removals, then measure the minimum duration.
An individual request or permission wire can disconnect and reconnect while
feedback remains valid; this revision does not detect every single-wire fault.

The supervisor's `external_bom.csv` specifies separate physical held-enable
and ARM switches with exact terminal wiring. Inspect each real switch's
continuity, insulate unused terminals, and verify bounce and contact sequencing.


The disconnected simulator harness can use a separate orientation-verified simulator plug containing
only these passive links:

`J4-14↔13`, `J4-15↔12`, `J4-16↔11`, `J4-17↔10`,
`J4-18↔9`, `J4-19↔8`.

The K7/K8 links reproduce documented default connectivity only. They are not
authorized vehicle bypass wiring. Verify every plug pin and isolation from
other nets; the carrier's header CSV gives the physical pin positions.

## Bench stimulus and first power-up

The hardware can be characterized before writing a controller. Use an isolated
bench stimulus source for WDI and manual 3.3 V logic for READY, reset and
requests. Set WDI to a measured 0–3.3 V square wave with 30 ms period; no
negative level. This synthetic heartbeat tests the circuit only. A real
controller must instead implement the guarded-cycle contract below.

The fixture parts/equipment are listed in
`hardware/review_evidence/fixture_bom.csv`. Standalone tests use a separate
fixture 3.3 V supply. For a later real ESP test, use its physically verified
shared rail and remove the separate fixture source; do not parallel the two
supplies. Include actual source impedance and probe loading in measurements.

1. With all supplies removed, verify assembly, connector/switch continuity,
   six NC paths, open NO paths and signal-to-logic isolation. Verify both
   interboard ground wires and returned-feed routing point by point.
2. Keep all requests and READY LOW. Apply regulated 5 V and shared 3.3 V
   fixture supplies; verify actual rail voltages and disabled coils before
   attaching signal sources. For arming, deliver at least 4.95 V to the
   returned carrier input and observe stable monitor recovery.
3. Use ten independently current-limited source nets: four stock/default
   sources, four DAC/alternate sources, and J4-8/J4-9. Fit 10 kΩ source
   resistors and a 100 kΩ load on each of six COM outputs. Provide controlled
   fixture references outside the carrier. Use distinct measured source
   levels to identify selection and calculate single/dual-load attenuation.
4. Hold physical ENABLE, supply valid WDI timing and raise READY after fixture
   outputs are verified. Wait through recovery and two qualified falling
   WDI edges. Keep requests LOW for at least 1 ms before pressing ARM.
   Confirm ARMED, permission and disabled requested coils before changing
   any request. Release ARM long enough to return its clock LOW.
5. Exercise all eight request combinations against the contact/truth tables.
   Then use the validation matrix for rail, watchdog, cable, deadman and
   injected-driver faults, recording actual COM/gate/coil waveforms.

The fixture sources, generator, supplies, scope and meters are test equipment,
not components that confer vehicle authority. Stop at any unexpected current,
unknown terminal or disagreement with the verified connectivity.

## Alternatives reviewed

| Alternative | Result |
|---|---|
| Two / three SN3257 | Channel grouping improves with three; SN3257 paths become high impedance at zero supply |
| Parallel NC contact across SN3257 | Attached chip still sees powered-off signals; stuck NC can contend with DAC |
| Fully isolated mechanical + SN hybrid | Needs extra isolation poles and transfer verification; direct Form-C is simpler |
| NC + NO isolated semiconductor relays | True zero-drive NC exists, but 12 switching elements before redundancy plus bounded nonoverlap and fault timing are required |
| Depletion-FET NC bridge | Physically possible; negative isolated gate drive, leakage, temperature and transition guarantees remain complex |
| Latching mechanical relay | Rejected: can remain on generated source with no coil power |
| Three DPDT packages | Changes K7/K8 control capability; not parity-equivalent |

The serious small semiconductor candidate is Panasonic AQY4C2P Form-B. It
conducts at zero input drive, so an all-solid-state passive bypass is possible
in principle. Published individual switching delays do not by themselves prove
that a complementary NC/NO pair cannot overlap under abrupt power loss.
Its published 8 Ω maximum at the stated test and 150 mA rating must fit the
measured path; manufacturer consultation is required for automotive use. It
needs a separate simulator investigation rather than a parallel bridge around
an SN3257. [Panasonic Form-B series](https://industry.panasonic.com/ap/en/products/control/relay/photomos/cc1b_aqy4c_p)

## Existing firmware compatibility

Do not use the supplied automatic sweep on this revision. It has no matching
dynamic watchdog contract and can start without a physical enable. Its
GPIO15 would occupy J3-23 assuming the referenced 38-pin header ordering.
The direct PCB net is J3-23→J4-4, whereas the common relay domain is J4-23. They are separate nets. J3 physical header numbers are not GPIO names.
With the same board/bus identification assumption, DAC1 brake outputs in the
sketch are unrouted: direct PCB evidence has J6 A/B pins 11/10 unconnected.
Verify the physical controller revision and header ordering before assigning GPIOs.

A later bench controller must boot in BYPASS, hold all requests low, validate
sources and supplies, begin qualified watchdog service, assert READY, await
manual ARM, and stop on stale command/DAC error/host loss. No timer-triggered
sweep, vehicle CAN actuation, PID, or automatic resume belongs in this fixture.

## Validation and release evidence

Run the host tests, native KiCad ERC, PCB DRC with schematic parity, and source
preservation hash check. Review the routed/exported schematic and footprints.
Use `docs/passive-bypass-validation.csv` for physical work and
`docs/passive-bypass-fmea.md` for explicit residual faults.

The host model checks ideal connectivity, gating and counterexamples. ERC and
DRC check the authored CAD data. None proves physical release, contact wear,
back-powering, automotive qualification, or Nissan diagnostic behavior.
No physical relay, ECU, actuator, vehicle or environmental result has been
obtained in this task.

Before a vehicle-specific revision, establish connector identities, measured
voltage/current/impedance, K7/K8 function, required physical safe state, allowed
channel error/correlation and timing, temperature/vibration/life requirements,
transient protection and driver takeover behavior. This prototype intentionally
does not invent those requirements or select actuator-rated substitutes.

## Review closure

Twelve specialists independently reviewed requirements, raw nets, signal
relays, power relays, semiconductor bypass, hybrids, supervision, drivers,
PCB integration, validation, FMEA and firmware compatibility. The subsequent
review rounds correct pin spacing, gate bias/drive, source current limits,
watchdog startup/rearm, K7/K8 labels and overly broad power-loss claims.
The detailed change/review record is `docs/passive-bypass-review-log.md`.

The final host suite passes 60 tests. Both routed boards have zero native ERC
and DRC violations, zero unconnected items and zero schematic-parity findings
under their recorded KiCad rules. The eighteen original contact terminals
match the carrier, and ten retained original source/library hashes are
unchanged. Editable CAD, local libraries, BOMs, assembly previews, Gerbers,
drill maps/files and positions are included for both boards.

See `hardware/review_evidence/README.md` and the final validation summary for
actual check records. All 34 main physical procedures and all 33 overlapping
supervisor probes remain pending. The design review is closed for the stated
bench scope; physical acceptance is the next step.
