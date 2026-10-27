# MiLa passive bypass bench board — revision A

This is an isolated, current-limited simulator contact board. **No vehicle use.**
It preserves the three existing control domains and six passive NC paths using
four nonlatching Omron G6K-2P-Y DC5 relays. RLY3/RLY4 each use one pole; their
second poles are explicitly unconnected. K7/K8 independence is preserved.

## Electrical envelope and interfaces

- JPWR1 pin 1: regulated 4.75–5.25 V after an external physical series-enable
  switch. JPWR1 pin 2: logic/coil GND. Set the supply current limit to 150 mA.
- JCTRL1: 1 REQ_GROUP, 2 REQ_K7, 3 REQ_K8, 4 COIL_PERMIT, 5 GND,
  6 CARRIER_5V_FEEDBACK (direct connection to 5V_RAW). Digital inputs 1–4
  are active high and nominal 3.3 V, including COIL_PERMIT from the supervisor.
  Feedback pin 6 carries up to 5.25 V to the external
  resistor-divider monitor only; never connect it to an ESP GPIO or supply it.
  HIGH must be at least 2.60 V at the board header, LOW at most 0.4 V.
  All N-FET gates have 330-ohm series resistance. Q1–Q4 off bias is 10 kohm;
  Q6 permit-gate off bias RPD6 is 82 kohm, matched to the external supervisor's
  low-load LVC output guarantee. P-FET gate-to-source bias RPG1 stays 10 kohm.
  All carrier resistors require 1% tolerance, including RPD6; the gate-voltage
  bounds must not be extended to unspecified resistor substitutions.
- J4B1 is a 12-pin bench subset of original J4; JDAC1 is a 4-pin bench subset of
  original J5/J6. **Neither connector shares the original physical pinout.**
  Use `pin_net_map.csv`; names preserve canonical original connector terminals.
  Headers are unshrouded and unkeyed: mark pin 1, check the fixture orientation
  against the assembly drawing, and add cable strain relief before testing.
- Each contact signal is limited to 0–5 V and 1 mA on the simulator. Contacts
  do not connect to board GND. Provide source/load references externally.
- External independent supervisor supplies COIL_PERMIT. This board does not
  implement watchdog, freshness, boot/brownout qualification, DAC validation,
  dual-channel plausibility, or a vehicle safety case.
- No energy storage or external source may feed COIL_5V. The P-FET body diode
  does not provide reverse-current blocking. Its source is 5V_RAW and drain is
  COIL_5V; reversing it defeats the power cutoff.

## Operation

COIL_PERMIT low or disconnected turns off the common high-side coil feed.
With COIL_PERMIT high, REQ_GROUP energizes RLY1/RLY2, REQ_K7 RLY3, and REQ_K8
RLY4. Healthy unpowered contacts connect 3–2 and 6–7; energized contacts connect
3–4 and 6–5. Relay supply removal eventually restores NC after mechanical
release and bounce. This is not instantaneous or immune to welded contacts.

The supervisor senses JCTRL1 pin 6 through its divider. Complete loss of this
control header or JPWR1 power drops carrier feedback and clears its ARM latch;
reconnection requires a new valid heartbeat qualification and manual ARM edge.
This does not detect every individual broken conductor or intermittent fault.

Flyback diode cathodes connect to COIL_5V, anodes to their coil drains. These
diodes protect drivers but lengthen release. Measure release/bounce/skew on
the actual assembled board, including high-side cutoff with a low-side stuck
on. K7/K8 mixed states remain reachable and are not declared vehicle-safe.

## Manufacturer pinout and local footprint correction

G6K-2P-Y DC5 coil 1(+), 8(-); pole A COM 3/NC 2/NO 4; pole B COM 6/NC 7/NO 5.
The manufacturer bottom-view drawing gives hole rows 0, 3.2, 5.4, 7.6 mm and
opposing row spacing 5.08 mm. The installed KiCad 10 G6K-2P-Y footprint has
NC pads 2/7 at 3.0 mm; the project-local footprint corrects them to 3.2 mm.
Hole diameter 0.85 mm and pad diameter 1.7 mm. Inspect a 1:1 print and real
relay before ordering. All FETs use SOT-23 pins 1 gate, 2 source, 3 drain.

Manufacturer sources:

- [Omron G6K](https://omronfs.omron.com/en_US/ecb/products/pdf/en-g6k.pdf),
  manufacturer THT G6K-2P-Y drawing and terminal arrangement.
- [AO3400A](https://www.aosmd.com/res/data_sheets/AO3400A.pdf)
- [AO3401A](https://www.aosmd.com/res/data_sheets/AO3401A.pdf)
- [Vishay 1N4148W-E3-08](https://www.vishay.com/docs/86356/1n4148w.pdf)

## CAD and verification

The 60×50 mm, two-layer, 1.6-mm board uses 0.25-mm traces, 0.20-mm clearance,
0.70/0.30-mm vias, and four 3.2-mm unplated mounting holes. Mechanical contacts
are separated from logic by the relay insulation; no semiconductor is placed
in an NC/COM/NO signal path. Bench headers are 2.54-mm friction-fit prototypes,
not an automotive connector solution. The PCB is reviewed against the same
component/pin manifest that creates the editable schematic and BOM.

Rebuild with KiCad's bundled Python:

```sh
/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.9/bin/python3.9 tools/build_passive_bypass_board.py
```

Review `validation/erc.json`, `validation/drc.json` including schematic parity,
`passive_bypass.net`, and `validation/commands.json`. Bench manufacturing files
under `manufacturing_bench_only/` are exported only if ERC/DRC/netlist commands
pass. Electrical CAD checks do not establish relay behavior or vehicle safety.
Original PCB1/PCB2 files and libraries are preserved.

## Required assembled-board acceptance

1. Without any supply, map all six NC connections and confirm all NO paths
   open, contact-to-logic isolation, no misplaced/mirrored relay pins.
2. With simulator sources/load current limited, check all eight combinations
   of REQ_GROUP/REQ_K7/REQ_K8 under valid permit against the canonical table.
3. Drop each request, permit, series-enable, power, and logic source separately;
   capture contact disconnect/NC restoration, bounce, skew, and coil current.
4. Hold each low-side driver on and remove high-side permit; then force Q5 on
   and verify request removal still releases each coil. Neither single cutoff
   failure is declared fail-safe against a concurrent other-driver fault.
5. Sweep 4.75–5.25 V with maximum four-coil load. Check thermal rise and verify
   the external supervisor withdraws permit before coil behavior is ambiguous.
6. Inspect soldering/polarities; perform 100%-net continuity before sources are
   attached. Do not connect a vehicle when these bench tests pass.
