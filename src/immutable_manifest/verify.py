"""Verify local files against a JSON manifest without network access."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath
from typing import Any


class ManifestError(ValueError):
    """The manifest is malformed or names an unsafe path."""


def _safe_path(root: Path, name: str) -> Path:
    path = PurePosixPath(name)
    if not name or path.is_absolute() or any(part in ("", ".", "..") for part in path.parts):
        raise ManifestError(f"unsafe relative path: {name!r}")
    target = root.joinpath(*path.parts)
    if not target.resolve().is_relative_to(root.resolve()):
        raise ManifestError(f"path escapes root: {name!r}")
    return target


def _digest(path: Path) -> tuple[int, str]:
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            size += len(chunk)
            digest.update(chunk)
    return size, digest.hexdigest()


def verify_manifest(root: Path, manifest: dict[str, Any]) -> list[dict[str, Any]]:
    """Return one deterministic result per entry; reject malformed manifests."""
    if not isinstance(manifest, dict) or manifest.get("schema") != "immutable-file-manifest-v1":
        raise ManifestError("unsupported schema")
    entries = manifest.get("files")
    if not isinstance(entries, list):
        raise ManifestError("files must be a list")
    seen: set[str] = set()
    results: list[dict[str, Any]] = []
    for item in entries:
        if not isinstance(item, dict) or set(item) != {"path", "bytes", "sha256"}:
            raise ManifestError("each file requires path, bytes, sha256")
        name, expected_size, expected_hash = item["path"], item["bytes"], item["sha256"]
        if not isinstance(name, str) or name in seen:
            raise ManifestError("path missing or duplicated")
        seen.add(name)
        if type(expected_size) is not int or expected_size < 0:
            raise ManifestError("bytes must be a nonnegative integer")
        if not isinstance(expected_hash, str) or len(expected_hash) != 64 or any(c not in "0123456789abcdef" for c in expected_hash):
            raise ManifestError("sha256 must be lowercase hexadecimal")
        target = _safe_path(root, name)
        if target.is_file():
            actual_size, actual_hash = _digest(target)
            status = "match" if (actual_size, actual_hash) == (expected_size, expected_hash) else "mismatch"
        else:
            actual_size, actual_hash, status = None, None, "missing"
        results.append({"path": name, "status": status, "bytes": actual_size, "sha256": actual_hash})
    return results


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Verify local files against an immutable manifest")
    parser.add_argument("root", type=Path)
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args()
    try:
        manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
        result = verify_manifest(args.root, manifest)
    except (ManifestError, OSError, json.JSONDecodeError) as exc:
        parser.error(str(exc))
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if all(item["status"] == "match" for item in result) else 1


if __name__ == "__main__":
    raise SystemExit(main())
