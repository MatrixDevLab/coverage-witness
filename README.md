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

This repository contains the product statement and validation boundary. The
implementation starts only after the falsifier below is checked against the
smallest useful fixture corpus.

## Roadmap

- [x] Create a dedicated public repository and state the problem boundary.
- [ ] Define a secret-free manifest, event, and completion-claim schema.
- [ ] Implement deterministic CLI output with explicit missing/unknown states.
- [ ] Add adversarial fixtures: omitted reads, duplicate reads, malformed events,
      path aliases, and claims that exceed observed coverage.
- [ ] Validate one reviewable integration sample end-to-end.
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
