# Email: MiLa 8-Relay PCB Replacement Plan

**Suggested subject:** Current plan for reducing the MiLa DBW PCB relay section

Hi,

I wanted to send you an updated summary of the plan for replacing the large
8-relay module on the Nissan LEAF drive-by-wire PCB.

## Executive summary

The existing PCB uses an 8-relay module, but only six relay contact groups are
actually connected. The module is the largest part of the board, so replacing
it is the main opportunity to reduce the PCB size.

We originally considered replacing the relays with TS3A5018 or SN3257-Q1
solid-state analog switches. Those parts could reduce the footprint, but they
do not preserve the existing relays' most important apparent safety behavior:
when board power is lost, the mechanical normally closed contacts return the
vehicle to its stock signal paths. An unpowered analog switch instead becomes
high impedance and disconnects both the stock and generated signals.

The current production direction is therefore to replace the oversized module
with only the smaller mechanical Form-C relay contacts the circuit actually
needs. This should reduce the board size while preserving passive stock-signal
bypass during a total controller power loss.

No final relay part number or production PCB revision has been approved yet.
Several electrical measurements and continuity tests must be completed first.

## Existing board architecture

The board is an ESP32-based drive-by-wire interface containing:

- An ESP32 controller
- An ADS1115 ADC for reading analog feedback
- Two MCP4728 DACs for generating analog control voltages
- An MCP2515 for Classical CAN communication
- A vehicle interface connector
- An 8-relay module that switches between stock/manual wiring and generated
  drive-by-wire signals

The general signal flow is:

```text
Vehicle feedback -> ADC -> ESP32
Vehicle CAN <-> MCP2515 <-> ESP32
ESP32 -> DACs -> relay changeover -> vehicle inputs or actuator interface
```

The complete PCB is approximately 146 x 122 mm. The existing relay-module
footprint is approximately 133 x 52 mm, making it the dominant size constraint.

## Relay usage and control grouping

Although the installed module contains eight relays, the PCB routes only six
contact groups, identified as K3 through K8.

The current KiCad evidence shows three control domains:

| Relay paths | Control grouping | Provisional function |
|---|---|---|
| K3 and K4 | Shared control through J4 pin 23 | Two related steering/analog paths |
| K5 and K6 | Shared control through J4 pin 23 | Two related accelerator/analog paths |
| K7 | Independent control from ESP32 header J3 pin 25 | One side of a brake/actuator circuit |
| K8 | Independent control from ESP32 header J3 pin 26 | Other side of a brake/actuator circuit |

The functional descriptions are provisional. The PCB net connections are
known, but the exact vehicle connector functions still require wiring and
measurement confirmation.

## Existing mechanical-relay behavior

Each used relay appears to provide a Form-C/SPDT changeover:

```text
                         NC: stock signal
                                \
Vehicle or ECU connection ------ COM
                                /
                         NO: generated signal
```

When the relay is de-energized, COM connects to NC and the stock vehicle signal
passes through. When energized, COM connects to NO and the generated or
alternate signal is selected.

The important working assumption is that total board power loss returns the
contacts to NC, restoring stock wiring without requiring the ESP32, firmware,
DACs, or logic power. This is passive fail-bypass.

That behavior still needs to be confirmed on the actual hardware with an
unpowered continuity test.

## Why the TS3A5018 is not the full replacement

The TS3A5018 contains four bidirectional SPDT analog switches in one small IC.
It was initially considered for the four low-current analog paths.

Its limitations include:

- A 1.65-3.6 V supply range
- Analog signals restricted to the powered supply range
- Several ohms of on-resistance
- Shared selection across all four channels
- No galvanic isolation
- No passive normally closed path when unpowered
- No automotive Q1 qualification
- Inability to replace any path carrying motor or actuator current

It may be useful in low-voltage signal applications, but it is not a safe
blanket replacement for this relay module.

Official datasheet:
https://www.ti.com/lit/ds/symlink/ts3a5018.pdf

## Why the SN3257-Q1 is not currently the production solution

The SN3257-Q1 is an automotive-qualified quad SPDT analog switch with lower
resistance and a wider powered signal range than the TS3A5018.

### Control-group limitation

All four channels in one SN3257 share the same `SEL` and active-low `EN` pins.

One SN3257 could reproduce the grouped K3-K6 behavior. A second SN3257 cannot
independently control K7 and K8. Full control equivalence would require three
devices:

```text
SN3257 U1 -> K3, K4, K5 and K6
SN3257 U2 -> K7
SN3257 U3 -> K8
```

The proposed channel mapping would be:

```text
D = relay COM
A = relay NC / stock bypass
B = relay NO / generated signal
```

Three devices solve the control-group mismatch, but they do not solve the
power-loss problem.

### Power-loss limitation

When the SN3257 loses power, its signal pins become high impedance:

```text
Stock signal -----X----- ECU
Generated signal -X----- ECU
```

This is fail-open rather than fail-bypass. Neither source remains connected to
the ECU or actuator interface.

Other unresolved concerns include:

- Powered-off signals are specified only to 3.6 V.
- A vehicle signal near 5 V could exceed that powered-off specification.
- Signal-pin current is limited to +/-25 mA.
- The part has no galvanic isolation.
- It does not provide complete automotive transient or short-to-battery
  protection by itself.
- K7/K8 may carry more current than a signal-level analog switch can tolerate.

An always-on supply or hold-up capacitor would reduce how often the switch
loses power, but it would not create passive bypass. A broken regulator,
ground, wire, or connector could still open every path.

Official datasheet:
https://www.ti.com/lit/ds/symlink/sn3257-q1.pdf

## Current proposed production architecture

The preferred direction is to remove the large 8-relay module and use compact,
sealed mechanical Form-C relays for only the six required contacts.

### If K7 and K8 always switch together

```text
DPDT relay A -> K3 + K4
DPDT relay B -> K5 + K6
DPDT relay C -> K7 + K8
```

This would reduce the design to three smaller relay packages.

### If K7 and K8 require independent control

```text
DPDT relay A -> K3 + K4
DPDT relay B -> K5 + K6
SPDT relay C -> K7
SPDT relay D -> K8
```

This would require four relay packages but would preserve the existing three
control domains.

No exact relay part should be selected until contact voltage, current, wetting
current, coil supply, release time, temperature, shock, vibration, and
qualification requirements are measured.

## K7/K8 concern

K7 and K8 form a cross-connected pair. If only one changes state, both output
connections may temporarily connect to the same source.

The four possible states need to be characterized:

```text
K7 off / K8 off
K7 on  / K8 off
K7 off / K8 on
K7 on  / K8 on
```

If either mixed state is prohibited, the revised design should make it
impossible through a common relay, hardware interlock, or independent safety
cutoff. Firmware timing alone should not be responsible for preventing an
unsafe state.

## Semiconductor bench evaluation

The SN3257 may still be evaluated on a current-limited simulator to measure:

- On-resistance error
- Leakage and back-powering
- Switching transients
- Channel interaction
- Reset behavior
- Brownout and total-power-loss behavior
- Open- and short-circuit response

A proposed bench fixture uses:

- One SN3257 for K3-K6
- A second SN3257 with K7/K8 paired only to test that hypothesis
- A current-limited 5 V supply
- One 100 nF X7R capacitor at each IC
- One shared 1 uF X7R bulk capacitor
- 10 kohm pull-downs on SEL and active-low EN
- 1 kohm source resistors for initial fault containment
- 10 kohm simulated ECU loads
- No Nissan harness, vehicle ECU, pedal, brake actuator, or steering circuit

This test would characterize the devices; it would not approve them for the
vehicle.

## Measurements required before redesign

The next steps are:

1. Continuity-map every existing COM, NC, and NO contact with the relay module
   unpowered and energized.
2. Confirm that total relay power loss restores the intended stock paths.
3. Verify that J4-23 controls K3-K6 and that the two ESP32 controls operate K7
   and K8 independently.
4. Measure all four K7/K8 state combinations on disconnected hardware.
5. Measure normal and maximum voltage and current on every contact path.
6. Measure source impedance, load impedance, frequency content, ground offset,
   inrush, and diagnostic behavior.
7. Verify installed relay coil voltage, JD-VCC voltage, and input polarity.
8. Determine whether K7/K8 carry signal current or actuator current.
9. Define the required response to MCU reset, brownout, watchdog timeout, power
   loss, open circuit, short to ground, and short to supply.
10. Select compact Form-C relay parts only after those requirements are known.
11. Create the redesign as a separate KiCad revision while preserving the
    original PCB files.
12. Add deterministic driver defaults, flyback suppression, test points, and
    any necessary K7/K8 hardware interlock.
13. Run ERC/DRC and simulator testing before connecting any vehicle hardware.

## Alternatives considered

### Hybrid analog switch plus safety relay

An SN3257 could perform normal switching while a separate normally closed
mechanical relay provides power-loss bypass. This is possible but requires
careful transfer interlocking and eliminates much of the size advantage.

### PhotoMOS arrangement

Form-A and Form-B PhotoMOS devices could emulate one Form-C contact. Six paths
would generally require approximately twelve devices, along with leakage,
resistance, transfer-timing, and automotive-qualification analysis.

### Always-on switch power

A protected always-on rail could improve normal reset behavior but would still
not protect against total regulator, wiring, ground, or connector failure.

For those reasons, smaller mechanical Form-C relays remain the most direct and
conservative solution.

## Current conclusion

The current plan is:

> Replace the oversized 8-relay module with only the six compact mechanical
> Form-C contacts the PCB actually needs, preserving normally closed stock
> bypass when the controller loses power.

The TS3A5018 and SN3257-Q1 remain useful evaluation candidates for low-current
bench simulations, but neither is currently approved as the production
replacement.

The final relay configuration and part numbers depend primarily on the K7/K8
behavior and the measurements listed above.

Thanks,

Liam
