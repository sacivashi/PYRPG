"""A tiny event listener. The game says what happened (`emit("victory", enemy="Wolf", size=2)`)
and whoever cares listens (`on("victory", count_quest_kills)`), so quests, effects (and later
unlocks and flavor text) can all react to the same moments without the code that fires them
knowing about any of it.

Events fired so far (PYRPG):
    explore      distance            every step out with Explore
    rest                             every rest attempt out there (success or not)
    rested                           a successful rest out there
    town_rest                        a paid rest in town
    victory      enemy, size         a won fight (after the rewards)
    fast_travel  depth               a paid (or free) fast travel
    defeated     enemy               a lost fight (before the death penalties)
    prayed                           praying at a sculpture (whether anything answers or not)
"""
from collections import defaultdict


class EventBus:
    def __init__(self):
        self._listeners = defaultdict(list)

    def on(self, event, listener):
        """Call `listener(**data)` every time `event` is emitted"""
        self._listeners[event].append(listener)

    def emit(self, event, **data):
        for listener in list(self._listeners[event]):
            listener(**data)
