"""兼容旧导入路径：from app.tool import ..."""

from app.tools.contract_tools import (
    contract_from_dict,
    extract_amount_with_confidence,
    extract_parties,
    extract_year,
    parse_contract,
    rank_contracts,
    search_contract,
    to_jsonable,
)
from app.tools.document_tools import search_documents

__all__ = [
    "contract_from_dict",
    "extract_amount_with_confidence",
    "extract_parties",
    "extract_year",
    "parse_contract",
    "rank_contracts",
    "search_contract",
    "search_documents",
    "to_jsonable",
]
