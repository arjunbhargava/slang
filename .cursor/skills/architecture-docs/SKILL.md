---
name: architecture-docs
description: >
  Design sensible architecture and write clear, didactic documentation. Use when
  designing or restructuring modules or system boundaries, writing or revising
  READMEs, design docs, ADRs, or module docs, or explaining how a system works.
  Not for routine code edits that don't change structure or docs.
---

# Architecture and documentation

Good architecture and good documentation both aim to let a newcomer build an
accurate mental model quickly. Choose the structure that is simplest to
explain correctly, and write the explanation that makes the structure obvious.
Ponytail minimalism still applies: no layer, document, or section without a
reader who needs it.

## Architecture

Before proposing structure, state the problem in terms of data and constraints:
inputs, outputs, state, who owns the state, latency/throughput/cost bounds, and
the failure modes that matter. Structure follows from these, not from patterns.

- **Deep modules** (Ousterhout): small interface, substantial hidden
  behaviour. A module whose interface is as complex as its implementation
  should be merged into its caller.
- **Boundaries where change or trust differs.** Split along axes that change
  independently (provider SDK vs. domain logic) or at trust boundaries
  (client vs. server). Don't split along axes that always change together.
- **Dependencies point inward.** Domain logic imports nothing
  provider-specific; adapters depend on the domain, never the reverse.
- **One owner per piece of state.** Name it. Everything else receives it
  explicitly or asks the owner.
- **Invariants are explicit.** Write each one down next to the code that
  enforces it, and enforce it in one place.
- **Make failure a first-class path.** For each external call: what happens on
  timeout, auth failure, partial result? Surface it; don't silently fall back.
- **Concrete first, abstract on the third use.** One implementation gets no
  interface. Two similar ones are often fine. Three justify extraction.

For a non-trivial decision, write it as a short ADR (Nygard format): context,
decision, consequences, and alternatives rejected with the reason. Store as
`docs/adr/NNNN-title.md`; never rewrite an accepted ADR, supersede it.

## Documentation

Classify every document by what the reader is doing (Diátaxis), and don't mix
the four kinds in one section:

| Kind | Reader's goal | Shape |
|---|---|---|
| Tutorial | Learn by doing | Guided path with a guaranteed working result |
| How-to | Accomplish a specific task | Numbered steps, prerequisites, no theory |
| Reference | Look something up | Complete, consistent, terse; generated where possible |
| Explanation | Understand why | Context, trade-offs, alternatives, history |

Didactic principles:

- **Open with the claim.** First paragraph: what this is, who it's for, and
  what the reader can do after reading. Include status (draft, stable,
  deprecated) when it isn't obvious.
- **Concrete before abstract.** Show one real example or data flow, then
  generalize. A single end-to-end trace (request → components → response)
  teaches more than a component list.
- **Define before use.** Introduce each term once, precisely, then use it
  consistently. Never use two names for one thing.
- **Progressive disclosure.** Overview → mechanism → edge cases. A reader who
  stops after the first section should still have a correct model, just a
  coarse one.
- **Explain why, not what.** Code shows what. Docs carry intent, constraints,
  rejected alternatives, and the conditions under which a decision should be
  revisited.
- **Quantify.** Prefer "p95 < 800 ms end of speech → first audio" to "fast".
  State units, bounds, and where numbers came from (measured vs. documented
  vs. assumed).
- **Diagrams as text.** ASCII or Mermaid in the markdown, so they diff and
  review. One diagram per level of abstraction (C4: context → container →
  component); never mix levels in one diagram.
- **Link, don't duplicate.** Each fact lives in one place. Reference external
  sources inline where the claim is made.

## Placement

- `README.md`: what it is, quickstart, pointer to the rest. Short.
- `docs/architecture.md`: system context, main data flow, module map,
  invariants, failure handling.
- `docs/adr/`: decisions.
- Module-level doc comment: that module's responsibility, invariants, and
  what it deliberately does not do.

## Review checklist

Before finishing, check the result against these:

1. Could a new engineer draw the main data flow after reading only the
   overview?
2. Is every term defined once and used consistently?
3. Does every component have one stated responsibility and owner of state?
4. Are failure modes and invariants written down where they're enforced?
5. Is there anything (a section, layer, or abstraction) that no reader needs?
   Delete it.
