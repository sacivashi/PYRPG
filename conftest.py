# Empty on purpose. Its presence tells pytest that the project root has no
# __init__.py, so pytest adds this directory to sys.path when collecting
# tests — letting test files use the same root-relative imports as the game
# itself (e.g. `from combat.combat_player import Player`).
