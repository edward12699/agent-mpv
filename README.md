# agent-mpv monorepo

This repository contains two subprojects:

- `ts-agent/`: the original Node.js + TypeScript contract analysis agent
- `py-agent/`: Python contract analysis agent (v2 = LangGraph workflow)

## Architecture (py-agent v2)

```text
FastAPI
  ↓
AgentService
  ↓
LangGraph Contract Agent
  ├── State: messages / question / route / contracts /
  │         need_rank / ranked_result / retrieved_docs / answer
  ↓
analyze (rule router)
  ├── structured → search → (rank?) → answer
  ├── document   → retrieve → answer
  └── unsupported → answer
```

LLM 只负责最终解释；流程由 Graph 显式控制。

### Key modules

```text
py-agent/app/
├── api/                 # FastAPI routes / schemas
├── services/
│   └── agent_service.py
├── graph/
│   ├── state.py
│   ├── nodes.py
│   ├── routes.py
│   └── contract_graph.py
├── tools/
│   ├── contract_tools.py
│   └── document_tools.py
├── rag/
│   ├── vector_store.py
│   └── retriever.py
└── llm_factory.py
```

## Capabilities

- Contract filtering (`search_contract`)
- Amount ranking (`rank_contracts`)
- RAG document search (`retrieve` / Chroma)
- Citation via `source` / `chunk_id`
- Checkpoint + `thread_id`
- Graph streaming (`astream`)
- Timeout / logging / pytest

Write ops (`delete_contract` / `update_contract` / `send_contract`) are reserved for future human-in-the-loop approval (`interrupt` → `resume`).

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
uvicorn app.api.main:app --reload --port 8000
```

### Day 14 验收

```bash
cd py-agent
source venv/bin/activate
PYTHONPATH=. python scripts/day14_contract_agent_v2.py
```

### Tests

```bash
cd py-agent
source venv/bin/activate
PYTHONPATH=. pytest -q
```

## Notes

- TypeScript app requires Node.js `>=20.6.0`.
- Keep `ts-agent/` and `py-agent/` independent for their own dependencies and tooling.

## 同时启动前后端

```bash
./scripts/dev.sh
```

自定义端口：

```bash
NEXT_PORT=3000 PY_PORT=8001 ./scripts/dev.sh
```

变量：

- `NEXT_PORT`：Next.js 端口
- `PY_HOST`：后端监听地址
- `PY_PORT`：后端端口

跑 `./scripts/dev.sh` 前，确保已经做过一次：

```bash
cd py-agent
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```
