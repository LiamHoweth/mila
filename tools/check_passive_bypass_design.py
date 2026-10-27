#!/usr/bin/env python3
"""Independent CAD connectivity audit against retained PCB 2.0 evidence.

Does not establish physical continuity, release timing, qualification or safety.
Run after rebuilding/exporting the new KiCad contact-carrier project.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
CARRIER = ROOT / "hardware/passive_bypass_rev_a"
ORIGINAL = ROOT / "capstone_Oscar_Zheng_Jared_05032026/PCB_2.0/PCBGerberFiles/PCB1.2.kicad_pcb"

# Explicit independent oracle: original module pad -> old connector pad ->
# new package pin. NC/NO identities of the old module still need a DMM test.
CONTACTS = (
  ("RLY1", "3", "J7", "17", "J4", "14"),
  ("RLY1", "2", "J7", "18", "J4", "13"),
  ("RLY1", "4", "J7", "16", "J5", "10"),
  ("RLY1", "6", "J7", "14", "J4", "15"),
  ("RLY1", "7", "J7", "15", "J4", "12"),
  ("RLY1", "5", "J7", "13", "J5", "11"),
  ("RLY2", "3", "J7", "11", "J4", "16"),
  ("RLY2", "2", "J7", "12", "J4", "11"),
  ("RLY2", "4", "J7", "10", "J6", "8"),
  ("RLY2", "6", "J7", "8", "J4", "17"),
  ("RLY2", "7", "J7", "9", "J4", "10"),
  ("RLY2", "5", "J7", "7", "J6", "9"),
  ("RLY3", "3", "J7", "5", "J4", "18"),
  ("RLY3", "2", "J7", "6", "J4", "9"),
  ("RLY3", "4", "J7", "4", "J4", "8"),
  ("RLY4", "3", "J7", "2", "J4", "19"),
  ("RLY4", "2", "J7", "3", "J4", "8"),
  ("RLY4", "4", "J7", "1", "J4", "9"),
)


def sexpr(source: str) -> list:
  """Small read-only parser for KiCad expressions; preserves quoted atoms."""
  root: list = []
  stack = [root]
  for token in re.findall(r'"(?:\\.|[^"\\])*"|[()]|[^\s()]+', source):
    if token == "(":
      expression: list = []
      stack[-1].append(expression)
      stack.append(expression)
    elif token == ")":
      if len(stack) == 1:
        raise ValueError("Unbalanced KiCad expression")
      stack.pop()
    else:
      stack[-1].append(json.loads(token) if token.startswith('"') else token)
  if len(stack) != 1 or len(root) != 1:
    raise ValueError("Unbalanced or multiple KiCad roots")
  return root[0]


def children(expression: list, kind: str) -> list[list]:
  return [node for node in expression if isinstance(node, list) and node and node[0] == kind]


def pcb_pads(path: Path) -> dict[tuple[str, str], str]:
  result = {}
  for fp in children(sexpr(path.read_text()), "footprint"):
    ref = next(node[2] for node in children(fp, "property") if node[1] == "Reference")
    for pad in children(fp, "pad"):
      nets = children(pad, "net")
      result[(ref, pad[1])] = nets[0][-1] if nets else ""
  return result


def xml_netlist(path: Path) -> tuple[dict, dict, dict]:
  doc = ET.parse(path).getroot()
  values = {comp.attrib["ref"]: comp.findtext("value") for comp in doc.findall("./components/comp")}
  pin_nets, net_nodes = {}, {}
  for net in doc.findall("./nets/net"):
    # Eeschema prefixes flat-sheet local labels with '/', while the pin CSV
    # deliberately presents connector names without that sheet path.
    name = net.attrib["name"].removeprefix("/")
    if name in net_nodes:
      raise ValueError(f"Ambiguous normalized net: {name}")
    nodes = {(node.attrib["ref"], node.attrib["pin"]) for node in net.findall("node")}
    net_nodes[name] = nodes
    for node in nodes:
      if node in pin_nets:
        raise ValueError(f"Duplicate netlist pin: {node}")
      pin_nets[node] = name
  return pin_nets, net_nodes, values


def audit_carrier(path: Path = CARRIER / "passive_bypass.net") -> list[str]:
  problems = []
  original = pcb_pads(ORIGINAL)
  pin_nets, nets, values = xml_netlist(path)

  def expect(ref: str, pin: str, net: str) -> None:
    actual = pin_nets.get((ref, pin))
    if actual != net:
      problems.append(f"{ref}.{pin}: expected {net}, got {actual}")

  for ref, pin, old_ref, old_pin, connector, connector_pin in CONTACTS:
    if not original[(old_ref, old_pin)] or original[(old_ref, old_pin)] != original[(connector, connector_pin)]:
      problems.append(f"Original evidence changed at {old_ref}.{old_pin}")
    expect(ref, pin, f"{connector}_{connector_pin}")
  for pad in range(19, 25):
    node = ("J7", str(pad))
    net = original.get(node)
    # KiCad assigns a named singleton net even to a no-connect pad.
    if net and (not net.startswith("unconnected-") or any(
      other != node and other_net == net for other, other_net in original.items()
    )):
      problems.append(f"Previously unused original contact J7.{pad} now connected")
  for pad in range(26, 32):
    if original[("J7", str(pad))] != original[("J4", "23")]:
      problems.append(f"Original common control no longer matches J7.{pad}")
  for pad, header in (("32", "25"), ("33", "26")):
    if original[("J7", pad)] != original[("J3", header)]:
      problems.append(f"Original independent control changed at J7.{pad}")

  signal_nets = {f"{row[4]}_{row[5]}" for row in CONTACTS}
  # No powered monitoring/protection branch may secretly share these paths.
  allowed_contact_nodes = {(row[0], row[1]) for row in CONTACTS}
  for net in signal_nets:
    for node in nets.get(net, set()):
      if node not in allowed_contact_nodes and node[0] not in {"J4B1", "JDAC1"}:
        problems.append(f"Unexpected semiconductor/branch on passive net {net}: {node}")

  for i, request in ((1, "REQ_GROUP"), (2, "REQ_GROUP"), (3, "REQ_K7"), (4, "REQ_K8")):
    ref = f"RLY{i}"
    if values.get(ref) != "G6K-2P-Y DC5":
      problems.append(f"Wrong/nonverified relay variant: {ref}")
    expect(ref, "1", "COIL_5V")
    expect(ref, "8", f"COIL_R{i}")
    expect(f"Q{i}", "3", f"COIL_R{i}")
    expect(f"Q{i}", "2", "GND")
    expect(f"Q{i}", "1", f"G_R{i}")
    expect(f"RG{i}", "1", request)
    expect(f"RG{i}", "2", f"G_R{i}")
    expect(f"RPD{i}", "1", f"G_R{i}")
    expect(f"RPD{i}", "2", "GND")
    expect(f"D{i}", "1", "COIL_5V")  # diode cathode
    expect(f"D{i}", "2", f"COIL_R{i}")
    if values.get(f"RG{i}") != "330R" or values.get(f"RPD{i}") != "10k":
      problems.append(f"Driver gate values changed for {ref}")
    if i in (3, 4):
      for pin in ("5", "6", "7"):
        net = pin_nets.get((ref, pin))
        if net and nets[net] != {(ref, pin)}:
          problems.append(f"Spare contact unexpectedly connected: {ref}.{pin}")

  for ref, pin, net in (
    ("JPWR1", "1", "5V_RAW"), ("JPWR1", "2", "GND"),
    ("JCTRL1", "1", "REQ_GROUP"), ("JCTRL1", "2", "REQ_K7"),
    ("JCTRL1", "3", "REQ_K8"), ("JCTRL1", "4", "COIL_PERMIT"),
    ("JCTRL1", "5", "GND"), ("JCTRL1", "6", "5V_RAW"),
    ("Q5", "2", "5V_RAW"), ("Q5", "3", "COIL_5V"), ("Q5", "1", "P_GATE"),
    ("Q6", "3", "P_GATE"), ("Q6", "2", "GND"), ("Q6", "1", "G_PERMIT"),
    ("RG6", "1", "COIL_PERMIT"), ("RG6", "2", "G_PERMIT"),
    ("RPD6", "1", "G_PERMIT"), ("RPD6", "2", "GND"),
    ("RPG1", "1", "5V_RAW"), ("RPG1", "2", "P_GATE"),
  ):
    expect(ref, pin, net)
  if values.get("Q5") != "AO3401A" or values.get("Q6") != "AO3400A":
    problems.append("Wrong high-side cutoff polarity/driver type")
  for ref in ("Q1", "Q2", "Q3", "Q4"):
    if values.get(ref) != "AO3400A":
      problems.append(f"Wrong low-side driver: {ref}")
  if values.get("RG6") != "330R" or values.get("RPD6") != "82k" or values.get("RPG1") != "10k":
    problems.append("Wrong cutoff gate bias values")
  if any(ref.startswith(("J", "C")) for ref, _ in nets.get("COIL_5V", set())):
    problems.append("Downstream coil rail has external connector or stored bulk energy")
  return problems


def audit_footprint() -> list[str]:
  path = CARRIER / "MiLa_Bench.pretty/Relay_G6K_2P_Y_corrected.kicad_mod"
  pads = {pad[1]: children(pad, "at")[0][1:3] for pad in children(sexpr(path.read_text()), "pad")}
  # Installed library origin uses coil pad 1 at x=0/y=0, pad 8 opposite.
  expected = {"1": (0, 0), "2": (0, 3.2), "3": (0, 5.4), "4": (0, 7.6),
              "8": (5.08, 0), "7": (5.08, 3.2), "6": (5.08, 5.4), "5": (5.08, 7.6)}
  return [f"Relay footprint pin {pin}: {pads.get(pin)} != {position}"
          for pin, position in expected.items()
          if tuple(map(float, pads.get(pin, ("nan", "nan")))) != position]


def audit_original_hashes() -> list[str]:
  manifest = ROOT / "hardware/review_evidence/original_source_hashes.json"
  return [f"Original source changed: {path}" for path, digest in json.loads(manifest.read_text()).items()
          if hashlib.sha256((ROOT / path).read_bytes()).hexdigest() != digest]


def main() -> int:
  problems = audit_carrier() + audit_footprint() + audit_original_hashes()
  report = {"scope": "CAD connectivity and source preservation only", "passed": not problems,
            "contact_terminal_count": len(CONTACTS), "problems": problems}
  out = ROOT / "hardware/review_evidence/connectivity_audit.json"
  out.write_text(json.dumps(report, indent=2) + "\n")
  print(json.dumps(report, indent=2))
  return 1 if problems else 0


if __name__ == "__main__":
  raise SystemExit(main())
