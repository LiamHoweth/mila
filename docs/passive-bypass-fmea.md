# Passive-bypass relay replacement: independent FMEA

Date: 2026-10-07. Status: analytical bench-design review, not hardware acceptance.

## Scope and conclusion

The proposed bench revision uses four nonlatching OMRON G6K-2P-Y DC5
relays. RLY1 replaces K3/K4 with two poles, RLY2 replaces K5/K6 with two
poles, RLY3 uses one pole for K7, and RLY4 uses one pole for K8. K7 and K8
remain independently controlled. AO3400A devices switch the coil low sides;
an AO3401A device disconnects their common positive supply. A separate physical
series deadman removes coil energy. The separate supervisor schematic contains
TPS3808G33-Q1 3.3 V monitoring, TPS3808G01-Q1 adjustable 5 V monitoring powered
through an isolated diode OR of the 3.3 V and 5 V rails, a TPS3430-Q1 window watchdog, two heartbeat qualification stages,
and a deliberate ARM-edge latch. Its lightly loaded 3.3 V LVC permission output controls the
carrier's common cutoff. Faults clear the qualification and arm state.

This prototype is for isolated 0–5 V signal simulators with no more than 1 mA
per signal path. It is not for an actuator, motor, vehicle harness, Nissan ECU,
or automotive supply. Existing J4/J3 control identities, voltage, polarity,
source impedance, and power domains remain unknown. Do not connect the new
logic directly to legacy controls on the basis of header numbering.

The design addresses the particular SN3257 failure mode: a semiconductor
selector that isolates its signal terminals when unpowered cannot preserve a
passive stock connection. Nonlatching Form-C contacts provide a connection
that does not need logic power after the contacts settle.

The supported claim is deliberately narrow:

> Removing coil energy returns healthy nonlatching contact poles to their
> verified NC connection after a finite release and bounce interval, without
> MCU, DAC, logic supply, or stored backup energy. K3–K6 NC paths may be called
> stock bypass only after their mapping is confirmed. K7/K8 are default
> connections until their actual function is established.

No claim is made for continuity throughout transfer, recovery from welded
contacts, every single component failure, sensor-pair synchronization, a safe
vehicle stop, automotive qualification, or an ASIL rating.

## Independent first-pass findings and design revisions

The initial review examined the selector principle before receiving other
specialists' conclusions. It found six material objections:

1. A welded NO contact can retain the generated source after coil power loss.
2. A broken COM/NC contact, connector, solder joint, or stock wire can leave the
   intercepted circuit open even with all relays released.
3. A low-side driver short can retain coil current while the coil rail survives.
4. A failed DAC can corrupt the selected signal before mechanical release
   completes.
5. Contact bounce and pole skew can create a temporary mixture of original and
   generated redundant sensor channels.
6. K7/K8 cross-wiring does not establish that they are low-current sensor
   selectors. The default state might be an actuator direction.

The revised four-relay design preserves K7/K8 independence, adds an upstream
electronic coil disconnect and a physical series deadman, and constrains the
entire demonstration to harmless current-limited simulators. The authored
supervisor schematic implements rail monitoring and hardware watchdog timing;
two qualified WDI falling edges and a new ARM edge with requests inactive are
needed to arm. A fault-cleared latch prevents automatic restart merely because
a rail or watchdog recovers. Those changes provide the previously omitted
active-inhibit reference circuit. They do not resolve welded contacts,
physical opens, release exposure, production output supervision, or the
vehicle's unknown required response. Circuit structure and ERC checks are
distinct from physical behavior, which remains NOT_RUN.

## Fault review

Priority is qualitative. Likelihood and diagnostic coverage cannot be assigned
credibly from drawings without component reliability data and measurements.
The following are counterexamples and required tests, not measured failures.

| Fault or condition | Effect | Treatment in this revision / residual limitation |
|---|---|---|
| Complete coil-power loss with healthy contacts | NC/default connection is restored after release and bounce | Intended result. Measure all poles with the actual suppression circuit. |
| Logic rail fails while coil supply survives | Undefined drive could energize relays | External PG3, gate defaults, upstream inhibit and latch clear must make this impossible in normal component operation. Test every sequencing order. |
| 5 V coil or DAC rail falls gradually | Chatter, retained invalid DAC output, or delayed transfer | PG5 must clear the latch before the defined rail requirement is violated. Threshold, tolerance, hysteresis and response time are acceptance inputs. |
| AO3400A drain-source short | Its relay remains on whenever coil supply is present | AO3401A/physical cutoff can remove its energy. Inject this fault with a drain-source jumper and simulator only. |
| AO3401A drain-source short | Electronic common cutoff loses authority | Physical series deadman still interrupts the defined coil-energy path; healthy low-side drivers still release. This is not redundant automatic fault tolerance. |
| Common gate logic/latch output stuck enabled | Automatic inhibit may not act | Physical interruption remains available. A single shared automatic-enable chain is not two independent safety channels. |
| Deadman contacts welded or cable shorted | Physical opening might not remove energy | Not covered by the passive-bypass claim. Investigate physical interlock ratings and fault detection before production use. |
| Complete carrier power/control connector removed and reinserted | Relays release; uncontrolled restart would occur if the supervisor never recognized removal | Returned carrier 5V_RAW through JCTRL1-6 to supervisor J5-7 makes sustained removal trip PG5. Require fresh qualification and ARM after recognition; characterize filter/detection time and brief chatter. |
| Individual request/permission conductor opens and reconnects while feedback stays valid | Relays can reenergize under the retained ARM state | Not universally detected. A fresh ARM is required after recognized faults, not every individual conductor interruption. |
| Coil power supplied through USB/backfeed/adapter | Intended cutoff may not remove all energy | Enumerate every source. AO3401A is one MOSFET with a body diode, not a general reverse-current blocker. No alternative source may feed the downstream coil rail. |
| Bulk capacitor downstream of physical cutoff | Coils may remain energized after switch opening | Put holdup capacitance upstream of the effective interruption or establish a tested hold-time bound. Local flyback recirculation still exists. |
| Flyback diode remains conducting after cutoff | Magnetic field decays slowly | Diode-only suppression can delay release. The complete release path must be characterized; a logic falling edge is not contact closure. |
| DAC rail fails before relay releases | ECU simulator receives zero/undefined/held voltage during transfer delay | Scope selected outputs, rail thresholds, coil current and final NC closure. Record fault exposure; do not describe it as instantaneous bypass. |
| DAC command/I²C updates stop but DAC holds last code | Valid-looking but stale generated command persists | WD/READY must depend on completed validated cycles. Future system needs command freshness and independent actual-output monitoring. |
| Firmware hangs but a timer interrupt still toggles watchdog | Window WD can remain satisfied | A free-running heartbeat does not establish control-loop progress. Test control-loop stall with interrupts still active. |
| READY asserted despite missing/incorrect DAC output | Active transfer can connect wrong source | Prototype READY is a contract, not an independent output monitor. A production implementation needs defined validation and feedback. |
| Both sensor channels have a wrong but correlated command | Simple correlation monitor can pass dangerous intent | Range/correlation alone cannot establish safe authority. Command limits, freshness, rate limits, override and application response remain requirements. |
| NO contact welded or mechanism stuck energized | Source remains generated despite zero coil energy | Not resolved by four single-stage selectors. Do not claim welded-contact tolerance. |
| NC contact high resistance or COM/NC open | Default connection becomes inaccurate or absent | Test low-load continuity/endurance, connectors and solder. A working coil-control circuit cannot fix a broken signal conductor. |
| One DPDT pole transfers before the other | Pair temporarily uses different sources | Measure both poles together. A shared armature does not establish zero skew or zero bounce. |
| Arm with generated and stock voltages unequal | Abrupt signal step and possible diagnostic response | Match outputs before arm for simulator evaluation. A production matching threshold must follow ECU requirements. |
| Power-off monitoring tap clamps stock circuit | Bypass is loaded despite healthy NC copper | This prototype should avoid unnecessary taps on bypass paths. Future taps must tolerate unpowered operation and meet leakage/fault-current requirements. |
| K7/K8 are actually motor polarity switches | Intermediate/default states can brake, reverse, or drive a motor | No motor/actuator use in this revision. Establish voltage, current, inductance, stall/inrush and all states first. |
| Driver is pressing the stock accelerator when fault occurs | Restoring stock may restore a substantial torque command | Stock bypass is a takeover behavior, not a demonstrated vehicle stop. Define emergency-stop objectives separately. |
| Relay, MOSFET or control pin accidentally receives vehicle battery | Bench component limits/protection may be exceeded | The bench board has no automotive power/transient claim. Direct legacy hookup is prohibited until the electrical interface is specified. |

## Required logic behavior

The complete two-module prototype includes an authored physical-supervisor
circuit: PG3, PG5 and watchdog status come from the specified monitor/watchdog
parts, not externally asserted good-input headers. The carrier by itself
only consumes incoming permission and requests; it does not implement that
supervision. The external controller supplies READY, WDI and reset, while
current-limited supplies and physical switches supply the fixture inputs.
READY remains a semantic assertion: the supervisor does not independently
measure the DAC output, validate command intent or establish sensor correlation.

Nominal permit is the conjunction of the required good signals. A fault clears
the ARM latch asynchronously; restoring the good inputs alone must not restore
coil authority. The latch may set only on a new deliberate ARM edge after the
permit is valid. Deadman opening must remove physical coil energy independent
of the latch's state. Test ARM held high across boot, fault, recovery and
deadman opening; it must not cause unwanted rearming.

The adjustable 5 V monitor takes its supply through a dual-rail diode OR.
It remains powered by 3.3 V when 5 V disappears, and its SENSE stays below
VDD when 5 V remains but 3.3 V disappears. Its divider/filter and threshold
tolerances belong in the measured response budget; guaranteed recovery needs
the specified arming supply of at least 4.95 V. Verify diode-OR voltage,
reverse leakage, output state and coil permission in every partial-power
sequence. The supply arrangement does not establish valid behavior at every
near-zero voltage. [TI TPS3808-Q1 datasheet](https://www.ti.com/lit/ds/symlink/tps3808-q1.pdf).

Default gate resistors are part of this behavior. Every supply sequence must
keep MOSFET gates within device limits and produce off states when control is
absent. The PMOS source/drain orientation must match the intended forward
feed. It must not be described as isolation in both current directions.

The AO3400A and AO3401A manufacturer sheets specify 30 V drain-source and
±12 V gate-source absolute limits. Those limits are not automotive transient
qualification. Coil-clamp stress plus supply and layout overshoot must remain
below the low-side device rating with margin. [AOS AO3400A datasheet](https://www.aosmd.com/sites/default/files/res/datasheets/AO3400A.pdf),
[AOS AO3401A datasheet](https://www.aosmd.com/sites/default/files/res/datasheets/AO3401A.pdf).

## Release and transition timing

The reaction time is an end-to-end quantity:

```text
fault onset
 + detector/supervisor delay
 + enable/latch/driver propagation
 + coil current decay with installed suppression
 + mechanical transfer
 + final NC bounce/settling
 = time until stable default connection
```

No single relay datasheet timing figure covers this complete chain. Fast
power loss can invalidate a selected DAC before the detector threshold is
reached or the contacts move. A valid result records both stable-default time
and the maximum duration/amplitude of the wrong or missing output.

The relevant tests are rapid and slow PG3/PG5 collapse, abrupt DAC-only loss,
watchdog loss, deadman opening, control-loop stall, and supply restoration.
Capture both redundant channels together. Repeat at intended bench supply and
load corners with the actual coil diode/clamp, not a substituted relay module.

OMRON specifies initial G6K resistance and operating/release figures; its
minimum-load reliability reference is not a lifelong milliohm promise. The
microload P-level entry uses a 50 Ω contact-resistance failure criterion and
requires actual application suitability checks. The exact DC5 part must be
nonlatching G6K, not G6KU. [OMRON G6K datasheet, ratings and characteristics](https://components.omron.com/us-en/system/files/2026-05/datasheet_pdf/K106-E1.pdf).

TE explains that suppression changes armature release and contact behavior;
the suppression used in the application must be included in verification.
A diode plus Zener/TVS may improve release, but increases switch voltage stress
and is not an unreviewed drop-in change. [TE relay coil suppression guidance](https://www.te.com/en/products/relays-and-contactors/electromechanical-relays/intersection/relay-coil-suppression-dc-relays.html).

## Semiconductor Form-B alternative

It would be incorrect to say all semiconductor relays lose their output
connection without supply power. Normally closed Form-B photorelays exist.
Panasonic identifies AQY410EH as normally closed; Toshiba identifies
TLP4176G as a 1-Form-B photorelay. They deserve a fair alternative review.
[Panasonic AQY410EH](https://industry.panasonic.com/global/en/products/control/relay/photomos/number/aqy410eh),
[Toshiba TLP4176G](https://toshiba.semicon-storage.com/us/semiconductor/product/isolators-solid-state-relays/photorelay-mosfet-output/detail.TLP4176G.html).

A Form-B device in the stock branch and Form-A device in the generated branch
can provide a normally connected stock path with no input-LED power. It offers
smaller packages, no mechanical bounce and no microload contact films. It
still requires a complete review of on-resistance, leakage, output
capacitance, nonlinear error, fault voltage, temperature, switching delays
and LED-input failure states.

Two separate devices are not a mechanically interlocked SPDT contact.
Normal switching and abrupt total power loss must not connect stock and DAC
simultaneously. On abrupt input-power loss the Form-B stock branch can close
before the Form-A DAC branch opens; firmware sequencing cannot prevent that
passive timing race. A valid solid-state solution needs bounded worst-case
non-overlap over temperature, supply decay and faults, or another architecture
that tolerates overlap. Series resistors can contain contention but add signal
error; their acceptability depends on real source/load limits.

As a screening example, a 25 Ω path at 1 mA produces a calculated 25 mV drop,
before leakage/source-impedance errors. TLP4176G's manufacturer page lists
25 Ω maximum on resistance and distinct millisecond switching limits. That
does not disqualify all Form-B products, but it does prevent assuming that
an available high-voltage part meets an unknown Nissan signal tolerance.
Neither a Form-B photorelay nor the selected mechanical relay is inherently
safe against every short/open internal failure.

The smaller voltage-driven Panasonic AQY4C2P Form-B family is also a serious
space-saving candidate. It is normally closed at zero input drive and uses
capacitive isolation rather than an LED input. Its existence means that
the higher-resistance legacy photorelays above must not be used to dismiss
all solid-state bypass solutions. Complementary branch timing, input-power
collapse, leakage and actual signal errors still require separate analysis.
[Panasonic CC TSON Form-B family](https://industry.panasonic.com/ap/en/products/control/relay/photomos/cc1b_aqy4c_p).

The four-relay choice is therefore a simple bench baseline with easy-to-audit
physical default paths. A Form-B/Form-A variant remains possible if measured
electrical requirements and passive non-overlap analysis support it. SN3257
powered-off isolation alone does not provide that function.

## Acceptance and remaining work

Each external simulator source must remain within 0–5 V and be current-limited
to no more than 1 mA, including a short to ground and source-to-source
contention. One option is at least 5.1 kΩ series resistance at every ideal
5 V source; the simulator's output error must then be computed with its load.
Those resistors are simulator fault containment, not production sensor-path
values.

Before a bench pass is recorded:

1. Verify all NC/COM/NO connections with power absent and each relay energized.
2. Exercise every K7/K8 combination with signal simulators only.
3. Verify every good-input truth-table row, ARM edge requirement, held-ARM
   behavior, physical cutoff and supply sequence.
4. Record actual selected-output, coil-current, release and bounce waveforms
   for each fault stimulus, including DAC-only collapse.
5. Demonstrate low-side short recovery via common cutoff and demonstrate
   physical deadman authority with the high-side switch deliberately bypassed.
6. Confirm no alternate power source or downstream capacitor defeats physical
   interruption. Measure leakage/backfeed rather than inferring it from names.
7. State explicitly that welded contacts and broken signal conductors remain
   outside the recovery guarantee.

Before even considering a vehicle revision, establish exact harness pin
identities, legacy control levels/polarities, coil-feed source, signal
impedances/currents, ECU diagnostic tolerances, actuator functions and required
fault response. Reevaluate the specified bench supervisor's monitor thresholds
and watchdog timing against the measured requirements, and specify the full
latency budget, actual-output readback and automotive protection. Production layout,
ERC/DRC, solder inspection, environmental tests and independent hardware
review are separate evidence. Analytical simulation and host truth-table
tests cannot stand in for those measurements.

## Review disposition

The four-relay architecture is acceptable to develop and verify as a bounded,
isolated simulator prototype. Its passive default-path principle resolves the
original total-power-loss selector mismatch. It does not establish a vehicle
safety case, recover from welded contacts, or guarantee uninterrupted bypass
during faults. This FMEA records analytical findings only; no physical relay,
DAC, harness, ECU, or vehicle test was performed by this review.
