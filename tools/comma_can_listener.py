#!/usr/bin/env python3
"""Confirm that comma's CAN service sees the MiLa bench heartbeat."""

from __future__ import annotations

import argparse
import time
from dataclasses import dataclass

TEST_CAN_ID = 0x5A5
MAGIC = b"MILA"


@dataclass(frozen=True)
class Heartbeat:
  sequence: int
  controller: int
  version: int


def decode_payload(data: bytes) -> Heartbeat | None:
  if len(data) != 8 or data[:4] != MAGIC:
    return None
  return Heartbeat(
    sequence=int.from_bytes(data[4:6], "little"),
    controller=data[6],
    version=data[7],
  )


def main() -> int:
  parser = argparse.ArgumentParser(
    description="Listen for the ESP32 MiLa heartbeat on comma's cereal CAN service."
  )
  parser.add_argument("--bus", type=int, default=None, help="match one src bus; default: any")
  parser.add_argument("--count", type=int, default=10, help="heartbeats required for success")
  parser.add_argument("--timeout", type=float, default=20.0, help="overall timeout in seconds")
  parser.add_argument("--addr", default="127.0.0.1", help="msgq host")
  args = parser.parse_args()

  import openpilot.cereal.messaging as messaging

  can_socket = messaging.sub_sock("can", addr=args.addr, conflate=False, timeout=1000)
  deadline = time.monotonic() + args.timeout
  received = 0
  seen_buses: set[int] = set()

  while received < args.count and time.monotonic() < deadline:
    for event in messaging.drain_sock(can_socket, wait_for_one=True):
      for frame in event.can:
        seen_buses.add(frame.src)
        if frame.address != TEST_CAN_ID or (args.bus is not None and frame.src != args.bus):
          continue
        heartbeat = decode_payload(bytes(frame.dat))
        if heartbeat is None:
          continue
        received += 1
        print(
          f"heartbeat {received}/{args.count}: bus={frame.src} id=0x{frame.address:03X} "
          f"sequence={heartbeat.sequence} controller=0x{heartbeat.controller:02X} "
          f"version={heartbeat.version} data={bytes(frame.dat).hex()}"
        )

  if received >= args.count:
    print(f"PASS: received {received} valid MiLa heartbeats")
    return 0

  buses = ",".join(str(bus) for bus in sorted(seen_buses)) or "none"
  print(f"FAIL: received {received}/{args.count}; observed CAN src buses: {buses}")
  return 2


if __name__ == "__main__":
  raise SystemExit(main())
