"""Offline verification of immutable file manifests."""

from .verify import ManifestError, verify_manifest

__all__ = ["ManifestError", "verify_manifest"]
