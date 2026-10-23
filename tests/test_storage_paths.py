import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from storage import paths


class StoragePathTests(unittest.TestCase):
    def test_source_mode_keeps_data_inside_source_storage(self):
        with patch.object(paths.sys, "frozen", False, create=True):
            self.assertEqual(paths.data_directory(), Path(paths.__file__).resolve().parent)
            self.assertEqual(
                paths.environment_file(),
                Path(paths.__file__).resolve().parents[2] / ".env",
            )

    def test_frozen_mode_uses_local_app_data_for_writable_files(self):
        with tempfile.TemporaryDirectory() as folder:
            with (
                patch.object(paths.sys, "frozen", True, create=True),
                patch.dict(os.environ, {"LOCALAPPDATA": folder}, clear=True),
            ):
                expected = Path(folder) / "JARVIS"
                self.assertEqual(paths.data_directory(), expected)
                self.assertEqual(paths.environment_file(), expected / ".env")

    def test_explicit_data_directory_override_wins_in_each_mode(self):
        with tempfile.TemporaryDirectory() as folder:
            override = Path(folder) / "custom-data"
            with (
                patch.object(paths.sys, "frozen", True, create=True),
                patch.dict(
                    os.environ,
                    {"LOCALAPPDATA": "ignored", "JARVIS_DATA_DIR": str(override)},
                    clear=True,
                ),
            ):
                self.assertEqual(paths.data_directory(), override)


if __name__ == "__main__":
    unittest.main()
