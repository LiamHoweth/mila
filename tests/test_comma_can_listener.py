from pathlib import Path
import sys
import unittest


TOOLS_PATH = Path(__file__).parents[1] / "tools"
sys.path.insert(0, str(TOOLS_PATH))
import comma_can_listener as MODULE


class DecodePayloadTests(unittest.TestCase):
  def test_decodes_valid_mcp2515_heartbeat(self):
    heartbeat = MODULE.decode_payload(bytes.fromhex("4d494c4134121501"))

    self.assertEqual(heartbeat.sequence, 0x1234)
    self.assertEqual(heartbeat.controller, 0x15)
    self.assertEqual(heartbeat.version, 1)

  def test_decodes_valid_mcp2518fd_heartbeat(self):
    heartbeat = MODULE.decode_payload(bytes.fromhex("4d494c41ffff1801"))

    self.assertEqual(heartbeat.sequence, 0xFFFF)
    self.assertEqual(heartbeat.controller, 0x18)

  def test_rejects_wrong_magic(self):
    self.assertIsNone(MODULE.decode_payload(bytes.fromhex("0000000000000000")))

  def test_rejects_wrong_length(self):
    self.assertIsNone(MODULE.decode_payload(b"MILA"))


if __name__ == "__main__":
  unittest.main()
