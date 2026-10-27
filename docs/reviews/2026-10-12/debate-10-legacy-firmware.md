# Debate 10 — Legacy nets versus firmware

2026-10-12. Participants: independent specialists 02 and 11. Each completed its phase-1 memo before this exchange. The legacy analyst read `11-firmware.md`, challenged its polarity/mapping conclusions directly, and received the firmware analyst's explicit acceptance of all three points below. **No dissent remains in this bounded exchange.** Agreement is not physical evidence.

**Challenge:** Can reversing the old sketch's active-low outputs establish compatibility with the new carrier, and can acknowledged DAC writes establish READY before bus/channel/harness identity is measured?

**Accepted correction 1 — polarity and topology are separate.** Inversion repairs only the logic convention. It cannot establish a physical GPIO map, change the original common group's separate external J4-23 route, implement independently controlled K7/K8 policy, or add READY/WDI. Original J3-25/26 are connector positions, not established GPIO25/26. See `02-legacy-nets.md` raw OLD:951–1038/2502–2523 and `11-firmware.md`, findings 1/4/5.

**Accepted correction 2 — the physical contact oracle is still missing.** The coordinator's fresh 18-terminal mapping and 207-pin source checks support CAD connectivity. Intended NC bypass/NO injection remains conditional on photo-inferred contact order because the old relay module uses a generic connector symbol. `docs/dbw-switch-redesign-review.md:31–40` explicitly requires continuity and polarity confirmation. Firmware cannot convert terminal equality into a measured bypass claim.

**Accepted correction 3 — ACK is insufficient for READY.** Firmware's response: “READY must stay LOW when physical DAC bus/channel-to-terminal identity is unknown.” ACK/readback can prove communication/retention, not which fixture/load receives the value or whether it is physically correct.

**Resolving experiment:** Produce a canonical physical header→GPIO→I2C controller→DAC address/channel→connector terminal→fixture/load manifest. Measure every original unpowered COM/NC pair; after verifying the installed relay module's supply/polarity, measure energized COM/NO on an isolated current-limited fixture. Check 100% disconnected-cable continuity, identify DAC channels using one-at-a-time harmless fixture codes, and scope requests/READY/WDI through cold boot, reset and controller/DAC-only power cycles.

Stop on any unmatched path, unexplained request or ambiguous identity. Until completed, preserve terminal names and hold READY LOW; neither analyst authorizes flashing, actuation or vehicle integration.
