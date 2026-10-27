#!/usr/bin/env python3
"""Decode the MiLa heartbeat with opendbc CANParser on a comma device."""

from __future__ import annotations

import argparse
from pathlib import Path

TEST_CAN_ID = 0x5A5
MESSAGE_NAME = "MILA_BENCH_HEARTBEAT"


def main() -> int:
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument("--bus", type=int, required=True, help="src bus found by comma_can_listener.py")
  parser.add_argument(
    "--dbc",
    type=Path,
    default=Path(__file__).with_name("mila_bench.dbc"),
    help="path to the bench DBC",
  )
  parser.add_argument("--count", type=int, default=10)
  args = parser.parse_args()

  import openpilot.cereal.messaging as messaging
  from opendbc.can.parser import CANParser
  from openpilot.selfdrive.pandad import can_capnp_to_list

  can_parser = CANParser(str(args.dbc), [(MESSAGE_NAME, 2)], args.bus)
  can_socket = messaging.sub_sock("can", conflate=False, timeout=1000)
  received = 0

  while received < args.count:
    raw_messages = messaging.drain_sock_raw(can_socket, wait_for_one=True)
    if not raw_messages:
      continue
    updated = can_parser.update(can_capnp_to_list(raw_messages))
    if TEST_CAN_ID not in updated:
      continue
    values = can_parser.vl[MESSAGE_NAME]
    received += 1
    print(
      f"decoded {received}/{args.count}: sequence={int(values['SEQUENCE'])} "
      f"controller=0x{int(values['CONTROLLER']):02X} version={int(values['VERSION'])}"
    )

  print(f"PASS: CANParser decoded {received} DBC heartbeats on bus {args.bus}")
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
