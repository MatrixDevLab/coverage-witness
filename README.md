# coverage-witness

`coverage-witness` is a small, dependency-free verifier for a narrow failure
boundary in delegated work: an agent may claim to have completed a requested
file review without opening every requested file.

The first version will compare three explicit inputs:

1. a requested-file manifest;
2. observed file events from an execution trace; and
3. a completion claim.

It will emit typed `covered`, `missing`, and `unknown` evidence. A completion
claim that cannot be reconciled with the observed events must not be treated as
complete. The tool does not judge semantic review quality, truth, or defect
absence; it witnesses task-local coverage only.

## Why this exists

The OverclaimBench study reports that frontier agents often fail to read every
requested file and frequently describe incomplete work as complete. The useful
engineering seam is narrower than general agent evaluation: compare a request
that names files with an independently recorded event stream before accepting a
completion claim.

## Status

The first dependency-free implementation now lives in `coverage_witness.py`.
It reads the JSON schema in [schema.md](schema.md), emits deterministic JSON
or a concise text rendering, and uses exit codes suitable for a downstream
policy (`0` covered, `1` missing, `2` unknown). The fixture corpus under
`fixtures/` and the unit/integration tests exercise the falsifier boundary
without network, credentials, an LLM, or a provider-specific adapter.

## Roadmap

- [x] Create a dedicated public repository and state the problem boundary.
- [x] Define a secret-free manifest, event, and completion-claim schema.
- [x] Implement deterministic CLI output with explicit missing/unknown states.
- [x] Add adversarial fixtures: omitted reads, duplicate reads, malformed events,
      path aliases, and claims that exceed observed coverage.
- [x] Validate one reviewable integration sample end-to-end.
- [ ] Stop at the deterministic fixture corpus and one integration sample
      unless an external consumer proves that a provider-specific adapter is
      necessary.

## Falsifier and stopping point

This hypothesis should be rejected or paused if users need semantic review
quality, provider-specific trace adapters, or workflow-engine integration before
the task-local verifier is useful, or if an existing tool already solves this
exact boundary with lower friction. V1 intentionally excludes LLM judgment,
credential handling, transport integrations, and claims about whether a file's
contents were correct.

See [the problem statement](docs/problem-statement.md) and
[the validation method](docs/validation.md).
