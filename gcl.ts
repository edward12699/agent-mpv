import OpenAI from "openai";
import type {
  ChatCompletionMessageParam,
  ChatCompletionTool
} from "openai/resources/chat/completions.js";

if (!process.env.DASHSCOPE_API_KEY) {
  throw new Error("缺少 DASHSCOPE_API_KEY，请先在环境变量中设置后再启动调试。");
}

const client = new OpenAI({
  apiKey: process.env.DASHSCOPE_API_KEY,
  baseURL: "https://dashscope.aliyuncs.com/compatible-mode/v1"
});

// ===== 模拟数据库 =====
const contracts = [
  {
    id: 1,
    text: "甲方：上海A公司，乙方：北京B公司，金额：100000元，日期：2023年1月1日"
  },
  {
    id: 2,
    text: "甲方：杭州C公司，乙方：深圳D公司，金额：300000元，日期：2024年5月20日"
  },
  {
    id: 3,
    text: "甲方：广州E公司，乙方：成都F公司，金额：500000元，日期：2022年8月15日"
  }
];

// ===== 工具 =====
function searchContract(query: string) {
  return contracts; // 简化：直接返回全部
}

// ===== 工具定义 =====
const tools: ChatCompletionTool[] = [
  {
    type: "function",
    function: {
      name: "search_contract",
      description: "查询合同数据，当涉及合同、金额、比较时必须调用",
      parameters: {
        type: "object",
        properties: {
          query: {
            type: "string",
            description: "查询条件"
          }
        },
        required: ["query"]
      }
    }
  }
];

// ===== Agent核心 =====
async function runAgent(question: string) {
  let messages: ChatCompletionMessageParam[] = [
    {
      role: "system",
      content: `
你是一个合同分析助手。

规则：
1. 涉及合同数据必须调用 search_contract
2. 拿到数据后必须自己分析
3. 找最大金额必须比较，不要瞎猜
`
    },
    {
      role: "user",
      content: question
    }
  ];

  // ===== 第一次：让AI决定工具 =====
  const first = await client.chat.completions.create({
    model: "qwen-plus", // 推荐这个
    messages,
    tools,
    tool_choice: "auto"
  });

  const msg = first.choices[0].message;

  // ===== 工具调用 =====
  if (msg.tool_calls) {
    const toolCall = msg.tool_calls[0];
    if (toolCall.type !== "function") {
      throw new Error("仅支持 function 工具调用");
    }
    const args = JSON.parse(toolCall.function.arguments);

    const toolResult = searchContract(args.query);

    messages.push(msg);

    messages.push({
      role: "tool",
      tool_call_id: toolCall.id,
      content: JSON.stringify(toolResult)
    });

    // ===== 第二次：生成最终答案 =====
    const second = await client.chat.completions.create({
      model: "qwen-plus",
      messages
    });

    return second.choices[0].message.content;
  }

  return msg.content;
}

// ===== 测试 =====
async function main() {
  const question = "帮我找金额最大的合同";

  const result = await runAgent(question);

  console.log(result);
}

main();