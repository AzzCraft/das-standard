# Build Requirements — das-standard

das-standard is a documentation-only repo. No build step is required.

## Toolchain

| Tool | Minimum | Purpose |
|------|---------|---------|
| `bash` | 3.2+ | verify script |
| `python3` | 3.10+ | schema validation in verify |
| `git` | 2.30+ | version pinning |

Install pinned verification dependencies before running local, CI, or release
verification:

```bash
python3 -m pip install -r requirements-verify.txt
```

`requirements-verify.txt` pins `jsonschema`, which is required by
`scripts/verify`.
