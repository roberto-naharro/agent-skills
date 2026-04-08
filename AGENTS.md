# Agent Skills — Findings & Reference

This document summarizes findings about the Claude Agent Skills standard, intended to guide the creation and maintenance of skills in this repository.

## What is the Agent Skills Standard?

The **Agent Skills** standard defines a portable, file-based format for packaging instructions, scripts, and resources that AI agents (primarily Claude) can load dynamically to improve performance on specialized tasks.

- **Official spec repository:** [anthropics/skills](https://github.com/anthropics/skills)
- **Standard homepage:** [agentskills.io](https://agentskills.io)
- **Anthropic engineering post:** [Equipping agents for the real world with Agent Skills](https://anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills)

---

## Skill Structure

A skill is a **folder** containing a required `SKILL.md` file and optional supporting resources:

```
<skill-name>/
├── SKILL.md          # Required
├── scripts/          # Optional: executable scripts
├── references/       # Optional: extended documentation
└── assets/           # Optional: templates, images, data files
```

### Folder naming rules
- Lowercase letters, numbers, and hyphens only
- Must match the `name` field in `SKILL.md`'s frontmatter

---

## The `SKILL.md` File

`SKILL.md` is the heart of every skill. It combines YAML frontmatter (metadata) with a Markdown body (instructions).

### Frontmatter

```yaml
---
name: my-skill-name
description: A clear description of what this skill does and when Claude should use it.
---
```

| Field | Required | Description | Constraints |
|-------|----------|-------------|-------------|
| `name` | Yes | Unique identifier for the skill | Lowercase, hyphens; max 64 chars; matches folder name |
| `description` | Yes | What the skill does and when to invoke it | Max 200 chars (Claude.ai); max 1024 chars (API) |

> **Tip:** The `description` is used by Claude to decide *when* to invoke the skill automatically. Write it as: *"Use when [trigger scenario]. This skill [what it does]."*

### Markdown body

Below the frontmatter, provide:
- Step-by-step instructions Claude should follow
- Examples of inputs and expected outputs
- Guidelines, constraints, and edge cases
- References to files in `scripts/`, `references/`, or `assets/` when relevant

Keep `SKILL.md` under ~500 lines to avoid context bloat. Move lengthy reference content into the `references/` subfolder.

### Minimal example

```markdown
---
name: code-review-checklist
description: Use when reviewing pull requests or code changes. Applies a personal checklist covering security, performance, readability, and test coverage.
---

# Code Review Checklist

When reviewing code, evaluate each change against the following checklist.

## Security
- No secrets or credentials committed
- Input validation present for user-facing data
- No obvious injection vulnerabilities

## Performance
- No N+1 queries
- Heavy operations are async or cached

## Readability
- Functions are small and single-purpose
- Variable names are descriptive

## Tests
- New behavior is covered by tests
- Edge cases are tested
```

---

## Optional Resource Folders

| Folder | Purpose |
|--------|---------|
| `scripts/` | Executable scripts (Python, Bash, Node.js, etc.) that Claude can run or reference |
| `references/` | In-depth documentation, extended use cases, additional markdown files |
| `assets/` | Templates, images, data files used when generating outputs |

Reference these from the `SKILL.md` body so Claude knows when and how to load them.

---

## How Claude Uses Skills

1. **Claude.ai:** Skills are uploaded via [Settings → Skills](https://claude.ai). Once equipped, Claude automatically invokes the skill when the conversation matches the `description`.
2. **Claude Code:** Skills can be installed as plugins from a GitHub repository:
   ```
   /plugin marketplace add <owner>/<repo>
   ```
3. **Claude API:** Skills are uploaded and referenced in API requests via the [Skills API](https://docs.claude.com/en/api/skills-guide).

---

## Best Practices

- **One skill per workflow.** Keep skills focused on a single, repeatable task rather than trying to handle everything in one file.
- **Write a strong description.** This is the primary signal Claude uses for automatic invocation. Include trigger phrases and use-case context.
- **Include examples.** Sample inputs and expected outputs help Claude apply the skill correctly.
- **Keep SKILL.md concise.** Aim for under 500 lines. Offload large reference material to `references/`.
- **Test your skill.** After writing, test in the target Claude environment to confirm the skill is invoked as intended and produces the expected output.
- **Version with Git.** Track changes to skills in source control so you can review, revert, or improve them over time.

---

## References

- [What are skills?](https://support.claude.com/en/articles/12512176-what-are-skills)
- [Using skills in Claude](https://support.claude.com/en/articles/12512180-using-skills-in-claude)
- [Creating custom skills](https://support.claude.com/en/articles/12512198-creating-custom-skills)
- [anthropics/skills — Official examples](https://github.com/anthropics/skills)
- [Agent Skills spec (agentskills.io)](https://agentskills.io)
- [Skills API Quickstart](https://docs.claude.com/en/api/skills-guide)
