import { NextResponse } from "next/server";
import { runAgentWithTrace } from "@/src/agent";

export async function POST(req: Request) {
  try {
    const body = await req.json();
    const question = body?.question?.trim();

    if (!question) {
      return NextResponse.json(
        { error: "请输入问题" },
        { status: 400 },
      );
    }

    const trace = await runAgentWithTrace(question);

    return NextResponse.json({
      question: trace.question,
      steps: trace.steps.map((s) => ({
        tool: s.tool,
        args: s.args,
        result: s.result,
      })),
      finalAnswer: trace.finalAnswer,
    });
  } catch (err) {
    const message =
      err instanceof Error ? err.message : "Agent 执行失败";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
