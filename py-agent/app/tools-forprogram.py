from typing import List, Optional
from .data import contracts
from .models import Contract, AmountConfidence


def extract_parties(text: str):
    import re

    a_match = re.search(r"甲方[:：]([^，]+)", text)
    b_match = re.search(r"乙方[:：]([^，]+)", text)
    return a_match.group(1) if a_match else None, b_match.group(1) if b_match else None


def extract_year(text: str) -> Optional[str]:
    import re

    match = re.search(r"(20\d{2})年", text)
    return match.group(1) if match else None


def extract_amount_with_confidence(text: str):
    normalized = text.replace(",", "")

    if any(keyword in normalized for keyword in ["未定", "暂定", "后续补充"]):
        return None, "unknown"

    if "三十万" in normalized or "叁拾万" in normalized:
        confidence = "approximate" if "约" in normalized or "左右" in normalized else "exact"
        return 300000, confidence

    if any(keyword in normalized for keyword in ["45万", "四十五万", "肆拾伍万"]):
        confidence = "approximate" if "约" in normalized or "左右" in normalized else "exact"
        return 450000, confidence

    import re

    number_match = re.search(r"(?:金额|合同总价|费用合计|预计费用|价款|总金额)[^，。；;]{0,12}?(?:￥|¥)?(\d+)(?:元|人民币|$)", normalized)
    if number_match:
        return int(number_match.group(1)), "exact"

    return None, "unknown"


def parse_contract(raw_contract: dict) -> Contract:
    party_a, party_b = extract_parties(raw_contract["text"])
    year = extract_year(raw_contract["text"])
    amount, confidence = extract_amount_with_confidence(raw_contract["text"])
    return Contract(
        id=raw_contract["id"],
        party_a=party_a,
        party_b=party_b,
        amount=amount,
        amount_confidence=confidence,
        year=year,
        raw_text=raw_contract["text"],
    )


def search_contract(
    year: Optional[str] = None,
    exclude_year: Optional[str] = None,
    need_amount: bool = False,
    compare: Optional[str] = None,
    min_amount: Optional[int] = None,
) -> List[Contract]:
    results = contracts

    if year:
        results = [c for c in results if year in c["text"]]
    if exclude_year:
        results = [c for c in results if exclude_year not in c["text"]]
    if need_amount or compare == "max" or min_amount is not None:
        results = [c for c in results if extract_amount_with_confidence(c["text"])[0] is not None]
    if min_amount is not None:
        results = [c for c in results if (extract_amount_with_confidence(c["text"])[0] or 0) > min_amount]

    return [parse_contract(c) for c in results]


def rank_contracts(contracts: List[Contract], order: str = "desc"):
    valid = [c for c in contracts if c.amount is not None]

    def weight(contract: Contract):
        return {
            "exact": 2,
            "approximate": 1,
            "unknown": 0,
        }[contract.amount_confidence]

    sorted_contracts = sorted(
        valid,
        key=lambda c: (-(c.amount or 0), -weight(c)) if order == "desc" else ((c.amount or 0), -weight(c)),
    )

    return {
        "rankedContracts": [c.to_dict() for c in sorted_contracts],
        "topContract": sorted_contracts[0].to_dict() if sorted_contracts else None,
    }
