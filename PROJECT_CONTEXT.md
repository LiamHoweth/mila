# MiLa Nissan DBW and comma 4 Project Context

Last updated: 2026-09-21

## Purpose

This is the starting document for AI agents and engineers working on the MiLa
Nissan drive-by-wire, ESP32, CAN, and comma 4 integration project. Read this
before proposing architecture, changing firmware, editing the PCB, or testing
hardware.

This file separates confirmed evidence from provisional assumptions. It is not
a vehicle approval, safety case, wiring authorization, or substitute for bench
measurements.

The broader, user-supplied lab description is in `MILA_CONTEXT.md`. Detailed
electrical evidence and test procedures are in the files listed under
`Source map` below.

## Project objective

MiLa is developing a lower-cost autonomous research vehicle based on a Nissan
LEAF and an existing ESP32 drive-by-wire interface board. The current work has
two related but distinct tracks:

1. Integrate a comma 4 and openpilot through the purchased Nissan comma harness
   for perception, vehicle-state parsing, planning, driver monitoring, logging,
   and safety-gated CAN control.
2. Understand and improve the existing ESP32/DAC/relay board that can substitute
   analog accelerator, brake, and steering-related signals.

The desired long-term division of responsibility has not been finalized. A
safe candidate architecture is:

```text
Vehicle CAN -> comma harness/panda -> comma 4/openpilot
                                      |
                                      +-> high-level bounded request
                                              |
                                              v
                                     supervised ESP32 DBW board
                                              |
                                  analog outputs / separate actuator hardware
```

For CAN actuation already supported by openpilot, the preferred path is:

```text
openpilot -> sendcan -> panda/opendbc safety -> vehicle CAN
```

Do not place an unconstrained ESP transmitter after panda and assume panda still
protects the vehicle. Panda can only validate the frame that passes through
panda; it cannot validate a frame later changed, delayed, repeated, or created
by the ESP.

## Vehicle identity and support status

- Prior project discussion described the target as a Nissan LEAF, possibly
  model year 2025. The exact VIN/model year/trim must be confirmed before using
  any wiring, DBC, harness, or control assumption.
- The purchased comma harness must be identified as Nissan A or Nissan B,
  including its generation/revision.
- Current upstream openpilot documentation reviewed on 2026-09-21 lists Nissan
  LEAF 2018-23 support with ProPILOT Assist. A 2025 LEAF must not be assumed to
  match that port.
- The upstream Nissan openpilot port currently sends steering-angle control,
  cruise cancellation, and applicable LKAS HUD messages. Nissan stock ACC
  remains responsible for longitudinal acceleration and braking.
- A DBC describes bit layout and scaling. It does not prove that an ID is
  present on this exact vehicle/bus, authorize transmission, or establish safe
  actuator behavior.

## System inventory

### Confirmed from workspace or supplied source

- The user identifies the controller as a 38-pin ESP32-WROOM-32D development
  board. The supplied reference image shows a CP2102 USB-to-UART interface, an
  AMS1117-family 3.3 V regulator, micro-USB, and a header pin labeled `V5`.
  Confirm the markings on the physical board before relying on the image for a
  power or pin-level decision.
- Two MCP4728 four-channel DACs on separate ESP32 I2C controllers.
- MCP2515 Classical CAN controller over SPI, configured in supplied firmware
  for 500 kbit/s with an 8 MHz oscillator assumption.
- Existing eight-relay module footprint, with six contact groups currently
  used in the PCB evidence.
- comma 4, comma harness box, and purchased Nissan vehicle harness.
- PCB 1.0 and PCB 2.0 KiCad source and fabrication files under
  `capstone_Oscar_Zheng_Jared_05032026/`.
- Guarded ESP32-to-comma CAN heartbeat firmware under
  `firmware/comma4_can_bench/`.

### Must still be physically verified

- Exact manufacturer/revision of the physical 38-pin ESP32 board and whether
  its USB and `V5` power paths include reverse-current protection.
- Exact MCP2515 module, CAN transceiver, logic voltage, and oscillator marking.
- Exact vehicle year/trim and Nissan A/B harness.
- Connector pin names and destinations for the DBW board and vehicle harness.
- Normal and fault voltage/current/impedance for every intercepted circuit.
- Relay module coil/JD-VCC voltage and input polarity.
- Whether K7 and K8 are allowed to change independently.
- Required safe behavior for each signal during MCU reset, brownout, board power
  loss, connector removal, and CAN loss.

## Architecture findings from prior discussions

### CAN node versus CAN gateway

One MCP2515 connected to one CAN pair makes the ESP another node on that bus.
The vehicle, ESP, and comma can all hear the same frame; the frame does not pass
through the ESP merely because all three are connected.

A true inline bidirectional gateway requires two electrically independent CAN
channels and two transceivers:

```text
vehicle CAN <-> controller/transceiver A <-> ESP32
             ESP32 <-> controller/transceiver B <-> comma-side CAN
```

For Classical CAN, a classic ESP32 could potentially use one MCP2515 channel
plus its internal TWAI controller and an external transceiver. CAN FD would
require CAN-FD-capable controllers such as MCP2518FD or an appropriate
multi-CAN automotive controller.

The project has not established that an inline ESP gateway is necessary. A
simpler and safer arrangement is often to let the comma harness/panda connect
directly to the vehicle and use the ESP only for auxiliary sensors or bounded
high-level requests.

### comma 4 role

The comma 4 provides cameras, compute, GPS/IMU, storage/connectivity, openpilot,
DBC parsing, and a CAN/CAN-FD vehicle interface with panda safety enforcement.
It is not a general analog-output, PWM motor-driver, relay-driver, or
high-current actuator controller.

For the current Nissan port, comma/openpilot CAN authority is principally
steering plus cruise cancellation and HUD traffic. Direct Nissan longitudinal
control would be a new safety-critical port requiring message discovery,
controller implementation, panda safety changes, tests, HIL, and closed-course
validation. It is not just a DBC edit.

## Supplied ESP32 auto-sweep firmware

Reference source supplied on 2026-09-21:

`/Users/howeth/Downloads/FabriceBoard_PID_AutoSweep(1).ino`

Treat this file as design intent and experimental reference, not approved
vehicle firmware. It was inspected but has not been compiled, flashed, or
physically validated in this workspace.

### What the sketch implements

- ESP32 Arduino firmware with a 100 Hz control loop.
- Two MCP4728 DACs, both at address `0x60`, on separate I2C buses:
  - DAC1: GPIO 21 SDA / GPIO 22 SCL.
  - DAC2: GPIO 33 SDA / GPIO 32 SCL.
- DAC1 channels A/B/C/D are assigned brake1, brake2, accelerator1,
  accelerator2.
- DAC2 channels A/B are assigned steering1 and steering2.
- MCP2515 SPI pins are SCK 18, MISO 19, MOSI 23, CS 5.
- MCP2515 initialization assumes Classical CAN at 500 kbit/s and an 8 MHz
  oscillator.
- Three active-low relay outputs are GPIO 15, GPIO 4, and GPIO 0. The code
  always changes all three together.
- GPIO 12 is driven high as `MODE_SRC`; GPIO 13 is read as `MODE_SNS`.
- After boot it waits 15 seconds, performs three 12-second triangle sweeps, and
  then de-energizes the relays and remains in a done state.
- Open-loop steering command is a differential offset: steer1 is center plus
  offset and steer2 is center minus offset.
- The first cycle ramps amplitude from zero to full amplitude.
- Output offset changes are slew-limited to 0.010 V per 100 Hz tick.
- Optional differential dither is 8 DAC counts at 4 Hz.
- Optional closed-loop mode reads steering feedback on CAN ID `0x002`, bytes
  0-1 as signed little-endian, divided by 10.
- Serial output at 115200 prints state and telemetry but accepts no commands.

### Calibration constants embedded in the sketch

These are code constants, not independently verified measurements:

| Signal | Value |
|---|---:|
| Accelerator channel 1 rest | 0.37 V |
| Accelerator channel 2 rest | 0.75 V |
| Brake channel 1 rest | 3.38 V |
| Brake channel 2 rest | 1.48 V |
| Steering center, both channels | 2.47 V |
| DAC full-scale assumption | 4.096 V |
| Open-loop steering amplitude | +/-0.30 V differential offset |
| Closed-loop target amplitude | +/-20 degrees |
| Closed-loop output saturation | +/-250 DAC counts, approximately 0.25 V |

### Closed-loop guards present in the sketch

- CAN feedback timeout: 400 ms.
- Non-convergence threshold: error above 8 degrees without at least 1 degree
  improvement for 4 seconds.
- Absolute error trip: 250 degrees.
- PID constants: KP 1.2, KI 1.5, KD 0.3.
- Integral clamp and output saturation are implemented.
- Dropping the mode switch can call the safe path only when
  `REQUIRE_SWITCH` is enabled.

### Important unresolved risks in the supplied defaults

- `REQUIRE_SWITCH` is currently `0`. The code therefore begins actuation
  automatically 15 seconds after boot without a physical deadman switch.
- `USE_CAN_FEEDBACK` is currently `0`. Missing CAN feedback does not prevent
  the default open-loop sweep.
- Relay engagement is not blocked when either MCP4728 initialization fails.
  A missing/unpowered DAC can therefore coexist with engaged relays.
- CAN initialization failure does not block the default open-loop sweep.
- GPIO 0, 2, and 15 have ESP32 boot/strapping implications that must be
  checked against the exact module and relay interface.
- No independent hardware watchdog, relay power cutoff, redundant plausibility
  monitor, or brownout-safe actuation inhibit is demonstrated by this sketch.
- The comments claim that powering only from the car avoids USB ground offset;
  that is a hypothesis requiring measured ground/reference and transient
  analysis, not a sufficient safety argument.
- Upstream Nissan DBC source defines CAN ID `0x002` as steering-angle data with
  a signed 16-bit signal and a `-0.1` scale. The sketch decodes signed raw data
  with a positive `0.1` scale and defaults `FEEDBACK_SIGN` to `+1`. Direction
  must be verified from captured frames and known wheel motion before enabling
  feedback.
- The sketch's rest voltages, sweep range, and assumption that the dual
  channels remain mutually plausible have not been checked against the exact
  vehicle ECUs.

Do not run this auto-sweep firmware on a vehicle merely because the code calls
its terminal states `SAFE`. The physical safe state depends on relay wiring,
DAC behavior, vehicle diagnostics, and actuator response.

## Existing PCB and relay findings

PCB 2.0 evidence currently indicates three relay control domains:

- K3-K6 share one control net at J4 pin 23.
- K7 is controlled separately from ESP32 header J3 pin 25.
- K8 is controlled separately from ESP32 header J3 pin 26.

The current mechanical Form-C contacts appear to return to normally-closed
stock/bypass paths when relay power is removed. This must be continuity-tested,
but it is a materially different failure mode from an unpowered analog switch.

Earlier evaluation found:

- Two SN3257-Q1 devices cannot reproduce all three control domains.
- Three SN3257-Q1 devices can reproduce the grouping in principle but become
  high impedance when unpowered; they do not provide passive NC bypass.
- Powered-off SN3257 signal limits, on resistance, leakage, current limits, and
  lack of automotive transient protection remain concerns.
- Compact sealed Form-C/DPDT mechanical signal relays remain the conservative
  direction if passive stock bypass on total board power loss is required.
- K7/K8 intermediate states may cross-connect both outputs to one source and
  must be understood before any hardware or firmware change.

The auto-sweep sketch and PCB analysis do not yet align perfectly: the sketch
commands only three relay GPIOs together, while PCB evidence shows K3-K6,
K7, and K8 as three independently wired control domains. Resolve which board,
adapter, or harness the sketch actually targets before assuming pin equivalence.

## Current ESP-to-comma CAN diagnostic

`firmware/comma4_can_bench/` is a separate guarded communications diagnostic.
It is not the auto-sweep/DBW firmware.

It supports MCP2515 and MCP2518FD and transmits only:

- Standard CAN ID `0x5A5`.
- Classical CAN at 500 kbit/s.
- Eight data bytes: ASCII `MILA`, 16-bit sequence, controller marker, version.
- Two frames per second.
- Maximum 30-second transmit window.
- Transmission requires both a GPIO 27-to-GND jumper and the serial command
  `ARM`.

Related tools:

- `tools/comma_can_listener.py`: proves raw comma cereal `can` reception and
  reports the source bus.
- `tools/comma_dbc_listener.py`: proves upstream `CANParser` decoding.
- `tools/mila_bench.dbc`: bench-only DBC for ID `0x5A5`.
- `tests/test_comma_can_listener.py`: host-side payload decoder tests.

Validation already completed:

- All four PlatformIO environments compiled on 2026-09-21.
- Four listener unit tests passed.
- Current upstream opendbc successfully decoded the fixture payload.

Not yet completed:

- MCP2515 physical loopback on the actual module.
- Isolated ESP-to-comma physical CAN test.
- Reverse comma-to-ESP bench message test.
- Sustained load, loss, latency, restart, or error-injection testing.
- Any vehicle-connected transmission.

ID `0x5A5` was absent from the reviewed Nissan LEAF DBC, but that does not prove
it is unused on every bus, year, or trim. Passive capture is required before
any vehicle connection.

## Safety architecture requirements

Keep observation, decision, and actuation conceptually separate:

```text
Observation: vehicle CAN -> comma and/or ESP receive-only parsing
Decision:    comma/openpilot or lab planner -> desired bounded action
Actuation:   safety supervisor -> controlled CAN or analog output -> vehicle
```

Minimum requirements before vehicle actuation work:

- Exact vehicle, connector, harness, bus, bitrate, and termination identified.
- Passive captures establish real message IDs, periods, counters, checksums,
  signs, scales, and source buses.
- Every intercepted analog path is measured for voltage, current, source/load
  impedance, diagnostic behavior, ground offset, bandwidth, and transients.
- Stock bypass behavior is verified with the board unpowered and unplugged.
- Outputs are inhibited during boot, reset, brownout, watchdog timeout, stale
  command, missing sensor, and invalid/plausibility-failed command.
- A physical enable/deadman and independent output cutoff are present.
- Dual-channel accelerator/brake/steering signals remain within the vehicle's
  correlation and diagnostic requirements in normal and fault conditions.
- Commands have rolling counters/freshness, bounds, rate limits, and a defined
  safe state.
- Bench simulators and current-limited supplies are used before ECU simulators,
  HIL, dynamometer, or closed-course vehicle testing.
- A second person and immediate physical power removal are available for later
  controlled vehicle tests. No public-road experimentation.

`safe`, `done`, or `trip` in software names are not evidence that the physical
system is fail-safe.

## Recommended next milestones

1. Record the exact Nissan model year/trim, harness A/B label and revision,
   comma harness-box generation, ESP32 module, MCP2515 crystal, and transceiver.
2. Preserve the supplied auto-sweep sketch unchanged as reference; do not make
   it the active vehicle firmware yet.
3. Complete the MCP2515 internal loopback test using
   `esp32_mcp2515_loopback`.
4. Complete the isolated ESP-to-comma `0x5A5` test described in
   `docs/comma4-can-bench-test.md`, with the vehicle disconnected.
5. Add and validate a harmless reverse comma-to-ESP heartbeat on the same
   isolated bench network.
6. Passively capture every accessible Nissan harness bus and compare CAN
   `0x002` against known steering motion and upstream DBC scaling.
7. Map the supplied firmware pins to the exact PCB revision and connector nets.
8. Run the existing relay continuity and control-group tests in
   `docs/bench_test_matrix.csv`.
9. Build sensor/ECU simulators for the six intercepted paths and validate
   calibration, correlation, reset, brownout, open/short, and stale-command
   behavior with no vehicle connected.
10. Decide whether comma/panda will perform supported CAN actuation, whether the
    ESP needs only high-level commands, or whether a separately reviewed analog
    DBW safety controller is required.

## Unresolved system questions

- What exact Nissan LEAF model year and ProPILOT configuration is the project
  using?
- Is the vehicle supported by the upstream Nissan port, or will it require a
  new port?
- Is the purchased connector Nissan A or Nissan B, and which physical buses are
  present at the harness?
- Is the final ESP role a CAN sensor node, a true two-channel gateway, an analog
  DBW controller, or some combination?
- What functions does the lab need beyond current openpilot steering and stock
  Nissan ACC?
- Does the existing board intercept real pedal/steering sensors, command an
  external linear actuator, or both?
- Which exact PCB revision and relay adapter does the auto-sweep firmware target?
- Why does the sketch gang all three relay GPIOs when PCB evidence exposes
  three control domains?
- Are the embedded rest voltages measurements from this exact vehicle, and what
  are their tolerance and correlation envelopes?
- Does CAN `0x002` appear on the bus connected to this MCP2515, and what is the
  verified sign/scale?
- What is the required system behavior if the comma, ESP, DAC, CAN link, one
  sensor channel, or power rail fails independently?

## Source map

Start with these files:

- `MILA_CONTEXT.md`: broad user-supplied MiLa laboratory background.
- `AGENT_NOTES.md`: concise current state and critical warnings.
- `docs/comma4-can-bench-test.md`: isolated ESP/MCP-to-comma procedure.
- `firmware/comma4_can_bench/`: guarded heartbeat firmware.
- `tools/comma_can_listener.py`: comma raw CAN listener.
- `tools/comma_dbc_listener.py`: DBC parsing listener.
- `tools/mila_bench.dbc`: bench-only heartbeat DBC.
- `docs/dbw-switch-redesign-review.md`: PCB net evidence, relay reconstruction,
  SN3257 analysis, open questions, and test planning.
- `docs/six_relay_mapping.csv`: reconstructed K3-K8 mapping.
- `docs/bench_test_matrix.csv`: non-vehicle electrical validation sequence.
- `docs/sn3257_adafruit1207_pinmap.csv`: bench adapter mapping only.
- `capstone_Oscar_Zheng_Jared_05032026/PCB_2.0/PCBGerberFiles/PCB1.2.kicad_sch`:
  primary editable PCB 2.0 schematic evidence.
- `/Users/howeth/Downloads/FabriceBoard_PID_AutoSweep(1).ino`: supplied automatic
  sweep firmware reference; external to the workspace and not validated.

Prior tasks reviewed for this context:

- `Test ESP CAN to Comma 4` (`01a0c48e-f7cc-75c1-9382-52e4352a11a0`).
- `CAN Gateway Architecture` (`6ab15251-8be0-83ea-adfc-d1e3574b027e`).
- `Assess SN3257 relay replacement` (`01a0b54a-e693-7053-aa26-cf6c953a6cb9`).
- `Plan TS3A5018 relay replacement` (`01a0ac51-0487-7353-b269-1e40d8638ecb`).
- `Add MiLa context markdown` (`01a0a09d-c9c6-74b1-9fc9-d72010db669e`).

When later measurements contradict this document, update the confirmed facts,
retain the old evidence in version control, and identify the measurement and
hardware revision that changed the conclusion.
