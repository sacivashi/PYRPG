from dataclasses import dataclass


@dataclass
class PlayerData:
    name: str
    role: str
    level: int
    hp: float
    stats: dict
