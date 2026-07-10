import { NextResponse } from "next/server";
import { execFile } from "node:child_process";
import { promisify } from "node:util";
import fs from "node:fs";
import path from "node:path";
import { runAgentWithTrace } from "@/src/agent";

const execFileAsync = promisify(execFile);

type BackendName = "ts" | "python";

function resolveBackend(backend?: string | null): BackendName {
  const normalized = typeof backend === "string" ? backend.toLowerCase() : "";
  if (normalized === "ts" || normalized === "python") {
    return normalized;
  }

  const configured = process.env.AGENT_BACKEND?.toLowerCase();
  if (configured === "ts" || configured === "python") {
    return configured;
  }

  return "ts";
}

async function runPythonAgent(question: string) {
  const repoRoot = path.resolve(process.cwd(), "..");
  const pyRoot = path.join(repoRoot, "py-agent");
  const venvPython = path.join(
    pyRoot,
    process.platform === "win32"
      ? "venv\\Scripts\\python.exe"
      : "venv/bin/python",
  );
  const pythonExecutable = fs.existsSync(venvPython) ? venvPython : "python3";
  const script = `
import json
import os
import sys
sys.path.insert(0, os.getcwd())
from app.agent import Agent
result = Agent().run(sys.argv[1])
print(json.dumps(result))
`;

  const { stdout } = await execFileAsync(
    pythonExecutable,
    ["-c", script, question],
    {
      cwd: pyRoot,
      env: {
        ...process.env,
        PYTHONIOENCODING: "utf-8",
      },
    },
  );

  return JSON.parse(stdout.trim());
}

export async function POST(req: Request) {
  try {
    const body = await req.json();
    const question = body?.question?.trim();

    if (!question) {
      return NextResponse.json({ error: "请输入问题" }, { status: 400 });
    }

    const backend = resolveBackend(body?.backend);
    const trace =
      backend === "python"
        ? await runPythonAgent(question)
        : await runAgentWithTrace(question);

    return NextResponse.json({
      backend,
      question: trace.question,
      steps: trace.steps.map((s: any) => ({
        tool: s.tool,
        args: s.args,
        result: s.result,
      })),
      finalAnswer: trace.finalAnswer,
    });
  } catch (err) {
    const message = err instanceof Error ? err.message : "Agent 执行失败";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
