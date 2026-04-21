import { runAgent } from "./agent.js";

async function main() {
  const questions = [
    "帮我找金额最大的合同",
    "帮我找2023年的合同",
    "帮我找不是2024年的合同",
    "帮我找金额超过20万的合同"
  ];

  for (const q of questions) {
    const result = await runAgent(q);

    console.log("\n=== 最终结构化展示 ===");
    console.log(result);

    console.log("\n==============================\n");
  }
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});