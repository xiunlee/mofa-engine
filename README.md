# Immutable Manifest Checker

A small offline Python tool that verifies local files against expected byte counts and SHA-256 digests. It has no network integration and uses fictional data in tests.

A manifest has this shape:

```json
{"schema":"immutable-file-manifest-v1","files":[{"path":"sample.txt","bytes":17,"sha256":"<64 lowercase hexadecimal characters>"}]}
```

Run `python -m unittest discover -s tests` with `PYTHONPATH=src`, or run `python -m immutable_manifest.verify ROOT MANIFEST.json`.

The package verifies files only. It does not select the current version, publish content, or connect to a storage provider.

No license has been granted yet. A code license can be added after its owner chooses one.
