from dataclasses import dataclass


@dataclass
class PlayerData:
    name: str
    role: str
    level: int
    hp: int
    stats: dict
    max_hp: int = None
