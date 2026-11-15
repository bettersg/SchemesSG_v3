# Agent skills

Skills that every contributor's coding agent should follow when working on
Schemes.sg copy and translations. Each skill folder holds a `SKILL.md`, any
reference files it points to, and the upstream `LICENSE`.

- `sgds-writing/`: English copy style.
- `translation/`: translating the frontend with Lingui.

## Vendored skills

Copied at a fixed commit so an upstream change can't alter agent behaviour
unnoticed. To update one, copy the folder again from a newer commit, review the
diff, and update the commit below.

| Skill | Upstream | Commit | Licence |
|---|---|---|---|
| `sgds-writing` | [govtechsg/sgds-web-component](https://github.com/govtechsg/sgds-web-component/tree/master/skills/sgds-writing) | `9a9f92b` | MIT |
| `translation/lingui-best-practices` | [lingui/skills](https://github.com/lingui/skills/tree/main/skills/lingui-best-practices) | `2be6e69` | MIT |
| `translation/enhanced-message-context` | [lingui/skills](https://github.com/lingui/skills/tree/main/skills/enhanced-message-context) | `2be6e69` | MIT |
| `translation/find-unwrapped-strings` | [lingui/skills](https://github.com/lingui/skills/tree/main/skills/find-unwrapped-strings) | `2be6e69` | MIT |

## How agents use them

These skills are read on demand, not loaded automatically. `AGENTS.md` tells
agents to open the matching `SKILL.md` only when the task is writing, reviewing,
or translating copy. Don't link this folder into an agent's own skills
directory (`.claude/skills/`, `.agents/skills/`): that lets the agent apply them
to unrelated work.
