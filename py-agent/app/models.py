from typing import Literal, Optional

AmountConfidence = Literal["exact", "approximate", "unknown"]

class Contract:
    def __init__(
        self,
        id: int,
        party_a: Optional[str],
        party_b: Optional[str],
        amount: Optional[int],
        amount_confidence: AmountConfidence,
        year: Optional[str],
        raw_text: str,
    ):
        self.id = id
        self.party_a = party_a
        self.party_b = party_b
        self.amount = amount
        self.amount_confidence = amount_confidence
        self.year = year
        self.raw_text = raw_text

    def to_dict(self):
        return {
            "id": self.id,
            "partyA": self.party_a,
            "partyB": self.party_b,
            "amount": self.amount,
            "amountConfidence": self.amount_confidence,
            "year": self.year,
            "rawText": self.raw_text,
        }
