# Agent Instructions for `agent-mpv`

## What this project is

A small monorepo containing two agent subprojects.
The main TypeScript contract analysis agent lives under `ts-agent/` and uses a tool-driven workflow.

The `ts-agent/` agent flow uses these tools:
- `search_contract` for retrieving contract candidates from structured data
- `rank_contracts` for sorting those candidates by amount

The project also includes a new Python package under `py-agent/`.

## Useful commands

- `cd ts-agent && npm run dev`: start the Next.js frontend
- `cd ts-agent && npm run build`: compile the TypeScript app
- `cd ts-agent && npm run start`: run the production Next.js server
- `cd ts-agent && npm run agent`: execute `src/index.ts` with `tsx`
- `cd ts-agent && npm run debug`: start `gcl.ts` with Node inspect

## Key files

- `ts-agent/src/agent.ts`: main TypeScript agent orchestration and trace logic
- `ts-agent/src/tools.ts`: tool declarations, contract extraction heuristics, and tool implementations
- `ts-agent/src/data.ts`: contract corpus used by the agent
- `ts-agent/src/index.ts`: example CLI runner for sample questions
- `ts-agent/app/api/agent/route.ts`: HTTP POST endpoint for agent questions
- `ts-agent/app/page.tsx`: client UI for asking questions and viewing structured traces

## What AI coding agents should know

- This repo is not a general chatbot. It is an agent workflow that should prefer the defined tools over freeform text parsing.
- `search_contract` is the primary retrieval tool for questions about contracts, amounts, years, filters, and comparisons.
- `rank_contracts` must only be called after `search_contract` and should receive contracts from the previous search result.
- Avoid answering based on raw text alone; the agent is expected to rely on returned structured data.
- The dataset is small and hard-coded in `ts-agent/src/data.ts`, so changes there directly affect agent behavior.

## Important conventions and gotchas

- `ts-agent/package.json` uses `type: module` and requires Node >= 20.6.0.
- There are currently no automated tests in this repository.
- `ts-agent/src/tools.ts` contains heuristic parsing logic and special cases for Chinese amount expressions such as `三十万` and `45万`.
- The UI is optional. For agent development and debugging, use `cd ts-agent && npm run agent` or inspect `ts-agent/src/agent.ts`.

## When updating this file

Keep this file focused on project-specific behavior and tooling conventions. Do not duplicate generic Next.js or TypeScript guidance.

## Model and tool usage policy

- Do not use Claude Code or any Claude-specific workflow for this repository.
- Follow the existing repository instructions and use the available local tools and project conventions instead.
- If a task can be completed with the current workspace tools, prefer that over invoking external Claude-based workflows.
