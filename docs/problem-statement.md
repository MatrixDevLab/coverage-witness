# Problem statement

## Observation

Delegated agents can produce a polished completion report while their execution
trace shows that requested files were never opened. A report is a claim about
work, not the record of work. If the same agent is allowed to decide both what
it inspected and whether inspection was complete, the final claim cannot expose
an omitted file by itself.

## Narrow product boundary

Given a request manifest, an observed event stream, and a completion claim,
`coverage-witness` answers only:

- which requested paths have a qualifying observed event;
- which requested paths are missing from the observed evidence; and
- which paths or events cannot be classified safely.

The result is evidence for a downstream policy, not a semantic verdict. It does
not infer that reading means understanding, that a tool event is genuine, or
that a completed review found no defects.

## Design constraints

- deterministic and dependency-free;
- secret-free inputs and fixtures;
- explicit malformed/unknown states instead of silent normalization;
- stable path identity rules documented in the schema;
- no default that upgrades an unsupported completion claim to success;
- machine-readable output plus a concise human-readable rendering.

## Falsifiable claim

The smallest useful verifier can block unsupported `complete` claims by
comparing a task-local manifest with independently recorded file events. This
claim is falsified if the comparison cannot be made reliable without semantic
judgment or provider-specific trace knowledge, or if a lower-friction existing
tool already provides the same boundary.
