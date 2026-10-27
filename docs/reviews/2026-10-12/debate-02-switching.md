# Debate 02 — Mechanical relays ↔ semiconductor alternatives

2026-10-12. Participants: specialists 03 and 04. Both completed independent memos before reading the counterpart. Explicit challenges and responses exchanged through agent messages. **No physical result was obtained.**

## Accepted corrections

- **Mechanical reviewer accepts:** Panasonic AQY4C2PX provides genuine zero-input-drive normally-closed continuity. Semiconductor isolation must not be generalized to every unpowered semiconductor switch. Its resistance, leakage, capacitance and transitions still require exact-part/application analysis. [Panasonic ASCTB453E, pp.1–4](https://mediap.industry.panasonic.eu/assets/download-files/import/semi_eng_cc1b_aqy4c_p.pdf).
- **Both accept:** G6K's 100 mΩ resistance measurement and 10 μA/10 mV P-level reference do not establish lifetime or accuracy at the fixture's actual minimum energy. Measure **first transfer after dwell before an ohmmeter or higher-current measurement conditions contacts**. [Manufacturer K106-E1, p.3, notes 1/4](https://components.omron.com/us-en/system/files/2026-05/datasheet_pdf/K106-E1.pdf).
- **Semiconductor reviewer accepts:** healthy Form-C contacts establish eventual settled default connectivity; nominal mechanical interlock proves neither uninterrupted delivery nor assembled cutoff timing. Diode-clamped release, bounce, pole skew and DAC collapse remain measured variables. Neither coil cutoff nor semiconductor input removal repairs a stuck-conducting signal branch.
- **Both accept:** a complementary Form-A/Form-B pair needs generated-branch isolation before default-branch reconnection, or separately justified bounded contention. A maximum reverse-ON time supplies no minimum NC-restoration delay; nominal timing cannot prove nonoverlap on supply collapse. Finite testing can expose overlap but cannot alone guarantee every unit/corner.
- **Both accept:** indexed +85°C G6K catalog information is a source claim, not fitted-lot verification; reconcile the purchased relay revision against the legacy +70°C PDF before expanding temperature scope.

## Decision and conditional dissent

Both support the current four nonlatching Form-C packages as the first isolated baseline because no exact complementary Form-A selection or passive sequencing proof exists. Conditional dissent: semiconductor continuity remains a legitimate pivot if cold-dwell contact error fails the declared simulator budget or a documented size constraint makes relays unsuitable. Selecting it requires supported error/leakage limits and collapse behavior; selecting relays requires supported dwell/transfer behavior. Unknown endpoint requirements preclude declaring either vehicle-suitable.

## Decisive experiment

Compare one assembled diode-clamped Form-C channel against one specifically selected Form-A/Form-B pair. Use distinguishable 0–5 V sources through containment resistors, ≤1 mA signal-fault currents and a declared load/error budget. Capture **both branch currents, COM, actual drive collapse and coil current**. Exercise independent and simultaneous abrupt/slow losses, cold dwell, normal transfer and stuck-branch substitutes. Record source overlap, open interval and cutoff-to-stable-default time. Extend the winning candidate to all six paths/three domains before system acceptance. Stop on missing settled default continuity, containment violation, unintended source coupling or violation of the predeclared simulator limits; unresolved application limits block vehicle advancement.
