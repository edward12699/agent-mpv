import { NextResponse } from "next/server";
import { execFile } from "node:child_process";
import { promisify } from "node:util";
import fs from "node:fs";
import path from "node:path";
import { runAgentWithTrace } from "@/src/agent";
import type { AgentResponse } from "../../types/agent";

const execFileAsync = promisify(execFile);
const API_BASE_URL_PY = process.env.NEXT_PUBLIC_AGENT_API_URL_PY;

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

async function runPythonAgent(question: string): Promise<AgentResponse> {
  // const repoRoot = path.resolve(process.cwd(), "..");
  // const pyRoot = path.join(repoRoot, "py-agent");
  // const venvPython = path.join(
  //   pyRoot,
  //   process.platform === "win32"
  //     ? "venv\\Scripts\\python.exe"
  //     : "venv/bin/python",
  // );
  // const pythonExecutable = fs.existsSync(venvPython) ? venvPython : "python3";
  // const { stdout } = await execFileAsync(
  //   pythonExecutable,
  //   ["-m", "app.runner", question],
  //   {
  //     cwd: pyRoot,
  //     env: {
  //       ...process.env,
  //       PYTHONIOENCODING: "utf-8",
  //     },
  //   },
  // );

  // const output = stdout.trim();
  // return JSON.parse(output);
  if (!API_BASE_URL_PY) {
    throw new Error("缺少 NEXT_PUBLIC_AGENT_API_URL");
  }
  const response = await fetch(`${API_BASE_URL_PY}/api/agent/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      question,
    }),
  });

  if (!response.ok) {
    let message = `请求失败：HTTP ${response.status}`;

    try {
      const errorBody = (await response.json()) as {
        detail?: string | Array<{ msg?: string }>;
      };

      if (typeof errorBody.detail === "string") {
        message = errorBody.detail;
      } else if (Array.isArray(errorBody.detail)) {
        message = errorBody.detail
          .map((item) => item.msg)
          .filter(Boolean)
          .join("；");
      }
    } catch {
      // 返回体不是 JSON 时，保留默认错误信息。
    }

    throw new Error(message);
  }

  return (await response.json()) as AgentResponse;
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
      finalAnswer: trace.finalAnswer || trace.answer,
    });
  } catch (err) {
    const message = err instanceof Error ? err.message : "Agent 执行失败";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
