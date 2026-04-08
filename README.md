# agent-skills

A personal repository of custom [Claude Agent Skills](https://github.com/anthropics/skills) — reusable instruction sets that teach Claude how to complete specific tasks in a repeatable way, available across all devices and platforms.

## What are Skills?

Skills are folders of instructions, scripts, and resources that Claude loads dynamically to improve performance on specialized tasks. A skill can teach Claude how to:

- Apply your personal writing style or brand guidelines
- Follow your organization's specific workflows
- Automate repeatable personal tasks
- Use specialized domain knowledge

Each skill is self-contained in its own folder with a `SKILL.md` file at its root.

## Repository Structure

```
agent-skills/
├── README.md          # This file
├── AGENTS.md          # Findings on the Agent Skills standard
└── skills/
    └── <skill-name>/
        ├── SKILL.md       # Required: instructions and metadata
        ├── scripts/       # Optional: executable scripts
        ├── references/    # Optional: extended documentation
        └── assets/        # Optional: templates, images, etc.
```

## How to Create a Skill

### 1. Create a skill folder

```
mkdir skills/my-skill-name
```

The folder name should use only lowercase letters, numbers, and hyphens.

### 2. Create a `SKILL.md` file

Every skill requires a `SKILL.md` file with YAML frontmatter and a markdown body:

```markdown
---
name: my-skill-name
description: A clear description of what this skill does and when Claude should use it.
---

# My Skill Name

[Add your instructions here that Claude will follow when this skill is active]

## Examples
- Example usage 1
- Example usage 2

## Guidelines
- Guideline 1
- Guideline 2
```

**Frontmatter fields:**

| Field | Required | Rules |
|-------|----------|-------|
| `name` | Yes | Lowercase, hyphens only; max 64 chars; must match folder name |
| `description` | Yes | Explains what it does and when to use it; max 200 chars for Claude.ai |

### 3. Add optional resources

- **`scripts/`** — Executable scripts (Python, Bash, etc.) referenced in instructions
- **`references/`** — In-depth documentation or extended use cases
- **`assets/`** — Templates, images, data files for generating outputs

### 4. Use your skill

**Claude.ai:** Upload the skill via [Settings → Skills](https://claude.ai) or use the repository as a skill source.

**Claude Code:** Register this repository as a plugin marketplace:
```
/plugin marketplace add roberto-naharro/agent-skills
```

**Claude API:** Upload skills via the [Skills API](https://docs.claude.com/en/api/skills-guide).

## Resources

- [anthropics/skills](https://github.com/anthropics/skills) — Official skill examples and the Agent Skills spec
- [Agent Skills standard](https://agentskills.io) — Full specification
- [Creating custom skills](https://support.claude.com/en/articles/12512198-creating-custom-skills) — Official how-to guide
- [Using skills in Claude](https://support.claude.com/en/articles/12512180-using-skills-in-claude) — How to equip Claude with skills
