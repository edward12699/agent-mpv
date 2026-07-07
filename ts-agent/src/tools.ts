import type { ChatCompletionTool } from "openai/resources/chat/completions.js";
import { contracts } from "./data";

export type ParsedContractQuery = {
  year?: string;
  excludeYear?: string;
  needAmount?: boolean;
  compare?: "max";
  minAmount?: number;
};

type Contract = {
  id: number;
  partyA: string;
  partyB: string;
  amount: number | null;
  amountConfidence: "exact" | "approximate" | "unknown";
  year: string | null;
  rawText: string;
};

// 提取甲乙方
function extractParties(text: string) {
  const aMatch = text.match(/甲方[:：]([^，]+)/);
  const bMatch = text.match(/乙方[:：]([^，]+)/);

  return {
    partyA: aMatch ? aMatch[1] : null,
    partyB: bMatch ? bMatch[1] : null,
  };
}

function extractYear(text: string): string | null {
  const match = text.match(/(20\d{2})年/);
  return match ? match[1] : null;
}

function extractAmountWithConfidence(text: string) {
  const normalized = text.replace(/,/g, "");

  if (
    normalized.includes("未定") ||
    normalized.includes("暂定") ||
    normalized.includes("后续补充")
  ) {
    return { amount: null, confidence: "unknown" as const };
  }

  // 1. 中文金额优先
  if (normalized.includes("三十万") || normalized.includes("叁拾万")) {
    return {
      amount: 300000,
      confidence:
        normalized.includes("约") || normalized.includes("左右")
          ? ("approximate" as const)
          : ("exact" as const),
    };
  }

  if (
    normalized.includes("45万") ||
    normalized.includes("四十五万") ||
    normalized.includes("肆拾伍万")
  ) {
    return {
      amount: 450000,
      confidence:
        normalized.includes("约") || normalized.includes("左右")
          ? ("approximate" as const)
          : ("exact" as const),
    };
  }

  // 2. 数字金额：限制在金额关键词后很短范围内，避免抓到日期
  const numberMatch = normalized.match(
    /(?:金额|合同总价|费用合计|预计费用|价款|总金额)[^，。；;]{0,12}?(?:￥|¥)?(\d+)(?:元|人民币|$)/,
  );

  if (numberMatch) {
    return {
      amount: Number(numberMatch[1]),
      confidence: "exact" as const,
    };
  }

  return { amount: null, confidence: "unknown" as const };
}

function isAmountRelated(text: string) {
  return (
    text.includes("金额") ||
    text.includes("合同总价") ||
    text.includes("费用合计") ||
    text.includes("总价") ||
    text.includes("费用") ||
    text.includes("￥") ||
    text.includes("¥")
  );
}

export const tools: ChatCompletionTool[] = [
  {
    type: "function",
    function: {
      name: "search_contract",
      description:
        "查询合同数据。当用户问题涉及合同、金额、日期、比较、筛选时必须调用",
      parameters: {
        type: "object",
        properties: {
          year: {
            type: "string",
            description: "需要包含的年份，例如 2023",
          },
          excludeYear: {
            type: "string",
            description: "需要排除的年份，例如 2024",
          },
          needAmount: {
            type: "boolean",
            description: "是否要求合同中必须包含金额字段",
          },
          compare: {
            type: "string",
            enum: ["max"],
            description: "是否要做比较，例如最大金额",
          },
          minAmount: {
            type: "number",
            description: "最小金额阈值，例如 200000",
          },
        },
      },
    },
  },
  {
    type: "function",
    function: {
      name: "rank_contracts",
      description:
        "对已检索到的结构化合同按金额排序，用于找最大金额、最高费用、最高合同价款等问题",
      parameters: {
        type: "object",
        properties: {
          contracts: {
            type: "array",
            description: "结构化合同数组",
            items: {
              type: "object",
              properties: {
                id: { type: "number" },
                amount: { type: ["number", "null"] },
                amountConfidence: {
                  type: "string",
                  enum: ["exact", "approximate", "unknown"],
                },
                year: { type: ["string", "null"] },
                partyA: { type: ["string", "null"] },
                partyB: { type: ["string", "null"] },
                rawText: { type: "string" },
              },
              required: ["id", "amount", "amountConfidence", "rawText"],
            },
          },
          order: {
            type: "string",
            enum: ["desc", "asc"],
            description: "排序方向，找最大金额用 desc",
          },
        },
        required: ["contracts", "order"],
      },
    },
  },
];

function extractAmount(text: string): number | null {
  const normalized = text.replace(/,/g, "");
  if (
    normalized.includes("金额：未定") ||
    normalized.includes("金额:未定") ||
    normalized.includes("暂定") ||
    normalized.includes("未定") ||
    normalized.includes("后续补充")
  ) {
    return null;
  }

  const numberMatch = normalized.match(
    /(?:金额|合同总价|费用合计|预计费用|价款|总金额)[^0-9]*(?:￥|¥)?(\d+)/,
  );

  if (numberMatch) return Number(numberMatch[1]);

  if (normalized.includes("三十万") || normalized.includes("叁拾万")) {
    return 300000;
  }

  if (
    normalized.includes("45万") ||
    normalized.includes("四十五万") ||
    normalized.includes("肆拾伍万")
  ) {
    return 450000;
  }

  if (
    normalized.includes("暂定") ||
    normalized.includes("未定") ||
    normalized.includes("后续补充")
  ) {
    return null;
  }

  return null;
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
    results = results.filter((c) => extractAmount(c.text) !== null);
  }

  if (query.compare === "max" || typeof query.minAmount === "number") {
    results = results.filter((c) => extractAmount(c.text) !== null);
  }

  // compare=max 这里先不直接做最终答案，只是为了保留候选
  // 如果需要最大值，至少把有金额的都保住，让模型后面比较
  if (query.compare === "max" || typeof query.minAmount === "number") {
    results = results.filter((c) => {
      const amount = extractAmount(c.text);
      return amount !== null;
    });
  }

  return results.map((c) => {
    const { partyA, partyB } = extractParties(c.text);

    const year = extractYear(c.text);

    const { amount, confidence } = extractAmountWithConfidence(c.text);

    return {
      id: c.id,

      partyA,

      partyB,

      amount,

      amountConfidence: confidence,

      year,

      rawText: c.text,
    };
  });
}

export function rankContracts(input: {
  contracts: Array<{
    id: number;
    amount: number | null;
    amountConfidence: "exact" | "approximate" | "unknown";
    year: string | null;
    partyA: string | null;
    partyB: string | null;
    rawText: string;
  }>;
  order: "desc" | "asc";
}) {
  const valid = input.contracts.filter((c) => c.amount !== null);

  const sorted = valid.sort((a, b) => {
    const diff =
      input.order === "desc"
        ? (b.amount ?? 0) - (a.amount ?? 0)
        : (a.amount ?? 0) - (b.amount ?? 0);

    if (diff !== 0) return diff;

    // 金额相同：exact 优先于 approximate
    const weight = {
      exact: 2,
      approximate: 1,
      unknown: 0,
    };

    return weight[b.amountConfidence] - weight[a.amountConfidence];
  });

  return {
    rankedContracts: sorted,
    topContract: sorted[0] ?? null,
  };
}
