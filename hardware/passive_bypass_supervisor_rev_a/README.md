# MiLa external relay supervisor — bench Rev A

This auxiliary circuit inhibits relay-coil power until rail health, a windowed firmware heartbeat, READY, held physical enable, and a fresh physical ARM press are present. It clears permission on a recognized fault and requires another ARM press after recovery. It is an isolated, room-temperature simulator prototype. Neither this circuit nor a passing CAD check establishes vehicle safety, uninterrupted signals, contact position, or independent command plausibility.

The schematic contains complete manufacturer-numbered pin connections and passive values. Custom pin-block symbols preserve real pin electrical types; identical named nets are connected. `pin_net.csv` and `netlist.xml` expose the actual circuit for audit. The carrier contains the coil drivers and four nonlatching DPDT relays. This supervisor has no signal contacts or ESP socket. The routed 80 × 60 mm, two-layer PCB has 64 circuit parts plus four mounting holes. Native ERC, DRC, unconnected-item and schematic-parity checks are all zero. Physical assembly and validation remain pending.

## Files and reproduction

- `mila_passive_bypass_supervisor_rev_a.kicad_sch`: editable complete circuit.
- `schematic.pdf` and `svg/`: exported schematic.
- `MiLaBench.kicad_sym`, `sym-lib-table`, `.kicad_pro`: local symbol library/project.
- `bom.csv`, `pin_net.csv`, `circuit.json`: parts, pin connections and board-generator input.
- `netlist.xml`: KiCad-exported connectivity, rather than a copy of the generator manifest.
- `erc.rpt`: KiCad electrical-rules report. No ERC exclusions are used.
- `bench_expectations.csv`: 33 physical probes, all PENDING.
- `.kicad_pcb`, project-local `.pretty` libraries and `fp-lib-table`: editable routed layout and local footprint copies.
- `pcb_validation/`: native checks, recorded export commands, final routing metrics and top/bottom/assembly previews.
- `manufacture/`: Gerbers, separate plated/unplated drill files, drill maps/report and positions CSV.

From the canonical MiLa directory:

```sh
python3 tools/build_passive_bypass_supervisor.py
/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli sch erc --severity-all --exit-code-violations --output hardware/passive_bypass_supervisor_rev_a/erc.rpt hardware/passive_bypass_supervisor_rev_a/mila_passive_bypass_supervisor_rev_a.kicad_sch
/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli sch export netlist --format kicadxml --output hardware/passive_bypass_supervisor_rev_a/netlist.xml hardware/passive_bypass_supervisor_rev_a/mila_passive_bypass_supervisor_rev_a.kicad_sch
python3 tools/build_passive_bypass_supervisor.py --verify-netlist hardware/passive_bypass_supervisor_rev_a/netlist.xml
```

The final schematic checkpoint has zero ERC violations. The explicit verifier checks 207 connected component pins and nine intentionally unconnected pins against KiCad's export. Supply flags describe externally or passively driven rails; they do not represent extra physical devices. CAD checks do not test timing, startup glitches, relay transfer, current ratings or analog outputs.

Rebuild the accepted supervisor PCB with KiCad's bundled Python:

```sh
/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.9/bin/python3.9 tools/build_passive_bypass_supervisor_board.py
```

The default rebuild uses `pcb_validation/accepted_layout.json`, containing the
accepted trace/via geometry and circuit/footprint hashes. A reconstruction from
a fresh board object passed native checks and exports. The hash guard rejects
changed circuit or footprint inputs: preserve the frozen source/export files
when reproducing this revision. A new schematic/netlist export may change
metadata hashes even when its electrical connections are equivalent; inspect
and validate a revised layout rather than bypassing that guard.

Use `--validate-existing` to check/export the saved PCB. `--reroute` invokes
exploratory routing and can require local repair; it is not the accepted build
path. The final board uses 0.25 mm tracks, 0.20 mm clearance, 0.70/0.30 mm vias
and four 3.2 mm unplated mounting holes. Actual power-pin decouplers are
approximately 1.89–2.51 mm away. The heartbeat clock uses a shared trunk with
7.3625/7.9375 mm branches; measured geometry skew is 0.575 mm. Geometry alone
does not establish propagation, setup/hold or asynchronous-edge acceptance.

## Supply and connector contract

Use a protected, current-limited 5.0 V bench supply, with 4.95–5.25 V available for guaranteed monitor recovery margin, and a shared ESP 3.3 V rail. Nominal room-temperature assembly testing uses 5.0 V and 3.3 V at 20–30°C. The monitor can inhibit arming at 4.75 V even if that voltage is allowed at the carrier. Maintain a common ground. Do not apply raw vehicle power. The upstream 5 V rail supplies the DAC system and one input of the U3 supply OR; it is separate from the switched coil feed. U13 is powered from 3.3 V.

| Connector | Pin sequence | Meaning |
|---|---|---|
| J1, 1×8 | 1 GND; 2 V3V3; 3 ESP_RESET_HEADER; 4 WDI_HEADER; 5 READY_HEADER; 6 REQ_L; 7 REQ_7; 8 REQ_8 | Controller interface. Explicit GPIO mapping belongs to the controller wiring manifest. |
| J2, 1×2 | 1 V5_SUP; 2 GND | Upstream protected regulated 5 V. |
| J3, 1×4 | 1 V5_SUP; 2 V5_COIL_SWITCHED; 3 V3V3; 4 DEADMAN_HEADER | External held two-pole normally-open enable: coil pole connects 1–2, auxiliary pole connects 3–4 only while held. |
| J4, 1×2 | 1 ARM_SW; 2 GND | Separate physical normally-open ARM button. |
| J5, 1×7 | 1 GND; 2 V5_COIL_SWITCHED; 3 COIL_PERMIT; 4 REQ_L; 5 REQ_7; 6 REQ_8; 7 CARRIER_5V_FEEDBACK | Carrier interface, including returned post-enable coil input. Match functions, not arbitrary connector pin numbers. |
| J6, 1×6 | 1 GND; 2 HEALTH_OK; 3 QUALIFIED; 4 HB_GOOD; 5 ARMED; 6 ZERO_REQ | 3.3 V status/test points. |

The generic 2.54 mm headers are bench connectors. Give the physical harness keyed connectors, strain relief and clear pin labels before any later integration. For J3 select **C&K 8221SHZGE**, a held DPDT momentary pushbutton using its two normally-open contacts only. Its gold-over-silver contacts support both 1 A at 28 V DC power switching and low-level/dry-circuit use; the auxiliary contact switches about 0.33 mA at 3.3 V. The manufacturer warns that the two poles need not make/break simultaneously. Connect J3-1 to switch COM1, J3-2 to NO2, J3-3 to COM4, and J3-4 to NO5. Insulate unused NC3 and NC6. Verify purchased terminal identity by continuity: released 1–3/4–6, pressed 1–2/4–5. A stable toggle or a firmware switch does not implement this held-enable requirement.

For J4 select **C&K 8125SHZBE**, a gold-contact SPDT momentary pushbutton: J4-1 to COM1, J4-2 to NO2, with NC3 insulated. Its 0.4 VA/20 V maximum dry-circuit rating covers the approximately 3.3 mA initial ARM-capacitor discharge and about 33 µA held current. Use insulated short 22 AWG leads, panel mounting and strain relief; label the independent buttons ENABLE and ARM. `external_bom.csv` records these off-board parts. Do not jumper J3 for acceptance testing that claims a physical power cut.

J5 must be wired by function to the carrier `GND`, `5V_RAW`, `COIL_PERMIT`, `REQ_GROUP`, `REQ_K7`, `REQ_K8`, and returned `5V_RAW` inputs respectively. `V5_COIL_SWITCHED` is the carrier's `5V_RAW`; it must not also be tied to upstream V5_SUP. J5-7 is returned through the carrier control connector JCTRL1-6 and tied directly to the carrier's post-physical-enable, pre-Q5 `5V_RAW`. Do not loop J5-7 to J5-2 locally: that would defeat control-connector continuity detection. This is a 5 V sense conductor to R22, never an ESP signal. Connect no downstream bulk storage capacitor to the coil feed. No USB, ESP 5 V pin, DAC rail or other source may backfeed it.

READY/WDI/request inputs are nominal 3.3 V and use short local wires. The assembled supervisor adds a 10 kΩ ground load to each request; the carrier adds further loads, particularly two driver loads to REQ_GROUP. Verify controller HIGH ≥2.60 V and carrier MOSFET gate ≥2.50 V under the complete loading. Contact-board input tolerance of 5.25 V does not permit applying 5 V to a connected ESP GPIO.

COIL_PERMIT is a supervisor-generated nominal 3.3 V signal intended solely for the carrier's AO3400A permission gate. Keep it separate from ESP GPIOs and status points. CARRIER_5V_FEEDBACK is a distinct 5 V wire that must never connect to the ESP.

## Exact supervision and state behavior

U1, TPS3430WQDRCRQ1, is the external window watchdog. Both VDD pins and its exposed pad are connected. R1 = 10 kΩ pulls CWD high; SET0 and SET1 are hard-wired low; R2 = 10 kΩ pulls CRST high. No GPIO can disable the watchdog. The falling-edge interval's lower bound is 7.65–10.35 ms and upper bound is 92.7–125.4 ms. Use 30 ms between falling edges, with a 1 ms HIGH pulse, after successful completion of three 10 ms application iterations. WDO remains low for 8.5–11.5 ms after a watchdog fault. It automatically attempts recovery, but the ARM latch does not automatically recover.

The watchdog startup has special timing: WDO is held low during startup/reset; the first subsequent falling WDI edge starts a window whose lower-bound check is suppressed. The separate heartbeat qualification is therefore necessary. A static HIGH/LOW cannot establish ongoing health. Do not generate WDI using a free-running timer, PWM, DMA or an interrupt that can continue after the actual test-control loop hangs.

U2, TPS3808G33QDBVRQ1, monitors the shared 3.3 V rail and the ESP hardware reset/enable line through its MR pin. Its nominal rail trip is 3.07 V; threshold tolerance and hysteresis apply. R3 = 100 kΩ to V3V3 selects nominal 300 ms release delay (180–420 ms specified). Connecting to an actual shared ESP rail is essential; a separate always-on supervisor rail would not detect loss of the controller's own 3.3 V.

U3, TPS3808G01QDBVRQ1, monitors **CARRIER_5V_FEEDBACK** through R22 = 100 kΩ 0.1% and R23 = 9.53 kΩ 0.1%. This observes actual coil input downstream of the physical switch and both complete carrier connectors. Sustained loss of either complete power/control connector causes this divider to fall; after the monitor recognizes the loss and clears the latch, reconnection cannot resume the previous armed state. Contact chatter shorter than the SENSE filter and supervisor recognition time need not latch a fault. C17 = 1 nF filters SENSE with about 8.7 µs nominal RC. Falling trip is nominal 4.655 V. IC accuracy and divider tolerances permit roughly 4.55–4.76 V trip; maximum hysteresis can make recovery require approximately 4.90 V. Use at least 4.95 V for arming, rather than treating 4.75 V as guaranteed recovery.

D1, BAS70-05-7-F, supplies U3 from an isolated OR of both rails: pin 1 anode V3V3, pin 2 anode V5_SUP, pin 3 common cathode V_PG5_SUP. U3's VDD, MR pull-high, CT/R4 and C3 use V_PG5_SUP. This keeps U3 powered when 5 V vanishes but USB keeps 3.3 V alive, and also keeps its SENSE below its supply when 5 V is present while 3.3 V is absent. A fixed G50 powered only from 5 V loses a defined output when its own supply collapses; powering it from 3.3 V while sensing 5 V would exceed recommended SENSE≤VDD. The divider plus diode OR removes those live-rail conflicts. Measure V_PG5_SUP and backfeed in every power sequence; do not infer behavior in the unspecified near-zero-supply region from absolute maximum ratings.

U1 WDO, U2 RESET and U3 RESET are open-drain and share HEALTH_N, pulled to V3V3 by R5 = 10 kΩ. No push-pull output is tied to that node. U4 is a Schmitt buffer for the open-drain edge; U5 buffers the physical-enable sense. U8/U9 form:

```text
QUALIFIED = HEALTH_OK AND READY AND DEADMAN_OK
ZERO_REQ  = NOT(REQ_L OR REQ_7 OR REQ_8)
```

QUALIFIED drives the asynchronous active-low clear pins on both U10 heartbeat stages and the U11 ARM latch. Recognized rail/reset/watchdog/READY/enable loss therefore clears both heartbeat qualification and ARM.

U6 inverts WDI so its falling edge clocks both U10 stages. The first accepted edge after qualification sets HB_ONE. R24 = 1 kΩ, C18 = 100 pF C0G 5%, and U14 SN74LVC1G17QDCKRQ1 delay and buffer HB_ONE into HB_ONE_SAFE before the second D input. A later accepted falling edge sets HB_GOOD. This observations chain requires a full inter-edge interval after READY and held enable; it does not independently prove the semantic validity of a firmware iteration.

R24/C18 provide approximately 100 ns nominal RC plus buffer delay, preserving positive same-clock hold margin. At the datasheet's 3 V threshold test point, U14 VT+ = 1.36–2.04 V, VT− = 0.77–1.35 V; U14 propagation is 1.5–8 ns at 3.3 V ±0.3 V. Use the actual threshold, R/C tolerance, source levels, loading and routing skew to verify:

```text
tCQ(min) + tRC-rise(min) + tU14(min) > tD-hold + positive clock skew
tCQ(max) + tRC-rise(max) + tU14(max) + tD-setup < next heartbeat interval
tRC-fall(max) + tU14(max) < minimum qualified-low time before a new heartbeat
```

The LVC74A requires data setup ≥3 ns, hold ≥1 ns, clear-inactive setup ≥2 ns and clear/clock pulse duration ≥3.3 ns at 3.3 V ±0.3 V. Its clock-to-Q is 1–5.2 ns. The exact 3.3 V Schmitt threshold and slow-edge delay are not separately bounded by the table's 3 V threshold row; measure the actual stage rather than asserting an interpolated certified limit. For the bench protocol, require QUALIFIED LOW ≥10 µs, hold request/READY states stable ≥1 ms before ARM, and start post-recovery heartbeat edges ≥1 ms after qualification. Hardware rail/watchdog release delays greatly exceed RC flush time. Test coincident asynchronous edges separately.

U12 sets ARM_D = HB_GOOD AND ZERO_REQ. U11 captures this only on a physical ARM rising edge. R6 = 100 kΩ, R7 = 1 kΩ and C14 = 1 µF form the ARM network; U6's Schmitt inverter makes pressing the normally-open button produce that edge. Press discharge is about 1 ms and release is about 100 ms nominal, subject to thresholds and capacitance. Verify actual contact bounce. A button held through a fault remains a constant clock level: restoring QUALIFIED does not create a fresh ARM clock edge. Release the button long enough for ARM_CLK to return LOW, then press it again. Requests must be LOW at this new edge.

U13 **SN74LVC1G08QDCKRQ1**, powered from V3V3, produces COIL_PERMIT only when ARMED AND QUALIFIED are high. R18 = 1 kΩ limits initial gate current; R19 = 82 kΩ and the carrier's RPD6 = 82 kΩ pull permission LOW while keeping static loading light. The carrier RG6 remains 330 Ω; R20/R21 remain 10 kΩ input pulldowns; C13 bypasses V3V3. This avoids relying on a 5 V AHCT driver's undefined behavior below its 4.5 V operating range during 5 V collapse.

TI's current LVC1G08-Q1 Rev H specifies recommended-temperature VOH ≥VCC−0.15 V at 100 µA, and Ioff ≤10 µA magnitude at VCC=0. With both 82 kΩ pulldowns, the complete static load is at most approximately **86.51 µA** at VCC=3.6 V, including 1% resistor corners and 100 nA MOSFET gate leakage. At VCC=3.0 V, VOH≥2.85 V produces calculated header ≥**2.78085 V** and Q6 gate ≥**2.76944 V**. Add no output indicator or other DC load that invalidates the 100 µA limit.

At VCC=0, a 10 µA source-like Ioff and 100 nA gate leakage give calculated Q6 gate ≤**0.41743 V** with intact pulldowns. This is a **leakage-voltage screening calculation, not a drain-current OFF guarantee**: the MOSFET threshold is measured at a specified drain current and does not bound drain current at this gate voltage. Opening either pulldown also reduces the margin. Measure Q6/Q5 gate voltage, drain behavior and coil current with V3V3=0/V5 present and through every partial 3.3 V ramp. Typical MOSFET capacitance can suggest approximately 26 µs discharge settling, but does not establish a bounded cutoff time. All these values are calculations awaiting physical validation.

## Firmware and physical boundaries

Boot/reset must keep READY and all relay requests LOW. Raise READY only after successful DAC initialization, acknowledgment of every required write, fresh command and communication checks, and measured simulator output acceptance. Stop WDI when the guarded control iteration fails. The existing autonomous AutoSweep source does not implement this contract and must not directly drive the new interface. READY LOW inhibits DAC absence only if firmware detects it and lowers READY. An ESP that keeps READY HIGH and valid WDI pulses while writing an incorrect DAC value remains outside this supervisor's detection capability.

Physical deadman release disconnects coil power even if the ARM latch or permission electronics fail high. The auxiliary contact also clears the latch. The returned carrier supply detects whole-connector loss but cannot detect an individual broken request/permission conductor while the feedback conductor stays connected. Such a conductor can resume its previously asserted state on reconnection; shorted feedback can conceal connector loss. Pole timing mismatch, welded enable contacts, stored energy, wiring shorts and backfeed remain physical test/fault-analysis matters. Releasing a nonlatching relay eventually restores its NC connection only with healthy contacts; the delay and bounce are finite. K7/K8 NC states are default connectivity, not a verified motor-off or stock-safe behavior.

The settled Boolean state model assumes valid voltages, valid minimum pulse widths, setup/hold/recovery timing and settled inputs. It cannot prove absence of metastability, narrow output pulses during arbitrary power ramps, asynchronous coincidences or stuck component faults. Bench acceptance must scope the real COIL_PERMIT, gate, coil current and every COM signal through those cases. The current design has one watchdog, one fault node and a single permission chain; it is not redundant or single-fault tolerant.

## Primary sources

- [TI TPS3430-Q1 watchdog, pins, startup and timing](https://www.ti.com/lit/ds/symlink/tps3430-q1.pdf)
- [TI TPS3808-Q1 supervisors, G01 divider, timing and supply limits](https://www.ti.com/lit/ds/symlink/tps3808-q1.pdf)
- [TI SN74LVC74A-Q1 flip-flops and timing](https://www.ti.com/lit/ds/symlink/sn74lvc74a-q1.pdf)
- [TI SN74LVC1G17-Q1 Schmitt buffers](https://www.ti.com/lit/ds/symlink/sn74lvc1g17-q1.pdf)
- [TI SN74LVC2G14-Q1 Schmitt inverters](https://www.ti.com/lit/ds/symlink/sn74lvc2g14-q1.pdf)
- [TI SN74LVC1G08-Q1 AND gates](https://www.ti.com/lit/ds/symlink/sn74lvc1g08-q1.pdf)
- [TI SN74LVC1G27 NOR gate](https://www.ti.com/lit/ds/symlink/sn74lvc1g27.pdf)
- [Diodes Incorporated BAS70-05 common-cathode array](https://www.diodes.com/datasheet/download/BAS70.pdf)
- [C&K 8020 momentary pushbuttons, pin numbers and contact ratings](https://www.ckswitches.com/media/1397/8020.pdf)
- [C&K exact 8221SHZGE and 8125SHZBE selection guide](https://www.ckswitches.com/media/2222/ck_short-form-catalogue.pdf)

U7 and D1 use catalog order codes; selecting several Q1 logic devices does not make the whole board automotive-qualified. Verify purchase availability, exact markings, all footprints and manufacturer revisions before assembly.
