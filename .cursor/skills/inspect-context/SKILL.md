---
name: inspect-context
description: Report every prompt layer, rule, skill, and tool injected into this agent's context.
disable-model-invocation: true
---

# Inspect injected context

Report what was injected into your context before the user's message. Do not
run tools or change files, except to write the report if the user asks for it.

List each layer in the order it appears, with its apparent source and whether
the user can edit it:

1. System prompt sections (list the headings or tag names, and summarize each
   section's directives in one line).
2. User rules, team rules, and project rules, identifying each rule by file
   path or name.
3. `AGENTS.md` files, and any nested ones.
4. Skills that were advertised (name and description), and any that were loaded.
5. Tools: built-in tools, dynamic/MCP namespaces, and subagent types.
6. Environment metadata (OS, workspace path, git state, date).

Then list:

- Directives that conflict with each other, and which one wins under the
  stated precedence.
- Directives that conflict with the project's rules or skills.

Quote text verbatim only when the user names a section to quote; otherwise
summarize. If you cannot tell where a layer came from, say so rather than
guessing.
