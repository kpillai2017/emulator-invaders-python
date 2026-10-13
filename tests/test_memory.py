"""ROM-loading tests using synthetic bytes, not game ROMs.

Run from the project root: python3 -m unittest discover -s tests -v
"""
import contextlib
import io
from pathlib import Path
import tempfile
import unittest

from memory import Memory


class MemoryTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix="tmp_rovo_", dir=Path(__file__).resolve().parents[1])
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "synthetic.rom"
        self.memory = Memory()

    def test_missing_rom(self):
        with contextlib.redirect_stderr(io.StringIO()) as error:
            self.assertFalse(self.memory.init(self.path))
        self.assertIn("Supply your own", error.getvalue())
        self.assertEqual(len(self.memory.memoryPtr), 0x8000)

    def test_invalid_sizes_leave_memory_unchanged(self):
        for size in (0, 8191, 8193, 32769):
            with self.subTest(size=size):
                self.path.write_bytes(b"\xAA" * size)
                before = bytes(self.memory.memoryPtr)
                with contextlib.redirect_stderr(io.StringIO()):
                    self.assertFalse(self.memory.init(self.path))
                self.assertEqual(bytes(self.memory.memoryPtr), before)

    def test_valid_rom(self):
        data = bytes(range(256)) * 32
        self.path.write_bytes(data)
        self.assertTrue(self.memory.init(self.path))
        self.assertEqual(self.memory.memoryPtr[:8192], data)
        self.assertEqual(self.memory.memoryPtr[8192:], bytes(0x8000 - 8192))


if __name__ == "__main__":
    unittest.main()
