# Diagram design system

The goal is diagrams a newcomer can read without help. Each one answers one
question, uses a small, fixed visual vocabulary explained by a legend, and
stays quiet enough that the eye lands on what matters. Colour and line style
always mean something; nothing is decorative.

Diagrams are Mermaid, written inline in markdown so GitHub renders them and
reviewers diff the source. Every rule below works within what GitHub's Mermaid
renderer supports.

## Principles

1. **One question per diagram.** Write the question above the diagram and the
   takeaway below it. If the takeaway needs "and", split the diagram.
2. **Semantic colour only.** Colour encodes the element's kind, and the kind is
   always shown twice, by colour and by shape, so a colour-blind reader or a
   greyscale print loses nothing.
3. **One accent.** Only core elements get the orange accent, so it draws the eye
   to where the important logic lives. If everything is highlighted, nothing is.
4. **Say what moves.** Edge labels are nouns for what flows (`committed
   transcript`), never verbs like `calls` or `uses`.
5. **Consistent identity.** An element has the same name, kind, and colour in
   every diagram, so readers can follow it as the diagrams zoom in.
6. **Small.** At most ~12 nodes, edge labels of at most 4 words, node subtitles
   of at most 5 words. Past that, split by level (context, then components,
   then one component's internals).

## Palette

Based on [Anthropic's brand palette](https://github.com/anthropics/skills/blob/main/skills/brand-guidelines/SKILL.md):
warm neutrals plus three muted accents. Fills are 20% tints of the accent over
Light. Contrast ratios are WCAG values.

| Token | Hex | Use |
|---|---|---|
| Dark | `#141413` | All text (≥ 14:1 on every fill) |
| Light | `#faf9f5` | Default fill, edge-label chips, boundary fill |
| Light Gray | `#e8e6dc` | Stores, notes, alternating sequence phases (`#f0eee6`) |
| Mid Gray | `#b0aea5` | Boundary borders, lifelines |
| Line | `#8a887f` | Edges and default borders (3.6:1 on white, 5.3:1 on GitHub dark) |
| Muted | `#5e5d59` | Boundary titles, secondary text (6.3:1 on Light) |
| Orange / tint | `#d97757` / `#f3dfd5` | Core |
| Green / tint | `#788c5d` / `#e0e3d7` | People, and states waiting on a person |
| Blue / tint | `#6a9bcc` / `#dde6ed` | External services |

Text is never placed directly on the page background. GitHub's dark mode
renders the diagram on `#0d1117`, so every piece of text must sit on a fill:
a node, a boundary, an edge-label chip, or a sequence phase.

## Vocabulary

A repo uses a subset of these kinds. Add a new kind only when none of these
fits, and add it here first.

| Kind | Shape | Mermaid | `classDef` |
|---|---|---|---|
| Person | Stadium | `id([Name])` | `fill:#e0e3d7,stroke:#788c5d,stroke-width:1.5px,color:#141413` |
| Core: owns state or policy | Rounded | `id(Name)` | `fill:#f3dfd5,stroke:#d97757,stroke-width:2px,color:#141413` |
| Module: adapter or plumbing we own | Rounded | `id(Name)` | `fill:#faf9f5,stroke:#8a887f,stroke-width:1px,color:#141413` |
| External service | Square | `id[Name]` | `fill:#dde6ed,stroke:#6a9bcc,stroke-width:1.5px,color:#141413` |
| Store: database, file, queue | Cylinder | `id[(Name)]` | `fill:#e8e6dc,stroke:#8a887f,stroke-width:1px,color:#141413` |
| Boundary: trust or deployment | Dashed region | `subgraph id [Name]` | `fill:#faf9f5,stroke:#b0aea5,stroke-dasharray:5 4,color:#5e5d59` |
| Planned (modifier) | Dashed border | `class id planned` | `stroke-dasharray:5 4` |

| Edge | Mermaid | Meaning |
|---|---|---|
| Primary path | `==>` | The route to read first. Keep it to one chain per diagram. |
| Data flow | `-->` | Something moves at runtime; the label says what |
| Optional or test-only | `-.->` | Paths not always taken, test entry points, planned edges |
| Request and response | one edge, label `request → response` | Draw one edge per relationship; the sequence diagram shows the round trip |

Node labels: title in `<b>…</b>`, then an optional one-line subtitle for the
node's role (`<b>Conversation agent</b><br/>history · tutoring policy`).
Separate list items with ` · `.

State diagrams reuse the same classes, keeping the same meanings: a Person
(green) state waits on a person, and Module (plain) means the system is
working. Sequence diagrams encode kind by participant order: people on the
left, then owned code, then externals on the right.

## Headers

GitHub renders each block on its own, so every block carries its own config.
Copy these verbatim. `fontFamily` must sit directly under `config`; under
`themeVariables` it is ignored.

Flowchart and state diagram:

```yaml
---
config:
  theme: base
  fontFamily: "ui-sans-serif, -apple-system, 'Segoe UI', 'Helvetica Neue', Arial, 'Noto Sans', sans-serif"
  themeVariables:
    fontSize: 15px
    primaryColor: "#faf9f5"
    primaryTextColor: "#141413"
    primaryBorderColor: "#8a887f"
    lineColor: "#8a887f"
    edgeLabelBackground: "#faf9f5"
    clusterBkg: "#faf9f5"
    clusterBorder: "#b0aea5"
  flowchart:
    curve: linear
    nodeSpacing: 40
    rankSpacing: 56
    padding: 14
---
```

Drop the `flowchart:` block for state diagrams. Put the `classDef` lines for
the kinds the diagram uses at the end of the block, followed by `class` lines.

Sequence diagram:

```yaml
---
config:
  theme: base
  fontFamily: "ui-sans-serif, -apple-system, 'Segoe UI', 'Helvetica Neue', Arial, 'Noto Sans', sans-serif"
  themeVariables:
    fontSize: 15px
    primaryTextColor: "#141413"
    lineColor: "#8a887f"
    actorBkg: "#faf9f5"
    actorBorder: "#8a887f"
    actorTextColor: "#141413"
    actorLineColor: "#b0aea5"
    signalColor: "#8a887f"
    signalTextColor: "#141413"
    noteBkgColor: "#e8e6dc"
    noteBorderColor: "#b0aea5"
    noteTextColor: "#141413"
    sequenceNumberColor: "#faf9f5"
  sequence:
    mirrorActors: false
    messageMargin: 36
    boxMargin: 8
---
```

In sequence diagrams:

- Use `autonumber`, so prose can refer to steps by number.
- Declare people with `participant`, not `actor`. An actor's label renders
  directly on the page background and disappears in dark mode.
- Wrap every message in a phase: `rect rgb(250, 249, 245)`, alternating with
  `rect rgb(240, 238, 230)`, each opening with `Note over <first>,<last>: Phase`.
  Phases give the story its chapters and keep message text on a light fill.
  Dotted arrows (`-->>`) are responses.

## Portability

- Don't use `linkStyle`: its edge indices break silently when a PR adds an edge.
- Don't use the `@{ shape: … }` node syntax or ELK layout, because GitHub's
  renderer may not support them.
- Add `accTitle:` and `accDescr:` to every diagram for screen readers.

## Page layout

`docs/architecture.md` is laid out in this order:

1. A status line: planned, partial, or implemented.
2. **How to read this doc**: the diagrams in reading order, each linked with its
   question.
3. **Legend**: a small flowchart with one example of each kind and edge the repo
   uses, followed by a table with columns `Element | Looks like | In <repo>`.
   The last column is the repo-specific meaning, for example "External service:
   a paid provider API reached over the network".
4. **Glossary**: every domain term that appears in a diagram, defined in one
   line each.
5. The diagrams, numbered, each as: heading, question, diagram, takeaway (1–3
   sentences, including any invariant the diagram can't show).

When a PR adds a kind, an edge style, or a term to any diagram, it updates the
legend and glossary in the same PR.

## Verify

Render every diagram against both GitHub page backgrounds, and look at the
images before committing:

```bash
npx -y -p @mermaid-js/mermaid-cli@11 mmdc -i docs/architecture.md -o /tmp/arch-light.png -b '#ffffff' -s 2
npx -y -p @mermaid-js/mermaid-cli@11 mmdc -i docs/architecture.md -o /tmp/arch-dark.png -b '#0d1117' -s 2
```

Check the renders for:

- Text sitting on the page background, which vanishes in dark mode.
- Overlapping labels.
- A diagram too wide to read at page width. Switch it to `TB` or split it.

As root, or in some sandboxes, Chromium needs `-p` pointing to a Puppeteer
config containing `{"args":["--no-sandbox"]}`. Attach the renders to the PR.
