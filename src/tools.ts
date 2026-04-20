import type { ChatCompletionTool } from "openai/resources/chat/completions.js";
import { contracts } from "./data.js";

export const tools: ChatCompletionTool[] = [
  {
    type: "function",
    function: {
      name: "search_contract",
      description: "查询合同数据。当用户问题涉及合同、金额、日期、比较、筛选时必须调用",
      parameters: {
        type: "object",
        properties: {
          query: {
            type: "string",
            description: "用户查询条件，比如：金额最大的合同、2023年的合同、金额超过20万的合同"
          }
        },
        required: ["query"]
      }
    }
  }
];


export function searchContract(query: string) {
  const q = query.toLowerCase();

  // 1. 先按明显条件筛
  let results = contracts.filter((c) => {
    if (q.includes("2023")) return c.text.includes("2023");
    if (q.includes("2024")) return c.text.includes("2024");
    if (q.includes("2022")) return c.text.includes("2022");

    if (
      q.includes("金额") ||
      q.includes("最大") ||
      q.includes("最贵") ||
      q.includes("超过")
    ) {
      return c.text.includes("金额");
    }

    return false;
  });

  // 2. 如果一个都没筛出来，再兜底
  if (results.length === 0) {
    results = contracts.slice(0, 2);
  }

  return results.slice(0, 3);
}