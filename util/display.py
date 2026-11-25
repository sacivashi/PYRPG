"""Plain-text layout helpers for the terminal: HP/MP bars, dividers and option grids. Kept tiny and
dependency-free on purpose — the Rich update replaces these, so everything goes through here."""

BAR_WIDTH = 12


def bar(current, maximum, width=BAR_WIDTH):
    """'██████░░░░░░' — how full current/maximum is"""
    share = 0 if not maximum else max(0.0, min(1.0, current / maximum))
    filled = round(share * width)
    if current > 0 and filled == 0:
        filled = 1          # still alive: never show an empty bar
    return "█" * filled + "░" * (width - filled)


def number(value):
    """HP can be fractional mid-fight (damage reduction); show it as a whole number"""
    return int(round(value))


def gauge(label, current, maximum):
    """'HP 12/25  ██████░░░░░░'"""
    return f"{label} {number(current):>3}/{number(maximum):<3} {bar(current, maximum)}"


def divider(title="", width=44):
    """'--- Turn 1 ---------------------------------'"""
    head = f"--- {title} " if title else ""
    return head + "-" * max(3, width - len(head))


def options(choices, columns=3):
    """A grid of '[1] Attack' entries, `columns` per row, padded so they line up"""
    cells = [f"[{key}] {label}" for key, label in choices]
    rows = [cells[i:i + columns] for i in range(0, len(cells), columns)]
    widths = [max(len(row[c]) for row in rows if c < len(row)) + 3 for c in range(columns)]
    return "\n".join("  " + "".join(cell.ljust(widths[c]) for c, cell in enumerate(row)).rstrip()
                     for row in rows)
