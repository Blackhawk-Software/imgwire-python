from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class ImgwireClientOptions:
    api_key: str
    base_url: str = "https://api.imgwire.dev"
    environment_id: Optional[str] = None
    timeout: float = 30.0
    max_retries: int = 2
    backoff_factor: float = 0.5
