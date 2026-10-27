"""Model-level properties and safety counterexamples; no physical evidence.

The illustrative timing values below are deliberately test fixtures. They are
not measured relay times, ECU thresholds, or a vehicle acceptance budget.
"""

from dataclasses import replace
from itertools import combinations, product
from pathlib import Path
import sys
import unittest


TOOLS_PATH = Path(__file__).parents[1] / "tools"
sys.path.insert(0, str(TOOLS_PATH))
import passive_bypass_model as MODEL


GOOD = MODEL.SupervisorInputs(True, True, True, True, True)
ALL_REQUESTED = MODEL.RelayRequests(True, True, True)
ZERO_REQUESTS = MODEL.RelayRequests()
OFF_COILS = dict.fromkeys(("RLY1", "RLY2", "RLY3", "RLY4"), False)
ON_COILS = dict.fromkeys(OFF_COILS, True)
ALL_NC = dict.fromkeys(("K3", "K4", "K5", "K6", "K7", "K8"), MODEL.ContactState.NC)
ALL_NO = dict.fromkeys(ALL_NC, MODEL.ContactState.NO)

# Independent oracle copied from the retained PCB mapping, rather than built
# from the model's POLES. These relationships must not drift with code changes.
PCB_MAPPING = {
  "K3": ("J4-14", "J4-13", "J5-10"),
  "K4": ("J4-15", "J4-12", "J5-11"),
  "K5": ("J4-16", "J4-11", "J6-8"),
  "K6": ("J4-17", "J4-10", "J6-9"),
  "K7": ("J4-18", "J4-9", "J4-8"),
  "K8": ("J4-19", "J4-8", "J4-9"),
}


def qualify_heartbeat(supervisor):
  supervisor.wdi_falling_edge()
  supervisor.wdi_falling_edge()


def armed_supervisor():
  supervisor = MODEL.ArmSupervisor()
  supervisor.set_inputs(GOOD)
  qualify_heartbeat(supervisor)
  supervisor.set_arm_request(True, requests=ZERO_REQUESTS)
  return supervisor


class SupervisorTests(unittest.TestCase):
  def test_power_up_never_arms_without_edge(self):
    supervisor = MODEL.ArmSupervisor()
    supervisor.set_inputs(GOOD)
    self.assertFalse(supervisor.armed)
    self.assertEqual(supervisor.coil_commands(ALL_REQUESTED), OFF_COILS)

  def test_arm_requires_two_qualified_falling_wdi_edges(self):
    supervisor = MODEL.ArmSupervisor()
    supervisor.set_inputs(GOOD)
    for accepted_edges in range(3):
      with self.subTest(accepted_edges=accepted_edges):
        supervisor.set_arm_request(False, requests=ZERO_REQUESTS)
        supervisor.set_arm_request(True, requests=ZERO_REQUESTS)
        self.assertEqual(supervisor.armed, accepted_edges == 2)
        self.assertEqual(supervisor.hb_good, accepted_edges == 2)
        supervisor.wdi_falling_edge()

  def test_pre_ready_heartbeat_edges_cannot_qualify_post_ready_arm(self):
    supervisor = MODEL.ArmSupervisor()
    supervisor.set_inputs(replace(GOOD, ready=False))
    for _ in range(4):
      supervisor.wdi_falling_edge()
    supervisor.set_inputs(GOOD)
    supervisor.set_arm_request(True, requests=ZERO_REQUESTS)
    self.assertFalse(supervisor.armed)
    supervisor.wdi_falling_edge()
    self.assertFalse(supervisor.hb_good)
    supervisor.wdi_falling_edge()
    self.assertTrue(supervisor.hb_good)
    # Completing heartbeat qualification does not invent another ARM edge.
    supervisor.set_arm_request(True, requests=ZERO_REQUESTS)
    self.assertFalse(supervisor.armed)

  def test_arm_edge_requires_all_three_request_nets_low(self):
    for bits in product((False, True), repeat=3):
      with self.subTest(requests=bits):
        supervisor = MODEL.ArmSupervisor()
        supervisor.set_inputs(GOOD)
        qualify_heartbeat(supervisor)
        supervisor.set_arm_request(True, requests=MODEL.RelayRequests(*bits))
        self.assertEqual(supervisor.armed, not any(bits))

  def test_failed_zero_request_arm_edge_is_not_queued(self):
    supervisor = MODEL.ArmSupervisor()
    supervisor.set_inputs(GOOD)
    qualify_heartbeat(supervisor)
    supervisor.set_arm_request(True, requests=ALL_REQUESTED)
    supervisor.set_arm_request(True, requests=ZERO_REQUESTS)
    self.assertFalse(supervisor.armed)
    supervisor.set_arm_request(False, requests=ZERO_REQUESTS)
    supervisor.set_arm_request(True, requests=ZERO_REQUESTS)
    self.assertTrue(supervisor.armed)

  def test_second_arm_edge_with_nonzero_request_clocks_disarm(self):
    supervisor = armed_supervisor()
    supervisor.set_arm_request(False, requests=ALL_REQUESTED)
    supervisor.set_arm_request(True, requests=ALL_REQUESTED)
    self.assertFalse(supervisor.armed)

  def test_fault_recovery_requires_two_fresh_edges_and_new_arm(self):
    supervisor = armed_supervisor()
    supervisor.set_inputs(replace(GOOD, watchdog_window_ok=False))
    supervisor.set_inputs(GOOD)
    supervisor.wdi_falling_edge()
    supervisor.set_arm_request(False, requests=ZERO_REQUESTS)
    supervisor.set_arm_request(True, requests=ZERO_REQUESTS)
    self.assertFalse(supervisor.armed)
    supervisor.wdi_falling_edge()
    supervisor.set_arm_request(True, requests=ZERO_REQUESTS)
    self.assertFalse(supervisor.armed)
    supervisor.set_arm_request(False, requests=ZERO_REQUESTS)
    supervisor.set_arm_request(True, requests=ZERO_REQUESTS)
    self.assertTrue(supervisor.armed)

  def test_healthy_high_side_cuts_every_stuck_low_side_after_inhibit(self):
    # Enumerate all 16 low-side fault masks, including all drivers stuck on.
    for mask in product((False, True), repeat=4):
      stuck = frozenset(
        relay for relay, selected in zip(sorted(OFF_COILS), mask) if selected
      )
      with self.subTest(stuck=stuck):
        supervisor = armed_supervisor()
        supervisor.set_inputs(replace(GOOD, physical_enable=False))
        self.assertEqual(
          supervisor.coil_commands(ALL_REQUESTED, low_side_stuck_on=stuck),
          OFF_COILS,
        )

  def test_failed_on_high_side_exposes_single_fault_inhibit_vulnerability(self):
    supervisor = MODEL.ArmSupervisor()
    # The physical enable is still held and the upstream coil supply is valid.
    # This demonstrates failed automatic inhibition, not manual feed bypass.
    supervisor.set_inputs(GOOD)
    self.assertFalse(supervisor.armed)
    self.assertEqual(
      supervisor.coil_commands(ALL_REQUESTED, high_side_stuck_on=True),
      ON_COILS,
    )
    # This intentionally demonstrates failure, not an all-fault safety proof.
    topology = MODEL.Topology(MODEL.settled_contacts(
      supervisor.coil_commands(ALL_REQUESTED, high_side_stuck_on=True)
    ))
    self.assertFalse(topology.exact_default_connections)

  def test_physical_coil_feed_cuts_failed_high_side_and_stuck_drivers(self):
    supervisor = armed_supervisor()
    supervisor.set_inputs(replace(GOOD, watchdog_window_ok=False))
    self.assertEqual(
      supervisor.coil_commands(
        ALL_REQUESTED, high_side_stuck_on=True,
        low_side_stuck_on=frozenset(OFF_COILS),
      ),
      ON_COILS,
    )
    supervisor.set_inputs(replace(GOOD, physical_enable=False))
    self.assertEqual(
      supervisor.coil_commands(
        ALL_REQUESTED, high_side_stuck_on=True,
        low_side_stuck_on=frozenset(OFF_COILS),
      ),
      OFF_COILS,
    )

  def test_zero_request_does_not_prove_a_low_side_driver_is_healthy(self):
    supervisor = armed_supervisor()
    coils = supervisor.coil_commands(
      ZERO_REQUESTS, low_side_stuck_on=frozenset({"RLY1"})
    )
    self.assertTrue(coils["RLY1"])
    self.assertFalse(coils["RLY2"])
    self.assertFalse(MODEL.Topology(MODEL.settled_contacts(coils)).exact_default_connections)

  def test_whole_carrier_bundle_removal_trips_returned_pg5_and_prevents_rearm(self):
    supervisor = armed_supervisor()
    supervisor.set_carrier_bundle_connected(False)
    self.assertFalse(supervisor.inputs.pg5)
    self.assertFalse(supervisor.armed)
    self.assertFalse(supervisor.hb_one)
    self.assertFalse(supervisor.hb_good)
    self.assertEqual(supervisor.coil_commands(ALL_REQUESTED), OFF_COILS)
    self.assertTrue(MODEL.Topology(MODEL.settled_contacts(
      supervisor.coil_commands(ALL_REQUESTED)
    )).exact_default_connections)
    # Supply/logic elsewhere may recover while carrier feedback is still open.
    supervisor.set_inputs(GOOD)
    qualify_heartbeat(supervisor)
    self.assertFalse(supervisor.inputs.pg5)
    self.assertFalse(supervisor.hb_good)
    supervisor.set_carrier_bundle_connected(True)
    self.assertFalse(supervisor.inputs.pg5)
    supervisor.set_inputs(GOOD)
    qualify_heartbeat(supervisor)
    supervisor.set_arm_request(True, requests=ZERO_REQUESTS)
    self.assertFalse(supervisor.armed)
    supervisor.set_arm_request(False, requests=ZERO_REQUESTS)
    supervisor.set_arm_request(True, requests=ZERO_REQUESTS)
    self.assertTrue(supervisor.armed)

  def test_whole_carrier_bundle_loss_removes_supply_even_with_stuck_drivers(self):
    supervisor = armed_supervisor()
    supervisor.set_carrier_bundle_connected(False)
    self.assertEqual(
      supervisor.coil_commands(
        ALL_REQUESTED, high_side_stuck_on=True,
        low_side_stuck_on=frozenset(OFF_COILS),
      ),
      OFF_COILS,
    )

  def test_single_request_wire_reconnection_can_reenergize_without_arm_edge(self):
    affected = {
      "common_k3_k6": {"RLY1", "RLY2"},
      "k7": {"RLY3"},
      "k8": {"RLY4"},
    }
    for domain, relays in affected.items():
      with self.subTest(domain=domain):
        supervisor = armed_supervisor()
        disconnected = supervisor.coil_commands(
          ALL_REQUESTED, disconnected_request_domains=frozenset({domain})
        )
        self.assertEqual(
          disconnected, {relay: relay not in relays for relay in OFF_COILS}
        )
        self.assertTrue(supervisor.inputs.pg5)
        self.assertTrue(supervisor.armed)
        # An individual wire is not supervised by the bundle power feedback.
        # No new ARM/heartbeat/input event occurs before restoration.
        self.assertEqual(supervisor.coil_commands(ALL_REQUESTED), ON_COILS)

  def test_single_permit_wire_reconnection_can_reenergize_without_arm_edge(self):
    supervisor = armed_supervisor()
    self.assertEqual(
      supervisor.coil_commands(ALL_REQUESTED, permit_wire_connected=False),
      OFF_COILS,
    )
    self.assertTrue(supervisor.inputs.pg5)
    self.assertTrue(supervisor.armed)
    self.assertEqual(supervisor.coil_commands(ALL_REQUESTED), ON_COILS)

  def test_exhaustive_permits_and_requested_domains(self):
    # 32 permit combinations x 8 request combinations. A missing permit must
    # inhibit every actuator; when all permits pass, grouping is exact.
    for permits in product((False, True), repeat=5):
      for requests in product((False, True), repeat=3):
        with self.subTest(permits=permits, requests=requests):
          supervisor = MODEL.ArmSupervisor()
          supervisor.set_inputs(MODEL.SupervisorInputs(*permits))
          qualify_heartbeat(supervisor)
          supervisor.set_arm_request(True, requests=ZERO_REQUESTS)
          outputs = supervisor.coil_commands(MODEL.RelayRequests(*requests))
          expected = {
            "RLY1": all(permits) and requests[0],
            "RLY2": all(permits) and requests[0],
            "RLY3": all(permits) and requests[1],
            "RLY4": all(permits) and requests[2],
          }
          self.assertEqual(outputs, expected)

  def test_every_inhibit_asynchronously_clears_and_consumes_held_arm(self):
    for field in ("pg5", "pg3", "watchdog_window_ok", "ready", "physical_enable"):
      with self.subTest(field=field):
        supervisor = armed_supervisor()
        self.assertTrue(supervisor.armed)
        supervisor.set_inputs(replace(GOOD, **{field: False}))
        # No MCU tick or ARM event is delivered after the fault.
        self.assertFalse(supervisor.armed)
        self.assertEqual(supervisor.coil_commands(ALL_REQUESTED), OFF_COILS)
        self.assertFalse(supervisor.hb_one)
        self.assertFalse(supervisor.hb_good)
        supervisor.set_inputs(GOOD)
        qualify_heartbeat(supervisor)
        supervisor.set_arm_request(True, requests=ZERO_REQUESTS)
        self.assertFalse(supervisor.armed)
        supervisor.set_arm_request(False, requests=ZERO_REQUESTS)
        supervisor.set_arm_request(True, requests=ZERO_REQUESTS)
        self.assertTrue(supervisor.armed)

  def test_arm_pressed_during_inhibit_is_not_queued(self):
    supervisor = MODEL.ArmSupervisor()
    supervisor.set_arm_request(True, requests=ZERO_REQUESTS)
    supervisor.set_inputs(GOOD)
    qualify_heartbeat(supervisor)
    supervisor.set_arm_request(True, requests=ZERO_REQUESTS)
    self.assertFalse(supervisor.armed)
    supervisor.set_arm_request(False, requests=ZERO_REQUESTS)
    supervisor.set_arm_request(True, requests=ZERO_REQUESTS)
    self.assertTrue(supervisor.armed)

  def test_heartbeat_does_not_substitute_for_qualified_ready(self):
    supervisor = MODEL.ArmSupervisor()
    supervisor.set_inputs(replace(GOOD, ready=False))
    for level in (False, True, False, True):
      supervisor.wdi_falling_edge()
      supervisor.set_arm_request(level, requests=ZERO_REQUESTS)
    self.assertFalse(supervisor.armed)
    self.assertFalse(supervisor.hb_good)
    self.assertEqual(supervisor.coil_commands(ALL_REQUESTED), OFF_COILS)

  def test_brief_fault_between_arm_events_still_latches_disarm(self):
    supervisor = armed_supervisor()
    supervisor.set_inputs(replace(GOOD, pg5=False))
    supervisor.set_inputs(GOOD)
    self.assertFalse(supervisor.armed)
    self.assertEqual(supervisor.coil_commands(ALL_REQUESTED), OFF_COILS)

  def test_all_inhibit_sequences_require_a_new_edge(self):
    # A recovered level never constitutes an ARM edge, for every nonempty
    # combination of missing permits, regardless of the active request group.
    for permits in product((False, True), repeat=5):
      if all(permits):
        continue
      supervisor = armed_supervisor()
      supervisor.set_inputs(MODEL.SupervisorInputs(*permits))
      supervisor.set_inputs(GOOD)
      qualify_heartbeat(supervisor)
      self.assertFalse(supervisor.armed)
      self.assertEqual(supervisor.coil_commands(ALL_REQUESTED), OFF_COILS)


class ContactTopologyTests(unittest.TestCase):
  def test_unpowered_default_paths_match_independent_pcb_oracle(self):
    topology = MODEL.Topology(MODEL.settled_contacts(OFF_COILS))
    for name, (common, default_source, alternate) in PCB_MAPPING.items():
      with self.subTest(pole=name):
        self.assertTrue(topology.connected(common, default_source))
        self.assertFalse(topology.connected(common, alternate))
        self.assertEqual(topology.selected_sources(common), {default_source})
    self.assertTrue(topology.exact_default_connections)

  def test_energized_alternate_paths_match_independent_pcb_oracle(self):
    topology = MODEL.Topology(MODEL.settled_contacts(ON_COILS))
    for name, (common, default_source, alternate) in PCB_MAPPING.items():
      with self.subTest(pole=name):
        self.assertFalse(topology.connected(common, default_source))
        self.assertTrue(topology.connected(common, alternate))
        self.assertEqual(topology.selected_sources(common), {alternate})
    self.assertFalse(topology.exact_default_connections)

  def test_all_stable_domain_commands_do_not_short_distinct_sources(self):
    supervisor = armed_supervisor()
    for request_bits in product((False, True), repeat=3):
      with self.subTest(requests=request_bits):
        states = MODEL.settled_contacts(
          supervisor.coil_commands(MODEL.RelayRequests(*request_bits))
        )
        topology = MODEL.Topology(states)
        for first, second in combinations(sorted(MODEL.SOURCE_NETS), 2):
          self.assertFalse(topology.connected(first, second))

  def test_k7_k8_independent_truth_table(self):
    # Both outputs sharing one source is distinct from shorting the two sources.
    expected = {
      (False, False): ("J4-9", "J4-8"),
      (False, True): ("J4-9", "J4-9"),
      (True, False): ("J4-8", "J4-8"),
      (True, True): ("J4-8", "J4-9"),
    }
    supervisor = armed_supervisor()
    for (k7, k8), (source18, source19) in expected.items():
      with self.subTest(k7=k7, k8=k8):
        contacts = MODEL.settled_contacts(
          supervisor.coil_commands(MODEL.RelayRequests(False, k7, k8))
        )
        topology = MODEL.Topology(contacts)
        self.assertEqual(topology.selected_sources("J4-18"), {source18})
        self.assertEqual(topology.selected_sources("J4-19"), {source19})
        self.assertFalse(topology.connected("J4-8", "J4-9"))

  def test_open_isolation_is_not_default_connections(self):
    topology = MODEL.Topology(dict.fromkeys(ALL_NC, MODEL.ContactState.OPEN))
    self.assertFalse(topology.exact_default_connections)
    for common, _, _ in PCB_MAPPING.values():
      self.assertEqual(topology.selected_sources(common), set())

  def test_both_state_exposes_source_short_for_every_pole(self):
    for name, (_, default_source, alternate) in PCB_MAPPING.items():
      with self.subTest(pole=name):
        states = dict(ALL_NC, **{name: MODEL.ContactState.BOTH})
        topology = MODEL.Topology(states)
        self.assertTrue(topology.connected(default_source, alternate))
        self.assertFalse(topology.exact_default_connections)

  def test_exhaustive_per_pole_fault_counterexamples_after_coil_removal(self):
    for name in PCB_MAPPING:
      for fault in MODEL.PoleFault:
        with self.subTest(pole=name, fault=fault):
          contacts = MODEL.settled_contacts(OFF_COILS, faults={name: fault})
          topology = MODEL.Topology(contacts)
          self.assertEqual(topology.exact_default_connections, fault == MODEL.PoleFault.STUCK_NC)

  def test_latching_counterexample_retains_generated_selection(self):
    contacts = MODEL.settled_contacts(OFF_COILS, latching=True, previous=ALL_NO)
    topology = MODEL.Topology(contacts)
    self.assertFalse(topology.exact_default_connections)
    self.assertEqual(topology.selected_sources("J4-14"), {"J5-10"})

  def test_removed_board_is_open_without_retained_bypass(self):
    topology = MODEL.Topology(ALL_NC, board_present=False)
    self.assertFalse(topology.exact_default_connections)
    for common, _, _ in PCB_MAPPING.values():
      self.assertEqual(topology.selected_sources(common), set())

  def test_verified_replacement_bypass_plug_restores_exact_default_mapping(self):
    topology = MODEL.Topology(ALL_NO, board_present=False, bypass_plug=True)
    self.assertTrue(topology.exact_default_connections)
    for common, default_source, alternate in PCB_MAPPING.values():
      self.assertTrue(topology.connected(common, default_source))
      self.assertFalse(topology.connected(common, alternate))

  def test_parallel_bypass_plug_is_rejected(self):
    with self.assertRaises(ValueError):
      MODEL.Topology(ALL_NO, board_present=True, bypass_plug=True)

  def test_omitted_pole_or_coil_cannot_silently_claim_bypass(self):
    with self.assertRaises(ValueError):
      MODEL.Topology({"K3": MODEL.ContactState.NC})
    with self.assertRaises(ValueError):
      MODEL.settled_contacts({"RLY1": False})
    with self.assertRaises(ValueError):
      MODEL.settled_contacts(OFF_COILS, latching=True)


class FiniteTransferTests(unittest.TestCase):
  def setUp(self):
    self.timing = {
      name: MODEL.ReleaseTiming(0.005, 0.008) for name in ALL_NC
    }

  def test_eventual_power_loss_default_connections_for_every_normal_command(self):
    supervisor = armed_supervisor()
    for request_bits in product((False, True), repeat=3):
      initial = MODEL.settled_contacts(
        supervisor.coil_commands(MODEL.RelayRequests(*request_bits))
      )
      with self.subTest(requests=request_bits):
        supervisor.set_inputs(replace(GOOD, pg5=False))
        self.assertEqual(supervisor.coil_commands(ALL_REQUESTED), OFF_COILS)
        snapshot = MODEL.power_loss_snapshot(0.008, initial, self.timing)
        self.assertTrue(snapshot.topology.exact_default_connections)
        # Rearm for the next case only using a new deliberate edge.
        supervisor.set_inputs(GOOD)
        qualify_heartbeat(supervisor)
        supervisor.set_arm_request(False, requests=ZERO_REQUESTS)
        supervisor.set_arm_request(True, requests=ZERO_REQUESTS)

  def test_dead_dac_can_remain_selected_before_relay_release(self):
    snapshot = MODEL.power_loss_snapshot(
      0.002, ALL_NO, self.timing, dac_hold_up_s=0.001
    )
    self.assertFalse(snapshot.dac_alive)
    self.assertEqual(snapshot.topology.selected_sources("J4-14"), {"J5-10"})
    self.assertFalse(snapshot.topology.exact_default_connections)

  def test_break_before_make_gap_is_not_continuous_default_connection(self):
    snapshot = MODEL.power_loss_snapshot(0.006, ALL_NO, self.timing)
    self.assertEqual(snapshot.topology.selected_sources("J4-14"), set())
    self.assertFalse(snapshot.topology.exact_default_connections)

  def test_pole_skew_exists_despite_common_dpdt_coil(self):
    timing = dict(self.timing, K3=MODEL.ReleaseTiming(0.001, 0.002))
    snapshot = MODEL.power_loss_snapshot(0.003, ALL_NO, timing)
    self.assertEqual(snapshot.topology.selected_sources("J4-14"), {"J4-13"})
    self.assertEqual(snapshot.topology.selected_sources("J4-15"), {"J5-11"})
    self.assertFalse(snapshot.topology.exact_default_connections)

  def test_k7_k8_release_skew_can_connect_both_outputs_to_same_source(self):
    timing = dict(self.timing, K7=MODEL.ReleaseTiming(0.001, 0.002))
    snapshot = MODEL.power_loss_snapshot(0.003, ALL_NO, timing)
    self.assertEqual(snapshot.topology.selected_sources("J4-18"), {"J4-9"})
    self.assertEqual(snapshot.topology.selected_sources("J4-19"), {"J4-9"})
    self.assertFalse(snapshot.topology.connected("J4-8", "J4-9"))

  def test_dac_hold_up_does_not_eliminate_contact_open_interval(self):
    snapshot = MODEL.power_loss_snapshot(
      0.006, ALL_NO, self.timing, dac_hold_up_s=0.020
    )
    self.assertTrue(snapshot.dac_alive)
    self.assertEqual(snapshot.topology.selected_sources("J4-14"), set())
    self.assertFalse(snapshot.topology.exact_default_connections)

  def test_time_does_not_repair_welded_or_latching_contacts(self):
    welded = MODEL.power_loss_snapshot(
      1.0, ALL_NO, self.timing, faults={"K3": MODEL.PoleFault.STUCK_NO}
    )
    latched = MODEL.power_loss_snapshot(1.0, ALL_NO, self.timing, latching=True)
    self.assertFalse(welded.topology.exact_default_connections)
    self.assertFalse(latched.topology.exact_default_connections)

  def test_invalid_time_contract_is_rejected(self):
    for first, second in ((-1, 1), (2, 1), (1, float("inf")), (float("nan"), 1)):
      with self.subTest(first=first, second=second):
        with self.assertRaises(ValueError):
          MODEL.ReleaseTiming(first, second)
    with self.assertRaises(ValueError):
      MODEL.power_loss_snapshot(-1, ALL_NO, self.timing)
    with self.assertRaises(ValueError):
      MODEL.power_loss_snapshot(float("nan"), ALL_NO, self.timing)
    with self.assertRaises(ValueError):
      MODEL.power_loss_snapshot(0, ALL_NO, self.timing, dac_hold_up_s=float("inf"))


if __name__ == "__main__":
  unittest.main()
