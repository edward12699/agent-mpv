import OpenAI from "openai";
import type {
  ChatCompletionMessageParam
} from "openai/resources/chat/completions.js";
import { tools, searchContract } from "./tools.ts";

if (!process.env.DASHSCOPE_API_KEY) {
  throw new Error("缺少 DASHSCOPE_API_KEY，请先设置环境变量");
}

const client = new OpenAI({
  apiKey: process.env.DASHSCOPE_API_KEY,
  baseURL: "https://dashscope.aliyuncs.com/compatible-mode/v1"
});

export async function runAgent(question: string) {
  const messages: ChatCompletionMessageParam[] = [
    {
      role: "system",
      content: `
你是一个合同分析助手。

规则：
1. 涉及合同、金额、日期、筛选、比较的问题，必须调用 search_contract
2. 拿到数据后，你必须基于数据分析，不能凭空猜
3. 如果用户问“最大金额”“最早日期”“某年合同”等问题，你要显式比较后再回答
4. 最终回答要简洁，但要给出依据
`
    },
    {
      role: "user",
      content: question
    }
  ];

  console.log("\n=== 用户问题 ===");
  console.log(question);

  const first = await client.chat.completions.create({
    model: "qwen-plus",
    messages,
    tools,
    tool_choice: "auto"
  });

  const msg = first.choices[0].message;

  console.log("\n=== 第一次模型输出 ===");
  console.log(JSON.stringify(msg, null, 2));

  if (msg.tool_calls && msg.tool_calls.length > 0) {
    const toolCall = msg.tool_calls[0];

    if (toolCall.type !== "function") {
      throw new Error("仅支持 function 工具调用");
    }

    const args = JSON.parse(toolCall.function.arguments);

    console.log("\n=== 工具调用参数 ===");
    console.log(args);

    const toolResult = searchContract(args.query);

    console.log("\n=== 工具返回结果 ===");
    console.log(JSON.stringify(toolResult, null, 2));

    messages.push(msg);

    messages.push({
      role: "tool",
      tool_call_id: toolCall.id,
      content: JSON.stringify(toolResult)
    });

    const second = await client.chat.completions.create({
      model: "qwen-plus",
      messages
    });

    console.log("\n=== 最终答案 ===");
    console.log(second.choices[0].message.content);

    return second.choices[0].message.content;
  }

  console.log("\n=== 未调用工具，直接回答 ===");
  console.log(msg.content);

  return msg.content;
}