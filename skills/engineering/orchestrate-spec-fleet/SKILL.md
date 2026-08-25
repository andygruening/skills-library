---
name: orchestrate-spec-fleet
description: Orchestrate a fleet of Codex agents from a decompose-spec task document for spec 0001 or another numbered spec. Use when the user asks Codex to run agents for every task in a decomposition task graph, create isolated worktrees, copy task instructions into each worktree under the spec directory, enforce dependency waits, and have each agent commit, push, and open a manually reviewed pull request without auto-merging.
---

# Orchestrate Spec Fleet

## Overview

Run a decomposed spec through implementation agents while preserving manual PR review. Treat the decomposition document's `Task Graph` and `Task Bodies` as the source of truth, and coordinate tasks in dependency order.

## Tool Setup

- Use `tool_search` to expose multi-agent tools when they are not already visible. Prefer `multi_agent_v1.spawn_agent`, `wait_agent`, `send_input`, and `close_agent` for implementation agents.
- Use repository-native Git/GitHub tooling (`git`, `gh`, GitHub MCP, or existing project scripts) to push branches and create pull requests. Request network or auth approval when the environment requires it.
- Never run PR merge, auto-merge, squash, cherry-pick, or branch-integration commands unless the user explicitly requests that exact action after review.

## Locate The Decomposition

1. Identify the repository root with `git rev-parse --show-toplevel`.
2. Find the spec directory for `0001` unless the user names another spec. Prefer paths such as `docs/specs/0001*`, `specs/0001*`, `docs/adr/0001*`, or any directory whose basename starts with the spec number.
3. Locate the decomposition task document under that spec directory. Prefer a file containing headings like `Task Graph`, `Task Bodies`, `Contract Change Protocol`, or `Open Questions`.
4. Read the full decomposition document before launching agents.
5. Extract every task's id/title, task body, dependencies, allowed parallelism, required interface artifacts, and whether the task may start against stubs or must wait for an implemented feature.
6. If multiple plausible decomposition documents exist and the correct one cannot be inferred from paths or content, ask the user to choose. If no decomposition document exists, stop and ask the user to create one with `decompose-spec`.

## Build The Run Plan

- Topologically sort the task graph. Treat explicit dependencies in `Task Graph` as authoritative.
- If the graph is incomplete, infer only obvious dependencies from task bodies and label them as inferred in your tracking notes.
- Separate tasks into:
  - `ready`: no unsatisfied dependencies.
  - `ready-against-contract`: dependencies provide public contracts/stubs and the task body explicitly allows work before implementation is merged.
  - `waiting-for-manual-merge`: requires a feature, implementation, migration, or behavior from another task that is not yet manually reviewed and merged.
  - `blocked`: missing task instructions, missing auth/remote, failing setup, or an upstream contract gap.
- Launch independent `ready` and `ready-against-contract` tasks in parallel when their write scopes do not overlap.
- Keep a tracking table with task id, title, dependencies, agent id, branch, worktree, status, PR URL, tests, and blockers.

## Agent Task Packet

Before spawning an agent, create a packet from the decomposition document. Include:

- Spec id and spec directory path.
- Source decomposition document path.
- Task id/title and the copied task body.
- Dependency list and the exact unblock condition for each dependency.
- Allowed write scope, coupling constraints, test expectations, and contract-change protocol.
- Branch name suggestion, such as `spec-0001/<task-id>-<slug>`.
- PR title format: `[0001][<task-id>] <task title>`.
- Required instruction-copy path inside the agent worktree, such as `<spec-dir>/tasks/<task-id>.md` unless the repository already has a task-instructions convention under that spec directory.

Every agent prompt must require the agent to copy its task instructions into its own worktree under the directory where the spec lives before making implementation changes. The copied file must be committed with the task changes.

## Agent Prompt Template

Use this shape for each spawned implementation agent:

```text
Implement <task-id>: <task title> for spec <spec-id>.

You are working in your own isolated worktree. Before editing implementation code:
1. Locate the spec directory at <spec-dir> in your worktree.
2. Create or update <spec-dir>/tasks/<task-id>.md.
3. Copy this task packet into that file, including the source decomposition path, task graph edges, dependencies, task body, contract-change protocol, and PR checklist.
4. Commit that instruction-copy file together with the implementation changes.

Task packet:
<paste packet>

Rules:
- Implement only this task's scope.
- Respect the dependency graph and coupling constraints.
- Do not edit another task's instruction copy.
- If you require a feature, implementation, migration, or contract from another task that is not manually merged yet, stop and report that you are waiting. Do not merge, cherry-pick, or work around it by editing the upstream task.
- If an upstream public interface is insufficient, stop with a contract-change request naming the provider task/domain, missing capability, consuming use case, proposed interface shape, fixture/test impact, and urgency.
- Run the relevant tests and checks.
- When complete, commit all changes, push the branch, and create a pull request.
- Never merge the pull request or enable auto-merge.

Final response must include branch, commit SHA, PR URL, tests run, and any follow-up/blocker notes.
```

## Dependency Gates

- A dependency is satisfied only when the task graph says it is not needed for this task, the dependent task can work against an already committed public contract/stub, or the prerequisite PR has been manually reviewed and merged by a human.
- If a downstream task requires an upstream feature and the upstream PR is only open, leave the downstream worktree waiting. Do not auto-merge the upstream PR.
- When an agent reports an upstream requirement, move it to `waiting-for-manual-merge` or `blocked` and preserve its worktree/agent state for later continuation.
- When the user says a prerequisite PR was reviewed and merged, verify with `git fetch` and repository/GitHub status before resuming dependent agents.
- Do not rebase or retarget dependent work onto an unreviewed task branch unless the user explicitly asks for that branch relationship.

## PR Requirements

- Use one branch and one PR per task.
- Require every task PR to include:
  - Source spec and decomposition document paths.
  - Path to the copied task instructions in that worktree.
  - Dependency status.
  - Summary of changes.
  - Tests/checks run.
  - Blockers, contract-change requests, or manual follow-ups.
- Leave all PRs open for manual review. Never mark them as merged, enable auto-merge, or tell another agent to merge them.
- If the repository has no remote, GitHub auth is unavailable, or PR creation fails, stop that task at the blocker and report the exact command/result needed for the user to resolve it.

## Monitoring And Completion

- Wait on running agents in batches and update the tracking table as each finishes or blocks.
- Review each finished agent's final response for branch, commit SHA, PR URL, tests, and dependency notes. If required data is missing, ask that agent for the missing details before closing it.
- Close completed agents after recording their output.
- Launch newly unblocked tasks only after verifying their dependency gate.
- Finish with a concise status table listing each task, status, branch, PR URL, tests, and any manual-review or dependency waits.
- Make clear which tasks are complete, which PRs await human review, and which tasks remain waiting because auto-merge is forbidden.
