from typing import Any
from .tools import search_contract, rank_contracts, Contract


class Agent:
    def __init__(self):
        self.steps = []

    def run(self, question: str) -> dict[str, Any]:
        self.steps = []
        if "最大" in question or "最高" in question:
            contracts = search_contract(compare="max")
            self.steps.append({"tool": "search_contract", "args": {"compare": "max"}, "result": [c.to_dict() for c in contracts]})
            ranked = rank_contracts(contracts, order="desc")
            self.steps.append({"tool": "rank_contracts", "args": {"order": "desc"}, "result": ranked})
            return {"question": question, "steps": self.steps, "finalAnswer": f"最高金额合同 ID {ranked['topContract']['id']}" if ranked["topContract"] else "未找到合同"}

        contracts = search_contract()
        self.steps.append({"tool": "search_contract", "args": {}, "result": [c.to_dict() for c in contracts]})
        return {"question": question, "steps": self.steps, "finalAnswer": f"找到 {len(contracts)} 条合同"}
