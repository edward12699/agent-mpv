import json
import sys

from .agent_langchain import Agent
from .llm import create_default_llm


def run_question(question: str):
    agent = Agent(llm=create_default_llm())
    return agent.run(question)


def main():
    if len(sys.argv) < 2 or not sys.argv[1].strip():
        raise RuntimeError("请输入问题")

    result = run_question(sys.argv[1].strip())
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
