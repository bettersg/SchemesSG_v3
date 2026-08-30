# Coding-agent harness practices (2026)

Research date: 2026-08-29. Primary-source findings used for the harness decision:

- Codex discovers `AGENTS.md` from repository root to the working directory; closer guidance overrides broader guidance. Keep root guidance short and scope real differences near governed code. [OpenAI](https://developers.openai.com/codex/guides/agents-md)
- Claude Code discovers `CLAUDE.md` and explicitly supports symlinking it to `AGENTS.md`. Instructions guide behavior; executable checks enforce invariants. [Anthropic](https://code.claude.com/docs/en/memory)
- Git worktrees isolate files, `HEAD`, and index but share refs/config and do not isolate ports, containers, volumes, caches, credentials, or external services. Select the base commit explicitly. [Git](https://git-scm.com/docs/git-worktree)
- Compose dependency order does not mean readiness. Health checks and `service_healthy` express readiness; bounded waits and propagated exit status make smoke proof reliable. [Docker](https://docs.docker.com/compose/how-tos/startup-order/) [Docker CLI](https://docs.docker.com/reference/cli/docker/compose/up/)
- Branch protection/rulesets enforce checks, review, CODEOWNER approval, and current-base integration; prose instructions do not. [GitHub](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches)
- OpenAI’s 2026 harness report replaced a monolithic instruction file with a short table of contents into maintained repository docs and mechanical freshness checks. [OpenAI](https://openai.com/index/harness-engineering/)

## SchemesSG implications

- Author root, backend, and frontend `AGENTS.md`; symlink colocated `CLAUDE.md` files.
- Start repository-changing tasks in explicit worktrees based on refreshed `origin/stg`; reserve `origin/main` for approved hotfixes.
- Keep credentialed development separate from deterministic secretless smoke.
- Require actual health and one observable frontend-to-backend journey for cross-boundary proof.
- Namespace or serialize Compose resources across task worktrees.
- Protect instruction, workflow, dependency, deployment, and secret-boundary changes with ownership and checks.

## Claims not made

Symlinks are not universal across every agent or archive environment. Worktrees do not isolate runtime resources. A running container is not necessarily ready. The local deterministic adapter does not validate production Firestore vector search, external LLMs, Slack, or deployed Firebase configuration.
