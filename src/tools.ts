import type { ChatCompletionTool } from "openai/resources/chat/completions.js";
import { contracts } from "./data.ts";

export type ParsedContractQuery = {
  year?: string;
  excludeYear?: string;
  needAmount?: boolean;
  compare?: "max";
  minAmount?: number;
};

export const tools: ChatCompletionTool[] = [
  {
    type: "function",
    function: {
      name: "search_contract",
      description: "查询合同数据。当用户问题涉及合同、金额、日期、比较、筛选时必须调用",
      parameters: {
        type: "object",
        properties: {
          year: {
            type: "string",
            description: "需要包含的年份，例如 2023"
          },
          excludeYear: {
            type: "string",
            description: "需要排除的年份，例如 2024"
          },
          needAmount: {
            type: "boolean",
            description: "是否要求合同中必须包含金额字段"
          },
          compare: {
            type: "string",
            enum: ["max"],
            description: "是否要做比较，例如最大金额"
          },
          minAmount: {
            type: "number",
            description: "最小金额阈值，例如 200000"
          }
        }
      }
    }
  }
];

function extractAmount(text: string): number {
  const match = text.match(/金额[:：]\s*(\d+)/);
  return match ? Number(match[1]) : 0;
}

export function searchContract(query: ParsedContractQuery) {
  let results = [...contracts];

  if (query.year) {
    results = results.filter((c) => c.text.includes(query.year!));
  }

  if (query.excludeYear) {
    results = results.filter((c) => !c.text.includes(query.excludeYear!));
  }

  if (query.needAmount) {
    results = results.filter((c) => /金额[:：]\s*\d+/.test(c.text));
  }

  if (typeof query.minAmount === "number") {
    results = results.filter((c) => extractAmount(c.text) > query.minAmount!);
  }

  // compare=max 这里先不直接做最终答案，只是为了保留候选
  // 如果需要最大值，至少把有金额的都保住，让模型后面比较
  if (query.compare === "max") {
    results = results.filter((c) => /金额[:：]\s*\d+/.test(c.text));
  }

  return results.slice(0, 5);
}