"use client";

import { useState } from "react";

type AgentStep = {
  tool: string;
  args: Record<string, unknown>;
  result: unknown;
};

type AgentResponse = {
  backend?: string;
  question: string;
  steps: AgentStep[];
  finalAnswer: string;
};

type BackendOption = "ts" | "python";

const EXAMPLES = [
  "找2023年金额最大的合同",
  "找不是2024年的最大金额合同",
  "帮我找金额超过20万的合同",
];

function summarizeStep(step: AgentStep): string {
  if (step.tool === "search_contract") {
    const list = Array.isArray(step.result) ? step.result : [];
    return `返回 ${list.length} 条候选合同`;
  }
  if (step.tool === "rank_contracts") {
    const r = step.result as { topContract?: { id?: number } } | null;
    const id = r?.topContract?.id;
    return id != null ? `topContract = ID${id}` : "未找到可排序合同";
  }
  return "已完成";
}

export default function Home() {
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<AgentResponse | null>(null);
  const [backend, setBackend] = useState<BackendOption>("ts");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const q = question.trim();
    if (!q) return;

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const res = await fetch("/api/agent", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: q, backend }),
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.error || "请求失败");
      }

      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "未知错误");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main style={styles.main}>
      <header style={styles.header}>
        <h1 style={styles.title}>合同分析 Agent 控制台</h1>
        <p style={styles.subtitle}>
          多工具 AI 工作流：检索 → 排序 → 最终答案
        </p>
      </header>

      <form onSubmit={handleSubmit} style={styles.form}>
        <label htmlFor="question" style={styles.label}>
          请输入问题
        </label>
        <div style={styles.controlsRow}>
          <label htmlFor="backend" style={styles.label}>
            选择后端
          </label>
          <select
            id="backend"
            value={backend}
            onChange={(e) => setBackend(e.target.value as BackendOption)}
            style={styles.select}
            disabled={loading}
          >
            <option value="ts">ts-agent 后台</option>
            <option value="python">py-agent 后台</option>
          </select>
        </div>
        <textarea
          id="question"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="例如：找2023年金额最大的合同"
          rows={3}
          style={styles.input}
          disabled={loading}
        />
        <button
          type="submit"
          disabled={loading || !question.trim()}
          style={{
            ...styles.button,
            opacity: loading || !question.trim() ? 0.6 : 1,
          }}
        >
          {loading ? "分析中…" : "开始分析"}
        </button>
      </form>

      <div style={styles.examples}>
        <span style={styles.examplesLabel}>示例：</span>
        {EXAMPLES.map((ex) => (
          <button
            key={ex}
            type="button"
            style={styles.chip}
            disabled={loading}
            onClick={() => setQuestion(ex)}
          >
            {ex}
          </button>
        ))}
      </div>

      {error && (
        <div style={styles.errorBox} role="alert">
          {error}
        </div>
      )}

      {loading && (
        <div style={styles.loading}>
          <span className="spinner" />
          Agent 正在执行工具链…
        </div>
      )}

      {result && (
        <section style={styles.output}>
          <div style={styles.block}>
            <h2 style={styles.blockTitle}>用户问题</h2>
            <p style={styles.questionText}>{result.question}</p>
          </div>

          {result.steps.map((step, i) => (
            <div key={i} style={styles.block}>
              <h2 style={styles.blockTitle}>
                Step {i + 1}: {step.tool}
              </h2>
              <p style={styles.summary}>{summarizeStep(step)}</p>
              <details style={styles.details}>
                <summary style={styles.summaryBtn}>展开 JSON</summary>
                <div style={styles.jsonSection}>
                  <p style={styles.jsonLabel}>参数 args</p>
                  <pre style={styles.pre}>
                    {JSON.stringify(step.args, null, 2)}
                  </pre>
                  <p style={styles.jsonLabel}>结果 result</p>
                  <pre style={styles.pre}>
                    {JSON.stringify(step.result, null, 2)}
                  </pre>
                </div>
              </details>
            </div>
          ))}

          <div style={{ ...styles.block, ...styles.finalBlock }}>
            <h2 style={styles.blockTitle}>
              Step {result.steps.length + 1}: 最终答案
            </h2>
            <pre style={styles.finalAnswer}>{result.finalAnswer}</pre>
          </div>
        </section>
      )}
    </main>
  );
}

const styles: Record<string, React.CSSProperties> = {
  main: {
    maxWidth: 720,
    margin: "0 auto",
    padding: "48px 24px 80px",
  },
  header: {
    marginBottom: 32,
  },
  title: {
    margin: 0,
    fontSize: 28,
    fontWeight: 700,
    letterSpacing: "-0.02em",
  },
  subtitle: {
    margin: "8px 0 0",
    color: "#8b9cb3",
    fontSize: 15,
  },
  form: {
    display: "flex",
    flexDirection: "column",
    gap: 12,
  },
  controlsRow: {
    display: "flex",
    flexDirection: "column",
    gap: 8,
  },
  label: {
    fontSize: 14,
    fontWeight: 500,
    color: "#a8b8cc",
  },
  input: {
    width: "100%",
    padding: "14px 16px",
    fontSize: 15,
    lineHeight: 1.5,
    borderRadius: 10,
    border: "1px solid #2a3544",
    background: "#1a2332",
    color: "#e7ecf3",
    resize: "vertical",
    outline: "none",
  },
  select: {
    width: "fit-content",
    minWidth: 180,
    padding: "10px 12px",
    fontSize: 14,
    borderRadius: 8,
    border: "1px solid #2a3544",
    background: "#1a2332",
    color: "#e7ecf3",
    outline: "none",
  },
  button: {
    alignSelf: "flex-start",
    padding: "12px 28px",
    fontSize: 15,
    fontWeight: 600,
    borderRadius: 8,
    border: "none",
    background: "linear-gradient(135deg, #3b82f6, #2563eb)",
    color: "#fff",
    cursor: "pointer",
  },
  examples: {
    display: "flex",
    flexWrap: "wrap",
    alignItems: "center",
    gap: 8,
    marginTop: 16,
  },
  examplesLabel: {
    fontSize: 13,
    color: "#6b7d94",
  },
  chip: {
    padding: "6px 12px",
    fontSize: 13,
    borderRadius: 20,
    border: "1px solid #2a3544",
    background: "#1a2332",
    color: "#a8b8cc",
    cursor: "pointer",
  },
  errorBox: {
    marginTop: 24,
    padding: "14px 16px",
    borderRadius: 8,
    background: "rgba(239, 68, 68, 0.12)",
    border: "1px solid rgba(239, 68, 68, 0.35)",
    color: "#fca5a5",
    fontSize: 14,
  },
  loading: {
    display: "flex",
    alignItems: "center",
    gap: 12,
    marginTop: 32,
    color: "#8b9cb3",
    fontSize: 14,
  },
  output: {
    marginTop: 32,
    display: "flex",
    flexDirection: "column",
    gap: 16,
  },
  block: {
    padding: "20px 22px",
    borderRadius: 12,
    background: "#1a2332",
    border: "1px solid #2a3544",
  },
  finalBlock: {
    borderColor: "#3b82f6",
    background: "linear-gradient(180deg, #1a2332 0%, #152238 100%)",
  },
  blockTitle: {
    margin: "0 0 10px",
    fontSize: 13,
    fontWeight: 600,
    textTransform: "uppercase",
    letterSpacing: "0.06em",
    color: "#6b9fff",
  },
  questionText: {
    margin: 0,
    fontSize: 16,
    lineHeight: 1.6,
  },
  summary: {
    margin: "0 0 12px",
    fontSize: 15,
    color: "#c5d0de",
  },
  details: {
    fontSize: 13,
  },
  summaryBtn: {
    cursor: "pointer",
    color: "#6b9fff",
    userSelect: "none",
  },
  jsonSection: {
    marginTop: 12,
  },
  jsonLabel: {
    margin: "8px 0 4px",
    fontSize: 12,
    color: "#6b7d94",
  },
  pre: {
    margin: 0,
    padding: 12,
    fontSize: 12,
    lineHeight: 1.5,
    borderRadius: 8,
    background: "#0f1419",
    overflow: "auto",
    maxHeight: 280,
    color: "#a8b8cc",
  },
  finalAnswer: {
    margin: 0,
    fontSize: 14,
    lineHeight: 1.6,
    whiteSpace: "pre-wrap",
    wordBreak: "break-word",
    color: "#e7ecf3",
  },
};
