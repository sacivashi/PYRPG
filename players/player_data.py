from dataclasses import dataclass, field


@dataclass
class PlayerData:
    name: str
    role: str
    level: int
    hp: int
    stats: dict
    max_hp: int = None
    gold: int = 0
    loot: list = field(default_factory=list)
    equipped: str = None
