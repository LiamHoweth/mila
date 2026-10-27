# ESP32 to comma 4 CAN bench test

## Goal and boundary

This test proves one narrow link:

```text
ESP32 -> SPI -> MCP2515 or MCP2518FD -> CAN transceiver -> CAN pair
       -> comma harness box / comma 4 panda -> pandad -> cereal `can`
       -> raw listener -> optional opendbc CANParser + DBC
```

It does **not** command steering, braking, throttle, cruise, or any Nissan ECU.
The firmware sends only a bench heartbeat on standard ID `0x5A5` at 2 Hz. The
payload is `MILA`, a 16-bit sequence, a controller byte (`0x15` or `0x18`), and
protocol version `0x01`.

An ESP transceiver attached directly to a vehicle-side CAN pair is an
independent bus node. Its frames do not pass through panda's transmit safety
checks before reaching the other nodes on that pair. The comma 4 can observe
those frames, but it is not a safety firewall for the ESP. This is why the
first physical test must be isolated and why this firmware cannot emit Nissan
control or diagnostic frames.

ID `0x5A5` is absent from the current upstream `nissan_leaf_2018` DBC. That is
not proof that the ID is unused on every Nissan, trim, model year, or bus. Keep
this test off a live vehicle network until a passive capture confirms there is
no collision. Never replace the test ID with a Nissan control or diagnostic ID.

## Why both controllers are supported

- MCP2515 supports Classical CAN 2.0B frames up to 1 Mbit/s. It is sufficient
  for this current 500 kbit/s, 8-byte Nissan/openpilot link test.
- MCP2518FD supports both Classical CAN and CAN FD. The included build forces
  `Normal20B` and an 8-byte Classical CAN frame for the Nissan test.
- A comma 4 being CAN-FD-capable does not make a Classical Nissan bus CAN FD.
  Bitrate and frame type are properties of the bus being joined.

The current upstream Nissan port assigns `nissan_leaf_2018_generated` to the
Leaf and constructs parsers for panda source buses 0, 1, and 2. The DBC tells
CANParser how a known frame's bits map to signals; it does not establish the
electrical link or discover where the frame entered the comma device.

## Required hardware checks

Before powering anything, record the exact labels on:

1. ESP32 board variant.
2. CAN controller (`MCP2515` or `MCP2518FD`).
3. CAN transceiver on the module.
4. Oscillator can (`8`, `16`, `20`, or `40 MHz`).
5. comma harness generation and Nissan A/B harness label.

Do not assume a generic MCP2515 module is ESP32-safe. Many boards use a 5 V
TJA1050/MCP2551-family transceiver and expose 5 V SPI logic. The ESP32 GPIO is
not 5 V tolerant. Use a verified 3.3 V-logic module/transceiver or proper level
translation. The CAN controller alone is not a physical-layer transceiver.

Use the purchased comma harness and harness box. Do not probe bare USB-C/OBD-C
contacts or feed an improvised supply into the comma 4. The official comma v3
harness-box schematic maps CAN0 to car, CAN1 to radar, CAN2 to camera, and CAN3
to comma power, but the exact accessible pair depends on Nissan A/B and the
connector orientation. Confirm the exact pair by schematic plus continuity;
do not rely on wire color alone.

## Wiring

Default ESP32 DevKit SPI pins in `include/can_config.h`:

| ESP32 | CAN module |
|---|---|
| GPIO 18 | SCK |
| GPIO 19 | SDO/MISO |
| GPIO 23 | SDI/MOSI |
| GPIO 5 | CS |
| GPIO 4 | INT (MCP2518FD only) |
| GPIO 27 | TX-enable jumper to GND |
| GND | Module GND and CAN-node ground/reference |

On the CAN side, connect CANH to CANH and CANL to CANL. Keep the pair twisted
and short. With all power off, measure resistance between CANH and CANL:

- About 60 ohms means two 120-ohm terminations are already present; do not add
  another termination.
- About 120 ohms means only one end is terminated; add one 120-ohm termination
  at the other physical end for the isolated bench.
- A very different value means stop and resolve the topology before power-up.

Use a fused, current-limited supply for bench equipment. Share only the ground
reference required by the selected transceiver/harness topology; do not connect
vehicle 12 V to an ESP32 or CAN module logic rail.

## Stage 1: controller-only loopback

Install PlatformIO, then build and upload the target that matches the module:

```sh
cd firmware/comma4_can_bench
pio run -e esp32_mcp2515_loopback
pio run -e esp32_mcp2515_loopback -t upload
pio device monitor -b 115200
```

For MCP2518FD, replace the environment with
`esp32_mcp2518fd_loopback`. Jumper GPIO 27 to GND and type `ARM` in the serial
monitor. A passing loopback prints matching `TX queued` and `RX` lines with ID
`0x5A5`. It stops automatically after 30 seconds. Type `STOP` or remove the
jumper to stop immediately.

Do not continue if initialization fails, RX does not mirror TX, or controller
error flags/counters rise. First verify SPI wiring and the oscillator constants
in `include/can_config.h`.

## Stage 2: isolated physical bus to comma 4

1. Remove power and configure the proper non-loopback build:

   ```sh
   pio run -e esp32_mcp2515
   pio run -e esp32_mcp2515 -t upload
   ```

   Use `esp32_mcp2518fd` for the FD-capable controller. It still sends a
   Classical CAN frame for this test.

2. Connect through a proper breakout/access harness to one verified comma CAN
   pair. Confirm H/L, ground reference, and termination with power off.
3. Power the comma 4 through the purchased harness/approved comma power path.
4. SSH into the comma 4. Copy `tools/comma_can_listener.py` to the openpilot
   checkout or another path under `/data`, then run it from `/data/openpilot`:

   ```sh
   cd /data/openpilot
   python3 /data/comma_can_listener.py --count 10 --timeout 20
   ```

5. Only after the listener is waiting, install the GPIO 27-to-GND jumper and
   type `ARM` in the ESP32 serial monitor.
6. Passing output reports ten valid heartbeats, the actual comma `src` bus, the
   counter, controller type, version, and raw bytes. Record the reported bus.
7. Remove the TX-enable jumper. Confirm the ESP32 prints `TX stopped`.

If ESP32 says frames were queued but comma sees nothing, do not increase the
rate or try Nissan IDs. Check, in order: oscillator selection, 500 kbit/s on
both nodes, H/L not swapped, common reference, termination, transceiver enable
pin/jumpers, CAN-controller error flags, the chosen harness side, and whether
pandad is publishing `can`.

## Stage 3: prove DBC parsing

After the raw listener identifies the bus, copy both
`tools/comma_dbc_listener.py` and `tools/mila_bench.dbc` to `/data`, then run:

```sh
cd /data/openpilot
python3 /data/comma_dbc_listener.py --bus 0 --dbc /data/mila_bench.dbc --count 10
```

Replace `0` with the bus reported in Stage 2. This uses the same upstream
`opendbc.can.parser.CANParser` shown in the supplied screenshot. A pass proves
the full raw-frame-to-DBC path. Keep this small DBC separate from the Nissan
production DBC; it is a diagnostic fixture, not vehicle knowledge.

## Vehicle gate

Do not connect the transmitter to the installed vehicle network until all of
these are recorded:

- exact Nissan model, model year, and harness A/B revision;
- passive capture of every harness bus and confirmed 500 kbit/s rate;
- no observed use of `0x5A5` on the selected bus;
- correct CANH/CANL continuity and about 60-ohm powered-off termination;
- controller loopback pass and isolated comma-link pass;
- a second person available to remove power, parked vehicle, wheels chocked,
  drive wheels lifted or dynamometer as appropriate, and no public-road test.

Any future Nissan message injection is a separate safety-reviewed task. Build
actuation through openpilot's upstream Nissan packer/controller and `sendcan`
path so panda safety gates comma-originated output. Do not use the external ESP
node to bypass that path or hand-author bytes from a DBC.

## Upstream references reviewed

- comma hardware repository, v3 `Harness_Box.pdf`, `Nissan_A_Harness.pdf`,
  `Nissan_B_Harness.pdf`, and `OBD-C.sch.pdf` at commit
  `530b7da136b6a6d4b0d37b95bdb3472c59f672f4`.
- openpilot `tools/scripts/car/can_printer.py` and pandad CAN conversion at
  commit `521db4c825d37eb5f29acf955daa88da003e4433`.
- opendbc Nissan `values.py`, `carstate.py`, and `can/parser.py` at commit
  `ba800b77187208286f39c22f692ac7c69e9324f2`.
- panda default Classical CAN bitrate (500 kbit/s) and safety firmware at
  commit `43ab39f7fb5dcad273e9f38cf215e3491f75b10d`.
