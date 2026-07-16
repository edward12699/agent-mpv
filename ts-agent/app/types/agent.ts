export interface AgentStep {
  tool: string;
  args: Record<string, unknown>;
  result: unknown;
}

export interface AgentResponse {
  question: string;
  steps: AgentStep[];
  answer: string;
}