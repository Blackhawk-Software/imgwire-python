from __future__ import annotations

import tempfile
import unittest
from io import BytesIO

from imgwire.uploads import resolve_upload_input


class UploadResolutionTests(unittest.TestCase):
    def test_resolves_path_input(self) -> None:
        with tempfile.NamedTemporaryFile(suffix=".jpg") as handle:
            handle.write(b"abc")
            handle.flush()

            resolved = resolve_upload_input(handle.name)

        self.assertEqual(resolved.file_name.endswith(".jpg"), True)
        self.assertEqual(resolved.content, b"abc")
        self.assertEqual(resolved.content_length, 3)

    def test_resolves_file_object_input(self) -> None:
        handle = BytesIO(b"payload")
        handle.name = "image.png"

        resolved = resolve_upload_input(handle)

        self.assertEqual(resolved.file_name, "image.png")
        self.assertEqual(resolved.content, b"payload")
        self.assertEqual(resolved.content_length, 7)

    def test_resolves_bytes_input(self) -> None:
        resolved = resolve_upload_input(b"payload", file_name="image.gif")

        self.assertEqual(resolved.file_name, "image.gif")
        self.assertEqual(resolved.content, b"payload")
        self.assertEqual(resolved.content_length, 7)


if __name__ == "__main__":
    unittest.main()
