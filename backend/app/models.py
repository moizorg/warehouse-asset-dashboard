from dataclasses import dataclass
from typing import Optional


@dataclass
class Asset:
    id: int
    asset_identifier: str
    category: str
    photograph_path: str
    created_at: str

    def to_dict(self, photograph_url: Optional[str] = None):
        return {
            "id": self.id,
            "asset_identifier": self.asset_identifier,
            "category": self.category,
            "photograph_path": self.photograph_path,
            "photograph_url": photograph_url,
            "created_at": self.created_at,
        }
