# agent-mpv monorepo

This repository is now organized as a monorepo with two subprojects:

- `ts-agent/`: the original Node.js + TypeScript contract analysis agent
- `py-agent/`: a new Python contract agent package

## Subproject layout

### `ts-agent/`

Contains the existing Next.js and tool-driven agent implementation:
- `package.json` and `package-lock.json`
- `src/` with `agent.ts`, `tools.ts`, `data.ts`, and example CLI runner
- `app/` with the frontend UI and API route
- `tsconfig.json`, `next.config.mjs`, and related config files

### `py-agent/`

A new Python package with:
- `app/data.py`, `app/models.py`, `app/tools.py`, `app/agent.py`, and `app/main.py`
- `requirements.txt`
- `venv/` for the local Python virtual environment

## Run commands

### TypeScript agent

```bash
cd ts-agent
npm install
npm run dev
```

### Python agent

```bash
cd py-agent
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app/main.py
```

## Notes

- The TypeScript app still requires Node.js `>=20.6.0`.
- The Python package is intentionally small and uses the same contract corpus logic in a separate implementation.
- Keep `ts-agent/` and `py-agent/` independent for their own dependencies and tooling.
