"""Independent checks of the exported native supervisor netlist.

The circuit generator and its JSON manifest are deliberately not imported.
Gate pin numbers and Boolean functions come from the manufacturer pin tables.
The evaluator covers settled, valid-voltage logic only: RC delay, metastability,
watchdog timing, READY semantics and physical power sequencing need bench tests.
"""

import csv
from itertools import product
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET


NETLIST = (
    Path(__file__).parents[1]
    / "hardware/passive_bypass_supervisor_rev_a/netlist.xml"
)
CARRIER_BOM = Path(__file__).parents[1] / "hardware/passive_bypass_rev_a/bom.csv"


def resistance(value):
    """Read numeric resistor tokens from the native XML/BOM values."""
    token = value.split()[0]
    if token.lower().endswith("k"):
        return float(token[:-1]) * 1000
    return float(token.removesuffix("R"))


def permit_bias(r18, r19, rg6, rpd6, output_voltage=None,
                output_leakage=0.0, gate_leakage=0.0):
    """Two-node resistor network; positive leakage injects current into a node."""
    a = 1 / r19 + 1 / rg6
    b = c = -1 / rg6
    d = 1 / rg6 + 1 / rpd6
    rhs_header = output_leakage
    if output_voltage is not None:
        a += 1 / r18
        rhs_header += output_voltage / r18
    determinant = a * d - b * c
    header = (rhs_header * d - b * gate_leakage) / determinant
    gate = (a * gate_leakage - c * rhs_header) / determinant
    current = (
        (output_voltage - header) / r18 if output_voltage is not None
        else output_leakage
    )
    return header, gate, current


class NativeSupervisor:
    """Evaluate actual exported connections with independent gate semantics."""

    def __init__(self):
        root = ET.parse(NETLIST).getroot()
        self.parts = {
            component.attrib["ref"]: component.findtext("value")
            for component in root.find("components")
        }
        self.nets = {}
        for net in root.find("nets"):
            for node in net.findall("node"):
                self.nets[(node.attrib["ref"], node.attrib["pin"])] = (
                    net.attrib["name"].removeprefix("/")
                )

    def pin(self, ref, pin):
        return self.nets[(ref, str(pin))]

    def evaluate(self, health, ready, deadman, requests, state=(False,) * 3):
        values = {
            "V3V3": True,
            "V5_SUP": True,
            "GND": False,
            "HEALTH_N": bool(health),
            "READY": bool(ready),
            "DEADMAN_RAW": bool(deadman),
            "REQ_L": bool(requests[0]),
            "REQ_7": bool(requests[1]),
            "REQ_8": bool(requests[2]),
        }
        for ref in ("U4", "U5"):
            values[self.pin(ref, 4)] = values[self.pin(ref, 2)]
        values[self.pin("U7", 4)] = not any(
            values[self.pin("U7", pin)] for pin in (1, 3, 6)
        )
        for ref in ("U8", "U9"):
            values[self.pin(ref, 4)] = (
                values[self.pin(ref, 1)] and values[self.pin(ref, 2)]
            )

        hb_one, hb_good, armed = state
        if not values[self.pin("U10", 1)]:
            hb_one = False
        if not values[self.pin("U10", 13)]:
            hb_good = False
        if not values[self.pin("U11", 1)]:
            armed = False
        state = (hb_one, hb_good, armed)
        values[self.pin("U10", 5)] = hb_one
        values[self.pin("U10", 9)] = hb_good
        values[self.pin("U11", 5)] = armed

        # The R24/C18 node and U14 noninverting Schmitt buffer are identities
        # after settling. This makes no claim about their physical delay.
        values[self.pin("R24", 2)] = values[self.pin("R24", 1)]
        values[self.pin("U14", 4)] = values[self.pin("U14", 2)]
        for ref in ("U12", "U13"):
            values[self.pin(ref, 4)] = (
                values[self.pin(ref, 1)] and values[self.pin(ref, 2)]
            )
        return values, state

    def heartbeat_edge(self, inputs, requests, state):
        values, state = self.evaluate(*inputs, requests, state)
        # U6 converts a falling WDI edge into the common positive clock edge.
        if values[self.pin("U10", 1)] and values[self.pin("U10", 13)]:
            state = (
                values[self.pin("U10", 2)],
                values[self.pin("U10", 12)],
                state[2],
            )
        return self.evaluate(*inputs, requests, state)

    def arm_level(self, inputs, requests, state, previous, current):
        values, state = self.evaluate(*inputs, requests, state)
        # Physical button press discharges ARM_RC; U6 inverts that transition.
        if not previous and current and values[self.pin("U11", 1)]:
            state = (state[0], state[1], values[self.pin("U11", 2)])
        return self.evaluate(*inputs, requests, state)


class NativeSupervisorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.circuit = NativeSupervisor()

    def test_manufacturer_gate_pin_connections(self):
        # TI LVC2G14, LVC1G27, LVC1G08 and LVC74A pin tables.
        expected = {
            ("U6", 1): "WDI", ("U6", 6): "HB_CLK",
            ("U6", 3): "ARM_RC", ("U6", 4): "ARM_CLK",
            ("U7", 1): "REQ_L", ("U7", 3): "REQ_7",
            ("U7", 6): "REQ_8", ("U7", 4): "ZERO_REQ",
            ("U8", 1): "HEALTH_OK", ("U8", 2): "READY",
            ("U8", 4): "HEALTH_READY",
            ("U9", 1): "HEALTH_READY", ("U9", 2): "DEADMAN_OK",
            ("U9", 4): "QUALIFIED",
            ("U10", 1): "QUALIFIED", ("U10", 13): "QUALIFIED",
            ("U10", 3): "HB_CLK", ("U10", 11): "HB_CLK",
            ("U10", 2): "V3V3", ("U10", 12): "HB_ONE_SAFE",
            ("U10", 5): "HB_ONE", ("U10", 9): "HB_GOOD",
            ("U11", 1): "QUALIFIED", ("U11", 2): "ARM_D",
            ("U11", 3): "ARM_CLK", ("U11", 5): "ARMED",
            ("U12", 1): "HB_GOOD", ("U12", 2): "ZERO_REQ",
            ("U12", 4): "ARM_D",
            ("U13", 1): "ARMED", ("U13", 2): "QUALIFIED",
            ("U13", 4): "PERMIT_DRIVER", ("U13", 5): "V3V3",
        }
        self.assertEqual(len(expected), 33)
        for (ref, pin), net in expected.items():
            with self.subTest(ref=ref, pin=pin):
                self.assertEqual(self.circuit.pin(ref, pin), net)

    def test_part_functions_and_unused_flipflop_inputs(self):
        expected_parts = {
            "U6": "SN74LVC2G14IDCKRQ1",
            "U7": "SN74LVC1G27DCKR",
            "U10": "SN74LVC74AQPWRG4Q1",
            "U11": "SN74LVC74AQPWRG4Q1",
            "U13": "SN74LVC1G08QDCKRQ1",
            "U14": "SN74LVC1G17QDCKRQ1",
        }
        for ref, value in expected_parts.items():
            self.assertEqual(self.circuit.parts[ref], value)
        for ref in ("U8", "U9", "U12"):
            self.assertEqual(self.circuit.parts[ref], "SN74LVC1G08QDCKRQ1")
        for ref in ("U10", "U11"):
            for pin in (4, 10, 14):
                self.assertEqual(self.circuit.pin(ref, pin), "V3V3")
            self.assertEqual(self.circuit.pin(ref, 7), "GND")
        for pin in (11, 12, 13):
            self.assertEqual(self.circuit.pin("U11", pin), "GND")

    def test_all_512_settled_boolean_combinations(self):
        count = 0
        for inputs in product((False, True), repeat=3):
            for requests in product((False, True), repeat=3):
                for state in product((False, True), repeat=3):
                    with self.subTest(inputs=inputs, requests=requests, state=state):
                        values, actual_state = self.circuit.evaluate(
                            *inputs, requests, state
                        )
                        qualified = all(inputs)
                        self.assertEqual(values["QUALIFIED"], qualified)
                        self.assertEqual(values["ZERO_REQ"], not any(requests))
                        self.assertEqual(
                            values["PERMIT_DRIVER"], qualified and actual_state[2]
                        )
                        if not qualified:
                            self.assertEqual(actual_state, (False,) * 3)
                        count += 1
        self.assertEqual(count, 512)

    def test_two_post_qualification_edges_use_previous_stage_value(self):
        for inputs in product((False, True), repeat=3):
            state = (False,) * 3
            for edge_count in range(3):
                with self.subTest(inputs=inputs, edge_count=edge_count):
                    expected = (
                        (False, False) if not all(inputs) or edge_count == 0
                        else (True, False) if edge_count == 1 else (True, True)
                    )
                    self.assertEqual(state[:2], expected)
                    _, state = self.circuit.heartbeat_edge(inputs, (False,) * 3, state)

    def test_arm_edge_samples_zero_requests_for_all_eight_states(self):
        for requests in product((False, True), repeat=3):
            with self.subTest(requests=requests):
                values, state = self.circuit.arm_level(
                    (True,) * 3, requests, (True, True, False), False, True
                )
                self.assertEqual(state[2], not any(requests))
                self.assertEqual(values["PERMIT_DRIVER"], not any(requests))

    def test_held_arm_does_not_rearm_after_each_async_clear_source(self):
        for failed_source in range(3):
            state = (True,) * 3
            inputs = [True] * 3
            inputs[failed_source] = False
            _, state = self.circuit.evaluate(*inputs, (False,) * 3, state)
            self.assertEqual(state, (False,) * 3)
            inputs = (True,) * 3
            for _ in range(2):
                _, state = self.circuit.heartbeat_edge(inputs, (False,) * 3, state)
            values, state = self.circuit.arm_level(
                inputs, (False,) * 3, state, True, True
            )
            self.assertFalse(values["PERMIT_DRIVER"])
            _, state = self.circuit.arm_level(inputs, (False,) * 3, state, True, False)
            values, state = self.circuit.arm_level(
                inputs, (False,) * 3, state, False, True
            )
            self.assertTrue(values["PERMIT_DRIVER"])

    def test_delayed_heartbeat_stage_is_noninverting_and_ground_referenced(self):
        expected = {
            ("R24", 1): "HB_ONE", ("R24", 2): "HB_STAGE_RC",
            ("C18", 1): "HB_STAGE_RC", ("C18", 2): "GND",
            ("U14", 2): "HB_STAGE_RC", ("U14", 3): "GND",
            ("U14", 4): "HB_ONE_SAFE", ("U14", 5): "V3V3",
        }
        for (ref, pin), net in expected.items():
            self.assertEqual(self.circuit.pin(ref, pin), net)
        self.assertEqual(self.circuit.parts["R24"], "1k 1%")
        self.assertEqual(self.circuit.parts["C18"], "100pF C0G 5% 10V")

    def test_5v_monitor_remains_supplied_from_either_upstream_rail(self):
        # BAS70-05 is dual common cathode: A1=1, A2=2, K=3. U3 uses the
        # adjustable G01, not a self-powered G50 whose RESET becomes undefined
        # when its own monitored supply fully disappears.
        self.assertEqual(self.circuit.parts["D1"], "BAS70-05-7-F")
        self.assertEqual(self.circuit.parts["U3"], "TPS3808G01QDBVRQ1")
        expected = {
            ("D1", 1): "V3V3", ("D1", 2): "V5_SUP",
            ("D1", 3): "V_PG5_SUP",
            ("U3", 1): "HEALTH_N", ("U3", 2): "GND",
            ("U3", 3): "V_PG5_SUP", ("U3", 5): "V5_SENSE",
            ("U3", 6): "V_PG5_SUP",
            ("R4", 1): "V_PG5_SUP", ("R4", 2): "PG5_CT",
            ("R22", 1): "CARRIER_5V_FEEDBACK", ("R22", 2): "V5_SENSE",
            ("R23", 1): "V5_SENSE", ("R23", 2): "GND",
            ("C3", 1): "V_PG5_SUP", ("C3", 2): "GND",
        }
        for (ref, pin), net in expected.items():
            self.assertEqual(self.circuit.pin(ref, pin), net)
        self.assertEqual(self.circuit.parts["R22"], "100k 0.1%")
        self.assertEqual(self.circuit.parts["R23"], "9.53k 0.1%")

    def test_actual_5v_sense_returns_through_carrier_control_connector(self):
        # The returned post-enable carrier feed is distinct from the live
        # upstream supervisor supply. Complete carrier/control detachment can
        # therefore pull SENSE low even while the supervisor remains powered.
        # Individual open request/permission wires are not detected by this.
        self.assertEqual(self.circuit.parts["J5"], "BENCH_1x07")
        feedback = self.circuit.pin("J5", 7)
        self.assertEqual(feedback, "CARRIER_5V_FEEDBACK")
        self.assertEqual(self.circuit.pin("R22", 1), feedback)
        self.assertNotEqual(feedback, self.circuit.pin("J2", 1))
        self.assertNotEqual(feedback, self.circuit.pin("D1", 2))
        self.assertEqual(self.circuit.pin("R22", 2), self.circuit.pin("U3", 5))
        self.assertEqual(self.circuit.pin("R23", 1), self.circuit.pin("U3", 5))
        self.assertEqual(self.circuit.pin("R23", 2), "GND")
        feedback_nodes = {
            node for node, net in self.circuit.nets.items() if net == feedback
        }
        self.assertEqual(feedback_nodes, {("J5", "7"), ("R22", "1")})

    def test_permit_output_drive_and_physical_coil_feed_are_separate(self):
        self.assertEqual(self.circuit.parts["R18"], "1k 1%")
        self.assertEqual(self.circuit.pin("R18", 1), "PERMIT_DRIVER")
        self.assertEqual(self.circuit.pin("R18", 2), "COIL_PERMIT")
        self.assertEqual(self.circuit.pin("R19", 1), "COIL_PERMIT")
        self.assertEqual(self.circuit.pin("R19", 2), "GND")
        self.assertEqual(self.circuit.parts["R19"], "82k 1%")
        self.assertEqual(self.circuit.pin("C13", 1), "V3V3")
        self.assertEqual(self.circuit.pin("C13", 2), "GND")
        # Including carrier RG6=330 ohm, initial gate-current upper bound is
        # below the LVC output recommendation. This is a resistor calculation.
        self.assertLess(3.6 / ((1000 + 330) * 0.99), 0.024)
        self.assertEqual(self.circuit.pin("J3", 1), "V5_SUP")
        self.assertEqual(self.circuit.pin("J3", 2), "V5_COIL_SWITCHED")
        self.assertEqual(self.circuit.pin("J5", 2), "V5_COIL_SWITCHED")
        self.assertEqual(self.circuit.pin("J5", 3), "COIL_PERMIT")
        # The external deadman contact, not a copper short in this schematic,
        # joins J3 pins1/2. Permission is not exposed on the ESP header J1.
        self.assertNotEqual(self.circuit.pin("J3", 1), self.circuit.pin("J3", 2))
        self.assertNotIn(
            "COIL_PERMIT", [self.circuit.pin("J1", pin) for pin in range(1, 9)]
        )

    def permit_resistors(self):
        with CARRIER_BOM.open(newline="") as source:
            carrier = {
                row["reference"]: row["value"] for row in csv.DictReader(source)
            }
        self.assertEqual(resistance(carrier["RPD6"]), 82000)
        self.assertEqual(resistance(carrier["RG6"]), 330)
        return (
            resistance(self.circuit.parts["R18"]),
            resistance(self.circuit.parts["R19"]),
            resistance(carrier["RG6"]),
            resistance(carrier["RPD6"]),
        )

    def test_lvc_100ua_output_spec_and_2v5_gate_margin_at_bias_corners(self):
        # TI SN74LVC1G08-Q1 Rev H, p6: VOH>=VCC-0.15 at IOH=-100uA.
        # AOS AO3400A Rev3.1: 2.5V RDS(on) guarantee, gate leakage<=100nA
        # under its stated condition. Evaluate only the room-temperature bench
        # resistor circuit; no analog switching or brownout timing is modeled.
        nominal = self.permit_resistors()
        for corners in product((0.99, 1.01), repeat=4):
            resistors = tuple(r * corner for r, corner in zip(nominal, corners))
            for gate_leakage in (-100e-9, 100e-9):
                with self.subTest(corners=corners, gate_leakage=gate_leakage):
                    _, _, current = permit_bias(
                        *resistors, output_voltage=3.6, gate_leakage=gate_leakage
                    )
                    self.assertLess(current, 100e-6)
                    _, gate, _ = permit_bias(
                        *resistors, output_voltage=3.0 - 0.15,
                        gate_leakage=gate_leakage
                    )
                    self.assertGreater(gate, 2.5)

    def test_powered_off_leakage_bias_is_below_threshold_as_screening_only(self):
        # TI Ioff<=10uA at VCC=0 and AOS gate leakage<=100nA give a
        # resistor-network voltage bound. Being below the 0.65V minimum
        # threshold is screening, NOT proof of zero drain/coil current.
        nominal = self.permit_resistors()
        for corners in product((0.99, 1.01), repeat=4):
            resistors = tuple(r * corner for r, corner in zip(nominal, corners))
            _, gate, _ = permit_bias(
                *resistors, output_leakage=10e-6, gate_leakage=100e-9
            )
            self.assertLess(gate, 0.43)
            self.assertLess(gate, 0.65)


if __name__ == "__main__":
    unittest.main()
