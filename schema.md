# Input schema

The CLI reads one JSON object from stdin or `--input FILE`:

```json
{
  "manifest": ["src/app.py", "README.md"],
  "events": [
    {"kind": "file_read", "path": "src/app.py"},
    {"kind": "file_read", "path": "./README.md"}
  ],
  "claim": {"status": "complete", "paths": ["src/app.py", "README.md"]}
}
```

`manifest` is the requested-file list. Each entry is a string or an object
with a `path` string; entries are required by default. `events` is an observed
event stream. Only events with `kind: "file_read"` provide coverage. Other
well-formed event kinds are retained only in the event counts. `claim.status`
must be `complete`, `partial`, or `unknown`; `claim.paths`, when present, is a
self-report and never adds coverage.

Paths are POSIX-relative, root-confined identities. `./src/app.py` and
`src/app.py` are aliases; `..`, absolute paths, NULs, and backslashes are
invalid rather than guessed at. Case is significant. Duplicate manifest paths,
malformed events, and claims naming paths outside the manifest produce explicit
`unknown` issues.

The machine result contains one status per manifest path (`covered`, `missing`,
or `unknown`) and an overall `verdict`. A complete claim is `covered` only
when every manifest path has a qualifying observed event and no issue exists.
Missing evidence yields `missing`; malformed or otherwise unsupported evidence
yields `unknown`. Exit codes are 0 for `covered`, 1 for `missing`, and 2 for
`unknown`.
