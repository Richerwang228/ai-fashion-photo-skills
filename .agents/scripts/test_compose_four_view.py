#!/usr/bin/env python3
"""Offline tests for compose_four_view.py."""

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image


SCRIPT = Path(__file__).with_name("compose_four_view.py")
SPEC = importlib.util.spec_from_file_location("compose_four_view", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class ComposeFourViewTests(unittest.TestCase):
    def test_composes_fixed_size_contact_sheet(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            inputs = []
            for index, color in enumerate(("red", "green", "blue", "black")):
                path = root / f"{index}.png"
                Image.new("RGB", (120 + index * 10, 240), color).save(path)
                inputs.append(path)
            output = root / "result.png"
            MODULE.compose(inputs, output, panel_width=100, height=200, gap=5)
            with Image.open(output) as result:
                self.assertEqual(result.size, (415, 200))
                self.assertEqual(result.format, "PNG")

    def test_requires_all_four_inputs(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with self.assertRaises(ValueError):
                MODULE.compose([], root / "result.png")


if __name__ == "__main__":
    unittest.main()
