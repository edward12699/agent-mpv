# Copilot Instructions for `agent-mpv`

This repository is a small monorepo with a TypeScript agent under `ts-agent/` and a new Python package under `py-agent/`.
The TypeScript agent is the primary AI workflow implementation.

## Key guidance for Copilot

- Prefer the existing agent workflow in `ts-agent/src/agent.ts`.
- Use `ts-agent/src/tools.ts` for all contract retrieval and sorting behavior.
- Do not treat this repo as a general chatbot.
- If a user asks about contracts, amounts, years, comparisons, or filters, the agent should use `search_contract` first.
- For maximum/highest amount questions, the agent should call `rank_contracts` after `search_contract` and use the returned sorted results.
- Do not answer based on raw `rawText` alone when structured amount data is available.

## Important files

- `ts-agent/src/agent.ts`: agent orchestration, tool chaining, and trace generation
- `ts-agent/src/tools.ts`: tool schema, search logic, amount extraction heuristics
- `ts-agent/src/data.ts`: contract corpus and raw text source data
- `ts-agent/app/api/agent/route.ts`: API endpoint wrapping the agent
- `ts-agent/app/page.tsx`: client UI for asking questions and showing trace output

## Run commands

- `cd ts-agent && npm run dev`: run the frontend
- `cd ts-agent && npm run build`: build the app
- `cd ts-agent && npm run agent`: run the CLI agent example

## Notes

- The TypeScript agent uses Node.js `>=20.6.0` and ESM (`type: module`).
- The current implementation has no automated tests.
- `ts-agent/src/tools.ts` contains several hard-coded Chinese amount extraction heuristics such as `三十万` and `45万`.
- A separate Python implementation lives in `py-agent/`.
