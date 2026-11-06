"""Parts library for SVG infographics.

Usage:
    import sys; sys.path.insert(0, "<skill directory>/scripts")
    from svgparts import Slide, C

    s = Slide("Figure title", "One sentence describing the figure (used as aria-label)")
    s.header("Slide heading", "Note at top right (optional)")
    ...
    s.render("out.png")    # saves out.svg, renders a 2x PNG, and checks the layout with real fonts

CLI:
    python3 svgparts.py render in.svg out.png   # convert an existing SVG to PNG
    python3 svgparts.py check in.svg            # report layout problems (exit 1 if any)
    python3 svgparts.py icons out.png           # draw the icon catalog

Colors, sizes, and weights follow the rules in SKILL.md. To change how a part looks,
change this file so that every figure stays consistent.
"""
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import unicodedata
from xml.sax.saxutils import escape

FONT = "'Hiragino Sans', 'Yu Gothic UI', 'Noto Sans JP', 'Noto Sans CJK JP', system-ui, sans-serif"

# Browsers used for PNG conversion, searched in order. SVGPARTS_CHROME overrides them.
_BROWSER_PATHS = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
]
_BROWSER_COMMANDS = ["google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "microsoft-edge", "msedge"]


def find_browser():
    """Return the browser executable used for PNG conversion. Raise if none is found."""
    env = os.environ.get("SVGPARTS_CHROME")
    if env:
        if os.path.exists(env) or shutil.which(env):
            return env
        raise FileNotFoundError(f"Browser set in SVGPARTS_CHROME not found: {env}")
    for p in _BROWSER_PATHS:
        if os.path.exists(p):
            return p
    for c in _BROWSER_COMMANDS:
        found = shutil.which(c)
        if found:
            return found
    raise FileNotFoundError(
        "Chrome, Chromium, or Edge not found. Set SVGPARTS_CHROME to the browser executable")


def _browser_cmd(*args):
    """Command line for the headless browser. SVGPARTS_CHROME_ARGS adds flags (for example --no-sandbox in CI)."""
    extra = os.environ.get("SVGPARTS_CHROME_ARGS", "").split()
    return [find_browser(), "--headless=new", "--disable-gpu", *extra, *args]


class C:
    """Colors. See the color table in SKILL.md for their roles."""
    PRIMARY = "#2563EB"
    PRIMARY_BG = "#EFF6FF"
    ORANGE = "#F97316"     # problems, points of attention
    ORANGE_BG = "#FFF7ED"
    ORANGE_LINE = "#FDBA74"
    GREEN = "#10B981"      # done, reached
    GREEN_BG = "#ECFDF5"
    BG = "#F8FAFC"
    CARD = "#FFFFFF"
    LINE = "#E2E8F0"
    TEXT = "#1E293B"
    SUB = "#64748B"
    ARROW = "#94A3B8"


# Icons drawn with strokes on a 24x24 grid. "CUR" is replaced with the stroke color (for filled dots).
# All shapes are original. New icons: strokes only, round joins, inside 2-22 of the grid.
ICONS = {
    "user": ['<circle cx="12" cy="8" r="4"/>',
             '<path d="M4,21 C4,16.6 7.6,14 12,14 C16.4,14 20,16.6 20,21"/>'],
    "users": ['<circle cx="9" cy="8" r="3.5"/>',
              '<path d="M2.5,20 C2.5,16.2 5.4,14 9,14 C12.6,14 15.5,16.2 15.5,20"/>',
              '<path d="M15,4.8 A3.5,3.5 0 0 1 15,11.6"/>',
              '<path d="M17.5,14.4 C20,15.2 21.5,17.3 21.5,20"/>'],
    "building": ['<rect x="4" y="3" width="16" height="18" rx="1.5"/>',
                 '<path d="M8,7.5 H10 M14,7.5 H16 M8,11.5 H10 M14,11.5 H16 M10,21 V16.5 H14 V21"/>'],
    "server": ['<rect x="3" y="4" width="18" height="7" rx="2"/>',
               '<rect x="3" y="13" width="18" height="7" rx="2"/>',
               '<circle cx="7" cy="7.5" r="0.9" fill="CUR" stroke="none"/>',
               '<circle cx="7" cy="16.5" r="0.9" fill="CUR" stroke="none"/>',
               '<path d="M11,7.5 H17 M11,16.5 H17"/>'],
    "database": ['<ellipse cx="12" cy="5.5" rx="8" ry="3"/>',
                 '<path d="M4,5.5 V18.5 C4,20.2 7.6,21.5 12,21.5 C16.4,21.5 20,20.2 20,18.5 V5.5"/>',
                 '<path d="M4,12 C4,13.7 7.6,15 12,15 C16.4,15 20,13.7 20,12"/>'],
    "laptop": ['<rect x="4.5" y="5" width="15" height="10.5" rx="1.5"/>',
               '<path d="M2,19 H22"/>'],
    "ai": ['<rect x="6" y="6" width="12" height="12" rx="2"/>',
           '<rect x="9.5" y="9.5" width="5" height="5" rx="1"/>',
           '<path d="M9.5,2.5 V6 M14.5,2.5 V6 M9.5,18 V21.5 M14.5,18 V21.5 '
           'M2.5,9.5 H6 M2.5,14.5 H6 M18,9.5 H21.5 M18,14.5 H21.5"/>'],
    "container": ['<path d="M12,2.5 L20.5,7 V17 L12,21.5 L3.5,17 V7 Z"/>',
                  '<path d="M3.5,7 L12,11.5 L20.5,7 M12,11.5 V21.5"/>'],
    "wallet": ['<path d="M5,7 L15.5,3.5 L16.5,7"/>',
               '<rect x="3" y="7" width="18" height="13" rx="2"/>',
               '<path d="M21,11.5 H17 A2,2 0 0 0 17,15.5 H21"/>'],
    "coin": ['<circle cx="12" cy="12" r="9"/>',
             '<circle cx="12" cy="12" r="5"/>'],
    "point": ['<circle cx="12" cy="12" r="9"/>',
              '<path d="M10,16.5 V7.5 H13 A2.6,2.6 0 0 1 13,12.7 H10"/>'],
    "warning": ['<path d="M12,3.5 L21.5,20 H2.5 Z"/>',
                '<path d="M12,9.5 V14"/>',
                '<circle cx="12" cy="17" r="0.9" fill="CUR" stroke="none"/>'],
    "check": ['<circle cx="12" cy="12" r="9"/>',
              '<path d="M8,12.3 L11,15.3 L16.3,9.3"/>'],
    "clock": ['<circle cx="12" cy="12" r="9"/>',
              '<path d="M12,7 V12 L15.5,14"/>'],
    "lock": ['<rect x="5" y="10.5" width="14" height="10.5" rx="2"/>',
             '<path d="M8,10.5 V7.5 A4,4 0 0 1 16,7.5 V10.5"/>'],
    "key": ['<circle cx="7.5" cy="16" r="4.5"/>',
            '<path d="M10.7,12.8 L20,3.5 M16.5,7 L19,9.5 M14,9.5 L16,11.5"/>'],
    "document": ['<path d="M6,2.5 H14 L19,7.5 V21.5 H6 Z"/>',
                 '<path d="M14,2.5 V7.5 H19 M9,12.5 H16 M9,16.5 H16"/>'],
    "bell": ['<path d="M6,16 V11 A6,6 0 0 1 18,11 V16 L19.5,18 H4.5 Z"/>',
             '<path d="M10,21 H14"/>'],
    "flag": ['<path d="M5,21 V3.5"/>',
             '<path d="M5,4 H17.5 L15,8 L17.5,12 H5"/>'],
    "shield": ['<path d="M12,3 L20,6 V12 C20,16.5 16.5,20 12,21.5 C7.5,20 4,16.5 4,12 V6 Z"/>'],
    "search": ['<circle cx="10.5" cy="10.5" r="6.5"/>',
               '<path d="M15.5,15.5 L21,21"/>'],
    "funnel": ['<path d="M3,4 H21 L14,12.5 V19 L10,21 V12.5 Z"/>'],
    "queue": ['<rect x="3" y="4" width="18" height="4.5" rx="1.2"/>',
              '<rect x="3" y="10" width="18" height="4.5" rx="1.2"/>',
              '<rect x="3" y="16" width="18" height="4.5" rx="1.2"/>'],
    "workflow": ['<rect x="2.5" y="3" width="7" height="6" rx="1.5"/>',
                 '<rect x="14.5" y="9" width="7" height="6" rx="1.5"/>',
                 '<rect x="2.5" y="15" width="7" height="6" rx="1.5"/>',
                 '<path d="M9.5,6 H12 V12 H14.5 M12,12 V18 H9.5"/>'],
}


# Width of each printable ASCII character (U+0020-U+007E) as a fraction of font-size.
# Measured in Chrome with Hiragino Sans; each value is the widest of weights 400, 500, and 600.
_ASCII_WIDTHS = [
    0.33, 0.34, 0.41, 0.72, 0.71, 0.94, 0.86, 0.23, 0.41, 0.41, 0.38, 0.69, 0.27, 0.41, 0.27, 0.52,
    0.71, 0.71, 0.71, 0.71, 0.71, 0.71, 0.71, 0.71, 0.71, 0.71, 0.27, 0.27, 0.54, 0.69, 0.54, 0.62,
    0.94, 0.81, 0.75, 0.79, 0.81, 0.69, 0.64, 0.79, 0.83, 0.29, 0.59, 0.78, 0.64, 0.99, 0.82, 0.84,
    0.71, 0.84, 0.77, 0.72, 0.71, 0.83, 0.78, 1.06, 0.81, 0.76, 0.71, 0.41, 0.52, 0.41, 0.59, 0.50,
    0.50, 0.63, 0.71, 0.63, 0.71, 0.64, 0.42, 0.69, 0.67, 0.27, 0.31, 0.65, 0.27, 1.01, 0.67, 0.67,
    0.71, 0.71, 0.49, 0.59, 0.43, 0.67, 0.62, 0.89, 0.62, 0.63, 0.54, 0.41, 0.42, 0.41, 0.61,
]


def text_width(s, size):
    """Estimated rendered width in px. ASCII uses the measured table above, full-width characters count as 1x,
    and anything else as 0.7x. Fonts differ by platform, so render() also measures the real widths."""
    w = 0.0
    for ch in s:
        o = ord(ch)
        if 0x20 <= o <= 0x7E:
            w += size * _ASCII_WIDTHS[o - 0x20]
        elif unicodedata.east_asian_width(ch) in ("F", "W", "A"):
            w += size
        else:
            w += size * 0.7
    return w


# Characters that must not start a line, and characters that must not end one (Japanese line-breaking rules).
_NO_LINE_START = set("、。，．,.・：；:;！？!?）」』】〕〉》ーぁぃぅぇぉっゃゅょゎァィゥェォッャュョヮヵヶ々")
_NO_LINE_END = set("（「『【〔〈《")


def _tokens(s):
    """Split text into units that are never broken: an ASCII word, a run of spaces, or one other character."""
    return re.findall(r"[ ]+|[\x21-\x7E]+|.", s)


# Particles after which a Japanese line usually breaks well (the end of a phrase).
_PARTICLES = set("はがをにでとのもへや")


def _is_hiragana(ch):
    return "\u3040" <= ch <= "\u309F"


def wrap(s, max_width, size=13):
    """Split s into lines that fit max_width (estimated with text_width). English breaks at spaces.
    Japanese breaks between characters, preferring a break after punctuation or after a particle that is
    followed by kanji, katakana, or ASCII (usually the end of a phrase), and never puts 、。」 etc. at the start
    of a line.
    A single unit wider than max_width is kept on its own line; the overflow check reports it."""
    toks = _tokens(s)
    lines, cur = [], []

    def width(ts):
        return text_width("".join(ts).strip(" "), size)

    def can_break(prev, nxt):
        return not (nxt[0] in _NO_LINE_START or prev[-1] in _NO_LINE_END)

    def good_break(prev, nxt):
        if nxt[0] == " " or prev[-1] == " " or prev[-1] in "、。，,・）」』】":
            return True
        return prev[-1] in _PARTICLES and not _is_hiragana(nxt[0])

    for t in toks:
        if not cur:
            if t.strip(" "):
                cur = [t]
            continue
        if width(cur + [t]) <= max_width:
            cur.append(t)
            continue
        # Choose where to break: the last good break that keeps the line at least half full, else the last allowed one.
        cand = cur + [t]
        best = None
        for i in range(len(cand) - 1, 0, -1):
            if width(cand[:i]) > max_width or not can_break(cand[i - 1], cand[i]):
                continue
            if best is None:
                best = i
            if good_break(cand[i - 1], cand[i]) and width(cand[:i]) >= max_width * 0.5:
                best = i
                break
        if best is None:
            best = len(cur)
        lines.append("".join(cand[:best]).strip(" "))
        cur = [x for x in cand[best:]]
        while cur and not cur[0].strip(" "):
            cur.pop(0)
    if cur:
        lines.append("".join(cur).strip(" "))
    return lines


def _mix(hex_color, other, t):
    """Blend hex_color toward other by t (0-1)."""
    a = [int(hex_color[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(other[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x + (y - x) * t):02X}" for x, y in zip(a, b))


def theme_colors(theme):
    """Expand a theme such as {"PRIMARY": "#7C3AED"} to every C role it affects. A missing light background
    (PRIMARY_BG, ORANGE_BG, GREEN_BG) or ORANGE_LINE is derived from its main color."""
    out = {}
    for k, v in (theme or {}).items():
        if not hasattr(C, k):
            raise ValueError(f"Unknown color role in theme: {k}")
        if not re.fullmatch(r"#[0-9A-Fa-f]{6}", v):
            raise ValueError(f"Theme colors must be #RRGGBB: {k}={v}")
        out[k] = v.upper()
    for main, bg in (("PRIMARY", "PRIMARY_BG"), ("ORANGE", "ORANGE_BG"), ("GREEN", "GREEN_BG")):
        if main in out and bg not in out:
            out[bg] = _mix(out[main], "#FFFFFF", 0.92)
    if "ORANGE" in out and "ORANGE_LINE" not in out:
        out["ORANGE_LINE"] = _mix(out["ORANGE"], "#FFFFFF", 0.45)
    return out


class Slide:
    def __init__(self, title, description, width=960, height=540, margin=24, pad=20, theme=None):
        """theme maps C role names to colors, for example {"PRIMARY": "#7C3AED", "GREEN": "#0F766E"}.
        The colors are swapped when the SVG is saved, so every part follows the theme."""
        self.W, self.H, self.M, self.PAD = width, height, margin, pad
        self.theme = theme_colors(theme)
        self.out = []
        self.warnings = []
        a = self.out.append
        a(f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
          f'viewBox="0 0 {width} {height}" font-family="{FONT}" role="img" aria-label="{escape(description)}">')
        a(f"<title>{escape(title)}</title>")
        a('<defs><filter id="sh" x="-10%" y="-10%" width="120%" height="130%">'
          '<feDropShadow dx="0" dy="3" stdDeviation="5" flood-color="#0F172A" flood-opacity="0.07"/></filter></defs>')
        a(f'<rect width="{width}" height="{height}" fill="{C.BG}"/>')

    # ---- basic elements ----
    def raw(self, svg):
        self.out.append(svg)

    def text(self, x, y, s, size=13, color=C.TEXT, weight=400, anchor="start", max_width=None, on_line=False):
        """With max_width, warns when the estimated width exceeds it, and render() checks the measured width.
        on_line=True marks text that is meant to sit on a line (it has its own background), so the check skips it."""
        extra = ""
        if max_width is not None:
            w = text_width(s, size)
            if w > max_width:
                self.warnings.append(f"Possible overflow: \"{s}\" estimated {w:.0f}px > allowed {max_width:.0f}px")
            extra += f' data-maxw="{max_width:.1f}"'
        if on_line:
            extra += ' data-online="1"'
        self.out.append(f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" font-weight="{weight}" '
                        f'fill="{color}" text-anchor="{anchor}"{extra}>{escape(s)}</text>')

    def paragraph(self, x, y, w, s, size=13, color=C.TEXT, weight=400, line_h=None, max_lines=None):
        """Text wrapped to width w with wrap(). y is the first baseline. Returns the baseline of the last line.
        Warns when the text needs more than max_lines lines."""
        line_h = line_h or round(size * 1.5)
        lines = wrap(s, w, size)
        if max_lines is not None and len(lines) > max_lines:
            self.warnings.append(f"Too many lines: \"{s}\" needs {len(lines)} lines > {max_lines}")
        for i, ln in enumerate(lines):
            self.text(x, y + i * line_h, ln, size, color, weight, max_width=w)
        return y + (len(lines) - 1) * line_h

    def _desc(self, desc, w, size=12, max_lines=2):
        """Description given as a list of lines, or as a string that is wrapped to w."""
        if isinstance(desc, str):
            lines = wrap(desc, w, size)
            if len(lines) > max_lines:
                self.warnings.append(f"Too many lines: \"{desc}\" needs {len(lines)} lines > {max_lines}")
            return lines
        return list(desc)

    def card(self, x, y, w, h, border=C.LINE, fill=C.CARD):
        """Card with 12px corners and a shadow. The border keeps it distinct where shadows are not rendered."""
        self.out.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="12" fill="{fill}" '
                        f'stroke="{border}" stroke-width="1" filter="url(#sh)" data-part="box"/>')

    def line(self, x1, y1, x2, y2, color=C.LINE, width=1):
        self.out.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{color}" stroke-width="{width}"/>')

    def arrow(self, x1, x2, y):
        """Right-pointing arrow. Drawn as one path for line and head, without <marker>."""
        self.out.append(f'<path d="M{x1:.1f},{y:.1f} H{x2:.1f} M{x2-6:.1f},{y-6:.1f} L{x2:.1f},{y:.1f} L{x2-6:.1f},{y+6:.1f}" '
                        f'stroke="{C.ARROW}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" fill="none" data-part="arrow"/>')

    def arrow_down(self, x, y1, y2):
        self.out.append(f'<path d="M{x:.1f},{y1:.1f} V{y2:.1f} M{x-6:.1f},{y2-6:.1f} L{x:.1f},{y2:.1f} L{x+6:.1f},{y2-6:.1f}" '
                        f'stroke="{C.ARROW}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" fill="none" data-part="arrow"/>')

    def pill(self, x, y, label, fill=C.PRIMARY, color="#FFFFFF", border=None, h=22, size=12, w=None):
        """Number or category badge. Without w, the width follows the text. Returns the badge width."""
        if w is None:
            w = round(text_width(label, size) + 24)
        s = f' stroke="{border}" stroke-width="1"' if border else ""
        self.out.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w}" height="{h}" rx="{h / 2}" fill="{fill}"{s} data-part="box"/>')
        self.text(x + w / 2, y + h / 2 + size * 0.36, label, size, color, 600, "middle")
        return w

    def dot(self, x, y, color, r=3.5):
        self.out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="{color}"/>')

    def numbered(self, cx, cy, n, r=12, fill=C.PRIMARY):
        self.out.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r}" fill="{fill}"/>')
        self.text(cx, cy + 5, str(n), 13, "#FFFFFF", 600, "middle")

    def icon(self, name, x, y, size=22, color=C.SUB):
        """Icon (a key of ICONS). (x, y) is the top left. The stroke looks 1.75px at any size."""
        k = size / 24
        body = "".join(ICONS[name]).replace("CUR", color)
        self.out.append(f'<g transform="translate({x:.1f},{y:.1f}) scale({k:.4f})" fill="none" stroke="{color}" '
                        f'stroke-width="{1.75 / k:.2f}" stroke-linecap="round" stroke-linejoin="round">{body}</g>')

    def connector(self, x1, y1, x2, y2, color=C.ARROW, label=None):
        """Arrow in any direction (head at the end point). label is written small above the midpoint."""
        import math
        if math.hypot(x2 - x1, y2 - y1) < 28:
            self.warnings.append(f"Arrow too short: ({x1:.0f},{y1:.0f})->({x2:.0f},{y2:.0f}) is "
                                 f"{math.hypot(x2 - x1, y2 - y1):.0f}px. Make it at least 28px")
        ang = math.atan2(y2 - y1, x2 - x1)
        hx1 = x2 - 7 * math.cos(ang - 0.6)
        hy1 = y2 - 7 * math.sin(ang - 0.6)
        hx2 = x2 - 7 * math.cos(ang + 0.6)
        hy2 = y2 - 7 * math.sin(ang + 0.6)
        self.out.append(f'<path d="M{x1:.1f},{y1:.1f} L{x2:.1f},{y2:.1f} M{hx1:.1f},{hy1:.1f} L{x2:.1f},{y2:.1f} L{hx2:.1f},{hy2:.1f}" '
                        f'stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" fill="none" data-part="arrow"/>')
        if label:
            self.text((x1 + x2) / 2, (y1 + y2) / 2 - 8, label, 12, C.SUB, 400, "middle")

    def titled(self, x, y, icon, title, size=15, color=C.TEXT, icon_color=C.SUB, max_width=None):
        """Heading with an icon. y is the text baseline."""
        self.icon(icon, x, y - size + 1 - (22 - size) / 2, 22, icon_color)
        self.text(x + 30, y, title, size, color, 600, max_width=None if max_width is None else max_width - 30)

    # ---- layout ----
    def columns(self, n, gap=12, left=None, right=None):
        """Split the area inside the side margins into n columns. Returns (width, x of each column)."""
        left = self.M if left is None else left
        right = self.W - self.M if right is None else right
        w = (right - left - gap * (n - 1)) / n
        return w, [left + i * (w + gap) for i in range(n)]

    # ---- composite parts ----
    def header(self, title, meta=None, y=42):
        """Slide heading (20px, 600) and note at top right (12px). The heading states the conclusion."""
        self.text(self.M, y, title, 20, C.TEXT, 600, max_width=self.W - 2 * self.M - (220 if meta else 0))
        if meta:
            self.text(self.W - self.M, y, meta, 12, C.SUB, 400, "end")

    def section(self, y, title):
        """Row heading (15px, 600)."""
        self.text(self.M, y, title, 15, C.TEXT, 600, max_width=self.W - 2 * self.M)

    def stat(self, x, y, w, label, value, color=C.TEXT, h=58, icon=None):
        """Label and value pair. Value is 16px, 500. With icon, an icon is placed on the right."""
        self.card(x, y, w, h)
        room = w - 2 * self.PAD - (30 if icon else 0)
        self.text(x + self.PAD, y + 22, label, 12, C.SUB, max_width=room)
        self.text(x + self.PAD, y + 45, value, 16, color, 500, max_width=room)
        if icon:
            self.icon(icon, x + w - self.PAD - 22, y + (h - 22) / 2, 22, color if color != C.TEXT else C.SUB)

    def stats(self, y, items, gap=12):
        """stat cards in one row. items = [(label, value, color) or (label, value, color, icon), ...]"""
        w, xs = self.columns(len(items), gap)
        for x, item in zip(xs, items):
            label, value, color = item[:3]
            self.stat(x, y, w, label, value, color, icon=item[3] if len(item) > 3 else None)

    def ratio(self, x, y, w, label, value, value_color, part_label, fraction,
              fill=C.GREEN, track=C.ORANGE_BG, h=58):
        """Card showing a total and the share of a part as one bar.
        Total on the left; the part's label and the bar on the right. The bar fill is fraction (0-1)."""
        self.card(x, y, w, h)
        self.text(x + self.PAD, y + 22, label, 12, C.SUB)
        self.text(x + self.PAD, y + 45, value, 16, value_color, 500)
        left = x + self.PAD + max(text_width(value, 16), text_width(label, 12)) + 24
        right = x + w - self.PAD
        self.text(right, y + 22, part_label, 12, C.SUB, 400, "end", max_width=right - left)
        bw = right - left
        self.raw(f'<rect x="{left:.1f}" y="{y + 33:.1f}" width="{bw:.1f}" height="10" rx="5" fill="{track}"/>')
        self.raw(f'<rect x="{left:.1f}" y="{y + 33:.1f}" width="{bw * fraction:.1f}" height="10" rx="5" fill="{fill}"/>')

    def node(self, x, y, w, h, icon, title, sub=(), accent=None):
        """Diagram element (person, system, data, etc.). Icon on top, then name and description, centered."""
        color = accent or C.TEXT
        self.card(x, y, w, h, accent or C.LINE)
        self.icon(icon, x + w / 2 - 12, y + 14, 24, accent or C.SUB)
        self.text(x + w / 2, y + 58, title, 13, color, 600, "middle", max_width=w - 16)
        for j, s_ in enumerate(self._desc(sub, w - 16)):
            self.text(x + w / 2, y + 78 + j * 17, s_, 12, C.SUB, 400, "middle", max_width=w - 16)

    def zone(self, x, y, w, h, label):
        """Frame marking an owner or environment (light fill, dashed). label goes at top left. Put nodes inside."""
        self.raw(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="14" fill="#F1F5F9" '
                 f'stroke="#CBD5E1" stroke-width="1" stroke-dasharray="4 4" data-part="zone"/>')
        self.text(x + 14, y + 19, label, 12, C.SUB, 600, max_width=w - 28)

    def span(self, x1, x2, y, label, color=C.SUB):
        """Bracket over x1-x2 with a label above, for ranges such as "before the email is sent"."""
        self.raw(f'<path d="M{x1:.1f},{y + 6:.1f} V{y:.1f} H{x2:.1f} V{y + 6:.1f}" stroke="{color}" stroke-width="1.5" '
                 f'fill="none" stroke-linecap="round" stroke-linejoin="round"/>')
        self.text((x1 + x2) / 2, y - 7, label, 12, color, 500, "middle", max_width=x2 - x1)

    def timeline(self, y, items, gap=16, left=None, right=None):
        """Events in time order at equal spacing (spacing is not proportional to time).
        items = [(time, heading, [description...], accent or None), ...]. y is the axis position."""
        w, xs = self.columns(len(items), gap, left, right)
        x0 = xs[0]
        x1 = xs[-1] + w
        self.line(x0, y, x1, y, C.LINE, 2)
        for x, (t, title, desc, accent) in zip(xs, items):
            color = accent or C.TEXT
            self.dot(x + 6, y, accent or C.PRIMARY, 5)
            self.text(x, y - 14, t, 14, color, 600, max_width=w)
            self.text(x, y + 28, title, 13, color, 600, max_width=w)
            for j, d in enumerate(self._desc(desc, w)):
                self.text(x, y + 48 + j * 18, d, 12, C.SUB, max_width=w)
        return w, xs

    # ---- decision diagrams ----
    def box(self, x, y, w, h, title, sub=None, fill=C.CARD, border=C.LINE, color=C.TEXT, rx=10, size=13,
            icon=None):
        """Process step in a decision diagram (rectangle without shadow). Text is centered.
        Without sub, a title wider than the box is wrapped to two lines.
        With icon, the icon sits left of the text and the pair is centered together."""
        self.raw(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx}" fill="{fill}" '
                 f'stroke="{border}" stroke-width="1.2" data-part="box"/>')
        if icon:
            room = w - 16 - 30
            tw = min(room, max(text_width(title, size), text_width(sub, 12) if sub else 0))
            gx = x + (w - 30 - tw) / 2
            self.icon(icon, gx, y + (h - 22) / 2, 22, color if color != C.TEXT else C.SUB)
            if sub:
                self.text(gx + 30, y + h / 2 - 3, title, size, color, 600, max_width=room)
                self.text(gx + 30, y + h / 2 + 14, sub, 12, C.SUB, 400, max_width=room)
            else:
                self.text(gx + 30, y + h / 2 + size * 0.36, title, size, color, 600, max_width=room)
            return
        if sub:
            self.text(x + w / 2, y + h / 2 - 3, title, size, color, 600, "middle", max_width=w - 16)
            self.text(x + w / 2, y + h / 2 + 14, sub, 12, C.SUB, 400, "middle", max_width=w - 16)
        else:
            lines = wrap(title, w - 16, size)
            if len(lines) == 2:
                self.text(x + w / 2, y + h / 2 - 3, lines[0], size, color, 600, "middle", max_width=w - 16)
                self.text(x + w / 2, y + h / 2 + 14, lines[1], size, color, 600, "middle", max_width=w - 16)
            else:
                self.text(x + w / 2, y + h / 2 + size * 0.36, title, size, color, 600, "middle", max_width=w - 16)

    def decision(self, x, y, w, h, label):
        """Decision in a decision diagram ("Has a plan?", etc.). Light blue and rounded, unlike process boxes."""
        self.box(x, y, w, h, label, fill=C.PRIMARY_BG, border=C.PRIMARY, color=C.PRIMARY, rx=h / 2)

    def terminal(self, x, y, w, h, label, color=C.SUB, sub=None):
        """End of a decision diagram (ACK, NACK, done, etc.). color shows what the outcome means."""
        bg = {C.GREEN: C.GREEN_BG, C.ORANGE: C.ORANGE_BG, C.PRIMARY: C.PRIMARY_BG}.get(color, "#F1F5F9")
        self.box(x, y, w, h, label, sub=sub, fill=bg, border=color, color=color if color != C.SUB else C.TEXT,
                 rx=min(h / 2, 14))

    def elbow(self, pts, color=C.ARROW, width=2):
        """Polyline arrow (head at the end). pts = [(x, y), ...]. Right-angle bends read best.
        Warns when the last segment is under 28px, which squashes the head. Put labels beside the line, not on it."""
        import math
        d = "M" + " L".join(f"{px:.1f},{py:.1f}" for px, py in pts)
        (ax, ay), (bx, by) = pts[-2], pts[-1]
        if math.hypot(bx - ax, by - ay) < 28:
            self.warnings.append(f"Arrow too short: ({ax:.0f},{ay:.0f})->({bx:.0f},{by:.0f}) is "
                                 f"{math.hypot(bx - ax, by - ay):.0f}px. Make it at least 28px")
        ang = math.atan2(by - ay, bx - ax)
        h1 = (bx - 7 * math.cos(ang - 0.6), by - 7 * math.sin(ang - 0.6))
        h2 = (bx - 7 * math.cos(ang + 0.6), by - 7 * math.sin(ang + 0.6))
        d += f" M{h1[0]:.1f},{h1[1]:.1f} L{bx:.1f},{by:.1f} L{h2[0]:.1f},{h2[1]:.1f}"
        self.raw(f'<path d="{d}" stroke="{color}" stroke-width="{width}" fill="none" '
                 f'stroke-linecap="round" stroke-linejoin="round" data-part="arrow"/>')

    def edge_label(self, x, y, label, color=C.SUB, bg=C.BG):
        """Label for an arrow ("Yes", "No", etc.) with a background fill so it does not sit on the line. y is the center."""
        w = text_width(label, 12) + 10
        self.raw(f'<rect x="{x - w / 2:.1f}" y="{y - 9:.1f}" width="{w:.1f}" height="18" rx="4" fill="{bg}"/>')
        self.text(x, y + 4.3, label, 12, color, 500, "middle", on_line=True)

    # ---- schematics, axes, ranges ----
    def sketch(self, x, y, w, h, xlabels=(), ylabel=None, note="Schematic (not actual values)"):
        """Frame for a schematic that explains a shape. Draw lines and areas on the returned Sketch in 0-1 coordinates.
        It is not a chart of real data, so note is always shown."""
        self.line(x, y, x, y + h, C.ARROW, 1.2)
        self.line(x, y + h, x + w, y + h, C.ARROW, 1.2)
        if ylabel:
            self.text(x + 6, y + 4, ylabel, 12, C.SUB)
        if note:
            self.text(x + w, y - 8, note, 12, C.SUB, 400, "end")
        n = len(xlabels)
        for i, lb in enumerate(xlabels):
            if not lb:
                continue
            fx = 0 if n == 1 else i / (n - 1)
            anchor = "start" if i == 0 else ("end" if i == n - 1 else "middle")
            self.text(x + fx * w, y + h + 18, lb, 12, C.SUB, 400, anchor)
        return Sketch(self, x, y, w, h)

    def scale(self, x, w, v0, v1):
        """Return a function mapping v0-v1 to x-(x+w) (for time-proportional axes, etc.)."""
        return lambda v: x + (v - v0) / (v1 - v0) * w

    def band(self, x1, x2, y, h, color, label=None, label_color=None):
        """Band showing a time window or range. color is the band color. label goes to the right of the band."""
        bg = {C.GREEN: C.GREEN_BG, C.ORANGE: C.ORANGE_BG, C.PRIMARY: C.PRIMARY_BG}.get(color, "#F1F5F9")
        self.raw(f'<rect x="{x1:.1f}" y="{y:.1f}" width="{max(x2 - x1, 4):.1f}" height="{h}" rx="{min(h / 2, 5)}" '
                 f'fill="{bg}" stroke="{color}" stroke-width="1.2"/>')
        if label:
            self.text(x2 + 8, y + h / 2 + 4.3, label, 12, label_color or C.SUB, 500)

    def range_bar(self, x, y, w, label, lo, hi, vmax, value, color=C.PRIMARY, label_w=150, value_w=96):
        """Horizontal bar from minimum to maximum. y is the row center. Use a charting library for precise comparisons."""
        self.text(x, y + 4.5, label, 12.5, C.TEXT, 400, max_width=label_w - 8)
        tx, tw = x + label_w, w - label_w - value_w
        self.raw(f'<rect x="{tx:.1f}" y="{y - 4:.1f}" width="{tw:.1f}" height="8" rx="4" fill="{C.LINE}"/>')
        x1, x2 = tx + lo / vmax * tw, tx + hi / vmax * tw
        self.raw(f'<rect x="{x1:.1f}" y="{y - 4:.1f}" width="{max(x2 - x1, 6):.1f}" height="8" rx="4" fill="{color}"/>')
        self.text(x + w, y + 4.5, value, 12.5, color if color != C.PRIMARY else C.TEXT, 500, "end")

    def chain(self, y, items, h=104, gap=44):
        """Nodes in one row joined by arrows. items = [(icon, name, [description...], accent or None), ...]"""
        w, xs = self.columns(len(items), gap)
        for i, (x, (icon, title, sub, accent)) in enumerate(zip(xs, items)):
            self.node(x, y, w, h, icon, title, sub, accent)
            if i < len(items) - 1:
                self.connector(x + w + 6, y + h / 2, x + w + gap - 6, y + h / 2)
        return w, xs

    def flow(self, y, items, h=84, gap=28, pad=16):
        """Boxes in a row joined by arrows.
        items = [(heading, [description line 1, line 2], accent or None), ...]
        A box with an accent gets its border and heading in that color."""
        w, xs = self.columns(len(items), gap)
        for i, (x, (title, desc, accent)) in enumerate(zip(xs, items)):
            self.card(x, y, w, h, accent or C.LINE)
            self.text(x + pad, y + 28, title, 14, accent or C.TEXT, 600, max_width=w - 2 * pad)
            for j, d in enumerate(self._desc(desc, w - 2 * pad)):
                self.text(x + pad, y + 51 + j * 18, d, 12, C.SUB, max_width=w - 2 * pad)
            if i < len(items) - 1:
                self.arrow(x + w + gap / 2 - 7, x + w + gap / 2 + 7, y + h / 2)
        return w, xs

    def bullets(self, x, y, w, items, size=13, step=24):
        """Bullet list. y is the baseline of the first line."""
        for j, item in enumerate(items):
            yy = y + j * step
            self.dot(x + 3, yy - size * 0.35, C.ARROW, 2.5)
            self.text(x + 12, yy, item, size, C.TEXT, max_width=w - 12)

    def status(self, x, y, label, color):
        """Dot and status label (green for done, gray for not started, orange for in progress)."""
        self.dot(x + 4, y - 4, color)
        self.text(x + 14, y, label, 12, color, 500)

    def table(self, x, y, w, headers, col_x, rows, highlight=(), head_h=30, row_h=31, row_icons=None):
        """Table. col_x is the left edge of each column (offset from the table's left edge).
        A cell is a string or (string, color, weight). highlight lists rows with a light blue background.
        row_icons gives one entry per row: an icon name, (icon name, color), or None. The icon (18px) goes at the
        start of the first column and the first cell moves right to make room."""
        n = len(rows)
        self.card(x, y, w, head_h + row_h * n)
        self.raw(f'<path d="M{x + 1:.1f},{y + head_h:.1f} V{y + 12:.1f} A11,11 0 0 1 {x + 12:.1f},{y + 1:.1f} '
                 f'H{x + w - 12:.1f} A11,11 0 0 1 {x + w - 1:.1f},{y + 12:.1f} V{y + head_h:.1f} Z" fill="#F1F5F9"/>')
        bounds = list(col_x) + [w]
        for k, hd in enumerate(headers):
            self.text(x + col_x[k], y + head_h / 2 + 4.5, hd, 12, C.SUB, 600)
        for i, row in enumerate(rows):
            ry = y + head_h + i * row_h
            if i in highlight:
                bottom = 11 if i == n - 1 else 0
                self.raw(f'<rect x="{x + 1:.1f}" y="{ry:.1f}" width="{w - 2:.1f}" height="{row_h - bottom}" fill="{C.PRIMARY_BG}"/>')
            self.line(x, ry, x + w, ry)
            shift = 0
            if row_icons and row_icons[i]:
                name, icolor = (row_icons[i], C.SUB) if isinstance(row_icons[i], str) else row_icons[i]
                self.icon(name, x + col_x[0], ry + (row_h - 18) / 2, 18, icolor)
                shift = 26
            for k, cell in enumerate(row):
                s, color, weight = (cell, C.TEXT, 400) if isinstance(cell, str) else cell
                dx = shift if k == 0 else 0
                self.text(x + col_x[k] + dx, ry + row_h / 2 + 5, s, 12.5 if k else 13, color, weight,
                          max_width=bounds[k + 1] - col_x[k] - dx - 12)

    def steps(self, x, y, items, step=50):
        """Numbered steps stacked vertically. items = [(heading, description), ...]. y is the center of the first circle."""
        for i, (title, desc) in enumerate(items):
            cy = y + i * step
            self.numbered(x + 12, cy, i + 1)
            self.text(x + 34, cy - 1, title, 14, C.TEXT, 600)
            self.text(x + 34, cy + 18, desc, 12, C.SUB)
            if i < len(items) - 1:
                self.line(x + 12, cy + 16, x + 12, cy + step - 16, C.LINE, 2)

    # ---- sequences, rules, action lists ----
    def sequence(self, y, actors, messages, step=30, head_h=44, left=None, right=None, numbered=True):
        """Sequence diagram. actors = [(key, name, sub or None, accent or None[, icon]), ...] are placed in equal columns
        with a dashed lifeline below each. messages = [(from_key, to_key, label, accent or None), ...] are drawn
        top to bottom, one row per step, with the label centered above the arrow on a background fill.
        With numbered=True, labels are prefixed "1. ", "2. ", and so on.
        Returns (x of each actor by key, y below the last message)."""
        n = len(actors)
        w, xs = self.columns(n, 12, left, right)
        cx = {a[0]: x + w / 2 for x, a in zip(xs, actors)}
        bottom = y + head_h + 24 + step * len(messages)
        for x, (key, name, sub, accent, *icon) in zip(xs, actors):
            self.box(x, y, w, head_h, name, sub=sub, color=accent or C.TEXT, border=accent or C.LINE,
                     icon=icon[0] if icon else None)
            self.raw(f'<path d="M{cx[key]:.1f},{y + head_h:.1f} V{bottom:.1f}" stroke="{C.LINE}" '
                     f'stroke-width="1.5" stroke-dasharray="4 4"/>')
        for i, (a, b, label, accent) in enumerate(messages):
            if a == b:
                raise ValueError(f"sequence(): message {i + 1} goes from {a!r} to itself")
            yy = y + head_h + 30 + i * step
            x1, x2 = cx[a], cx[b]
            d = 1 if x2 > x1 else -1
            color = accent or C.ARROW
            self.connector(x1 + 6 * d, yy, x2 - 6 * d, yy, color)
            text = f"{i + 1}. {label}" if numbered else label
            tw = text_width(text, 12)
            mid = (x1 + x2) / 2
            self.raw(f'<rect x="{mid - tw / 2 - 4:.1f}" y="{yy - 19:.1f}" width="{tw + 8:.1f}" height="15" rx="3" '
                     f'fill="{C.BG}"/>')
            self.text(mid, yy - 7, text, 12, accent or C.SUB, 500 if accent else 400, "middle",
                      max_width=self.W - 2 * self.M, on_line=True)
        return cx, bottom

    def rule_row(self, x, y, w, cond, result, cond_sub=None, result_sub=None, color=C.PRIMARY, label="Yes",
                 split=0.42, h=64, cond_icon=None, result_icon=None):
        """One "if this, then that" row: a card with the condition, an arrow with a label, and a card with the
        result in the accent color. split is the share of w given to the condition card. cond_icon and result_icon
        put an icon before each title. Returns y below the row."""
        gap = max(64, text_width(label, 12) + 40)
        cw = (w - gap) * split
        rw = w - gap - cw
        for cx_, cww, title, sub, accent, icon in [(x, cw, cond, cond_sub, None, cond_icon),
                                                   (x + cw + gap, rw, result, result_sub, color, result_icon)]:
            self.card(cx_, y, cww, h, accent or C.LINE)
            ty = y + (27 if sub else h / 2 + 5)
            if icon:
                self.titled(cx_ + self.PAD, ty, icon, title, 14, accent or C.TEXT, accent or C.SUB,
                            max_width=cww - 2 * self.PAD)
            else:
                self.text(cx_ + self.PAD, ty, title, 14, accent or C.TEXT, 600, max_width=cww - 2 * self.PAD)
            if sub:
                self.text(cx_ + self.PAD, y + 48, sub, 12, C.SUB, max_width=cww - 2 * self.PAD)
        self.connector(x + cw + 8, y + h / 2, x + cw + gap - 8, y + h / 2, label=label)
        return y + h

    def action_list(self, y, items, x=None, w=None, h=46, gap=6, title_w=None):
        """Rows of follow-up actions: title, description, and status.
        items = [(title, description, status, status_color), ...]. title_w is the width of the title column
        (by default the widest title plus 40px). Returns y below the last row."""
        x = self.M if x is None else x
        w = self.W - 2 * self.M if w is None else w
        if title_w is None:
            title_w = max(text_width(t, 14) for t, *_ in items) + 40 + self.PAD
        status_w = max(text_width(st, 12) for _, _, st, _ in items) + 14 + self.PAD
        for i, (title, desc, st, color) in enumerate(items):
            ry = y + i * (h + gap)
            self.card(x, ry, w, h)
            self.text(x + self.PAD, ry + h / 2 + 5, title, 14, C.TEXT, 600, max_width=title_w - self.PAD - 12)
            self.text(x + title_w, ry + h / 2 + 5, desc, 12.5, C.SUB,
                      max_width=w - title_w - status_w - 16)
            self.status(x + w - status_w, ry + h / 2 + 5, st, color)
        return y + len(items) * (h + gap) - gap

    # ---- swimlanes, before/after, trees, roadmaps ----
    def swimlane(self, y, lanes, steps, edges=None, cols=None, lane_h=88, label_w=None, gap=72, box_h=48):
        """Swimlane diagram. lanes = [(key, name), ...] are horizontal bands, one per owner.
        steps = [(lane_key, col, title, accent or None), ...] place a box in a lane at column col (0-based).
        edges = [(i, j, label or None), ...] join steps by index; by default each step joins the next.
        label_w defaults to the widest lane name plus 40px. Returns y below the last lane."""
        cols = cols or max(c for _, c, _, _ in steps) + 1
        if label_w is None:
            label_w = max(text_width(name, 13) for _, name in lanes) + 40
        x0 = self.M + label_w
        col_w = (self.W - self.M - x0) / cols
        bw = col_w - gap
        row = {key: i for i, (key, _) in enumerate(lanes)}
        for i, (key, name) in enumerate(lanes):
            ly = y + i * lane_h
            fill = "#F1F5F9" if i % 2 == 0 else C.BG
            self.raw(f'<rect x="{self.M:.1f}" y="{ly:.1f}" width="{self.W - 2 * self.M:.1f}" height="{lane_h}" '
                     f'fill="{fill}"/>')
            self.text(self.M + 14, ly + lane_h / 2 + 5, name, 13, C.TEXT, 600, max_width=label_w - 24)
        self.line(x0, y, x0, y + len(lanes) * lane_h, C.LINE, 1)
        boxes = []
        for lane, col, title, accent in steps:
            bx = x0 + col * col_w + gap / 2
            by = y + row[lane] * lane_h + (lane_h - box_h) / 2
            self.box(bx, by, bw, box_h, title, color=accent or C.TEXT, border=accent or C.LINE)
            boxes.append((bx, by))
        if edges is None:
            edges = [(i, i + 1, None) for i in range(len(steps) - 1)]
        for i, j, label in edges:
            (ax, ay), (bx, by) = boxes[i], boxes[j]
            ca, cb = steps[i][1], steps[j][1]
            if ay == by:
                d = 1 if bx > ax else -1
                x1, x2 = (ax + bw, bx) if d > 0 else (ax, bx + bw)
                self.connector(x1 + 6 * d, ay + box_h / 2, x2 - 6 * d, by + box_h / 2)
                if label:
                    self.edge_label((x1 + x2) / 2, ay + box_h / 2 - 16, label)
            elif ca == cb:
                d = 1 if by > ay else -1
                y1, y2 = (ay + box_h, by) if d > 0 else (ay, by + box_h)
                self.elbow([(ax + bw / 2, y1 + 4 * d), (bx + bw / 2, y2 - 4 * d)])
                if label:
                    self.edge_label(ax + bw / 2 + 8 + text_width(label, 12) / 2, (y1 + y2) / 2, label)
            else:
                d = 1 if bx > ax else -1
                sx = ax + bw if d > 0 else ax
                ex = bx if d > 0 else bx + bw
                mx = (sx + ex) / 2
                self.elbow([(sx + 4 * d, ay + box_h / 2), (mx, ay + box_h / 2), (mx, by + box_h / 2),
                            (ex - 6 * d, by + box_h / 2)])
                if label:
                    self.edge_label(mx, (ay + by + box_h) / 2, label)
        return y + len(lanes) * lane_h

    def before_after(self, y, before, after, titles=("Before", "After"), h=None, gap=64, step=26, icons=None):
        """Two cards side by side with an arrow between them. before and after are lists of lines; a line given as
        (text, True) is a changed line and is colored (orange before, green after). icons = (before icon, after
        icon) puts an icon before each title, in the card's accent color. Returns y below the cards."""
        w = (self.W - 2 * self.M - gap) / 2
        n = max(len(before), len(after))
        h = h or 56 + n * step
        for k, (x, title, items, color) in enumerate([(self.M, titles[0], before, C.ORANGE),
                                                       (self.M + w + gap, titles[1], after, C.GREEN)]):
            self.card(x, y, w, h)
            if icons and icons[k]:
                self.titled(x + self.PAD, y + 30, icons[k], title, 15, C.TEXT, color, max_width=w - 2 * self.PAD)
            else:
                self.text(x + self.PAD, y + 30, title, 15, C.TEXT, 600, max_width=w - 2 * self.PAD)
            for i, item in enumerate(items):
                text, changed = (item, False) if isinstance(item, str) else item
                yy = y + 60 + i * step
                self.dot(x + self.PAD + 3, yy - 4.5, color if changed else C.ARROW, 3 if changed else 2.5)
                self.text(x + self.PAD + 14, yy, text, 13, color if changed else C.TEXT, 500 if changed else 400,
                          max_width=w - 2 * self.PAD - 14)
        self.connector(self.M + w + 14, y + h / 2, self.M + w + gap - 14, y + h / 2)
        return y + h

    def tree(self, y, root, box_w=None, box_h=52, level_gap=40, gap=16, left=None, right=None):
        """Hierarchy such as an org chart. root = (title, sub or None, [children...], accent or None[, icon]),
        where each child has the same shape. Leaves are spread evenly; a parent is centered over its children.
        Returns y below the deepest level."""
        left = self.M if left is None else left
        right = self.W - self.M if right is None else right

        def leaves(nd):
            return 1 if not nd[2] else sum(leaves(c) for c in nd[2])

        def depth(nd):
            return 1 + max((depth(c) for c in nd[2]), default=0)

        n = leaves(root)
        slot = (right - left) / n
        bw = box_w or min(180, slot - gap)
        if bw > slot - gap:
            self.warnings.append(f"tree(): boxes of {bw:.0f}px do not fit {n} leaves in {right - left:.0f}px")

        def place(nd, lvl, first):
            k = leaves(nd)
            cx = left + (first + k / 2) * slot
            by = y + lvl * (box_h + level_gap)
            title, sub, kids, accent, *icon = nd
            self.box(cx - bw / 2, by, bw, box_h, title, sub=sub, color=accent or C.TEXT, border=accent or C.LINE,
                     icon=icon[0] if icon else None)
            if kids:
                mid = by + box_h + level_gap / 2
                xs, f = [], first
                for c in kids:
                    xs.append(place(c, lvl + 1, f))
                    f += leaves(c)
                d = (f"M{cx:.1f},{by + box_h:.1f} V{mid:.1f} M{min(xs):.1f},{mid:.1f} H{max(xs):.1f} " +
                     " ".join(f"M{x:.1f},{mid:.1f} V{mid + level_gap / 2:.1f}" for x in xs))
                self.raw(f'<path d="{d}" stroke="{C.ARROW}" stroke-width="1.5" fill="none" data-part="line"/>')
            return cx

        place(root, 0, 0)
        return y + depth(root) * (box_h + level_gap) - level_gap

    def roadmap(self, y, periods, rows, label_w=150, row_h=40, bar_h=24):
        """Roadmap. periods = ["Q1", "Q2", ...] are equal columns. rows = [(name, [(start, end, label, color), ...]),
        ...] where start and end are in period units (0 is the start of the first period, 1.5 is the middle of the
        second). The label goes inside the bar when it fits, otherwise to its right. Returns y below the last row."""
        x0, x1 = self.M + label_w, self.W - self.M
        f = self.scale(x0, x1 - x0, 0, len(periods))
        top = y + 28
        for i, p in enumerate(periods):
            self.text((f(i) + f(i + 1)) / 2, y + 14, p, 12, C.SUB, 500, "middle", max_width=f(1) - f(0) - 8)
            self.line(f(i), top, f(i), top + len(rows) * row_h, C.LINE, 1)
        self.line(f(len(periods)), top, f(len(periods)), top + len(rows) * row_h, C.LINE, 1)
        for r, (name, bars) in enumerate(rows):
            ry = top + r * row_h
            self.line(self.M, ry, x1, ry, C.LINE, 1)
            self.text(self.M, ry + row_h / 2 + 5, name, 13, C.TEXT, 600, max_width=label_w - 12)
            for start, end, label, color in bars:
                bx1, bx2 = f(start) + 3, f(end) - 3
                bg = {C.GREEN: C.GREEN_BG, C.ORANGE: C.ORANGE_BG, C.PRIMARY: C.PRIMARY_BG}.get(color, "#F1F5F9")
                by = ry + (row_h - bar_h) / 2
                self.raw(f'<rect x="{bx1:.1f}" y="{by:.1f}" width="{bx2 - bx1:.1f}" height="{bar_h}" rx="6" '
                         f'fill="{bg}" stroke="{color}" stroke-width="1.2" data-part="box"/>')
                if text_width(label, 12) <= bx2 - bx1 - 16:
                    self.text(bx1 + 8, by + bar_h / 2 + 4.3, label, 12, color if color != C.SUB else C.TEXT, 500,
                              max_width=bx2 - bx1 - 16)
                else:
                    self.text(bx2 + 8, by + bar_h / 2 + 4.3, label, 12, C.SUB, 500, max_width=x1 - bx2 - 8)
        self.line(self.M, top + len(rows) * row_h, x1, top + len(rows) * row_h, C.LINE, 1)
        return top + len(rows) * row_h

    # ---- output ----
    def save(self, path, quiet=False):
        """Write the SVG and print the estimate-based warnings (unless quiet)."""
        svg = "\n".join(self.out + ["</svg>"]) + "\n"
        if self.theme:
            swap = {getattr(C, k).upper(): v for k, v in self.theme.items()}
            svg = re.sub(r"#[0-9A-Fa-f]{6}\b", lambda m: swap.get(m.group(0).upper(), m.group(0)), svg)
        with open(path, "w", encoding="utf-8") as f:
            f.write(svg)
        if not quiet:
            for w in self.warnings:
                print("WARN", w, file=sys.stderr)
        return path

    def render(self, png_path, svg_path=None, scale=2, check_layout=True):
        """Save the SVG (next to the PNG unless svg_path is given), render the PNG, and run check().
        Problems found by check() are printed and kept in self.issues."""
        svg_path = svg_path or os.path.splitext(png_path)[0] + ".svg"
        self.save(svg_path, quiet=True)
        png = render(svg_path, png_path, scale)
        self.issues = check(svg_path) if check_layout else []
        # The measured check replaces the estimated overflow warnings; other warnings are still printed.
        for w in self.warnings:
            if not (check_layout and w.startswith("Possible overflow")):
                print("WARN", w, file=sys.stderr)
        for i in self.issues:
            print("CHECK", i, file=sys.stderr)
        return png


class Sketch:
    """Schematic returned by Slide.sketch(). (0, 0) is bottom left, (1, 1) is top right."""

    def __init__(self, slide, x, y, w, h):
        self.s, self.x, self.y, self.w, self.h = slide, x, y, w, h

    def p(self, fx, fy):
        return self.x + fx * self.w, self.y + (1 - fy) * self.h

    def line(self, pts, color=C.PRIMARY, width=2.5, dash=False):
        d = "M" + " L".join("{:.1f},{:.1f}".format(*self.p(fx, fy)) for fx, fy in pts)
        da = ' stroke-dasharray="6 5"' if dash else ""
        self.s.raw(f'<path d="{d}" stroke="{color}" stroke-width="{width}" fill="none" '
                   f'stroke-linecap="round" stroke-linejoin="round"{da} data-part="line"/>')

    def area(self, pts, color, opacity=0.18):
        d = "M" + " L".join("{:.1f},{:.1f}".format(*self.p(fx, fy)) for fx, fy in pts) + " Z"
        self.s.raw(f'<path d="{d}" fill="{color}" fill-opacity="{opacity}" stroke="none" data-part="area"/>')

    def label(self, fx, fy, text, color=C.SUB, anchor="start", size=12, weight=500):
        px, py = self.p(fx, fy)
        self.s.text(px, py, text, size, color, weight, anchor)


def render(svg_path, png_path, scale=2):
    """Render to PNG with a headless Chrome-family browser. The size is read from the SVG width/height."""
    with open(svg_path, encoding="utf-8") as f:
        head = f.read(2000)
    w = int(float(re.search(r'width="([\d.]+)"', head).group(1)))
    h = int(float(re.search(r'height="([\d.]+)"', head).group(1)))
    svg_abs, png_abs = os.path.abspath(svg_path), os.path.abspath(png_path)
    if os.path.exists(png_abs):
        os.remove(png_abs)
    subprocess.run(_browser_cmd("--hide-scrollbars", f"--force-device-scale-factor={scale}", f"--window-size={w},{h}",
                                f"--screenshot={png_abs}", pathlib.Path(svg_abs).as_uri()),
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return png_abs


# Runs in the browser. Collects layout problems as strings into the element #out.
_CHECK_JS = r"""
document.fonts.ready.then(() => {
  const svg = document.querySelector('svg');
  const W = +svg.getAttribute('width'), H = +svg.getAttribute('height');
  const out = [];
  const r = b => ({x1: b.x, y1: b.y, x2: b.x + b.width, y2: b.y + b.height});
  const name = t => JSON.stringify(t.textContent.length > 40 ? t.textContent.slice(0, 40) + '…' : t.textContent);
  // Horizontal extent is measured. Vertical extent comes from the baseline and font size (0.85em above, 0.18em
  // below) because getBBox() height is the font's line height, which differs widely between fonts.
  const glyphs = t => {
    const bb = t.getBBox(), size = +t.getAttribute('font-size') || 13, base = t.y.baseVal[0].value;
    return {x1: bb.x, x2: bb.x + bb.width, y1: base - 0.85 * size, y2: base + 0.18 * size};
  };
  const texts = [...svg.querySelectorAll('text')].filter(t => t.textContent.trim()).map(t => ({t, b: glyphs(t)}));
  const boxes = [...svg.querySelectorAll('[data-part="box"]')].map(e => r(e.getBBox()));
  const arrows = [...svg.querySelectorAll('[data-part="arrow"]')];
  const lines = [...svg.querySelectorAll('[data-part="arrow"], [data-part="line"]')];
  const samples = el => { const n = el.getTotalLength(), p = []; for (let d = 0; d <= n; d += 2) p.push(el.getPointAtLength(d)); return p; };
  const inter = (a, b, m) => a.x1 + m < b.x2 && b.x1 + m < a.x2 && a.y1 + m < b.y2 && b.y1 + m < a.y2;
  const inside = (a, b) => a.x1 >= b.x1 && a.x2 <= b.x2 && a.y1 >= b.y1 && a.y2 <= b.y2;
  for (const {t, b} of texts) {
    const maxw = t.getAttribute('data-maxw');
    const w = t.getComputedTextLength();
    if (maxw !== null && w > +maxw + 0.5)
      out.push(`Overflow: ${name(t)} is ${w.toFixed(0)}px > allowed ${(+maxw).toFixed(0)}px`);
    if (b.x1 < 0 || b.y1 < 0 || b.x2 > W || b.y2 > H)
      out.push(`Outside the canvas: ${name(t)}`);
    for (const c of boxes) {
      if (inter(b, c, 0) && !inside(b, c))
        out.push(`Crosses the edge of a box: ${name(t)}`);
    }
  }
  for (let i = 0; i < texts.length; i++)
    for (let j = i + 1; j < texts.length; j++)
      if (inter(texts[i].b, texts[j].b, 1))
        out.push(`Overlapping text: ${name(texts[i].t)} and ${name(texts[j].t)}`);
  for (const a of lines) {
    const pts = samples(a);
    const what = a.getAttribute('data-part') === 'arrow' ? 'Arrow' : 'Line';
    for (const {t, b} of texts) {
      if (t.getAttribute('data-online')) continue;
      if (pts.some(p => p.x > b.x1 + 1 && p.x < b.x2 - 1 && p.y > b.y1 + 1 && p.y < b.y2 - 1))
        out.push(`${what} crosses text: ${name(t)}`);
      else if (pts.some(p => p.x > b.x1 - 2 && p.x < b.x2 + 2 && p.y > b.y1 - 2 && p.y < b.y2 + 2))
        out.push(`${what} touches text: ${name(t)}`);
    }
  }
  for (const a of svg.querySelectorAll('[data-part="area"]')) {
    for (const {t, b} of texts) {
      const probe = [[b.x1 + 1, b.y1 + 1], [b.x2 - 1, b.y1 + 1], [b.x1 + 1, b.y2 - 1], [b.x2 - 1, b.y2 - 1],
                     [(b.x1 + b.x2) / 2, (b.y1 + b.y2) / 2]];
      if (probe.some(([x, y]) => a.isPointInFill(new DOMPoint(x, y))))
        out.push(`Filled area covers text: ${name(t)}`);
    }
  }
  for (const a of arrows) {
    const pts = samples(a);
    for (const c of boxes) {
      if (pts.some(p => p.x > c.x1 + 3 && p.x < c.x2 - 3 && p.y > c.y1 + 3 && p.y < c.y2 - 3)
          && !pts.every(p => p.x >= c.x1 && p.x <= c.x2 && p.y >= c.y1 && p.y <= c.y2))
        out.push(`Arrow enters a box: the box at (${c.x1.toFixed(0)},${c.y1.toFixed(0)})`);
    }
  }
  document.getElementById('out').textContent = '@@CHECK@@' + JSON.stringify([...new Set(out)]) + '@@END@@';
});
"""


def check(svg_path):
    """Open the SVG in a headless Chrome-family browser and return layout problems found with the real fonts:
    text wider than its max_width, text outside the canvas or across the edge of a card or box, overlapping text,
    lines or arrows that cross or touch text, arrows that enter a box, and filled areas over text.
    An empty list means no problems were found."""
    with open(svg_path, encoding="utf-8") as f:
        svg = f.read()
    with tempfile.TemporaryDirectory() as d:
        page = os.path.join(d, "check.html")
        with open(page, "w", encoding="utf-8") as f:
            f.write('<!doctype html><meta charset="utf-8"><body style="margin:0">' + svg +
                    '<pre id="out"></pre><script>' + _CHECK_JS + "</script></body>")
        res = subprocess.run(_browser_cmd("--virtual-time-budget=5000", "--dump-dom", pathlib.Path(page).as_uri()),
                             check=True, capture_output=True, text=True, encoding="utf-8")
    m = re.search(r"@@CHECK@@(.*?)@@END@@", res.stdout, re.S)
    if not m:
        raise RuntimeError("check() got no result from the browser")
    import html
    import json
    return json.loads(html.unescape(m.group(1)))


def catalog(png_path):
    """Render all icons to a PNG. Check shapes with this after adding or changing an icon."""
    names = list(ICONS)
    cols = 7
    rows = (len(names) + cols - 1) // cols
    s = Slide("Icon catalog", "Catalog of svgparts icons", width=cols * 120 + 48, height=rows * 96 + 48)
    for i, name in enumerate(names):
        x = 24 + (i % cols) * 120
        y = 24 + (i // cols) * 96
        s.card(x + 4, y + 4, 112, 88)
        s.icon(name, x + 60 - 16, y + 18, 32, C.TEXT)
        s.text(x + 60, y + 76, name, 12, C.SUB, 400, "middle")
    svg = os.path.splitext(png_path)[0] + ".svg"
    s.save(svg)
    return render(svg, png_path)


if __name__ == "__main__":
    if len(sys.argv) == 4 and sys.argv[1] == "render":
        print(render(sys.argv[2], sys.argv[3]))
    elif len(sys.argv) == 3 and sys.argv[1] == "check":
        problems = check(sys.argv[2])
        for p in problems:
            print("CHECK", p)
        sys.exit(1 if problems else 0)
    elif len(sys.argv) == 3 and sys.argv[1] == "icons":
        print(catalog(sys.argv[2]))
    else:
        print("usage: svgparts.py render in.svg out.png | svgparts.py check in.svg | svgparts.py icons out.png",
              file=sys.stderr)
        sys.exit(2)
