"""The terminal's look (v1.1.1): HP/MP bars, dividers, option grids, tables, the title banner and
the colors on everything the game prints. Everything visual goes through here.

Color comes from Rich (`pip install rich`). It's switched on once, by enable() in main.py, and only
when Rich is installed and the output is a real terminal. Otherwise every helper gives the plain
text it always did: tests, piped output and players without Rich see no escape codes.

Most of the game just print()s plain sentences. Once color is on, those go through HIGHLIGHTS
(regex -> style) on their way out, so "11 damage", "+5 HP" or "(charging!)" get colored without
the code that printed them knowing anything about it.
"""
import io
import os
import re
import sys

try:
    from rich.console import Console
    from rich.table import Table
    from rich.text import Text
    from rich import box
    RICH = True
except ImportError:  # the game still runs without Rich, just in plain text
    RICH = False

ENABLED = False
BAR_WIDTH = 12
FRAME = ("▕", "▏")  # thin edges that hug the bar
FRAME_STYLE = "grey58"  # a middle gray: shows on dark and light terminals alike

BANNER = r"""
 ____   __   __  ____    ____     ____
|  _ \  \ \ / / |  _ \  |  _ \   / ___|
| |_) |  \ V /  | |_) | | |_) | | |  _
|  __/    | |   |  _ <  |  __/  | |_| |
|_|       |_|   |_| \_\ |_|      \____|"""

# regex -> Rich style, applied in order (later ones win where they overlap)
HIGHLIGHTS = [
    (r"^=== .* ===$", "bold bright_white"),
    (r"^=== (VICTORY|Combat over) ===$", "bold green"),
    (r"^=== (DEFEAT|FLED|It got away) ===$", "bold red"),
    (r"^--- .*", "grey50"),
    (r"^\[.*'s turn\]$|^\[Your turn\]$", "bold"),
    (r"^\s*\[[0-9a-z]{1,3}\]", "bold cyan"),
    (r"\b\d+(\.\d+)? (searing )?damage\b", "bold orange1"),
    (r"\b\d+(\.\d+)? HP\b", "bold green"),
    (r"(sears|leeches|siphons|costs|drains)( you)?( for)? \d+(\.\d+)? HP", "bold red"),
    (r"deals \d+(\.\d+)? damage to you|You take \d+(\.\d+)? \w* ?damage|counters for \d+ damage", "bold red"),
    (r"\b\d+ (gold|coins)\b|\bGold:? \d+", "bold yellow"),
    (r"\d+(\.\d+)?% EXP", "bold cyan"),
    (r"\*\*\* LEVEL UP!.*", "bold green"),
    (r"✦ Unlocked: .* ✦", "bold magenta"),
    (r"\(charging!\)", "bold red"),
    (r"\(guarding\)", "bold cyan"),
    (r"\((fled|defeated)\)", "grey50"),
    (r"^  » .*", "italic grey70"),
    (r"\(auto-saved\)", "grey50"),
    (r"^Invalid .*|^❌.*", "red"),
    (r"blessed!", "bold green"),
    (r"cursed!", "bold red"),
]
_COMPILED = [(re.compile(pattern, re.MULTILINE), style) for pattern, style in HIGHLIGHTS]
_ANSI = re.compile(r"(\x1b\[[0-9;]*m)")
_console = None


# --- switching color on -----------------------------------------------------------------------------

def _windows_vt():
    """Let the old Windows console understand color codes (newer terminals already do)"""
    if os.name != "nt":
        return
    try:
        import ctypes
        kernel = ctypes.windll.kernel32
        handle = kernel.GetStdHandle(-11)
        mode = ctypes.c_uint32()
        if kernel.GetConsoleMode(handle, ctypes.byref(mode)):
            kernel.SetConsoleMode(handle, mode.value | 0x0004)
    except Exception:
        pass


class _Highlighted:
    """sys.stdout, with HIGHLIGHTS applied to whatever gets written"""
    def __init__(self, stream):
        self._stream = stream

    def write(self, text):
        return self._stream.write(highlight(text))

    def __getattr__(self, name):
        return getattr(self._stream, name)


def enable():
    """Turn color on, if Rich is here and we're printing to a terminal. Returns whether it's on."""
    global ENABLED, _console
    if ENABLED or not RICH or not sys.stdout.isatty() or os.environ.get("NO_COLOR"):
        return ENABLED
    _windows_vt()
    real = Console()
    _console = Console(file=io.StringIO(), force_terminal=True, legacy_windows=False,
                       color_system=real.color_system or "256", width=real.width, soft_wrap=True)
    ENABLED = True
    sys.stdout = _Highlighted(sys.stdout)
    return True


def _render(renderable):
    """A Rich renderable -> the text with color codes, ready for a plain print()"""
    with _console.capture() as captured:
        _console.print(renderable, end="")
    return captured.get()


def paint(text, style):
    """`text` in a Rich style ("bold red"); plain when color is off"""
    return _render(Text(text, style=style)) if ENABLED else text


def highlight(text):
    """Color the parts of a printed line that HIGHLIGHTS knows; already-colored parts are left alone"""
    if not ENABLED or not text.strip():
        return text
    parts = _ANSI.split(text)
    styled = []
    for i, part in enumerate(parts):
        if i % 2 or not part:           # an escape code, or nothing between two
            styled.append(part)
            continue
        line = Text(part)
        for pattern, style in _COMPILED:
            for match in pattern.finditer(part):
                line.stylize(style, match.start(), match.end())
        styled.append(_render(line) if line.spans else part)
    return "".join(styled)


# --- bars --------------------------------------------------------------------------------------------

def bar(current, maximum, width=BAR_WIDTH, kind="HP"):
    """'▕██████░░░░░░▏' — how full current/maximum is, in a thin gray frame. HP goes green/yellow/red
    as it drains; MP is blue."""
    share = 0 if not maximum else max(0.0, min(1.0, current / maximum))
    filled = round(share * width)
    if current > 0 and filled == 0:
        filled = 1          # still alive: never show an empty bar
    left, right = FRAME
    if not ENABLED:
        return left + "█" * filled + "░" * (width - filled) + right
    color = "dodger_blue1" if kind == "MP" else "green3" if share > 0.5 else "yellow3" if share > 0.25 else "red3"
    frame = FRAME_STYLE
    return (paint(left, frame) + paint("█" * filled, color) + paint("░" * (width - filled), "grey35")
            + paint(right, frame))


def number(value):
    """HP can be fractional mid-fight (damage reduction); show it as a whole number"""
    return int(round(value))


def gauge(label, current, maximum):
    """'HP 12/25  ▕██████░░░░░░▏'"""
    return f"{label} {number(current):>3}/{number(maximum):<3} {bar(current, maximum, kind=label)}"


def divider(title="", width=44):
    """'--- Turn 1 ---------------------------------'"""
    head = f"--- {title} " if title else ""
    return head + "-" * max(3, width - len(head))


# --- menus and tables ------------------------------------------------------------------------------------

def options(choices, columns=3):
    """A grid of '[1] Attack' entries, numbered down each column, padded so they line up:

        [1] Explore          [4] View Stats
        [2] Rest             [5] Manage Loot
        [3] Return to Town   [6] Save Game
                  [7] Exit Game

    Whatever doesn't fill a whole row goes centered on a last row."""
    cells = [f"[{key}] {label}" for key, label in choices]
    height = len(cells) // columns
    if height == 0:  # fewer than one row's worth: just one row
        height, columns = 1, len(cells)
    grid, rest = cells[:height * columns], cells[height * columns:]
    rows = [[grid[c * height + r] for c in range(columns)] for r in range(height)]
    widths = [max(len(row[c]) for row in rows) + 3 for c in range(columns)]
    if rest:
        leftover = "   ".join(rest)
        full = sum(widths) - 3
        rows.append([" " * max(0, (full - len(leftover)) // 2) + leftover])
    lines = []
    for row in rows:
        line = "".join(cell.ljust(widths[c]) for c, cell in enumerate(row)).rstrip()
        if ENABLED:  # color each key, keeping the padding worked out on the plain text
            line = re.sub(r"\[([0-9a-z]{1,3})\]", lambda m: paint(m.group(0), "bold cyan"), line)
        lines.append("  " + line)
    return "\n".join(lines)


def menu(title, choices, columns=2, subtitle=None):
    """A menu screen: '=== Town ===', an optional line under it, then the options grid"""
    lines = [f"\n=== {title} ==="]
    if subtitle:
        lines.append(subtitle)
    lines.append(options(choices, columns))
    return "\n".join(lines)


def table(headers, rows, title=None):
    """Rows of cells under headers: a Rich table when color is on, aligned plain columns otherwise"""
    rows = [[str(cell) for cell in row] for row in rows]
    if ENABLED:
        grid = Table(title=title, box=box.ROUNDED, header_style="bold cyan", title_style="bold",
                     title_justify="left")
        for header in headers:
            grid.add_column(header)
        for row in rows:
            grid.add_row(*row)
        return _render(grid).rstrip("\n")
    widths = [max(len(str(cell)) for cell in column) for column in zip(headers, *rows)]
    line = lambda cells: "  " + "   ".join(cell.ljust(width) for cell, width in zip(cells, widths)).rstrip()
    out = [title] if title else []
    out += [line(headers), "  " + "   ".join("-" * width for width in widths)]
    out += [line(row) for row in rows]
    return "\n".join(out)


def banner(version):
    """The title screen's PYRPG, with the version under its right edge"""
    art = BANNER.strip("\n")
    width = max(len(line) for line in art.splitlines())
    tag = f"v{version}".rjust(width)
    return (paint(art, "bold bright_magenta") + "\n" + paint(tag, "grey50")) if ENABLED else f"{art}\n{tag}"
