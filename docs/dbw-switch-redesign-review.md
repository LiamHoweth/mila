# Drive-by-wire relay replacement design review

Status: design-review and bench-planning document only. Not approved for installation in a vehicle.

Date: 2026-09-18

## Executive finding

Do not replace the six used relay contacts with two SN3257-Q1 devices on the production PCB yet.

Two separate blockers were found:

1. The PCB 2.0 wiring has three control domains. Relay-module channels K3-K6 share one control net (J4 pin 23), while K7 and K8 have separate controls (ESP32 header J3 pins 25 and 26). One SN3257 can replace the four grouped paths. A second SN3257 cannot independently reproduce K7 and K8 because all four of its channels share SEL and active-low EN.
2. An unpowered SN3257-Q1 makes every signal pin high impedance. The present mechanical contacts fall back to their NC paths without board power. The SN3257 therefore does not reproduce the passive bypass behavior that appears to be a primary safety property of the relay design.

The project contains no firmware, BOM, connector pin-function document, vehicle wiring diagram, measured voltage/current data, or transient specification. The statement that the signals are 0-5 V is not sufficient to qualify any semiconductor switch.

## Evidence quality

### Confirmed from PCB 2.0 source

- The relay module is schematic/PCB reference J7, using a custom 37-pin footprint.
- J7 contact terminals 1-18 are routed; terminals 19-24 are not routed.
- J7 IN1-IN6 (pins 26-31) are tied together on J4 pin 23. Of those, the used contact sets are K3-K6; K1 and K2 have unused contact terminals.
- J7 IN7 (pin 32) is driven by ESP32 header J3 pin 25.
- J7 IN8 (pin 33) is driven by ESP32 header J3 pin 26.
- J7 pin 34 (VCC) is on the 5 V module rail; pin 35 is ground; pin 36 is unconnected; pin 37 (JD-VCC) is J4 pin 22.
- PCB 2.0 changed the two highest-numbered relay contact sets from DAC inputs to cross-connected J4 pins 8 and 9, and changed IN7/IN8 from the common input group to separate MCU header pins.
- The board outline is approximately 146.16 mm by 122.16 mm. The relay footprint occupies approximately x=57.59-190.84 mm and y=40.91-92.91 mm in PCB coordinates.

### Inferred and requiring continuity confirmation

- The relay terminal order is inferred from the photographed module silkscreen as NO-COM-NC in ascending numeric order within each three-terminal set. Confirm with an ohmmeter on the unpowered module before relying on the NC/NO names below.
- The PDF associates the wiring with accelerator, linear-actuator braking, and future steering, but it does not label J4 pin functions. The functional labels in the relay table are therefore provisional.
- K7/K8 form a cross-connected pair that resembles a polarity/signal swap. Although the controls are electrically independent, the intended firmware may command them together. No firmware was supplied to prove this.
- The conceptual PDF shows a 12 V source associated with the relay module while the photographed relays are marked SRD-05VDC-SL-C. This is a serious documentation/hardware inconsistency. Measure JD-VCC and read the installed relay markings before applying power.

## Six-relay reconstruction (PCB 2.0)

"Energized" means the relay coil is energized, not the logic level at an opto-isolated module input. The module input polarity was not documented and must be measured.

| Relay | COM net | NC net | NO net | Unpowered/default path | Energized path | Control source | Control independence | Provisional function | Voltage/current | Isolation |
|---|---|---|---|---|---|---|---|---|---|---|
| J7/K3 | J7-17 = J4-14 | J7-18 = J4-13 | J7-16 = J5-10 (MCP4728 VB) | J4-14 to J4-13 | J4-14 to DAC VB | J7 IN3/J7-28 = J4-23 | Grouped with K1-K6; used group K3-K6 | Future steering path A (inferred from PDF) | Unknown | Contact-to-coil isolation present; whole-board isolation not established |
| J7/K4 | J7-14 = J4-15 | J7-15 = J4-12 | J7-13 = J5-11 (MCP4728 VA) | J4-15 to J4-12 | J4-15 to DAC VA | J7 IN4/J7-29 = J4-23 | Grouped with K1-K6; used group K3-K6 | Future steering path B (inferred from PDF) | Unknown | Same |
| J7/K5 | J7-11 = J4-16 | J7-12 = J4-11 | J7-10 = J6-8 (MCP4728 VD) | J4-16 to J4-11 | J4-16 to DAC VD | J7 IN5/J7-30 = J4-23 | Grouped with K1-K6; used group K3-K6 | Accelerator/sensor path A (inferred) | Unknown | Same |
| J7/K6 | J7-8 = J4-17 | J7-9 = J4-10 | J7-7 = J6-9 (MCP4728 VC) | J4-17 to J4-10 | J4-17 to DAC VC | J7 IN6/J7-31 = J4-23 | Grouped with K1-K6; used group K3-K6 | Accelerator/sensor path B (inferred) | Unknown | Same |
| J7/K7 | J7-5 = J4-18 | J7-6 = J4-9 | J7-4 = J4-8 | J4-18 to J4-9 | J4-18 to J4-8 | J7 IN7/J7-32 = J3-25 | Electrically independent | Linear-actuator braking path A / half of cross-connected pair (inferred) | Unknown; do not assume sensor current | Same |
| J7/K8 | J7-2 = J4-19 | J7-3 = J4-8 | J7-1 = J4-9 | J4-19 to J4-8 | J4-19 to J4-9 | J7 IN8/J7-33 = J3-26 | Electrically independent | Linear-actuator braking path B / half of cross-connected pair (inferred) | Unknown; do not assume sensor current | Same |

K7/K8 intermediate states are potentially hazardous: if only one changes state, both COM nets can be connected to the same J4 source net. Determine whether that is intentional, tolerated, or prohibited before changing hardware or firmware.

## Existing behavior under power faults

| Fault | Existing mechanical contacts | SN3257-Q1 replacement |
|---|---|---|
| MCU reset / GPIO high impedance | K3-K6 are controlled externally through J4-23; K7/K8 likely de-energize, but module-input bias is undocumented | Internal 6 Mohm pulls make SEL=0 and EN=0, selecting A paths while VDD remains valid; external 10 kohm pulls are still recommended for a robust reset state |
| Loss of 3.3 V only | Relay outcome depends on optocoupler/control wiring; K7/K8 likely de-energize but must be measured | With a valid 5 V switch supply, external SEL pull-downs can select bypass; do not rely on the 6 Mohm internal pulls in a safety design |
| Loss of 5 V logic rail | Coil behavior depends on separate JD-VCC and the module topology | If VDD < 1.5 V all signal pins are high impedance; there is no NC bypass |
| Loss of JD-VCC / coil power | All relay contacts mechanically return to NC | Not applicable; loss of switch VDD opens all paths |
| Board unplugged but harness remains through contact terminals | NC metal contacts can preserve the bypass path | Semiconductor switch cannot preserve a path without its own valid supply |
| Vehicle signal present while board is off | Metal contact behavior is independent of electronics | Powered-off protection is specified only for 0-3.6 V; a 5 V vehicle signal is outside the powered-off recommended range |

## SN3257-Q1 electrical suitability

TI's current Rev. D data sheet gives the following limits:

- VDD: 1.5-5.5 V recommended.
- Signal range while powered: 0 to min(2 x VDD, 5.5 V).
- Signal range while VDD < 1.5 V: 0-3.6 V only.
- Continuous signal current: +/-25 mA.
- On resistance: 2 ohm typical, 5 ohm maximum.
- On-resistance flatness: 1 ohm typical, 2.5 ohm maximum.
- On/off leakage: up to +/-0.9 uA across temperature; powered-off leakage up to +/-8 uA.
- Logic thresholds: VIH >= 1.2 V, VIL <= 0.45 V; 3.3 V GPIO is compatible.
- SEL and EN have weak 6 Mohm internal pull-downs.
- EN=0, SEL=0 selects all A paths; EN=0, SEL=1 selects all B paths; EN=1 opens all paths.
- Signal pins have a 6 V absolute maximum and are not specified as short-to-battery or ISO 7637 protected.

Consequences:

- A powered 5 V signal is within range if VDD is at least 2.5 V, but a 5 V signal while the board is off is not within the 3.6 V powered-off limit.
- Five ohms can be negligible or unacceptable depending on vehicle input impedance and source resistance. With a 10 kohm load it contributes about 0.05% divider error; with a 1 kohm effective load it contributes about 0.5%. Leakage can add millivolts to tens of millivolts on high-impedance nodes.
- The 25 mA limit rules out any path that is actually an actuator drive, relay coil drive, lamp drive, or low-impedance interface.
- Adding enough series resistance to survive a 12-14 V short-to-battery fault can itself create unacceptable sensor error. Do not attempt to solve this by guessing a resistor value.
- AEC-Q100 qualification does not make the complete circuit safe for an accelerator, brake, or steering function. System fault analysis and vehicle-level validation remain required.

Verdict by path: unresolved for all six paths until voltage, current, impedance, fault, and power-off behavior are measured. K7/K8 are especially suspect because their cross-connected topology may not be low-current analog sensing.

## Control-group compatibility

| Architecture | K3-K6 common group | K7 independent | K8 independent | Passive bypass with no board power | Verdict |
|---|---:|---:|---:|---:|---|
| Two SN3257-Q1 | Yes | No | No | No | Reject for PCB 2.0 as documented |
| Two SN3257-Q1, K7/K8 forced to one control | Yes | Paired only | Paired only | No | Bench-only hypothesis after proving paired operation is required |
| One SN3257-Q1 plus one TS5A23157-Q1 | Yes | Yes | Yes | No; TS5A23157-Q1 also lacks SN3257-style powered-off isolation | Electrical-control match only; not a fail-safe production replacement |
| Three SN3257-Q1 | Yes | Yes | Yes | No | Control match, but wasteful and still fails the power-off requirement |
| Six Form-C mechanical contacts (for example, three DPDT signal relays) | Yes | Yes | Yes | Yes | Preferred architecture if passive bypass is a requirement, subject to contact/current/environment qualification |
| Form-A plus Form-B PhotoMOS pair per channel | Possible | Possible | Possible | Potentially, but requires 12 devices and careful transfer timing/fault analysis | Not preferred without a formal safety analysis |

## Recommended architecture

### Production direction

Preserve normally-closed mechanical bypass unless the vehicle-level safety requirements explicitly allow an open circuit when this PCB loses power. Replace the eight-relay module with only the six contacts actually used, preferably as three compact sealed DPDT signal relays:

- DPDT relay A: K3 + K4, common control J4-23.
- DPDT relay B: K5 + K6, common control J4-23.
- DPDT relay C: K7 + K8 only if bench/firmware analysis proves these contacts must always transfer together.

If K7 and K8 genuinely require independent operation, use two SPDT relays for them instead of one DPDT relay. Select the exact relay only after measuring wetting current, maximum current, coil rail, contact voltage, shock/vibration, temperature, and required automotive/environmental qualification. The current files are not sufficient to choose a safe part number.

Add hardware interlocking or a single control for K7/K8 if the half-switched states are forbidden. Do not rely only on sequential firmware writes.

### Semiconductor evaluation direction

Use SN3257-Q1 only on a current-limited bench simulator. A practical evaluation is:

- U_SW1 SN3257QPWRQ1: four grouped paths K3-K6.
- U_SW2 SN3257QPWRQ1: K7 and K8 on channels 1 and 2, but only to evaluate the paired-control hypothesis. Channels 3 and 4 are grounded as unused inputs.
- VDD = clean 5.0 V bench supply. This permits 0-5 V signals while powered, but not 5 V signals when VDD is off.
- 100 nF X7R at each VDD pin plus one shared 1 uF X7R close to the two adapters.
- 10 kohm pull-down on each SEL and EN. EN may instead be tied directly to ground for a dedicated two-state A/B test.
- No vehicle connection.

## Pin-by-pin SN3257 bench schematic

Both PW and DYY packages use the same pin numbers. A = unpowered-relay NC/bypass side, B = energized-relay NO/injected side, D = relay COM side.

Companion drawing: `sn3257_bench_schematic.svg`.

### U_SW1: replaces K3-K6 for bench simulation

| Pin | Name | Bench net |
|---:|---|---|
| 1 | SEL | SW_GRP_SEL; 10 kohm to GND; drive from isolated bench logic only |
| 2 | S1A | K3_NC_J4_13 |
| 3 | S1B | K3_NO_DAC_J5_10_VB |
| 4 | D1 | K3_COM_J4_14 |
| 5 | S2A | K4_NC_J4_12 |
| 6 | S2B | K4_NO_DAC_J5_11_VA |
| 7 | D2 | K4_COM_J4_15 |
| 8 | GND | BENCH_GND |
| 9 | D3 | K5_COM_J4_16 |
| 10 | S3B | K5_NO_DAC_J6_8_VD |
| 11 | S3A | K5_NC_J4_11 |
| 12 | D4 | K6_COM_J4_17 |
| 13 | S4B | K6_NO_DAC_J6_9_VC |
| 14 | S4A | K6_NC_J4_10 |
| 15 | active-low EN | SW_GRP_EN_N; 10 kohm to GND (or direct GND for two-state test) |
| 16 | VDD | BENCH_5V; 100 nF X7R to pin 8 at the IC |

### U_SW2: paired-only K7/K8 experiment

| Pin | Name | Bench net |
|---:|---|---|
| 1 | SEL | SW_PAIR_SEL; 10 kohm to GND; one control changes K7 and K8 together |
| 2 | S1A | K7_NC_J4_9 |
| 3 | S1B | K7_NO_J4_8 |
| 4 | D1 | K7_COM_J4_18 |
| 5 | S2A | K8_NC_J4_8 |
| 6 | S2B | K8_NO_J4_9 |
| 7 | D2 | K8_COM_J4_19 |
| 8 | GND | BENCH_GND |
| 9 | D3 | GND (unused channel) |
| 10 | S3B | GND (unused channel) |
| 11 | S3A | GND (unused channel) |
| 12 | D4 | GND (unused channel) |
| 13 | S4B | GND (unused channel) |
| 14 | S4A | GND (unused channel) |
| 15 | active-low EN | SW_PAIR_EN_N; 10 kohm to GND (or direct GND for two-state test) |
| 16 | VDD | BENCH_5V; 100 nF X7R to pin 8 at the IC |

This second adapter intentionally cannot test K7 and K8 independently. That limitation is the compatibility finding, not a missing wire.

## Adafruit 1207 adapter wiring

The Adafruit board is a straight 16-pin breakout: IC pin N goes to breakout header position N. Use the TSSOP side, orient the SN3257 pin-1 mark to the breakout pin-1 mark, and continuity-check every header before power. The two header rows are 0.6 inches apart on 0.1 inch pitch. Do not infer pin orientation from how the adapter happens to sit on a breadboard.

See `sn3257_adafruit1207_pinmap.csv` for a connector-ready table.

## Bench-only wiring diagram

```text
Sensor simulator A ---- SxA   SN3257   Dx ---- ECU-load simulator
DAC simulator B ------- SxB      |
                                SEL <--- guarded bench switch / logic
                                 EN --- 10k to GND
                                  |
                           5.0 V, current limited

No Nissan harness, pedal, brake actuator, steering circuit, or vehicle power is used.
```

For each channel, use two independent 0-5 V sources through at least 1 kohm current-limiting resistors during the first switching tests and a 10 kohm load at D. These resistor values are for bench fault containment only; they are not proposed production values.

## Placement and routing plan

Companion concept drawing: `pcb_placement_plan.svg`.

### Mechanical-relay production option

- Remove J7 and its 133.25 mm x 52 mm module courtyard/footprint.
- Reserve the former J7 region for the compact relays and their drivers. Place contact pins toward J4 and DAC traces; place coils and drivers toward the logic side.
- Keep NC/COM/NO routing short, paired by function, and clearly labeled. Do not run sensor traces parallel to ESP32 antenna, CAN, relay coil, or switching-regulator traces.
- Keep the ESP32 antenna keep-out free of copper and components.
- Put a test point on every COM, NC, NO, control, 5 V, 3.3 V, ground, and coil-supply net.
- Maintain a continuous ground plane under semiconductor signal switches. Keep relay contact isolation clearances per the selected relay and voltage/fault requirements.
- Add individual flyback suppression at every discrete relay coil; choose diode/TVS strategy to meet required release time. Do not reuse the module's undocumented suppression assumptions.

### SN3257 prototype/possible later production

- Use PW/TSSOP for hand-built prototypes. Use DYY only for assembly-house production after the circuit is validated; DYY is 4.1-4.3 mm by 1.9-2.1 mm, 0.5 mm pitch, with a 1.05 mm x 0.30 mm example land.
- PW is TI package drawing PW0016A: body 4.9-5.1 mm by 4.3-4.5 mm, 0.65 mm pitch, with a 1.50 mm x 0.45 mm example land and approximately 5.8 mm overall land-pattern span. It is much easier to inspect and rework.
- Place each 100 nF capacitor directly between pins 16 and 8 with no signal trace between the capacitor and IC.
- Place switches near the J4 connector-side entry to minimize vehicle-net stubs; route DAC branches separately and join only at switch pins.
- Avoid test-point stubs on high-impedance analog nets. Use compact pads immediately adjacent to the route.
- Keep all six channels over a quiet solid ground reference. Do not share return neck-downs with CAN transceiver or relay/actuator current.

## Provisional BOM changes

### Bench evaluation BOM

| Qty | Item | Part/value | Notes |
|---:|---|---|---|
| 2 | Quad SPDT switch | SN3257QPWRQ1 | TSSOP-16; bench only |
| 2 | Breakout | Adafruit 1207 | Use TSSOP side |
| 2 | Local bypass capacitor | 100 nF, X7R, >=16 V | One per IC, pins 16-8 |
| 1 | Local bulk capacitor | 1 uF, X7R, >=16 V | Near both adapters |
| 4 | Logic pull-down | 10 kohm, 1% | SEL and active-low EN for both ICs |
| 12 | Bench source resistor | 1 kohm, 1% | Current limitation for first six-channel tests |
| 6 | Simulated load | 10 kohm, 0.1% preferred | Initial ECU input simulator |
| 1 | Fused/current-limited 5 V supply | <=50 mA initial limit | Raise only after expected-current calculation |
| 1 set | Test headers/wire | keyed and labeled | No loose dupont leads for fault tests |

### Remove only after architecture approval

- J7 eight-relay module.
- J7 custom footprint and its 37-pin through-hole interface.
- J7 IN1/IN2 traces and pads, which presently energize unused relays.
- Relay-module VCC/GND/JD-VCC connections if they serve no other function.
- J4 pin 22 only if it is proven to be solely the relay JD-VCC feed.

Do not delete J4 pin 22, J4 pin 23, or any harness net based only on the current drawings.

## ERC/DRC checklist

- All switch pins use the verified TI pin numbers, not a generic 74x3257 symbol assumption.
- EN has an overbar/active-low name and a deterministic external bias.
- SEL=0 maps to the intended bypass A path on every channel.
- No signal exceeds 0-5.5 V while powered or 0-3.6 V while the SN3257 supply is below 1.5 V.
- Worst-case current, including faults, is below 25 mA per SN3257 signal pin.
- Unused SN3257 D/S pins are grounded.
- All control pins are tied to defined levels and remain within 0-5.5 V during all power sequences.
- 100 nF decoupling is within a few millimeters of each VDD/GND pair.
- No NC and NO net is accidentally shorted by copper, test points, or adapter orientation.
- K7/K8 forbidden intermediate states are either impossible in hardware or explicitly tested safe.
- Analog routes avoid the ESP32 antenna, CAN lines, clocks, and relay/actuator current loops.
- Production footprint is checked against TI DYY0016A or the current PW drawing.
- Run KiCad ERC and DRC after a real revised schematic/PCB exists; the current environment has no KiCad CLI, so no tool-generated report was possible.

## Bench validation matrix and limits

See `bench_test_matrix.csv` for the detailed sequence. Minimum gates before any vehicle-related discussion:

1. Continuity-map every relay terminal unpowered and energized; the table above must match exactly.
2. Measure each vehicle-side signal with the existing system only: minimum, maximum, source impedance, load impedance, steady current, inrush, frequency content, ground offset, and behavior during vehicle wake/sleep.
3. Measure K7/K8 current and verify whether either single-relay intermediate state occurs in firmware or during reset.
4. Confirm installed relay coil voltage and actual JD-VCC voltage.
5. On simulators, demonstrate voltage error <= the Nissan diagnostic tolerance, not an arbitrary percentage. Until that tolerance is known, use a provisional engineering target of <=5 mV static error and <=10 mV transient deviation for screening only.
6. Demonstrate no back-powering above 100 uA into any unpowered rail during bench screening. This is a provisional screening limit, not a vehicle requirement.
7. Power-off test at 3.6 V maximum for SN3257. A 5 V power-off test is expected to be outside the data-sheet recommended condition and is a design failure, not a characterization target.
8. Perform open/short fault injection only through current-limiting resistance and with no vehicle hardware attached.

## Unresolved measurements/questions

- What are the official J4 pin names and vehicle connector/harness destinations for pins 8-19, 22, and 23?
- Are K3/K4 truly future steering, or do they already carry a live vehicle function?
- Are K5/K6 the two accelerator sensor channels? What are their transfer functions and plausibility limits?
- What exactly do K7/K8 switch, and what current flows in each state?
- Must K7 and K8 always transfer simultaneously? What happens during the half-switched states?
- Is J4-23 an external key/enable input, a ground, or another control source?
- Are the relay-module inputs active-low, and what are their pull-ups/pull-downs when the ESP32 or 5 V rail is absent?
- Is J4-22 actually 12 V? If so, why does the documentation/photo show SRD-05VDC relays?
- What are the vehicle signal normal, cranking, jump-start, reverse-polarity, load-dump, ESD, and short-to-battery/ground requirements?
- What diagnostic currents and pull-up/pull-down resistances are present in the Nissan ECU?
- What voltage error, ratiometric error, stuck-at behavior, and response time trigger a DTC or unsafe command?
- Is contact galvanic isolation a formal safety requirement or merely a consequence of the module choice?
- What is the required safe state when this board is off: true pedal/brake bypass, open circuit, or another state?
- Where is the firmware that drives J3 pins 25/26, and what does it do at boot, reset, watchdog expiry, brownout, and CAN loss?

## Source inventory used

- `/Users/howeth/Desktop/MiLa/MILA_CONTEXT.md` - project context only; no circuit parameters.
- `/Users/howeth/Desktop/MiLa/capstone_Oscar_Zheng_Jared_05032026/Schematics/DBWSchematic.pdf` - conceptual one-page wiring drawing.
- `/Users/howeth/Desktop/MiLa/capstone_Oscar_Zheng_Jared_05032026/Schematics/DBWSchematicComponents.pdf` - photographed module/connector pin references.
- `/Users/howeth/Desktop/MiLa/capstone_Oscar_Zheng_Jared_05032026/PCB_1.0/PCB1.2.kicad_sch` - earlier editable schematic.
- `/Users/howeth/Desktop/MiLa/capstone_Oscar_Zheng_Jared_05032026/PCB_1.0/PCB1.2.kicad_pcb` - earlier editable PCB.
- `/Users/howeth/Desktop/MiLa/capstone_Oscar_Zheng_Jared_05032026/PCB_1.0/PCB1.2.kicad_pro` - earlier project settings.
- `/Users/howeth/Desktop/MiLa/capstone_Oscar_Zheng_Jared_05032026/PCB_1.0/PCB1.2GBR/` - earlier Gerber/drill set.
- `/Users/howeth/Desktop/MiLa/capstone_Oscar_Zheng_Jared_05032026/PCB_2.0/PCBGerberFiles/PCB1.2.kicad_sch` - current editable schematic and primary net evidence.
- `/Users/howeth/Desktop/MiLa/capstone_Oscar_Zheng_Jared_05032026/PCB_2.0/PCBGerberFiles/PCB1.2.kicad_pcb` - current editable PCB and primary routing evidence.
- `/Users/howeth/Desktop/MiLa/capstone_Oscar_Zheng_Jared_05032026/PCB_2.0/PCBGerberFiles/PCB1.2.kicad_pro` - current project settings.
- `/Users/howeth/Desktop/MiLa/capstone_Oscar_Zheng_Jared_05032026/PCB_2.0/PCBGerberFiles/8-Relay Module.kicad_mod` - custom module footprint and pin labels.
- `/Users/howeth/Desktop/MiLa/capstone_Oscar_Zheng_Jared_05032026/PCB_2.0/PCBGerberFiles/PCB1.2GBR/PCB1.3/` - current Gerber/drill set.
- `/Users/howeth/Desktop/MiLa/capstone_Oscar_Zheng_Jared_05032026/PCB_2.0/PCBGerberFiles.zip` - archive duplicate of current source/Gerbers.
- `/Users/howeth/Desktop/MiLa/capstone_Oscar_Zheng_Jared_05032026/PCB_2.0/Final PCB.jpeg` - routed-board view.
- `/Users/howeth/Desktop/MiLa/capstone_Oscar_Zheng_Jared_05032026/PCB_2.0/PCB Case 1.HEIC` - assembled board/enclosure photograph.
- `/Users/howeth/Desktop/MiLa/capstone_Oscar_Zheng_Jared_05032026/PCB_2.0/PCB Case 2.HEIC` - assembled board/enclosure photograph.
- `/Users/howeth/Desktop/MiLa/capstone_Oscar_Zheng_Jared_05032026/PCB_2.0/PCBGerberFiles/PCB test/PCB test.kicad_sch` - unrelated/incomplete ESP32 test schematic; no switch design.
- `/Users/howeth/Desktop/MiLa/capstone_Oscar_Zheng_Jared_05032026/PCB_2.0/PCBGerberFiles/PCB test/PCB test.kicad_pcb` - empty PCB shell.

No BOM, firmware, Nissan connector document, vehicle wiring diagram, measurements, or local component datasheets were present.

External component references used:

- TI SN3257-Q1 Rev. D data sheet: https://www.ti.com/lit/ds/symlink/sn3257-q1.pdf
- TI SN3257-Q1 product page: https://www.ti.com/product/SN3257-Q1
- TI DYY0016A package drawing: https://edgeworker.ti.com/lit/pdf/mpss115c
- TI PW0016A package drawing is included in the SN3257-Q1 data-sheet package section; TI land pattern is 16 x 1.50 mm by 0.45 mm at 0.65 mm pitch.
- Adafruit 1207 product page: https://www.adafruit.com/product/1207
- TI TS5A23157-Q1 Rev. B data sheet (comparison only): https://www.ti.com/lit/ds/symlink/ts5a23157-q1.pdf

## Source-file change decision

The original KiCad sources were not modified. Although editable, they do not contain named vehicle nets, formal relay symbols, or enough electrical requirements to choose a production-safe replacement. Creating a routable vehicle PCB now would falsely imply that the architecture had passed the missing safety and electrical gates. This review and the bench-only mapping files are the new revision artifacts.
