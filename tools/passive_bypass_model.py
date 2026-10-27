"""Ideal connectivity/state model for the MiLa passive-bypass bench design.

This is a test oracle, not firmware, SPICE, a relay reliability model, or vehicle
approval. Timing arguments are supplied assumptions, not G6K specifications.
READY is an external assertion whose semantic validity is assumed. A watchdog
heartbeat does not establish command freshness, plausibility, calibrated DACs,
or actual contact position.
"""

from dataclasses import dataclass, fields, replace
from enum import Enum
from math import isfinite
from typing import Mapping


class ContactState(str, Enum):
  NC = "nc"
  OPEN = "open"
  NO = "no"
  BOTH = "both"


class PoleFault(str, Enum):
  STUCK_NC = "stuck_nc"
  STUCK_NO = "stuck_no"
  STUCK_OPEN = "stuck_open"
  STUCK_BOTH = "stuck_both"


FAULT_STATE = {
  PoleFault.STUCK_NC: ContactState.NC,
  PoleFault.STUCK_NO: ContactState.NO,
  PoleFault.STUCK_OPEN: ContactState.OPEN,
  PoleFault.STUCK_BOTH: ContactState.BOTH,
}


@dataclass(frozen=True)
class Pole:
  name: str
  relay: str
  common: str
  normally_closed: str
  normally_open: str


# Electrical mapping is from docs/six_relay_mapping.csv. Endpoint functions are
# deliberately not inferred from net names. The RLY3/RLY4 unused second poles
# are not modeled as connected to any vehicle circuit.
POLES = (
  Pole("K3", "RLY1", "J4-14", "J4-13", "J5-10"),
  Pole("K4", "RLY1", "J4-15", "J4-12", "J5-11"),
  Pole("K5", "RLY2", "J4-16", "J4-11", "J6-8"),
  Pole("K6", "RLY2", "J4-17", "J4-10", "J6-9"),
  Pole("K7", "RLY3", "J4-18", "J4-9", "J4-8"),
  Pole("K8", "RLY4", "J4-19", "J4-8", "J4-9"),
)
POLE_NAMES = frozenset(pole.name for pole in POLES)
RELAY_NAMES = frozenset(pole.relay for pole in POLES)
SOURCE_NETS = frozenset(
  net for pole in POLES for net in (pole.normally_closed, pole.normally_open)
)


@dataclass(frozen=True)
class SupervisorInputs:
  pg5: bool = False
  pg3: bool = False
  watchdog_window_ok: bool = False
  ready: bool = False
  physical_enable: bool = False

  @property
  def permits_arm(self) -> bool:
    return all(getattr(self, field.name) for field in fields(self))


@dataclass(frozen=True)
class RelayRequests:
  common_k3_k6: bool = False
  k7: bool = False
  k8: bool = False

  @property
  def zero_request(self) -> bool:
    return not (self.common_k3_k6 or self.k7 or self.k8)


class ArmSupervisor:
  """Ideal asynchronous-clear latch with edge-only manual rearm.

  Every input change must be delivered through set_inputs. Any false permit
  immediately clears ARM and both heartbeat qualifiers without an MCU step.
  Two subsequent falling WDI edges qualify HB_GOOD. ARM clocks the conjunction
  of HB_GOOD and zero request; an edge with a nonzero request clocks false.
  Edges during inhibit are consumed; a held ARM level never rearms on recovery.
  Actual pulse widths, metastability, reset dominance, and partial rail behavior
  require component analysis and physical tests.
  """

  def __init__(self) -> None:
    self.inputs = SupervisorInputs()
    self.armed = False
    self.hb_one = False
    self.hb_good = False
    self._arm_level = False
    self._carrier_bundle_connected = True

  def set_inputs(self, inputs: SupervisorInputs) -> None:
    if not self._carrier_bundle_connected:
      inputs = replace(inputs, pg5=False)
    self.inputs = inputs
    if not inputs.permits_arm:
      self.armed = False
      self.hb_one = False
      self.hb_good = False

  def set_carrier_bundle_connected(self, connected: bool) -> None:
    """Model the complete carrier power/control connector and returned PG5.

    The carrier feedback is after the physical enable and before the high-side
    cutoff. Complete bundle removal opens that feedback and trips modeled PG5;
    the relay contacts themselves may remain installed in the signal harness.
    Analog detection/release delays must be physically measured. Reconnection
    does not itself restore PG5: deliver a subsequent valid set_inputs event.
    Individual request/permit wire breaks do not necessarily affect feedback.
    """
    self._carrier_bundle_connected = bool(connected)
    if not connected:
      self.set_inputs(replace(self.inputs, pg5=False))

  def wdi_falling_edge(self) -> None:
    """Shift one heartbeat edge through the ideal two-stage qualification.

    Window validity is a separate supervisor input. Even two accepted edges
    prove no command semantics; the externally asserted READY contract is still
    an assumption. The physical IC must meet clock/reset timing limits.
    """
    if self.inputs.permits_arm:
      self.hb_good = self.hb_one
      self.hb_one = True
    else:
      self.armed = False
      self.hb_one = False
      self.hb_good = False

  def set_arm_request(self, level: bool, *, requests: RelayRequests) -> None:
    rising_edge = bool(level) and not self._arm_level
    self._arm_level = bool(level)
    if not self.inputs.permits_arm:
      self.armed = False
    elif rising_edge:
      self.armed = self.hb_good and requests.zero_request

  def coil_commands(
    self,
    requests: RelayRequests,
    *,
    high_side_stuck_on: bool = False,
    low_side_stuck_on: frozenset[str] = frozenset(),
    disconnected_request_domains: frozenset[str] = frozenset(),
    permit_wire_connected: bool = True,
  ) -> dict[str, bool]:
    """Ideal coil energization through high-side power and low-side requests.

    Stuck low-side drivers remain cut off by a healthy disabled high-side gate.
    A failed-on high-side gate can defeat supervisor inhibition when requests
    remain asserted and the manual coil-feed contact stays closed. This model
    assumes both healthy poles of the held physical-enable switch agree; its
    feed contact cuts coil power even if the high-side gate fails on. ZERO_REQ
    senses request nets, not physical driver faults.
    Complete power/control bundle loss cuts supply and invalidates returned PG5.
    A single request or permit wire can open and reconnect while PG5 remains
    valid; if ARM stays latched, reconnecting it can immediately energize coils.
    Voltage thresholds, transistor leakage, and coil dynamics are not modeled.
    """
    if not set(low_side_stuck_on) <= RELAY_NAMES:
      raise ValueError("Stuck drivers must name RLY1 through RLY4")
    if not set(disconnected_request_domains) <= {
      "common_k3_k6", "k7", "k8"
    }:
      raise ValueError("Disconnected request domains must name common_k3_k6/k7/k8")
    high_side_on = high_side_stuck_on or (
      self.armed and self.inputs.permits_arm and permit_wire_connected
    )
    low_side_requests = {
      "RLY1": requests.common_k3_k6 and "common_k3_k6" not in disconnected_request_domains,
      "RLY2": requests.common_k3_k6 and "common_k3_k6" not in disconnected_request_domains,
      "RLY3": requests.k7 and "k7" not in disconnected_request_domains,
      "RLY4": requests.k8 and "k8" not in disconnected_request_domains,
    }
    return {
      relay: self._carrier_bundle_connected and self.inputs.physical_enable and high_side_on
      and (requested or relay in low_side_stuck_on)
      for relay, requested in low_side_requests.items()
    }


def _validate_poles(values: Mapping[str, object], *, complete: bool) -> None:
  names = set(values)
  if not names <= POLE_NAMES or (complete and names != POLE_NAMES):
    raise ValueError("Contact mapping must use K3 through K8 exactly")


def settled_contacts(
  coil_commands: Mapping[str, bool],
  *,
  faults: Mapping[str, PoleFault] | None = None,
  latching: bool = False,
  previous: Mapping[str, ContactState] | None = None,
) -> dict[str, ContactState]:
  """Return settled ideal contacts, exposing stuck and latching counterexamples.

  Coils powered select NO. For the rejected latching alternative, absence of a
  reset pulse retains the previous physical state when coil power disappears.
  This function makes no release-time or contact-synchrony guarantee.
  """
  if set(coil_commands) != RELAY_NAMES:
    raise ValueError("Coil commands must cover RLY1 through RLY4 exactly")
  faults = faults or {}
  _validate_poles(faults, complete=False)
  if latching and previous is None:
    raise ValueError("Latching state requires previous contact positions")
  if previous is not None:
    _validate_poles(previous, complete=True)
  contacts = {}
  for pole in POLES:
    if pole.name in faults:
      contacts[pole.name] = FAULT_STATE[PoleFault(faults[pole.name])]
    elif coil_commands[pole.relay]:
      contacts[pole.name] = ContactState.NO
    elif latching:
      contacts[pole.name] = ContactState(previous[pole.name])
    else:
      contacts[pole.name] = ContactState.NC
  return contacts


class Topology:
  """Undirected physical contact graph; does not model ECU/load behavior."""

  def __init__(
    self,
    contacts: Mapping[str, ContactState],
    *,
    board_present: bool = True,
    bypass_plug: bool = False,
  ) -> None:
    _validate_poles(contacts, complete=True)
    if board_present and bypass_plug:
      raise ValueError("Bypass plug replaces the board; it is not parallel wiring")
    self.graph: dict[str, set[str]] = {
      net: set() for pole in POLES
      for net in (pole.common, pole.normally_closed, pole.normally_open)
    }
    for pole in POLES:
      state = ContactState(contacts[pole.name])
      if bypass_plug:
        self._join(pole.common, pole.normally_closed)
      elif board_present:
        if state in (ContactState.NC, ContactState.BOTH):
          self._join(pole.common, pole.normally_closed)
        if state in (ContactState.NO, ContactState.BOTH):
          self._join(pole.common, pole.normally_open)

  def _join(self, first: str, second: str) -> None:
    self.graph[first].add(second)
    self.graph[second].add(first)

  def component(self, net: str) -> frozenset[str]:
    if net not in self.graph:
      raise ValueError(f"Unknown net: {net}")
    visited = set()
    pending = [net]
    while pending:
      current = pending.pop()
      if current not in visited:
        visited.add(current)
        pending.extend(self.graph[current] - visited)
    return frozenset(visited)

  def connected(self, first: str, second: str) -> bool:
    if second not in self.graph:
      raise ValueError(f"Unknown net: {second}")
    return second in self.component(first)

  def selected_sources(self, common: str) -> frozenset[str]:
    return self.component(common) & SOURCE_NETS

  @property
  def exact_default_connections(self) -> bool:
    """Matches retained NC wiring; does not establish vehicle-safe defaults.

    K7/K8 endpoint function and its safe default remain unverified. This graph
    includes isolation: a BOTH pole joining NC and NO fails the default mapping.
    """
    return all(
      self.selected_sources(pole.common) == {pole.normally_closed}
      for pole in POLES
    )


@dataclass(frozen=True)
class ReleaseTiming:
  no_opens_at_s: float
  nc_settles_at_s: float

  def __post_init__(self) -> None:
    if not (
      isfinite(self.no_opens_at_s)
      and isfinite(self.nc_settles_at_s)
      and 0 <= self.no_opens_at_s <= self.nc_settles_at_s
    ):
      raise ValueError("Release timing must satisfy 0 <= NO-open <= NC-settled")


@dataclass(frozen=True)
class PowerLossSnapshot:
  topology: Topology
  dac_alive: bool


def power_loss_snapshot(
  elapsed_s: float,
  initial_contacts: Mapping[str, ContactState],
  release_timing: Mapping[str, ReleaseTiming],
  *,
  dac_hold_up_s: float = 0,
  faults: Mapping[str, PoleFault] | None = None,
  latching: bool = False,
  board_present: bool = True,
  bypass_plug: bool = False,
) -> PowerLossSnapshot:
  """Model the finite transition after immediate removal of coil power.

  Each healthy energized pole retains NO until its supplied opening time,
  then remains OPEN until its supplied final NC-settle time. This conservative
  gap models a possible transition; it does not predict actual bounce waveform.
  Different timings deliberately allow DPDT pole skew. DAC availability is a
  separate assumption, illustrating dead-DAC selection before contact release.
  """
  if not (isfinite(elapsed_s) and isfinite(dac_hold_up_s)) or min(elapsed_s, dac_hold_up_s) < 0:
    raise ValueError("Elapsed and hold-up times must be finite and nonnegative")
  _validate_poles(initial_contacts, complete=True)
  _validate_poles(release_timing, complete=True)
  faults = faults or {}
  _validate_poles(faults, complete=False)
  contacts = {}
  for pole in POLES:
    initial = ContactState(initial_contacts[pole.name])
    timing = release_timing[pole.name]
    if pole.name in faults:
      contacts[pole.name] = FAULT_STATE[PoleFault(faults[pole.name])]
    elif latching or initial == ContactState.NC:
      contacts[pole.name] = initial
    elif elapsed_s >= timing.nc_settles_at_s:
      contacts[pole.name] = ContactState.NC
    elif elapsed_s >= timing.no_opens_at_s:
      contacts[pole.name] = ContactState.OPEN
    else:
      contacts[pole.name] = initial
  return PowerLossSnapshot(
    Topology(contacts, board_present=board_present, bypass_plug=bypass_plug),
    elapsed_s < dac_hold_up_s,
  )
