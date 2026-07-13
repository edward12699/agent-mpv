from .agent_langchain import Agent
from .llm import create_default_llm


def main():
    agent = Agent(llm=create_default_llm())
    questions = [
        "找2023年金额最大的合同",
        "找不是2024年的最大金额合同",
    ]
    for question in questions:
        trace = agent.run(question)
        print(trace)


if __name__ == "__main__":
    main()
