from items.items_data import get_item_names
from util.file_io import get_data, read_csv

# data/quests.csv — one row per quest:
#   id          unique key; progress and completion are saved under it
#   title       shown on the quest board
#   type        what counts as progress — a QUEST_TYPES key below, or "spend"
#   target      what the type is matched against (see QUEST_TYPES)
#   amount      how many times it has to happen
#   reward      a number = gold, a perk name from PERKS below, or an item name from items.csv
#   description shown on the quest board (quote it if it contains commas)

# Event quest types: the game reports what happened with PYRPG.quest_event(type, value, amount),
# and each type decides whether that value counts toward a quest's target. Adding a type is one
# line here plus a quest_event() call wherever that thing happens.
QUEST_TYPES = {
    "defeat": lambda target, value: value.lower() == target.lower(),  # won a fight against enemy `value`
    "use":    lambda target, value: value.lower() == target.lower(),  # did action `value`, e.g. FAST_TRAVEL
    "reach":  lambda target, value: int(value) >= int(target),        # explored to depth `value` (fast travel doesn't count)
}
# "spend" isn't an event — it's paid at the quest board itself (give `target` gold)
SUPPORTED_TYPES = set(QUEST_TYPES) | {"spend"}

# Non-gold rewards. Claiming one adds it to PlayerData.perks; whatever it affects uses it up.
PERKS = {
    "free_fast_travel": "your next fast travel is free",
}

# "use" quest targets the game reports
FAST_TRAVEL = "fast travel"


def get_quests():
    """{quest_id: {title, type, target, amount, reward, description}}, in file order.
    reward is an int (gold) or a lowercase str (a PERKS key or an item name)."""
    quests = {}
    for row in read_csv(get_data("quests_csv")):
        quest = {column: value.strip() for column, value in row.items()}
        quest["type"] = quest["type"].lower()
        quest["amount"] = int(quest["amount"])
        quest["reward"] = int(quest["reward"]) if quest["reward"].isdigit() else quest["reward"].lower()
        quests[quest.pop("id")] = quest
    return quests


def reward_item(reward):
    """The items.csv name a reward refers to (rewards are stored lowercase), or None"""
    if isinstance(reward, int):
        return None
    return next((name for name in get_item_names() if name.lower() == reward), None)


def grant_reward(player_data, reward):
    """Gold goes to gold, an item into loot, anything else is a perk"""
    if isinstance(reward, int):
        player_data.gold += reward
    elif reward_item(reward):
        player_data.loot.append(reward_item(reward))
    else:
        player_data.perks.append(reward)


def describe_reward(reward):
    if isinstance(reward, int):
        return f"{reward} gold"
    return PERKS.get(reward) or reward_item(reward) or reward


def quest_progress(quest_id, quest, quest_flags):
    """How far along a quest is, from the saved quest_flags. Saves from before quests.csv stored a
    finished defeat quest as {"defeated_<target>": True} — that still counts as complete."""
    if quest["type"] == "defeat" and quest_flags.get(f"defeated_{quest['target'].lower()}") is True:
        return quest["amount"]
    return min(quest["amount"], quest_flags.get(quest_id, 0))
