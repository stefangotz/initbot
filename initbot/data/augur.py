from dataclasses import dataclass


@dataclass(frozen=True)
class AugurData:
    description: str
    roll: int
