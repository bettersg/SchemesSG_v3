# Concise, cross-agent repository instructions

Research date: 2026-09-13. Scope: root `AGENTS.md`; retain the existing scoped
files and `CLAUDE.md` symlinks. Personal/global agent configuration is unchanged.

## Sources and findings

- [AGENTS.md specification](https://agents.md/): plain Markdown is the portable
  format; nested files carry subproject guidance. It does not require a template.
- [Anthropic best practices](https://code.claude.com/docs/en/best-practices): keep
  persistent instructions short, retain non-obvious commands and project gotchas,
  link detailed documentation, and provide observable verification criteria.
  Its pruning test is whether removing a line would cause mistakes.
- [Anthropic memory documentation](https://code.claude.com/docs/en/memory): Claude
  reads `CLAUDE.md`, not `AGENTS.md` directly; a symlink is explicitly supported.
  Imports load at startup, so splitting a large file into unconditional imports
  does not reduce loaded context. The recommendation is under 200 lines per file,
  not a target to fill. Instructions guide behavior; they do not enforce security.
- [User-linked article](https://x.com/adiix_official/status/2097014889990545608):
  recommends conditional document loading, proportionate tests, explicit completion
  criteria, and identifying the instruction responsible for a pause. These are
  useful design proposals, not evidence that this repository can drop its gates.

Exa search found supporting material; Exa fetch retrieved the three primary
sources above. Exa could not retrieve the X post (`SOURCE_NOT_AVAILABLE`), and an
exact-post search did not recover it. The article text was read through the
[FxTwitter public mirror](https://api.fxtwitter.com/status/2097014889990545608).
The mirror returned the matching post ID, author, article, and embedded code blocks;
this is a secondary retrieval path, not independent verification of its claims.

## Applied decisions

- Preserve one canonical source and all three existing Claude symlinks. Explicitly
  route agents to scoped instructions rather than assume identical discovery.
- Replace vague reference lists with task-triggered pointers. Keep worktree and
  production safety rules inline because they matter before taking action.
- Route PR field details to the existing template; keep all sections mandatory.
- State an implementation completion contract and a diagnostic blocker report.
  This does not authorize changes for a review-only request or expand permission
  to deploy, merge, publish, or change external systems.
- Keep required test tiers; avoid repeated or broader checks without a reason.
  Test selection and evidence remain authoritative in `docs/verification.md`.
- Keep provider/model settings, pricing, hook recipes, and permission bypasses out
  of shared instructions. The article's model-specific claims were not verified
  or adopted. No personal configuration or skills were changed.

## Verification scope

Use the existing harness/preflight tests, check all referenced local paths and
Claude symlinks, and review retained policies against the base version. A file
integrity check alone does not prove instruction adherence: fresh Codex and Claude
sessions should identify scoped instructions, worktree preflight, and the required
verification tier before editing. Record any unperformed session check at handoff.

## Local evidence

- Worktree: `/Users/tracilim/Projects/SchemesSG_v3-concise-agent-guidance`.
- Branch: `docs/concise-agent-guidance`; base: `origin/stg` at
  `fe5e5073cef068220eccb44c966bff91a2ce02e1`.
- `./scripts/test-harness.sh`: passed, including worktree create/preflight tests.
- `./scripts/worktree-preflight.sh`: passed; `git diff --check`: passed.
- Local path check: all 11 referenced paths exist; all three Claude symlinks
  target their colocated `AGENTS.md`.
- Fresh Claude print-mode session, restricted to Read with hooks, MCP servers,
  and skills disabled: correctly identified the canonical source, Claude bridge,
  frontend instructions, preflight, verification policy, and completion rule.
  This ran against the initial revision before a final wording-only trim; it
  checks discovery, not implementation adherence or the full personal setup.
- A separate fresh Codex session was not run. Static path checks do not establish
  runtime discovery for every agent.
- No application tests: documentation-only change; no runtime behavior changed.
  Required maintainer review still applies through `.github/CODEOWNERS`.
