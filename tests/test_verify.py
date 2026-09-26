import hashlib
import tempfile
import unittest
from pathlib import Path

from immutable_manifest import ManifestError, verify_manifest


class VerifyManifestTests(unittest.TestCase):
    def test_match_and_changed_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "sample.txt"
            target.write_bytes(b"fictional sample\n")
            manifest = {"schema": "immutable-file-manifest-v1", "files": [{
                "path": "sample.txt", "bytes": 17,
                "sha256": hashlib.sha256(b"fictional sample\n").hexdigest(),
            }]}
            self.assertEqual(verify_manifest(root, manifest)[0]["status"], "match")
            target.write_bytes(b"changed\n")
            self.assertEqual(verify_manifest(root, manifest)[0]["status"], "mismatch")

    def test_rejects_escape_and_symlink(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = {"schema": "immutable-file-manifest-v1", "files": [{
                "path": "../outside.txt", "bytes": 0, "sha256": "0" * 64,
            }]}
            with self.assertRaises(ManifestError):
                verify_manifest(root, manifest)
            (root / "link").symlink_to(Path(directory).parent)
            manifest["files"][0]["path"] = "link/other.txt"
            with self.assertRaises(ManifestError):
                verify_manifest(root, manifest)

    def test_missing_and_duplicate(self):
        with tempfile.TemporaryDirectory() as directory:
            item = {"path": "absent.txt", "bytes": 0, "sha256": "0" * 64}
            manifest = {"schema": "immutable-file-manifest-v1", "files": [item]}
            self.assertEqual(verify_manifest(Path(directory), manifest)[0]["status"], "missing")
            manifest["files"].append(item)
            with self.assertRaises(ManifestError):
                verify_manifest(Path(directory), manifest)


if __name__ == "__main__":
    unittest.main()
