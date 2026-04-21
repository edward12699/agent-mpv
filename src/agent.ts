import OpenAI from "openai";
import type {
  ChatCompletionMessageParam
} from "openai/resources/chat/completions.js";
import { tools, searchContract } from "./tools.ts";

if (!process.env.DASHSCOPE_API_KEY) {
  throw new Error("缺少 DASHSCOPE_API_KEY，请先设置环境变量");
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
2. 调用工具时，必须把用户问题拆成结构化参数
3. 如果用户问“不是2024年的合同”，要把 excludeYear 设为 "2024"
4. 如果用户问“2023年的合同”，要把 year 设为 "2023"
5. 如果用户问“金额最大的合同”，要把 needAmount=true，并把 compare 设为 "max"
6. 如果用户问“金额超过20万的合同”，要把 minAmount 设为 200000
7. 拿到工具结果后，必须基于结果回答，不能凭空猜
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

    const toolResult = searchContract(args);

    console.log("\n=== 工具返回结果 ===");
    console.log(JSON.stringify(toolResult, null, 2));

    messages.push(msg);

    messages.push({
      role: "tool",
      tool_call_id: toolCall.id,
      content: JSON.stringify(toolResult)
    });

    messages.push({
        role: "system",
        content: `
      你现在要基于工具返回的数据，输出严格 JSON，不要输出任何额外解释。
      
      返回格式如下：
      {
        "matchedContracts": [合同ID数组],
        "reasoning": "简要说明你是如何根据数据得出结果的",
        "finalAnswer": "给用户看的最终结论"
      }
      
      要求：
      1. matchedContracts 必须是数组
      2. reasoning 必须简洁
      3. finalAnswer 必须是给用户看的最终一句话
      4. 只返回 JSON，不要使用 markdown，不要加代码块
      `
      });
      
      const second = await client.chat.completions.create({
        model: "qwen-plus",
        messages,
        response_format: { type: "json_object" }
      });
      
      const raw = second.choices[0].message.content ?? "{}";
      
      console.log("\n=== 第二次模型原始输出 ===");
      console.log(raw);
      
      const parsed = safeParseJSON(raw);
      
      console.log("\n=== 结构化结果 ===");
      console.log(JSON.stringify(parsed, null, 2));
      
      return parsed;
  }

  console.log("\n=== 未调用工具，直接回答 ===");
  console.log(msg.content);

  return msg.content;
}