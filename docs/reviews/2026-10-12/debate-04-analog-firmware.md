# Debate 04 — Analog/DAC ↔ firmware

2026-10-12. Participants: independent specialists 07 and 11. Actual challenge/response exchange completed; no controller implementation or physical test. Evidence: `07-analog.md`, `11-firmware.md`, supervisor `README.md:78–97`, and Microchip DS22187E §§3.4–3.5, 4.0–4.2.

**Accepted corrections and boundaries**

- Firmware accepted analog's explicit fault distinction: PG5 observes returned carrier coil input. With that input powered, separate DAC-only collapse can remain invisible. ACK, initial discovery, DAC register readback and EEPROM RDY/BSY cannot establish correct physical outputs.
- Both distinguish four predicates: register/configuration readback establishes digital stored state; RDY/BSY reports EEPROM programming activity; independent voltage measurement establishes the observed analog value; fresh authorized command identity/age establishes the requested value. None alone establishes ECU acceptance or safe vehicle behavior.
- Firmware accepted that startup or General Call reset can recall plausible old EEPROM outputs. Detected unexpected reset/state, DAC rail loss, output mismatch or monitoring freshness loss must latch disarm, require renewed validation and a new manual ARM. Recalled plausible codes must not satisfy fresh-command authority.
- Firmware confirmed first failed validation cycle immediately lowers READY and all requests, blocks further WDI and latches fault. Three-cycle aggregation must not delay recognized-fault handling.
- Analog accepted firmware's scope correction: the first manually supervised transfer fixture may use independent external instruments and operator-held enable/READY. An onboard ADC redesign is unnecessary before relay characterization. That limited run does not prove automatic detection during continuing requests.
- The proposed 30 ms falling WDI cadence with 1 ms HIGH follows the documented watchdog window, conditional on three successful 10 ms application iterations. A 10 ms edge interval can violate the 10.35 ms lower corner. Thirty milliseconds is service scheduling, not a fault-response guarantee; cutoff/contact-return time includes detector or watchdog expiry, gates, coil decay, release and bounce.

**Discriminating experiments**

1. Hold carrier rail valid; collapse DAC VDD. Record both rails, paired source/COM voltages, READY, requests, WDI, permission and coil current.
2. Present an ACKed wrong complementary pair within nominal range; separately replay old command identity after reset. Test voltage validity and intent freshness independently.
3. Reset DAC with deliberately recorded nonneutral EEPROM state while controller remains powered. Observe recall before readiness and confirm disarm/requalification.
4. Stall application validation while a diagnostic timer continues. Verify no production heartbeat survives the stall. Measure first-detection-to-READY-low and final COM return independently.

**Remaining limitation, not resolved by agreement:** correct range/correlation and fresh authorization still cannot prove correct driving intent, endpoint plausibility or application timing acceptance. These remain requirements for later qualified engineering review. Stop screening on unexpected engagement/rearm, unrecognized injected fault, current-limit violation or unidentified mapping. No completed fault coverage is awarded to the proposal.
