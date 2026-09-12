import json

from app.agent_langchain import TOOLS


def inspect_tools() -> None:
    for current_tool in TOOLS:
        print("=" * 80)
        print("name:")
        print(current_tool.name)

        print("\ndescription:")
        print(current_tool.description)

        print("\ninput schema:")
        schema = current_tool.get_input_schema().model_json_schema()
        print(
            json.dumps(
                schema,
                ensure_ascii=False,
                indent=2,
            )
        )


if __name__ == "__main__":
    inspect_tools()
