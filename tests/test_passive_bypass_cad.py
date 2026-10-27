"""Actual exported CAD mapping, not a copy of the generator's part table."""

from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).parents[1] / "tools"))
import check_passive_bypass_design as CHECK


class PassiveCarrierCadTests(unittest.TestCase):
  def test_exported_cad_preserves_eighteen_original_contact_terminals(self):
    self.assertEqual(CHECK.audit_carrier(), [])

  def test_manufacturer_footprint_pin_pitch_is_corrected(self):
    self.assertEqual(CHECK.audit_footprint(), [])

  def test_historical_kicad_sources_are_unchanged(self):
    self.assertEqual(CHECK.audit_original_hashes(), [])


if __name__ == "__main__":
  unittest.main()
