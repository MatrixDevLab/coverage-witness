# Validation method

The first implementation is successful only if it passes all of these checks:

1. A secret-free fixture corpus covers complete coverage, omitted paths,
   duplicate events, malformed events, path aliases, and unsupported claims.
2. Repeated runs over identical inputs produce byte-identical machine output.
3. Every unsupported completion claim is classified as `unknown` or `missing`,
   never silently accepted as complete.
4. The validator distinguishes an observed event from an agent-authored claim;
   the claim cannot add coverage by itself.
5. A small integration sample produces a reviewable result from a manifest and
   trace without an LLM, network, credentials, or provider-specific adapter.
6. The complete diff, tests, compilation/lint checks, and repository history
   are reviewed before any release decision.

The stopping point is one deterministic fixture corpus and one integration
sample. Further adapters or semantic review checks require evidence from an
external consumer.
