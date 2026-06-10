import OpenAI from "openai";
import type { ChatCompletionMessageParam } from "openai/resources/chat/completions.js";
import { tools, searchContract, rankContracts } from "./tools";

function requireApiKey() {
  if (!process.env.DASHSCOPE_API_KEY) {
    throw new Error("缺少 DASHSCOPE_API_KEY，请先设置环境变量");
  }
}

function classifyError(
  question: string,
  toolArgs: any,
  toolResult: any[],
  finalResult: any,
) {
  const errors: string[] = [];

  // 1️⃣ 参数错误
  if (question.includes("最大") && toolArgs.compare !== "max") {
    errors.push("参数错误：缺少 compare=max");
  }

  if (question.includes("不是") && !toolArgs.excludeYear) {
    errors.push("参数错误：缺少 excludeYear");
  }

  // 2️⃣ 检索错误
  if (toolResult.length === 0) {
    errors.push("检索错误：没有返回任何数据");
  }

  if (
    question.includes("不是2024") &&
    toolResult.some((c) => c.year?.includes("2024"))
  ) {
    errors.push("检索错误：返回了不该包含的2024数据");
  }

  // 3️⃣ 推理错误
  if (finalResult?.matchedContracts?.length === 0 && toolResult.length > 0) {
    errors.push("推理错误：有数据但没有选出结果");
  }

  return errors;
}

function safeParseJSON(content: string) {
  try {
    return JSON.parse(content);
  } catch (error) {
    console.error("\n=== JSON 解析失败 ===");
    console.error(content);
    throw error;
  }
}

const client = new OpenAI({
  apiKey: process.env.DASHSCOPE_API_KEY,
  baseURL: "https://dashscope.aliyuncs.com/compatible-mode/v1",
});

export type AgentStep = {
  tool: string;
  args: Record<string, unknown>;
  result: unknown;
};

export type AgentTrace = {
  question: string;
  steps: AgentStep[];
  finalAnswer: string;
};

export async function runAgentWithTrace(question: string): Promise<AgentTrace> {
  requireApiKey();

  const steps: AgentStep[] = [];
  const messages: ChatCompletionMessageParam[] = [
    {
      role: "system",
      content: `
你是一个合同分析 Agent。

你可以使用这些工具：
1. search_contract：根据条件检索合同，返回结构化合同数据
2. rank_contracts：对结构化合同按金额排序

规则：
1. 涉及合同、金额、日期、筛选、比较的问题，必须先调用 search_contract
2. 如果用户要找最大金额、最高费用、最高价款，必须在 search_contract 之后调用 rank_contracts
3. 不要自己从 rawText 里猜金额，优先使用工具返回的 amount 字段
4. amount 为 null 的合同不能参与金额排序
5. 如果金额相同，amountConfidence=exact 优先于 approximate
6. 最终回答必须基于工具返回结果
7. 严禁在同一轮同时调用 search_contract 和 rank_contracts
8. rank_contracts 的 contracts 参数必须来自上一轮 search_contract 的工具返回结果
9. 如果没有拿到 search_contract 返回结果，不允许调用 rank_contracts
`,
    },
    {
      role: "user",
      content: question,
    },
  ];

  console.log("\n=== 用户问题 ===");
  console.log(question);

  for (let step = 1; step <= 5; step++) {
    const response = await client.chat.completions.create({
      model: "qwen-plus",
      messages,
      tools,
      tool_choice: "auto",
    });

    const msg = response.choices[0].message;

    console.log(`\n=== 第 ${step} 次模型输出 ===`);
    console.log(JSON.stringify(msg, null, 2));

    if (!msg.tool_calls || msg.tool_calls.length === 0) {
      const raw = msg.content ?? "{}";

      console.log("\n=== 最终模型输出 ===");
      console.log(raw);

      return {
        question,
        steps,
        finalAnswer: raw,
      };
    }

    const toolCalls = (msg.tool_calls ?? []).filter(
      (t) => t.type === "function",
    );

    const hasSearchAndRankInSameTurn =
      toolCalls.some((t) => t.function.name === "search_contract") &&
      toolCalls.some((t) => t.function.name === "rank_contracts");

    const executableToolCalls = hasSearchAndRankInSameTurn
      ? toolCalls.filter((t) => t.function.name === "search_contract")
      : toolCalls;

    let finalMsg = msg;

    if (hasSearchAndRankInSameTurn) {
      console.log("\n=== 修正非法工具链，只保留 search_contract ===");

      finalMsg = {
        ...msg,
        tool_calls: toolCalls.filter(
          (t) => t.function.name === "search_contract",
        ),
      };
    }

    messages.push(finalMsg);

    for (const toolCall of executableToolCalls) {
      const name = toolCall.function.name;
      const args = JSON.parse(toolCall.function.arguments);

      console.log("\n=== 工具调用 ===");
      console.log(name, args);

      let toolResult: unknown;

      if (name === "search_contract") {
        toolResult = searchContract(args);
      } else if (name === "rank_contracts") {
        toolResult = rankContracts(args);
      } else {
        throw new Error(`未知工具：${name}`);
      }

      console.log("\n=== 工具返回结果 ===");
      console.log(JSON.stringify(toolResult, null, 2));

      steps.push({
        tool: name,
        args,
        result: toolResult,
      });

      messages.push({
        role: "tool",
        tool_call_id: toolCall.id,
        content: JSON.stringify(toolResult),
      });
    }
  }

  throw new Error("Agent 超过最大工具调用轮数");
}

export async function runAgent(question: string) {
  const trace = await runAgentWithTrace(question);
  return trace.finalAnswer;
}
