# MiLa passive bypass bench Rev A — complete design package

Start with `docs/passive-bypass-design.md`, then each board's README and
assembly drawing. The final design uses four nonlatching Form-C relay packages
on a 60 × 50 mm carrier and a separate 80 × 60 mm window-watchdog/rail/manual-arm
supervisor. All six original contact paths and three control domains are kept.
The two new boards require their documented harness; they are not mechanically
or electrically pin-compatible with the original eight-relay module.

This package is for an isolated 0–5 V, ≤1 mA room-temperature signal simulator.
Power loss restores healthy contacts to NC only after finite coil decay,
release and bounce. K7/K8 default connections have no confirmed vehicle safety
meaning. No physical result or vehicle installation authorization is included.

## Included deliverables

- `docs/passive-bypass-design.md`: exact contact/interboard mapping, circuit,
  firmware contract, fixture, first-power-up procedure and reviewed alternatives.
- `docs/passive-bypass-review-log.md`, `passive-bypass-fmea.md` and
  `passive-bypass-validation.csv`: review closure, faults and pending test plan.
- `hardware/passive_bypass_rev_a/`: carrier schematic/layout/project, corrected
  local G6K footprint, libraries, BOM/netlist, previews, checks and fabrication.
- `hardware/passive_bypass_supervisor_rev_a/`: supervisor schematic/layout,
  local libraries, component/off-board switch BOMs, netlist and pin table,
  accepted routing geometry, previews, checks and fabrication.
- `hardware/review_evidence/`: independent root evidence, unchanged-source
  manifest, fixture BOM and design overview.
- `tools/` and `tests/`: generators, auditable ideal model, connectivity checks
  and 60 host tests. The retained CAN test/helper is included to reproduce the
  unchanged four-test baseline.
- `capstone_Oscar_Zheng_Jared_05032026/`: only the ten retained original KiCad
  source/library files used for mapping/preservation comparison. They are
  reference copies, not the new fabrication files.
- `SHA256_MANIFEST.json`: hash of every payload file except the manifest itself.

## Validation

Both new boards pass native KiCad ERC/DRC with zero unconnected items and zero
schematic-parity findings under their recorded rules. Sixty host tests pass.
Ten original CAD source/library files are unchanged. Gerber, drill, map and
position exports succeeded. Read `validation-summary-final.json` for the final
asset hashes and reports; no per-item ERC/DRC exclusions were used.

The 34 main physical procedures are NOT_RUN; 33 overlapping supervisor probes
are PENDING. Ideal/model/CAD evidence does not establish timing, contact faults,
partial-power behavior, leakage cutoff, signal plausibility or vehicle safety.

## Reproduce checks

From the extracted package root, using Python 3:

```sh
python3 -m unittest discover -s tests -q
python3 tools/check_passive_bypass_design.py
python3 tools/build_passive_bypass_supervisor.py --verify-netlist hardware/passive_bypass_supervisor_rev_a/netlist.xml
```

Use KiCad 10 for native schematic/PCB checks. Board generation requires its
bundled Python/wx/pcbnew runtime; ordinary Python generates the supervisor
schematic. The generator constants reflect the original macOS KiCad install.
Adjust runtime/tool paths if used on another host. Both board READMEs describe
rebuild commands; exporting or rebuilding requires rerunning ERC/DRC/parity.
The frozen circuit, native CAD and accepted supervisor route are the source
for this release. UUIDs may differ on full schematic regeneration.

Preserve the original source. Do not connect the fixture to a Nissan harness,
ECU, pedal, brake actuator, steering system or live vehicle CAN bus. Complete
the measured acceptance plan and establish application requirements before
creating a vehicle-specific revision.
