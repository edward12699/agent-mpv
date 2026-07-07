from .agent import Agent


def main():
    agent = Agent()
    questions = [
        "找2023年金额最大的合同",
        "找不是2024年的最大金额合同",
    ]
    for question in questions:
        trace = agent.run(question)
        print(trace)


if __name__ == "__main__":
    main()
