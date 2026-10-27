# MiLa Agent Notes

- Read `PROJECT_CONTEXT.md` first for the consolidated Nissan DBW, ESP32,
  comma 4, PCB, prior-task, and supplied auto-sweep firmware context. The
  auto-sweep sketch is reference evidence only and is not vehicle-approved.
- `docs/MiLa_Complete_Project_Notes.docx` consolidates the lab/research scope,
  local and upstream codebases, firmware behavior, PCB mapping, relay decisions,
  validation, and prior-chat sources as of 2026-10-07.
- The KiCad nets confirm six used relay paths, K3-K8: K3-K6 share a control,
  while K7/K8 have separate controls and cross-connected sources. Read
  `docs/dbw-switch-redesign-review.md` before replacing them; semiconductor
  power-off isolation does not provide the existing passive NC bypass.
- The 2026-10-07 replacement reference is `docs/passive-bypass-design.md`,
  with review history/FMEA and physical test matrix beside it. It uses four
  nonlatching G6K-2P-Y DC5 packages, preserving all six paths/three domains.
  K7/K8 default connections have no confirmed vehicle safety meaning.
- Editable bench CAD, BOMs, connector maps and fabrication outputs are under
  `hardware/passive_bypass_rev_a/` and `hardware/passive_bypass_supervisor_rev_a/`.
  Keep original PCB1/PCB2 files intact. These modules are for isolated 0–5 V,
  ≤1 mA signal simulators; they are not a vehicle installation release.
- The supervisor requires qualified heartbeat plus a new zero-request ARM
  edge. Its PG5 divider senses returned carrier input through JCTRL1-6/J5-7;
  do not locally loop feedback at the supervisor. Individual signal-wire
  reconnection and sufficiently short connector chatter can escape detection.
- The final permission buffer is 3.3 V LVC with 82 kΩ header/Q6 gate bias;
  request gates retain 10 kΩ. CAD/model checks cannot establish partial-power
  behavior, physical release/bounce, contact faults or vehicle acceptance.
- Both bench PCBs passed native ERC/DRC/connectivity/parity with zero findings
  on 2026-10-07; 60 host tests passed. Root evidence is under
  `hardware/review_evidence/`. The supervisor generator rebuilds its accepted
  layout from a hash-guarded routing snapshot; `--reroute` is exploratory.
- The user identifies the current controller as a 38-pin ESP32-WROOM-32D
  development board; the reference image shows CP2102 USB-UART, an
  AMS1117-family regulator, micro-USB, and a `V5` header. Verify the physical
  board revision before assuming USB/`V5` reverse-current protection.
- `firmware/comma4_can_bench/` is a guarded ESP32 CAN-link diagnostic for
  MCP2515 and MCP2518FD. It sends only bench ID `0x5A5` at 2 Hz after both a
  GPIO 27-to-GND jumper and serial `ARM`; TX auto-stops after 30 seconds.
- `tools/comma_can_listener.py` proves raw comma `can` reception first.
  `tools/comma_dbc_listener.py` plus `tools/mila_bench.dbc` then proves
  `opendbc.can.parser.CANParser` decoding.
- Validation on 2026-09-21: all four PlatformIO environments compiled, four
  host listener tests passed, and upstream opendbc parsed the fixture payload.
- The four host listener tests passed again on 2026-10-07. No physical result
  for this CAN diagnostic is recorded in the reviewed sources. Before hardware use,
  verify the controller module's oscillator, transceiver logic voltage, exact
  Nissan model/year and A/B harness, CAN pair, 500 kbit/s rate, and termination.
- Keep this diagnostic off a live vehicle bus until a passive capture confirms
  no `0x5A5` collision. An external ESP CAN node bypasses panda TX safety;
  vehicle-control messages must instead use the safety-gated openpilot
  `sendcan` path after a separate review.
- The October 12 independent review is in
  `docs/mila-pcb-multi-agent-review-2026-10-12.md`; specialist/debate/committee
  evidence is under `docs/reviews/2026-10-12/`. Fresh 60-test and native CAD
  checks pass; physical acceptance remains pending. Inventory first, retain
  Rev A, and measure actual transfer before further integration.
- Q6 short defeats the automatic high-side cutoff; a shorted individual
  driver can pick up on the first zero-request ARM. PG5 does not directly
  detect separately powered DAC failure. These are explicit coverage limits.
- CAN diagnostic Normal mode can ACK/error-participate before ARM; STOP
  halts new enqueues without a demonstrated physical last-frame bound.
- Before future accepted-layout capture/release, replace assertion-only
  guards and bind fresh reports to exact input/output hashes. Current matched
  Rev A evidence remains valid; no guard implementation changed in this review.
- On October 12, two isolated, linked bench ESP32s were flashed with the
  separate `output/can-two-node-2026-10-12/` diagnostic (`bench_serial_16mhz`).
  This user-authorized bench build uses serial ARM without a GPIO 27 jumper;
  original guarded firmware remains intact. The live console at localhost:8765
  verified 20/20 exact peer receptions in each direction, zero gaps/errors,
  and both nodes disarmed. Reports are in `reports/`; current delivery and
  hashes are in `serial-bench-delivery.json` and `validation.json`.
- Verified original 4 MiB flash backups are in that project's `flash-backups/`.
  Bind them to MAC/chip identity: initial A is `78:1c:3c:f5:bf:dc` /
  `DCBFF53C1C78`, initial B is `f8:b3:b7:21:c8:20` / `20C821B7B3F8`.
  USB port names and dashboard A/B labels can swap. Physical MCP crystals,
  actual wire bitrate, and logic voltage remain unverified. Use 115200 baud;
  initial A's full backup required the small-packet `backup_flash.py` reader
  after bulk serial transfers corrupted packets.
