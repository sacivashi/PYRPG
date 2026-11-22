from dataclasses import dataclass, field


@dataclass
class PlayerData:
    name: str
    role: str
    level: int
    hp: int
    stats: dict
    mana: int = None
    max_hp: int = None
    gold: int = 0
    loot: list = field(default_factory=list)
    equipped: str = None
    exp: float = 0
    in_town: bool = True
    distance: int = 0
    depth_reached: int = 0  # deepest distance ever reached — never goes down, fast travel's ceiling
    failed_attempts: int = 0
    quest_flags: dict = field(default_factory=dict)  # progress markers, e.g. {"defeated_cat": True}
    completed_quests: list = field(default_factory=list)  # quest ids already turned in — can't reclaim
    accepted_quests: list = field(default_factory=list)  # quest ids taken from the board — only these count progress
    quest_choices: dict = field(default_factory=dict)  # quest id -> the choice made on completion, e.g. {"lost_wallet": "Give"}
    known_spells: list = field(default_factory=list)  # learned spells/abilities (spells/spells_data.py names)
    item_state: dict = field(default_factory=dict)  # per-item progress, e.g. Thunder use counts, Sleight of stats wins
    perks: list = field(default_factory=list)  # unspent quest perks, e.g. "free_fast_travel" (quests/quests_data.py PERKS)
